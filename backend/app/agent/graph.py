"""LangGraph agent that drives the Log Interaction screen.

Flow:  START -> agent -> (tools -> agent)* -> END

The `agent` node is the Groq LLM with all tools bound. When it decides to call
one or more tools, `tools_condition` routes to the `ToolNode`, which executes the
tools (they patch the shared form state), then control returns to the agent to
produce a final natural-language reply.
"""
import datetime
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .llm import get_llm
from .state import AgentState
from .tools import ALL_TOOLS


def _system_message(form: dict) -> SystemMessage:
    today = datetime.date.today().isoformat()
    return SystemMessage(content=f"""You are the AI Assistant embedded in a pharmaceutical CRM \
"Log HCP Interaction" screen used by field sales representatives.

Today's date is {today}.

Your job is to control the interaction form on the left using your tools — the rep
must NEVER have to type into the form manually. Always act through tools:

- log_interaction   : populate the form from a natural-language description of a visit.
- edit_interaction  : change/correct specific fields the rep points out.
- summarize_notes   : condense raw or voice-note text into "Topics Discussed".
- suggest_followups : propose next-step actions when asked.
- search_hcp        : look up a Healthcare Professional in the CRM database.
- save_interaction  : persist the completed form to the database.

Guidelines:
- Resolve relative dates: "today" = {today}. Use ISO dates (YYYY-MM-DD) and 24h time (HH:MM).
- Sentiment must be exactly Positive, Neutral, or Negative.
- interaction_type is one of Meeting, Call, Email, Conference, Virtual, Other. Infer
  it from the channel described ("on a call"/"phone" -> Call, "met"/"visited" ->
  Meeting, "emailed" -> Email, "zoom"/"video" -> Virtual). Set it whenever the
  channel is stated, even if the form currently shows a different default.
- Write topics_discussed as an elaborated professional interaction note: 3-4
  bullet points (each line starting with "* ") that expand the stated topic into
  the discussion points a pharma rep would record (efficacy/benefits, clinical
  positioning, HCP questions/concerns). Keep it on-topic; avoid fabricated
  statistics or specific study names.
- For any field you cannot determine, OMIT it entirely. Never pass the string
  "null", "none" or empty values. List fields (attendees, materials_shared,
  samples_distributed) must be JSON arrays of strings.
- Call the appropriate tool(s) for the request; you may call several in one turn.
- After acting, reply in ONE or TWO short sentences summarizing what you changed,
  then add a brief, proactive offer to help with a relevant NEXT step — for
  example suggesting follow-up actions, capturing outcomes, or saving the
  interaction. E.g.: "Would you like me to suggest follow-up actions for this visit?"
- Do not invent facts the rep did not provide.

Current form state (JSON):
{json.dumps(form, ensure_ascii=False)}
""")


def _agent_node(state: AgentState) -> dict:
    """Call the tool-bound LLM with a fresh system prompt reflecting the latest form."""
    llm = get_llm(tools=ALL_TOOLS)
    messages = [_system_message(state.get("form", {}))] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", _agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))

    builder.add_edge(START, "agent")
    # If the LLM asked for tools, run them; otherwise finish.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()


# Compiled once and reused across requests.
GRAPH = build_graph()


def run_agent(message: str, form: dict, history: list) -> dict:
    """Run one turn of the agent.

    Returns dict with keys: reply, form_updates, suggestions, tool_calls.
    """
    lc_history = []
    for m in history:
        role = getattr(m, "role", None) or m.get("role")
        content = getattr(m, "content", None) or m.get("content", "")
        if role == "user":
            lc_history.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_history.append(AIMessage(content=content))

    initial_state = {
        "messages": lc_history + [HumanMessage(content=message)],
        "form": form or {},
        "form_updates": {},
        "suggestions": [],
    }

    result = GRAPH.invoke(initial_state, config={"recursion_limit": 12})

    # Final assistant text = last AIMessage with content and no tool calls.
    reply = ""
    for m in reversed(result["messages"]):
        if isinstance(m, AIMessage) and m.content and not getattr(m, "tool_calls", None):
            reply = m.content
            break
    if not reply:
        reply = "Done."

    # Collect the names of tools that were actually invoked this turn.
    tool_calls = []
    for m in result["messages"]:
        for tc in getattr(m, "tool_calls", None) or []:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name:
                tool_calls.append(name)

    return {
        "reply": reply,
        "form_updates": result.get("form_updates", {}),
        "suggestions": result.get("suggestions", []),
        "tool_calls": tool_calls,
    }

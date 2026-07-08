"""LangGraph tools the CRM agent can call.

There are SIX tools (the assignment requires a minimum of five). The two
mandatory ones are `log_interaction` and `edit_interaction`.

    1. log_interaction    -> populate the form from a natural-language description
    2. edit_interaction   -> change specific fields that are already filled
    3. summarize_notes    -> LLM-summarize voice/long notes into "Topics Discussed"
    4. suggest_followups  -> LLM-generate next-step recommendations
    5. search_hcp         -> look up a Healthcare Professional in the CRM database
    6. save_interaction   -> persist the current form to the database

Form-mutating tools return a `Command` that updates the shared graph state:
`form` (merged snapshot) and `form_updates` (the delta sent back to the UI).
"""
import json
import re
from typing import Annotated, List, Optional, Union

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from ..database import SessionLocal
from ..models import HCP, Interaction
from .llm import get_llm

# Fields that hold lists rather than plain strings.
LIST_FIELDS = {"attendees", "materials_shared", "samples_distributed"}

# List-typed params accept a JSON array OR a comma-separated string OR null, so
# that weaker models (e.g. gemma2-9b-it) that emit strings or the literal "null"
# still pass Groq's tool-schema validation. Values are cleaned in _delta().
ListParam = Optional[Union[List[str], str]]

# Strings the LLM uses to mean "empty" — must never end up in the form.
_NULLISH = {"", "null", "none", "n/a", "na", "undefined", "unknown"}

# Every form field the agent is allowed to write.
FORM_FIELDS = [
    "hcp_name", "interaction_type", "date", "time", "attendees",
    "topics_discussed", "materials_shared", "samples_distributed",
    "sentiment", "outcomes", "follow_up_actions",
]


def _is_nullish(value) -> bool:
    return isinstance(value, str) and value.strip().lower() in _NULLISH


def _to_list(value):
    """Coerce an array / comma-or-newline string / null into a clean list (or None)."""
    if value is None or _is_nullish(value):
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in re.split(r"[,\n;]+", value)]
    elif isinstance(value, (list, tuple)):
        parts = [str(p).strip() for p in value]
    else:
        return None
    parts = [p for p in parts if p and not _is_nullish(p)]
    return parts or None


def _delta(**kwargs) -> dict:
    """Build a clean field->value delta.

    Drops None and LLM "null"-ish placeholders, and normalizes list fields
    whether the model sent an array or a comma-separated string.
    """
    out = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        if key in LIST_FIELDS:
            cleaned = _to_list(value)
            if cleaned:
                out[key] = cleaned
        elif not _is_nullish(value):
            out[key] = value.strip() if isinstance(value, str) else value
    return out


def _form_command(delta: dict, tool_call_id: str, message: str) -> Command:
    """Return a Command that patches the form and records the change."""
    return Command(
        update={
            "form": delta,
            "form_updates": delta,
            "messages": [ToolMessage(content=message, tool_call_id=tool_call_id)],
        }
    )


# ---------------------------------------------------------------------------
# 1. LOG INTERACTION  (mandatory)
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: ListParam = None,
    topics_discussed: Optional[str] = None,
    materials_shared: ListParam = None,
    samples_distributed: ListParam = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Extract details from a natural-language description of an HCP interaction and
    populate the Log Interaction form.

    Infer as many fields as possible from the user's message. Rules:
    - `date` must be ISO format YYYY-MM-DD (resolve words like "today"/"yesterday").
    - `time` must be 24h HH:MM.
    - `sentiment` must be exactly one of: Positive, Neutral, Negative.
    - `interaction_type` must be one of: Meeting, Call, Email, Conference, Virtual, Other.
      Infer it from the channel the rep describes: "call"/"phone"/"spoke on the
      phone"/"rang" -> Call; "met"/"visited"/"in person" -> Meeting; "emailed" ->
      Email; "zoom"/"video"/"teams"/"webinar" -> Virtual; "conference"/"congress"/
      "booth" -> Conference. Always set it when the channel is stated, even to
      override the current value.
    - `topics_discussed` should be an elaborated, professional interaction note
      written as 3-4 bullet points (each line starting with "* ") that expand the
      stated topic(s) into the discussion points a pharmaceutical field rep would
      realistically record — e.g. the product's efficacy profile and patient
      benefits, its clinical positioning, and the HCP's questions or concerns on
      safety/tolerability. Keep it on-topic and professional; use general phrasing
      rather than fabricated statistics or specific study names.
      Example input "discussed Product Y efficacy" ->
        * Discussed Product Y's efficacy profile and its potential benefits for patients.
        * Reviewed clinical data highlighting Product Y's positioning versus alternatives.
        * Addressed the HCP's questions regarding Product Y's safety and tolerability.
    - `attendees`, `materials_shared`, `samples_distributed` are lists of strings.
    Only pass the fields you can actually determine from the message.
    """
    delta = _delta(
        hcp_name=hcp_name, interaction_type=interaction_type, date=date, time=time,
        attendees=attendees, topics_discussed=topics_discussed,
        materials_shared=materials_shared, samples_distributed=samples_distributed,
        sentiment=sentiment, outcomes=outcomes, follow_up_actions=follow_up_actions,
    )
    if not delta:
        return Command(update={"messages": [ToolMessage(
            content="No fields could be extracted from that message.",
            tool_call_id=tool_call_id)]})
    return _form_command(
        delta, tool_call_id,
        "Logged interaction fields: " + ", ".join(delta.keys()),
    )


# ---------------------------------------------------------------------------
# 2. EDIT INTERACTION  (mandatory)
# ---------------------------------------------------------------------------
@tool
def edit_interaction(
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: ListParam = None,
    topics_discussed: Optional[str] = None,
    materials_shared: ListParam = None,
    samples_distributed: ListParam = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Correct or change specific fields that are ALREADY on the form, leaving every
    other field untouched.

    Use this when the user says things like "actually the name was Dr. John" or
    "change the sentiment to negative". Pass ONLY the field(s) that should change.
    Same formatting rules as log_interaction (ISO date, HH:MM time, sentiment in
    Positive/Neutral/Negative).
    """
    delta = _delta(
        hcp_name=hcp_name, interaction_type=interaction_type, date=date, time=time,
        attendees=attendees, topics_discussed=topics_discussed,
        materials_shared=materials_shared, samples_distributed=samples_distributed,
        sentiment=sentiment, outcomes=outcomes, follow_up_actions=follow_up_actions,
    )
    if not delta:
        return Command(update={"messages": [ToolMessage(
            content="Nothing to edit — no target field was provided.",
            tool_call_id=tool_call_id)]})
    return _form_command(
        delta, tool_call_id,
        "Updated fields: " + ", ".join(delta.keys()),
    )


# ---------------------------------------------------------------------------
# 3. SUMMARIZE NOTES  (uses the LLM inside the tool)
# ---------------------------------------------------------------------------
@tool
def summarize_notes(
    raw_notes: str,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Summarize raw call notes or a voice-note transcript into concise, professional
    'Topics Discussed' bullet points and write them to the form.

    Pass the rep's raw dictation/notes as `raw_notes`.
    """
    llm = get_llm()
    prompt = (
        "You are a pharmaceutical CRM assistant. Summarize the field rep's raw notes "
        "below into 2-4 concise, professional bullet points capturing the key clinical "
        "and commercial discussion topics. Return ONLY the bullet points.\n\n"
        f"Notes:\n{raw_notes}"
    )
    summary = llm.invoke(prompt).content.strip()
    return _form_command(
        {"topics_discussed": summary}, tool_call_id,
        "Summarized the notes into Topics Discussed.",
    )


# ---------------------------------------------------------------------------
# 4. SUGGEST FOLLOW-UPS  (uses the LLM + reads current form state)
# ---------------------------------------------------------------------------
@tool
def suggest_followups(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Generate three short, actionable follow-up recommendations based on the
    interaction currently on the form (e.g. schedule a meeting, send a document,
    add the HCP to an advisory board). Use when the rep asks for next steps.
    """
    form = state.get("form", {})
    llm = get_llm(temperature=0.3)
    prompt = (
        "Based on this logged HCP interaction, suggest exactly THREE short, concrete "
        "follow-up actions for the sales rep. One per line, no numbering, no preamble.\n\n"
        f"Interaction JSON:\n{json.dumps(form, ensure_ascii=False)}"
    )
    text = llm.invoke(prompt).content
    suggestions = [
        line.strip("-•* ").strip()
        for line in text.splitlines()
        if line.strip()
    ][:3]
    return Command(
        update={
            "suggestions": suggestions,
            "form": {"ai_suggested_followups": suggestions},
            "form_updates": {"ai_suggested_followups": suggestions},
            "messages": [ToolMessage(
                content="Suggested follow-ups: " + " | ".join(suggestions),
                tool_call_id=tool_call_id)],
        }
    )


# ---------------------------------------------------------------------------
# 5. SEARCH HCP  (reads the database)
# ---------------------------------------------------------------------------
@tool
def search_hcp(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Search the CRM database for a Healthcare Professional by (partial) name.
    If exactly one HCP matches, it is set as the form's HCP Name. Otherwise the
    matches are returned so the rep can pick one.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(HCP)
            .filter(HCP.name.ilike(f"%{query}%"))
            .limit(5)
            .all()
        )
        matches = [
            {"name": r.name, "specialty": r.specialty, "institution": r.institution}
            for r in rows
        ]
    finally:
        db.close()

    if not matches:
        msg = f"No HCP found matching '{query}'."
        return Command(update={"messages": [ToolMessage(content=msg, tool_call_id=tool_call_id)]})

    if len(matches) == 1:
        name = matches[0]["name"]
        return _form_command(
            {"hcp_name": name}, tool_call_id,
            f"Matched HCP '{name}' ({matches[0]['specialty']}) and set it on the form.",
        )

    listing = "; ".join(f"{m['name']} ({m['specialty']})" for m in matches)
    return Command(update={"messages": [ToolMessage(
        content=f"Found {len(matches)} matching HCPs: {listing}",
        tool_call_id=tool_call_id)]})


# ---------------------------------------------------------------------------
# 6. SAVE INTERACTION  (writes the database)
# ---------------------------------------------------------------------------
@tool
def save_interaction(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Persist the current interaction form to the CRM database. Use when the rep
    says something like "save this" or "log it". Requires at least an HCP name.
    """
    form = state.get("form", {})
    if not form.get("hcp_name"):
        return Command(update={"messages": [ToolMessage(
            content="Cannot save yet — the HCP name is missing.",
            tool_call_id=tool_call_id)]})

    db = SessionLocal()
    try:
        record = Interaction(
            hcp_name=form.get("hcp_name"),
            interaction_type=form.get("interaction_type"),
            date=form.get("date"),
            time=form.get("time"),
            attendees=form.get("attendees") or [],
            topics_discussed=form.get("topics_discussed"),
            materials_shared=form.get("materials_shared") or [],
            samples_distributed=form.get("samples_distributed") or [],
            sentiment=form.get("sentiment"),
            outcomes=form.get("outcomes"),
            follow_up_actions=form.get("follow_up_actions"),
            ai_suggested_followups=form.get("ai_suggested_followups") or [],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        saved_id = record.id
    finally:
        db.close()

    return Command(update={"messages": [ToolMessage(
        content=f"Saved interaction #{saved_id} for {form.get('hcp_name')}.",
        tool_call_id=tool_call_id)]})


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    summarize_notes,
    suggest_followups,
    search_hcp,
    save_interaction,
]

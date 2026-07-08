"""LangGraph shared state definition."""
from typing import Annotated, Any, Dict, List

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer that shallow-merges dict updates from multiple tools in a turn."""
    return {**(left or {}), **(right or {})}


def extend_list(left: List[Any], right: List[Any]) -> List[Any]:
    """Reducer that concatenates list updates."""
    return (left or []) + (right or [])


class AgentState(TypedDict):
    # Conversation with the LLM (system/human/ai/tool messages).
    messages: Annotated[list, add_messages]
    # Full current form snapshot. Tools return only the delta; the reducer merges.
    form: Annotated[Dict[str, Any], merge_dicts]
    # Only the fields changed during THIS request — sent back to the frontend.
    form_updates: Annotated[Dict[str, Any], merge_dicts]
    # AI-suggested follow-ups produced this turn.
    suggestions: Annotated[List[str], extend_list] 

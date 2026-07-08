"""Pydantic request/response schemas."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat / agent
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str                     # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    # The frontend is the source of truth for the form; it sends the current
    # snapshot so tools like `edit_interaction` know what already exists.
    form: Dict[str, Any] = Field(default_factory=dict)
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    form_updates: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    tool_calls: List[str] = Field(default_factory=list)


class TranscribeRequest(BaseModel):
    # Base64-encoded audio (may be a data: URL). Recorded in the browser.
    audio_base64: str
    mime: str = "audio/webm"


class TranscribeResponse(BaseModel):
    text: str


# ---------------------------------------------------------------------------
# Interactions (CRUD)
# ---------------------------------------------------------------------------
class InteractionBase(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    topics_discussed: Optional[str] = None
    materials_shared: List[str] = Field(default_factory=list)
    samples_distributed: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: List[str] = Field(default_factory=list)


class InteractionCreate(InteractionBase):
    pass


class InteractionOut(InteractionBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# HCP
# ---------------------------------------------------------------------------
class HCPOut(BaseModel):
    id: int
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}

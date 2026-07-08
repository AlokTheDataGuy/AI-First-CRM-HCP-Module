"""Chat + voice-transcription endpoints (both AI-powered)."""
import base64
import os
import tempfile
import traceback

from fastapi import APIRouter
from groq import Groq

from ..agent.graph import run_agent
from ..config import get_settings
from ..schemas import ChatRequest, ChatResponse, TranscribeRequest, TranscribeResponse

router = APIRouter(prefix="/api", tags=["chat"])

# Map browser MIME types to file extensions Groq Whisper accepts.
_MIME_EXT = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
}


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    if not settings.groq_api_key:
        return ChatResponse(
            reply="⚠️ GROQ_API_KEY is not set on the server. Add it to backend/.env "
                  "(get a free key at https://console.groq.com/keys) and restart.",
        )

    try:
        result = run_agent(
            message=req.message,
            form=req.form,
            history=req.history,
        )
        return ChatResponse(**result)
    except Exception as exc:  # noqa: BLE001 - surface a friendly error to the UI
        traceback.print_exc()
        return ChatResponse(reply=f"Sorry, the AI agent hit an error: {exc}")


@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe(req: TranscribeRequest) -> TranscribeResponse:
    """Transcribe a recorded voice note using Groq's Whisper model.

    Accepts base64 audio (optionally a data: URL) captured by the browser's
    MediaRecorder, and returns the transcript text.
    """
    settings = get_settings()
    if not settings.groq_api_key:
        return TranscribeResponse(text="⚠️ GROQ_API_KEY is not set on the server.")

    # Strip a possible "data:audio/webm;base64," prefix.
    payload = req.audio_base64.split(",", 1)[-1]
    audio_bytes = base64.b64decode(payload)

    ext = _MIME_EXT.get(req.mime.split(";")[0].strip(), ".webm")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        client = Groq(api_key=settings.groq_api_key)
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file.read()),
                model=settings.groq_whisper_model,
            )
        return TranscribeResponse(text=(result.text or "").strip())
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return TranscribeResponse(text=f"⚠️ Transcription failed: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

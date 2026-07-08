"""Application configuration loaded from environment / .env file."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Groq LLM
    # NOTE: the assignment named gemma2-9b-it, but Groq decommissioned that model
    # on 2025-10-08. The assignment also sanctions llama-3.3-70b-versatile, which
    # is active and far more reliable for multi-tool calling, so it is the default.
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    # Groq Whisper model used to transcribe recorded voice notes.
    groq_whisper_model: str = "whisper-large-v3-turbo"

    # Database (SQLAlchemy URL). Defaults to a local SQLite file.
    database_url: str = "sqlite:///./hcp_crm.db"

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # langchain-groq reads GROQ_API_KEY from the environment; make sure it's set.
    if settings.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
    return settings

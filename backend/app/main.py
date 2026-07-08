"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import chat, interactions
from .seed import seed

settings = get_settings()

app = FastAPI(
    title="AI-First CRM — HCP Log Interaction API",
    version="1.0.0",
    description="FastAPI + LangGraph + Groq backend for the Log HCP Interaction screen.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(interactions.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": settings.groq_model,
        "groq_key_configured": bool(settings.groq_api_key),
        "database": {
            "dialect": engine.url.get_backend_name(),
            "url": engine.url.render_as_string(hide_password=True),
        },
    }

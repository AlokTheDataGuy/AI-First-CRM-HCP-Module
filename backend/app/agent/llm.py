"""Groq LLM factory (LangChain ChatGroq)."""
from langchain_groq import ChatGroq

from ..config import get_settings


def get_llm(tools=None, temperature: float = 0.0):
    """Return a ChatGroq instance, optionally with tools bound.

    The model id comes from GROQ_MODEL (default: gemma2-9b-it as required by the
    assignment). Set GROQ_MODEL=llama-3.3-70b-versatile for the most reliable
    multi-tool function calling.
    """
    settings = get_settings()
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key or None,
        temperature=temperature,
    )
    if tools:
        return llm.bind_tools(tools)
    return llm

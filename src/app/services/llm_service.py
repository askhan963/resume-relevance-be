"""
LLM client factory.

Provides a unified interface to get either a Groq (Llama 3) or
Google Gemini LangChain chat model, based on project configuration.
"""

import logging
from functools import lru_cache
from typing import Literal

logger = logging.getLogger(__name__)

LLMProvider = Literal["groq", "gemini"]


def get_llm(provider: LLMProvider | None = None):
    """
    Get a LangChain chat model instance for the specified provider.

    Parameters
    ----------
    provider : LLMProvider | None
        "groq" or "gemini". Defaults to DEFAULT_LLM_PROVIDER from settings.

    Returns
    -------
    BaseChatModel
        A configured LangChain chat model ready for chain use.

    Raises
    ------
    ValueError
        If the provider is unknown or API key is missing.
    RuntimeError
        If the required LangChain package is not installed.
    """
    from ..core.config import settings

    resolved_provider = provider or settings.DEFAULT_LLM_PROVIDER

    if resolved_provider == "groq":
        return _get_groq_llm(settings)
    elif resolved_provider == "gemini":
        return _get_gemini_llm(settings)
    else:
        raise ValueError(f"Unknown LLM provider: '{resolved_provider}'. Choose 'groq' or 'gemini'.")


def _get_groq_llm(settings):
    """Initialize a Groq (Llama 3) LangChain chat model."""
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        raise RuntimeError("langchain-groq is not installed. Run: pip install langchain-groq")

    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in your environment.")

    logger.info(f"Using Groq model: {settings.GROQ_MODEL}")
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


def _get_gemini_llm(settings):
    """Initialize a Google Gemini LangChain chat model."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise RuntimeError(
            "langchain-google-genai is not installed. Run: pip install langchain-google-genai"
        )

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in your environment.")

    logger.info(f"Using Gemini model: {settings.GEMINI_MODEL}")
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=settings.LLM_MAX_TOKENS,
    )


def get_llm_with_fallback(primary: LLMProvider = "groq", fallback: LLMProvider = "gemini"):
    """
    Attempt to get the primary provider's LLM, falling back to secondary if unavailable.

    Parameters
    ----------
    primary : LLMProvider
        Preferred LLM provider.
    fallback : LLMProvider
        Fallback LLM provider if primary fails.

    Returns
    -------
    BaseChatModel
        A configured LangChain chat model.
    """
    try:
        return get_llm(primary)
    except (ValueError, RuntimeError) as e:
        logger.warning(f"Primary LLM provider '{primary}' unavailable: {e}. Falling back to '{fallback}'.")
        return get_llm(fallback)

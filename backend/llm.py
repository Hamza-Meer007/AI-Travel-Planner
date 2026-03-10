from functools import lru_cache

from openai import RateLimitError
from langchain_openai import ChatOpenAI

from backend.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_PROVIDER_DISPLAY_NAME,
    LLM_REASONING_EFFORT,
    LLM_AUTH_ERROR_MESSAGE,
    LLM_QUOTA_ERROR_MESSAGE,
    LLM_RATE_LIMIT_ERROR_MESSAGE,
)


@lru_cache(maxsize=1)
def initialize_llm() -> ChatOpenAI:
    """Initialize and cache the LLM instance to avoid repeated instantiations."""
    if not LLM_API_KEY:
        raise RuntimeError(
            f"{LLM_PROVIDER_DISPLAY_NAME} API key is missing. "
            "Add it to .env and restart the server."
        )

    chat_openai_kwargs = {
        "model": LLM_MODEL,
        "api_key": LLM_API_KEY,
    }

    if LLM_PROVIDER == "groq":
        chat_openai_kwargs["base_url"] = LLM_BASE_URL
        chat_openai_kwargs["model_kwargs"] = {
            "reasoning_effort": LLM_REASONING_EFFORT,
        }

    return ChatOpenAI(**chat_openai_kwargs)


def get_llm_rate_limit_message(error: RateLimitError) -> str:
    """Translate a provider rate-limit error into an actionable user-facing message."""
    error_body = getattr(error, "body", {}) or {}
    error_details = error_body.get("error", {}) if isinstance(error_body, dict) else {}
    error_code = error_details.get("code")

    if error_code in {"insufficient_quota", "quota_exceeded"}:
        return LLM_QUOTA_ERROR_MESSAGE

    return LLM_RATE_LIMIT_ERROR_MESSAGE


def is_ai_service_error(message: str) -> bool:
    """Return True if the message represents an AI configuration or quota failure."""
    if not message:
        return False

    return message in {
        LLM_AUTH_ERROR_MESSAGE,
        LLM_QUOTA_ERROR_MESSAGE,
        LLM_RATE_LIMIT_ERROR_MESSAGE,
    }

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# LLM provider configuration
# ---------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT", "medium")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_API_KEY = GROQ_API_KEY if LLM_PROVIDER == "groq" else os.getenv("OPENAI_API_KEY")

SERP_API_KEY = os.getenv("SERP_API_KEY") or os.getenv("SERPER_API_KEY")

LLM_PROVIDER_DISPLAY_NAME = "Groq" if LLM_PROVIDER == "groq" else "OpenAI"

# ---------------------------------------------------------------------------
# User-facing error messages
# ---------------------------------------------------------------------------
LLM_AUTH_ERROR_MESSAGE = (
    f"{LLM_PROVIDER_DISPLAY_NAME} authentication failed. "
    "Update the API key in .env and restart the server."
)
LLM_QUOTA_ERROR_MESSAGE = (
    f"{LLM_PROVIDER_DISPLAY_NAME} quota exceeded. "
    "Add billing or increase your quota, then restart the search."
)
LLM_RATE_LIMIT_ERROR_MESSAGE = (
    f"{LLM_PROVIDER_DISPLAY_NAME} rate limit reached. Wait a moment and try again."
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

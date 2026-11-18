import os

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024

# Anthropic client policy, shared by the API, evals, and tests.
API_TIMEOUT_S = 30
API_MAX_RETRIES = 1

MAX_TEXT_CHARS = 20_000
DEFAULT_CURRENCY = "USD"


def joblens_api_key() -> str:
    """Read per call so the key can be rotated (and tests can monkeypatch it)."""
    return os.environ.get("JOBLENS_API_KEY", "")

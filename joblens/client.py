import anthropic

from joblens.config import API_MAX_RETRIES, API_TIMEOUT_S


def make_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(  # reads ANTHROPIC_API_KEY
        timeout=API_TIMEOUT_S, max_retries=API_MAX_RETRIES
    )

from collections.abc import Callable
from dataclasses import dataclass

import anthropic
from anthropic.types import Usage

from joblens.config import DEFAULT_CURRENCY, MAX_TOKENS, MODEL
from joblens.schema import JobPosting

SYSTEM_PROMPT = (
    "Extract structured data from the job posting. "
    "Use only information stated in the posting. "
    "If a field is not stated, return null; do not infer or guess."
)


class ExtractionError(Exception):
    """The model ran but didn't produce a usable posting for this input."""

    def __init__(self, message: str, usage: Usage | None = None):
        super().__init__(message)
        self.usage = usage  # failed calls still cost tokens


class NoOutputError(ExtractionError):
    """The model finished normally but returned nothing parseable.

    Kept distinct because it's an upstream fault, not a problem with the input.
    """


@dataclass(frozen=True)
class Extraction:
    posting: JobPosting
    usage: Usage


Extractor = Callable[[str], Extraction]


def extract(text: str, client: anthropic.Anthropic) -> Extraction:
    msg = client.messages.parse(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        output_format=JobPosting,
    )
    if msg.stop_reason == "max_tokens":
        raise ExtractionError(
            "Output truncated at max_tokens; JSON may be incomplete", msg.usage
        )
    if msg.stop_reason == "refusal":
        raise ExtractionError("Model refused to extract this posting", msg.usage)
    if msg.parsed_output is None:
        raise NoOutputError("Model returned no structured output", msg.usage)
    return Extraction(normalize(msg.parsed_output), msg.usage)


def normalize(posting: JobPosting) -> JobPosting:
    """Apply business rules to model output. Pure, so it's testable offline."""
    if posting.salary_currency is None:
        # Business rule, not a model guess.
        return posting.model_copy(update={"salary_currency": DEFAULT_CURRENCY})
    return posting

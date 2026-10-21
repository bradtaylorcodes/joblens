import anthropic

from joblens.schema import JobPosting

MODEL = "claude-sonnet-5-5"
DEFAULT_CURRENCY = "USD"

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


class ExtractionError(Exception):
    pass


def extract(text: str) -> JobPosting | None:
    msg = client.messages.parse(
        model=MODEL,
        max_tokens=1024,
        system="Extract structured data from the job posting.",
        messages=[{"role": "user", "content": text}],
        output_format=JobPosting,
    )
    if msg.stop_reason == "max_tokens":
        raise ExtractionError("Output truncated at max_tokens; JSON may be incomplete")
    if msg.stop_reason == "refusal":
        raise ExtractionError("Model refused to extract this posting")
    posting = msg.parsed_output
    if posting is not None and posting.salary_currency is None:
        posting.salary_currency = DEFAULT_CURRENCY  # business rule, not a model guess
    return posting

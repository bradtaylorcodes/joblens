# JobLens
LLM service that extracts structured data from job postings.

## Commands
- Run tests: `uv run pytest` (tests call the live API and cost ~$0.01)

## Rules
- Use the Anthropic SDK directly; no LLM frameworks.
- Default model: `claude-sonnet-5-5`.
- Read the API key from ANTHROPIC_API_KEY; never hardcode keys.
- `joblens/schema.py` and `tests/` are owned by me: don't edit them without asking.

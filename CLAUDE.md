# JobLens
LLM service that extracts structured data from job postings.

## Commands
- Tests: `uv run --env-file .env pytest` (test_extract.py calls the live API, ~$0.01)
- Eval: `uv run --env-file .env python -m evals.run` (~$0.11)
- Server: `uv run --env-file .env fastapi dev` (http://localhost:8000; POST /extract calls the live API and needs JOBLENS_API_KEY set, sent as the X-API-Key header)
- Container check: `docker build -t joblens . && docker run --rm -p 8080:8080 -e JOBLENS_API_KEY=test -e ANTHROPIC_API_KEY=dummy joblens` (http://localhost:8080; with the dummy key, POST /extract returns 502 at no cost)

## Rules
- Use the Anthropic SDK directly; no LLM frameworks.
- Default model: `claude-sonnet-5-5`.
- Read the API key from ANTHROPIC_API_KEY; never hardcode keys.
- `joblens/schema.py` and `tests/` are owned by me: don't edit them without asking.
- Deploy: deploys and secrets (`fly secrets`) are done by me; never run `fly` commands.

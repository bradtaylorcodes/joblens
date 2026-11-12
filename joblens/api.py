import logging
import time
from collections.abc import Callable
from functools import partial
from typing import Annotated

import anthropic
from anthropic.types import Usage
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints

from joblens.extract import ExtractionError, cost, extract_with_usage
from joblens.schema import JobPosting

MAX_TEXT_CHARS = 20_000

logger = logging.getLogger("joblens.api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:  %(name)s  %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

api_client = anthropic.Anthropic(timeout=30, max_retries=1)  # reads ANTHROPIC_API_KEY

Extractor = Callable[[str], tuple[JobPosting | None, Usage]]


def get_extractor() -> Extractor:
    return partial(extract_with_usage, client=api_client)


class ExtractRequest(BaseModel):
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_CHARS),
    ]


app = FastAPI(title="JobLens")


@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency = time.perf_counter() - start
    usage: Usage | None = getattr(request.state, "usage", None)
    if usage is None:
        tokens = "input_tokens=- output_tokens=- cost_usd=-"
    else:
        tokens = (
            f"input_tokens={usage.input_tokens} output_tokens={usage.output_tokens} "
            f"cost_usd={cost(usage):.6f}"
        )
    logger.info(
        f"{request.method} {request.url.path} status={response.status_code} "
        f"latency={latency:.3f}s {tokens}"
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"] if p != "body")
        messages.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


@app.post("/extract")
def extract_endpoint(
    req: ExtractRequest,
    request: Request,
    extractor: Annotated[Extractor, Depends(get_extractor)],
) -> JobPosting:
    try:
        posting, usage = extractor(req.text)
    except ExtractionError as e:
        request.state.usage = e.usage
        raise HTTPException(422, str(e)) from None
    except anthropic.RateLimitError:
        raise HTTPException(503, "Upstream rate limited; retry later") from None
    except anthropic.APITimeoutError:
        raise HTTPException(504, "Upstream timed out") from None
    except anthropic.APIError:
        raise HTTPException(502, "Upstream error") from None

    request.state.usage = usage
    if posting is None:
        raise HTTPException(502, "Model returned no structured output")
    return posting

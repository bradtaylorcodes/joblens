import logging
import secrets
import time
from contextlib import asynccontextmanager
from functools import cache, partial
from typing import Annotated

import anthropic
from anthropic.types import Usage
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, StringConstraints

from joblens.client import make_client
from joblens.config import MAX_TEXT_CHARS, joblens_api_key
from joblens.extract import ExtractionError, Extractor, NoOutputError, extract
from joblens.logging_config import configure_logging
from joblens.pricing import cost
from joblens.schema import JobPosting

logger = logging.getLogger(__name__)


@cache
def get_client() -> anthropic.Anthropic:
    return make_client()


def get_extractor(
    client: Annotated[anthropic.Anthropic, Depends(get_client)],
) -> Extractor:
    return partial(extract, client=client)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: Annotated[str | None, Depends(api_key_header)]) -> None:
    expected = joblens_api_key()
    if not expected:
        logger.error("JOBLENS_API_KEY is not set; rejecting request")
        raise HTTPException(500, "Server misconfigured")
    if key is None or not secrets.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(401, "Invalid or missing API key")


class ExtractRequest(BaseModel):
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_CHARS),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(title="JobLens", lifespan=lifespan)


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
        "%s %s status=%d latency=%.3fs %s",
        request.method,
        request.url.path,
        response.status_code,
        latency,
        tokens,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"] if p != "body")
        messages.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


@app.exception_handler(ExtractionError)
async def extraction_error(request: Request, exc: ExtractionError):
    request.state.usage = exc.usage
    status = 502 if isinstance(exc, NoOutputError) else 422
    return JSONResponse(status_code=status, content={"detail": str(exc)})


@app.exception_handler(anthropic.APIError)
async def upstream_error(request: Request, exc: anthropic.APIError):
    # Generic messages only: upstream error text may leak internals.
    if isinstance(exc, anthropic.RateLimitError):
        status, detail = 503, "Upstream rate limited; retry later"
    elif isinstance(exc, anthropic.APITimeoutError):
        status, detail = 504, "Upstream timed out"
    else:
        status, detail = 502, "Upstream error"
    return JSONResponse(status_code=status, content={"detail": detail})


@app.post("/extract", dependencies=[Depends(require_api_key)])
def extract_endpoint(
    req: ExtractRequest,
    request: Request,
    extractor: Annotated[Extractor, Depends(get_extractor)],
) -> JobPosting:
    result = extractor(req.text)
    request.state.usage = result.usage
    return result.posting

import anthropic
import httpx
import pytest
from anthropic.types import Usage
from fastapi.testclient import TestClient

from joblens.api import MAX_TEXT_CHARS, app, get_extractor
from joblens.extract import ExtractionError
from joblens.schema import JobPosting

POSTING = JobPosting(
    work_mode="remote",
    company="Acme",
    location=None,
    salary_min=100_000,
    salary_max=150_000,
    salary_currency="USD",
    required_skills=["Python"],
    discipline="backend",
)
USAGE = Usage(input_tokens=500, output_tokens=80)
UPSTREAM_REQ = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
SECRET = "boom-secret-upstream-detail"


class FakeExtractor:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0

    def __call__(self, text: str):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def use(fake: FakeExtractor) -> FakeExtractor:
    app.dependency_overrides[get_extractor] = lambda: fake
    return fake


def test_happy_path(client):
    use(FakeExtractor(result=(POSTING, USAGE)))
    r = client.post("/extract", json={"text": "Senior backend engineer at Acme"})
    assert r.status_code == 200
    assert r.json() == POSTING.model_dump()


def test_empty_text_rejected(client):
    fake = use(FakeExtractor(result=(POSTING, USAGE)))
    r = client.post("/extract", json={"text": ""})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)
    assert fake.calls == 0


def test_text_too_long_rejected(client):
    fake = use(FakeExtractor(result=(POSTING, USAGE)))
    r = client.post("/extract", json={"text": "x" * (MAX_TEXT_CHARS + 1)})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)
    assert fake.calls == 0


def test_extraction_error_is_422(client):
    use(FakeExtractor(error=ExtractionError("Model refused to extract this posting", USAGE)))
    r = client.post("/extract", json={"text": "posting"})
    assert r.status_code == 422
    assert r.json() == {"detail": "Model refused to extract this posting"}


def test_rate_limit_is_503(client):
    err = anthropic.RateLimitError(
        SECRET, response=httpx.Response(429, request=UPSTREAM_REQ), body=None
    )
    use(FakeExtractor(error=err))
    r = client.post("/extract", json={"text": "posting"})
    assert r.status_code == 503
    assert SECRET not in r.text


def test_timeout_is_504(client):
    use(FakeExtractor(error=anthropic.APITimeoutError(request=UPSTREAM_REQ)))
    r = client.post("/extract", json={"text": "posting"})
    assert r.status_code == 504
    assert set(r.json()) == {"detail"}


def test_other_api_error_is_502(client):
    err = anthropic.InternalServerError(
        SECRET, response=httpx.Response(500, request=UPSTREAM_REQ), body=None
    )
    use(FakeExtractor(error=err))
    r = client.post("/extract", json={"text": "posting"})
    assert r.status_code == 502
    assert r.json() == {"detail": "Upstream error"}
    assert SECRET not in r.text

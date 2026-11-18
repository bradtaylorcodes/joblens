"""Tests for pure logic; no API calls."""

import pytest
from anthropic.types import Usage

from joblens.config import MODEL
from joblens.extract import normalize
from joblens.pricing import PRICES, cost
from joblens.schema import JobPosting


def posting(**overrides) -> JobPosting:
    fields = dict(
        work_mode="remote",
        company="Acme",
        location=None,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        required_skills=[],
        discipline="backend",
    )
    return JobPosting(**(fields | overrides))


def test_normalize_defaults_currency_to_usd():
    assert normalize(posting()).salary_currency == "USD"


def test_normalize_keeps_stated_currency():
    assert normalize(posting(salary_currency="CAD")).salary_currency == "CAD"


def test_default_model_has_pricing():
    assert MODEL in PRICES


def test_cost():
    usage = Usage(input_tokens=1_000_000, output_tokens=100_000)
    assert cost(usage, "claude-sonnet-5-5") == pytest.approx(3.0)


def test_cost_unknown_model_raises():
    with pytest.raises(ValueError, match="No pricing"):
        cost(Usage(input_tokens=1, output_tokens=1), "not-a-model")

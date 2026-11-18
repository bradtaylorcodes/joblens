from pathlib import Path

import pytest

from joblens.client import make_client
from joblens.extract import extract

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def client():
    return make_client()


def test_posting_without_salary(client):
    p = extract((FIX / "posting_1.txt").read_text(), client).posting
    assert p.company == "Tactacam"
    assert p.work_mode == "remote"
    assert p.salary_min == None and p.salary_currency == "USD"


def test_posting_with_salary(client):
    p = extract((FIX / "posting_2.txt").read_text(), client).posting
    assert p.company == "Honeycomb"
    assert p.work_mode == "remote"
    assert p.salary_min == 160_000 and p.salary_currency == "USD"

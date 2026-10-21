from pathlib import Path

from joblens.extract import extract

FIX = Path(__file__).parent / "fixtures"


def test_posting_without_salary():
    p = extract((FIX / "posting_1.txt").read_text())
    assert p is not None
    assert p.company == "Tactacam"
    assert p.work_mode == "remote"
    assert p.salary_min == None and p.salary_currency == "USD"


def test_posting_with_salary():
    p = extract((FIX / "posting_2.txt").read_text())
    assert p is not None
    assert p.company == "Honeycomb"
    assert p.work_mode == "remote"
    assert p.salary_min == 160_000 and p.salary_currency == "USD"

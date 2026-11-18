import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
from anthropic.types import Usage

from joblens.client import make_client
from joblens.extract import ExtractionError, extract
from joblens.pricing import cost
from joblens.schema import JobPosting

RUNS = 3

ROOT = Path(__file__).parent.parent
CASES = ROOT / "evals" / "cases.json"
FIX = ROOT / "tests" / "fixtures"


@dataclass
class Run:
    fixture: str
    expected: dict
    posting: JobPosting | None
    error: str | None
    usage: Usage | None
    latency: float


@dataclass
class FieldScore:
    passes: int = 0
    total: int = 0
    failures: list[tuple] = field(default_factory=list)


def run_once(
    fixture: str, expected: dict, text: str, client: anthropic.Anthropic
) -> Run:
    start = time.perf_counter()
    try:
        result = extract(text, client)
        posting, usage, error = result.posting, result.usage, None
    except ExtractionError as e:
        posting, usage, error = None, e.usage, f"<error: {e}>"
    return Run(fixture, expected, posting, error, usage, time.perf_counter() - start)


def matches(expected, got) -> bool:
    if isinstance(expected, str) and isinstance(got, str):
        return expected.casefold() == got.casefold()
    return expected == got


def actual(run: Run, name: str):
    if run.posting is None:
        return run.error
    return getattr(run.posting, name)


def score(runs: list[Run]) -> dict[str, FieldScore]:
    scores: dict[str, FieldScore] = {}
    for run in runs:
        for name, expected in run.expected.items():
            s = scores.setdefault(name, FieldScore())
            s.total += 1
            got = actual(run, name)
            if run.posting is not None and matches(expected, got):
                s.passes += 1
            else:
                s.failures.append((run.fixture, expected, got))
    return scores


def print_report(runs: list[Run]) -> None:
    scores = score(runs)
    for name, s in scores.items():
        print(f"{name}: {s.passes}/{s.total}")
        for failure in s.failures:
            print(f"  {failure!r}")

    passes = sum(s.passes for s in scores.values())
    total = sum(s.total for s in scores.values())
    latencies = [r.latency for r in runs]

    print()
    print(f"Overall: {passes}/{total} ({passes / total:.1%})")
    print(f"Cost: ${sum(cost(r.usage) for r in runs if r.usage):.4f}")
    print(
        f"Latency: mean {sum(latencies) / len(latencies):.2f}s, "
        f"max {max(latencies):.2f}s"
    )


def main() -> None:
    client = make_client()
    runs = []
    for case in json.loads(CASES.read_text()):
        text = (FIX / case["fixture"]).read_text()
        runs += [
            run_once(case["fixture"], case["expected"], text, client)
            for _ in range(RUNS)
        ]
    print_report(runs)


if __name__ == "__main__":
    main()

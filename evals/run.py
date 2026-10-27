import json
import time
from pathlib import Path

from joblens.extract import ExtractionError, extract_with_usage

RUNS = 3
INPUT_PRICE = 2 / 1_000_000  # USD per token, Sonnet 5.5
OUTPUT_PRICE = 10 / 1_000_000

ROOT = Path(__file__).parent.parent
CASES = ROOT / "evals" / "cases.json"
FIX = ROOT / "tests" / "fixtures"


def matches(expected, got) -> bool:
    if isinstance(expected, str) and isinstance(got, str):
        return expected.casefold() == got.casefold()
    return expected == got


def main() -> None:
    cases = json.loads(CASES.read_text())
    results: dict[str, dict] = {}  # field -> {passes, total, failures}
    cost = 0.0
    latencies: list[float] = []

    for case in cases:
        fixture = case["fixture"]
        text = (FIX / fixture).read_text()
        for _ in range(RUNS):
            start = time.perf_counter()
            try:
                posting, usage = extract_with_usage(text)
                error = None
            except ExtractionError as e:
                posting, usage, error = None, e.usage, f"<error: {e}>"
            latencies.append(time.perf_counter() - start)
            if usage is not None:
                cost += (
                    usage.input_tokens * INPUT_PRICE
                    + usage.output_tokens * OUTPUT_PRICE
                )

            for field, expected in case["expected"].items():
                r = results.setdefault(field, {"passes": 0, "total": 0, "failures": []})
                r["total"] += 1
                if posting is None:
                    got = error or "<no output>"
                    r["failures"].append((fixture, expected, got))
                    continue
                got = getattr(posting, field)
                if matches(expected, got):
                    r["passes"] += 1
                else:
                    r["failures"].append((fixture, expected, got))

    for field, r in results.items():
        print(f"{field}: {r['passes']}/{r['total']}")
        for failure in r["failures"]:
            print(f"  {failure!r}")

    passes = sum(r["passes"] for r in results.values())
    total = sum(r["total"] for r in results.values())
    print()
    print(f"Overall: {passes}/{total} ({passes / total:.1%})")
    print(f"Cost: ${cost:.4f}")
    print(
        f"Latency: mean {sum(latencies) / len(latencies):.2f}s, "
        f"max {max(latencies):.2f}s"
    )


if __name__ == "__main__":
    main()

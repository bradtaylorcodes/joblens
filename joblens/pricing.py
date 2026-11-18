from anthropic.types import Usage

from joblens.config import MODEL

# USD per token: (input, output)
PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (2 / 1_000_000, 10 / 1_000_000),
}


def cost(usage: Usage, model: str = MODEL) -> float:
    try:
        input_price, output_price = PRICES[model]
    except KeyError:
        raise ValueError(f"No pricing for model {model!r}; add it to PRICES") from None
    return usage.input_tokens * input_price + usage.output_tokens * output_price

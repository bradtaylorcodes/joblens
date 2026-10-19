import anthropic

MODEL = "claude-sonnet-5-5"
PRICE_IN, PRICE_OUT = 2.00, 10.00  # USD per MTok, check the pricing page

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def ask(messages, max_tokens=500):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system="You are concise. Answer in at most three sentences.",
        messages=messages,
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    u = msg.usage
    cost = (u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT) / 1_000_000
    print(
        f"{text}\n-- stop={msg.stop_reason} in={u.input_tokens} out={u.output_tokens} ${cost:.6f}"
    )
    return text


if __name__ == "__main__":
    first = "My favourite language is Go."
    reply = ask([{"role": "user", "content": first}])
    ask(
        [
            {"role": "user", "content": first},
            {"role": "assistant", "content": reply},
            {"role": "user", "content": "What's my favourite language?"},
        ]
    )

"""Token → cost pricing. Approximate per-1K-token USD rates by model."""

from __future__ import annotations

# (input_per_1k, output_per_1k) in USD. Groq's published rates; echo ~ free.
PRICES: dict[str, tuple[float, float]] = {
    "llama-3.3-70b-versatile": (0.00059, 0.00079),
    "llama-3.1-8b-instant": (0.00005, 0.00008),
}
_DEFAULT = (0.0002, 0.0004)


def compute_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICES.get(model, _DEFAULT)
    return round((tokens_in / 1000) * pin + (tokens_out / 1000) * pout, 6)

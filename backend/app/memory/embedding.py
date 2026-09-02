"""Embeddings.

The default `HashingEmbedder` is deterministic and dependency-free, so memory
works offline. It's a hashed bag-of-words vector — lexical, not deeply semantic,
but real cosine similarity over it recalls similar requests well (and it's
swappable for a sentence-transformer or an embeddings API later).
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN = re.compile(r"[a-z0-9]+")


def _stable_hash(token: str) -> int:
    # hashlib, not built-in hash(): built-in hashing of str is randomised per
    # process, which would break recall of embeddings persisted by earlier runs.
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")


class Embedder(ABC):
    dim: int

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder(Embedder):
    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _TOKEN.findall(text.lower()):
            h = _stable_hash(tok)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))  # both are L2-normalised

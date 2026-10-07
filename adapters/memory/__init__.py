"""Adapter in memoria e deterministici.

Non sono "mock da test": il FakeLLM è anche il motore della turbolenza
dello stress test (latenza/errori/costo iniettabili e riproducibili), così
la demo dal vivo non dipende da quanto è lento il cloud quel giorno.
"""
from __future__ import annotations

import hashlib
import math
import random
from typing import Callable, Iterable, Sequence

from core.domain.errors import IndexNotReady, ProviderError, ProviderTimeout
from core.domain.models import CallRecord, LLMResult, Source, Trace
from core.ports import (
    ClockPort, CostLedgerPort, DocumentSourcePort, EmbedderPort, IdGeneratorPort,
    LLMPort, MetricsPort, TraceStorePort, VectorIndexPort,
)


class FakeLLM(LLMPort):
    """Modello finto, configurabile per prefisso di modello.

    behaviours: {"cloud/": {"fail": True}, "ollama/": {"latency_ms": 900, "reply": "bug"}}
    - fail: solleva ProviderError
    - latency_ms > timeout_s*1000: solleva ProviderTimeout (come un client reale)
    - reply: str o callable(prompt) -> str
    """

    def __init__(self, behaviours: dict | None = None, default_reply: str = "ok",
                 jitter_seed: int | None = None):
        self.behaviours = behaviours or {}
        self.default_reply = default_reply
        self.calls: list[tuple[str, str]] = []
        self._rng = random.Random(jitter_seed) if jitter_seed is not None else None

    def _cfg(self, model: str) -> dict:
        for prefix, cfg in self.behaviours.items():
            if model.startswith(prefix):
                return cfg
        return {}

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None) -> LLMResult:
        self.calls.append((model, prompt))
        cfg = self._cfg(model)
        if cfg.get("fail"):
            raise ProviderError(f"{model}: {cfg.get('error', 'provider non disponibile')}")
        latency = int(cfg.get("latency_ms", 50))
        if self._rng and cfg.get("jitter_ms"):
            latency += int(self._rng.uniform(0, cfg["jitter_ms"]))
        if timeout_s is not None and latency > timeout_s * 1000:
            raise ProviderTimeout(f"{model}: {latency}ms > {timeout_s * 1000:.0f}ms")
        reply = cfg.get("reply", self.default_reply)
        text = reply(prompt) if callable(reply) else reply
        return LLMResult(text=text, model=model, tokens_in=max(1, len(prompt) // 4),
                         tokens_out=max(1, len(text) // 4), latency_ms=latency)

    def calls_to(self, prefix: str) -> int:
        return sum(1 for m, _ in self.calls if m.startswith(prefix))


class InMemoryLedger(CostLedgerPort):
    def __init__(self):
        self._recs: list[CallRecord] = []

    def record(self, rec):
        self._recs.append(rec)

    def records(self):
        return list(self._recs)


class InMemoryTraceStore(TraceStorePort):
    def __init__(self):
        self._traces: list[Trace] = []

    def trace(self, trace, record):
        self._traces.append(trace)

    def traces(self):
        return list(self._traces)


class RecordingMetrics(MetricsPort):
    def __init__(self):
        self.seen: list[CallRecord] = []

    def observe(self, rec):
        self.seen.append(rec)


class FixedClock(ClockPort):
    def __init__(self, t: float = 1_790_000_000.0, step: float = 0.0):
        self.t, self.step = t, step

    def now(self):
        self.t += self.step
        return self.t


class SequentialIds(IdGeneratorPort):
    def __init__(self, prefix: str = "flight"):
        self.prefix, self.n = prefix, 0

    def new_id(self):
        self.n += 1
        return f"{self.prefix}-{self.n:03d}"


class HashEmbedder(EmbedderPort):
    """Bag-of-words con hashing stabile (md5): deterministico, senza rete.
    Abbastanza buono da far vincere il chunk con le stesse parole."""
    dim = 256

    def embed(self, text):
        v = [0.0] * self.dim
        for w in text.lower().split():
            w = w.strip(".,;:!?()[]\"'")
            if len(w) < 3:
                continue
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        n = math.sqrt(sum(x * x for x in v))
        return [x / n for x in v] if n else v


class MemoryIndex(VectorIndexPort):
    def __init__(self):
        self._items: list[tuple[str, str]] | None = None
        self._vecs: list[list[float]] = []

    def build(self, items, vectors):
        self._items, self._vecs = list(items), [list(v) for v in vectors]
        return len(self._items)

    def search(self, vector, top_k):
        if self._items is None:
            raise IndexNotReady("indice non costruito")
        scored = [Source(path=p, chunk=c, score=sum(a * b for a, b in zip(vector, v)))
                  for (p, c), v in zip(self._items, self._vecs)]
        return sorted(scored, key=lambda s: s.score, reverse=True)[:top_k]


class MemoryDocuments(DocumentSourcePort):
    def __init__(self, docs: dict[str, str] | None = None):
        self.docs = dict(docs or {})

    def documents(self) -> Iterable[tuple[str, str]]:
        return sorted(self.docs.items())

    def add(self, name, text):
        self.docs[name] = text
        return name

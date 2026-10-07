"""Advisor di rotta via contratto /v1/systemone (Rizzo Flow, Open-Jev).

Una domanda di tipo `choice`: il server ritorna una probabilità per
candidato. Stesso client per entrambi i motori, cambiano endpoint e nome
modello (Rizzo accetta solo `rizzo-latest`: `open-jev` gli dà 422).
"""
from __future__ import annotations

import time

from core.domain.errors import ProviderError
from core.ports import RouteAdvisorPort
from adapters.llm.http import post_json

ENGINES = {
    "rizzo": ("http://127.0.0.1:8017/v1/systemone", "rizzo-latest"),
    "openjev": ("http://127.0.0.1:8791/v1/systemone", "open-jev"),
}


class SystemOneAdvisor(RouteAdvisorPort):
    def __init__(self, name: str, endpoint: str, model: str, timeout_s: float = 5.0):
        self.name, self.endpoint, self.model, self.timeout_s = name, endpoint, model, timeout_s

    @classmethod
    def engine(cls, name: str, timeout_s: float = 5.0) -> "SystemOneAdvisor":
        if name not in ENGINES:
            raise ValueError(f"motore sconosciuto {name!r}: {sorted(ENGINES)}")
        endpoint, model = ENGINES[name]
        return cls(name, endpoint, model, timeout_s)

    def choose(self, state, question, candidates):
        body = {"model": self.model, "state": state,
                "questions": {"decision": {"type": "choice", "instructions": question,
                                           "criteria": {cid: desc for cid, desc in candidates}}}}
        t0 = time.monotonic()
        raw = post_json(self.endpoint, body, timeout_s=self.timeout_s)
        latency = int((time.monotonic() - t0) * 1000)
        try:
            probs = {str(k): float(v) for k, v in raw["answers"]["decision"]["probabilities"].items()}
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise ProviderError(f"{self.name}: risposta malformata {str(raw)[:200]}") from e
        expected = {c for c, _ in candidates}
        if set(probs) != expected:
            raise ProviderError(f"{self.name}: id {sorted(probs)} != candidati {sorted(expected)}")
        return probs, latency

"""Modelli di dominio: valori immutabili che attraversano tutto il sistema.

Nessuna dipendenza esterna. Ogni oggetto che finisce in un log, in una
slide o in una risposta MCP ha un `to_dict()` serializzabile JSON.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

ROUTE_LOCAL = "local"
ROUTE_CLOUD = "cloud"
ROUTE_LOCAL_RAG = "local_rag"


@dataclass(frozen=True)
class ModelCatalog:
    """Quale modello serve ciascuna rotta. Nomi con prefisso di provider:
    `ollama/…` (locale), `vllm/…` (locale, server OpenAI-compatible),
    `cloud/…` (a consumo)."""
    local: str = "ollama/qwen2.5:7b"
    cloud: str = "cloud/gpt-4o"
    rag: str = "ollama/qwen2.5:7b"


@dataclass(frozen=True)
class RoutingContext:
    """Stato del mondo al momento della decisione."""
    local_only: bool = False
    budget_remaining_eur: Optional[float] = None
    budget_guard_eur: float = 0.0


@dataclass(frozen=True)
class Classification:
    kind: str            # classification | extraction | reasoning | rag_query
    complexity: str      # low | high
    sensitive: bool
    reasons: tuple[str, ...]
    keyword_hit: bool = True     # False = il tipo è un default: la regola sta tirando a indovinare

    def to_dict(self) -> dict:
        return {**asdict(self), "reasons": list(self.reasons)}


@dataclass(frozen=True)
class RouteDecision:
    route: str
    model: str
    fallbacks: tuple[str, ...]
    escalation: Optional[str]
    estimated_cost_class: str     # near_zero | metered
    cloud_allowed: bool
    reason: str
    rules: tuple[str, ...]
    classification: Classification

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "model": self.model,
            "fallbacks": list(self.fallbacks),
            "escalation": self.escalation,
            "estimated_cost_class": self.estimated_cost_class,
            "cloud_allowed": self.cloud_allowed,
            "reason": self.reason,
            "rules": list(self.rules),
            "classification": self.classification.to_dict(),
        }


@dataclass(frozen=True)
class LLMResult:
    """Risposta di un modello: token CONTATI dal motore, non stimati."""
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int


@dataclass(frozen=True)
class Source:
    path: str
    chunk: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CallRecord:
    """Una riga del registro costi: il mattone di ogni numero del talk."""
    ts: float
    request_id: str
    route: str
    model: str
    kind: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_eur: float
    cost_if_cloud_eur: float
    fallback: bool = False
    fallback_reason: str = ""
    escalated: bool = False
    sensitive: bool = False
    cloud_allowed: bool = True
    tokens_saved_by_compression: int = 0
    rules: tuple[str, ...] = field(default_factory=tuple)
    advisor_engine: str = ""
    advisor_choice: str = ""
    advisor_p: float = 0.0
    advisor_agreed: bool = False
    advisor_applied: bool = False
    advisor_latency_ms: int = 0

    def to_dict(self) -> dict:
        return {**asdict(self), "rules": list(self.rules)}

    @staticmethod
    def from_dict(d: dict) -> "CallRecord":
        known = {k: d[k] for k in CallRecord.__dataclass_fields__ if k in d}
        known["rules"] = tuple(known.get("rules", ()))
        return CallRecord(**known)


@dataclass(frozen=True)
class Trace:
    """Prompt e risposta completi: restano in casa (trace store locale) e
    alimentano il Data Flywheel."""
    request_id: str
    ts: float
    prompt: str
    output: str
    route: str
    model: str
    kind: str
    sensitive: bool
    fallback: bool
    feedback: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Trace":
        return Trace(**{k: d[k] for k in Trace.__dataclass_fields__ if k in d})


@dataclass(frozen=True)
class CompressionResult:
    text: str
    tokens_before: int
    tokens_after: int
    method: str

    @property
    def saved(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)

"""AdvisedRouter: un piccolo modello locale come "secondo controllore di volo".

Le regole dure decidono COSA è permesso; il modello sceglie solo tra le
rotte permesse. In shadow si misura (accordo con la regola, confidenza,
latenza) prima di fidarsi: è così che si decide se lo switch vale la
latenza che aggiunge.

Modalità:
- shadow   : misura soltanto;
- active   : il modello decide su ogni richiesta;
- fallback : il modello viene chiamato SOLO quando nessuna parola chiave ha
             deciso il tipo (la regola sta tirando a indovinare): è lì che
             cadono gli errori delle regole, e la latenza si paga solo lì.
both_orders: chiede due volte con i candidati in ordine inverso e media le
probabilità (contro il bias di posizione), al doppio della latenza.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.domain.errors import ProviderError
from core.domain.models import ROUTE_CLOUD, ROUTE_LOCAL, ROUTE_LOCAL_RAG, ModelCatalog, RouteDecision
from core.domain.policy import ROUTE_DESCRIPTIONS, reroute
from core.ports import RouteAdvisorPort

MODES = ("off", "shadow", "active", "fallback")
QUESTION = "Which route should serve this request? Pick the cheapest route that can answer it well."


@dataclass(frozen=True)
class Advice:
    engine: str
    choice: str
    p: float
    probabilities: dict
    latency_ms: int
    agreed: bool
    applied: bool
    note: str = ""
    error: str = ""


class AdvisedRouter:
    def __init__(self, advisor: RouteAdvisorPort, mode: str = "shadow", min_confidence: float = 0.6,
                 catalog: ModelCatalog | None = None, max_state_chars: int = 1200, both_orders: bool = False,
                 descriptions: dict[str, str] | None = None, question: str = QUESTION):
        if mode not in MODES:
            raise ValueError(f"modalità {mode!r} non valida: {MODES}")
        self.advisor, self.mode, self.min_confidence = advisor, mode, min_confidence
        self.catalog, self.max_state_chars = catalog or ModelCatalog(), max_state_chars
        self.both_orders, self.descriptions, self.question = both_orders, descriptions or ROUTE_DESCRIPTIONS, question

    def _state(self, prompt: str, base: RouteDecision) -> str:
        c = base.classification
        text = prompt if len(prompt) <= self.max_state_chars else prompt[:self.max_state_chars] + " …[truncated]"
        return (f"Request: {text}\n"
                f"Signals: {len(prompt)} chars, {len(prompt.split())} words, kind guess={c.kind}, "
                f"complexity guess={c.complexity}")

    def decide(self, prompt: str, base: RouteDecision) -> tuple[RouteDecision, Advice | None]:
        if self.mode == "off" or (self.mode == "fallback" and base.classification.keyword_hit):
            return base, None
        allowed = [r for r in (ROUTE_LOCAL, ROUTE_CLOUD, ROUTE_LOCAL_RAG)
                   if r != ROUTE_CLOUD or base.cloud_allowed]
        candidates = [(r, self.descriptions[r]) for r in allowed]
        state = self._state(prompt, base)
        try:
            probs, latency = self.advisor.choose(state, self.question, candidates)
            if self.both_orders and len(candidates) > 1:
                rev, lat2 = self.advisor.choose(state, self.question, list(reversed(candidates)))
                probs = {k: (probs.get(k, 0.0) + rev.get(k, 0.0)) / 2 for k in set(probs) | set(rev)}
                latency += lat2
        except ProviderError as e:
            return base, Advice(self.advisor.name, "", 0.0, {}, 0, False, False, error=str(e)[:200])
        valid = {k: v for k, v in probs.items() if k in allowed}
        if not valid:
            return base, Advice(self.advisor.name, "", 0.0, probs, latency, False, False,
                                error="nessuna scelta tra i candidati")
        choice = max(valid, key=valid.get)
        p = valid[choice]
        agreed = choice == base.route
        if self.mode == "shadow" or agreed:
            return base, Advice(self.advisor.name, choice, p, probs, latency, agreed, False)
        if p < self.min_confidence:
            return base, Advice(self.advisor.name, choice, p, probs, latency, agreed, False,
                                note=f"confidenza {p:.2f} < {self.min_confidence}: vince la regola")
        return reroute(base, choice, self.catalog), Advice(self.advisor.name, choice, p, probs, latency, agreed, True)

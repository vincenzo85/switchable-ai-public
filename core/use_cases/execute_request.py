"""ExecuteRequest: il volo completo di UNA richiesta.

decide_route → (RAG: recupera contesto) → (rotta a pagamento: comprimi)
→ modello primario → fallback se il provider cade o è lento
→ escalation al cloud se la risposta locale non passa la validazione
→ registro costi + metriche + trace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from core.domain.errors import DomainError, ProviderError
from core.domain.models import (
    ROUTE_CLOUD, ROUTE_LOCAL_RAG, CallRecord, LLMResult, ModelCatalog, RouteDecision,
    RoutingContext, Source, Trace,
)
from core.domain.policy import decide_route
from core.domain.pricing import cost_if_cloud, cost_of
from core.domain.text import approx_tokens
from core.ports import (
    ClockPort, CostLedgerPort, IdGeneratorPort, LLMPort, MetricsPort, PromptCompressorPort, TracerPort,
)

Validator = Callable[[str], bool]


@dataclass(frozen=True)
class Budget:
    daily_limit_eur: float
    guard_eur: float          # sotto questo residuo il cloud si spegne (local-first)


@dataclass(frozen=True)
class ExecutionResult:
    decision: RouteDecision
    text: str
    record: CallRecord
    sources: tuple[Source, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {"decision": self.decision.to_dict(), "text": self.text,
                "record": self.record.to_dict(), "sources": [s.to_dict() for s in self.sources]}


def build_rag_prompt(question: str, sources: tuple[Source, ...]) -> str:
    ctx = "\n\n".join(f"[{i}] ({s.path})\n{s.chunk}" for i, s in enumerate(sources, 1))
    return ("Rispondi in italiano usando SOLO il contesto qui sotto. Cita le fonti come [1], [2]. "
            "Se il contesto non basta, dillo esplicitamente.\n\n"
            f"CONTESTO:\n{ctx}\n\nDOMANDA: {question}\nRISPOSTA:")


def _non_empty(text: str) -> bool:
    return bool(text.strip())


class ExecuteRequest:
    def __init__(self, *, llm: LLMPort, ledger: CostLedgerPort, clock: ClockPort, ids: IdGeneratorPort,
                 catalog: ModelCatalog | None = None, tracer: TracerPort | None = None,
                 metrics: MetricsPort | None = None, retriever=None,
                 compressor: PromptCompressorPort | None = None, compress_threshold_tokens: int = 1500,
                 keep_ratio: float = 0.5, budget: Budget | None = None, local_only: bool = False,
                 cloud_timeout_s: float = 60.0, local_timeout_s: float = 300.0, advisor=None):
        self.llm, self.ledger, self.clock, self.ids = llm, ledger, clock, ids
        self.catalog = catalog or ModelCatalog()
        self.tracer, self.metrics, self.retriever = tracer, metrics, retriever
        self.compressor, self.compress_threshold, self.keep_ratio = compressor, compress_threshold_tokens, keep_ratio
        self.budget, self.local_only = budget, local_only
        self.cloud_timeout_s, self.local_timeout_s = cloud_timeout_s, local_timeout_s
        self.advisor = advisor          # AdvisedRouter opzionale (Rizzo Flow / Open-Jev)

    # -- contesto ---------------------------------------------------------------
    def cloud_spent_today(self) -> float:
        day = int(self.clock.now() // 86400)
        return sum(r.cost_eur for r in self.ledger.records()
                   if r.model.startswith("cloud/") and int(r.ts // 86400) == day)

    def routing_context(self) -> RoutingContext:
        if self.budget is None:
            return RoutingContext(local_only=self.local_only)
        remaining = self.budget.daily_limit_eur - self.cloud_spent_today()
        return RoutingContext(local_only=self.local_only, budget_remaining_eur=remaining,
                              budget_guard_eur=self.budget.guard_eur)

    def decide(self, prompt: str) -> RouteDecision:
        return self.decide_with_advice(prompt)[0]

    def decide_with_advice(self, prompt: str):
        base = decide_route(prompt, self.routing_context(), self.catalog)
        if self.advisor is None:
            return base, None
        return self.advisor.decide(prompt, base)

    # -- esecuzione -------------------------------------------------------------
    def _call(self, model: str, prompt: str, max_tokens: Optional[int]) -> LLMResult:
        timeout = self.cloud_timeout_s if model.startswith("cloud/") else self.local_timeout_s
        return self.llm.complete(model, prompt, max_tokens=max_tokens, timeout_s=timeout)

    def _maybe_compress(self, text: str, question: str = "") -> tuple[str, int]:
        if self.compressor is None or approx_tokens(text) <= self.compress_threshold:
            return text, 0
        r = self.compressor.compress(text, keep_ratio=self.keep_ratio, question=question)
        return r.text, r.saved

    def execute(self, prompt: str, *, validator: Validator | None = None,
                max_tokens: int | None = None) -> ExecutionResult:
        decision, advice = self.decide_with_advice(prompt)
        rid = self.ids.new_id()
        sources: tuple[Source, ...] = ()
        saved = 0
        sent = prompt
        errors: list[str] = []

        if decision.route == ROUTE_LOCAL_RAG:
            if self.retriever is None:
                raise ProviderError("rotta RAG senza retriever: costruisci l'indice (rag-build)")
            try:
                sources = tuple(self.retriever.retrieve(prompt))
                sent = build_rag_prompt(prompt, sources)
            except DomainError as e:
                # indice non pronto: si risponde in locale senza contesto, il dato
                # non esce comunque; il motivo finisce nel registro.
                errors.append(f"RAG degradato: {e}")
        elif decision.route == ROUTE_CLOUD:
            # si comprime solo ciò che si paga: in locale il token costa ~0
            sent, saved = self._maybe_compress(prompt)

        chain = (decision.model, *decision.fallbacks)
        result = None
        for model in chain:
            try:
                result = self._call(model, sent, max_tokens)
                break
            except ProviderError as e:
                msg = str(e)
                errors.append(msg if msg.startswith(model) else f"{model}: {msg}")
        if result is None:
            raise ProviderError("tutte le rotte sono cadute — " + " | ".join(errors))

        billed = [result]
        escalated = False
        check = validator or _non_empty
        if decision.escalation and decision.cloud_allowed and not check(result.text):
            try:
                esc = self._call(decision.escalation, sent, max_tokens)
                billed.append(esc)
                result, escalated = esc, True
            except ProviderError as e:
                errors.append(f"escalation {decision.escalation}: {e}")

        fell_back = result.model != decision.model and not escalated
        if fell_back and not any(e.startswith(("cloud/", "ollama/", "vllm/")) for e in errors):
            errors.append(f"fallback eseguito dal gateway: servito da {result.model}")
        record = CallRecord(
            ts=self.clock.now(), request_id=rid, route=decision.route, model=result.model,
            kind=decision.classification.kind,
            tokens_in=sum(r.tokens_in for r in billed), tokens_out=sum(r.tokens_out for r in billed),
            latency_ms=sum(r.latency_ms for r in billed) + (advice.latency_ms if advice else 0),
            cost_eur=sum(cost_of(r.model, r.tokens_in, r.tokens_out) for r in billed),
            cost_if_cloud_eur=sum(cost_if_cloud(r.tokens_in, r.tokens_out) for r in billed),
            fallback=fell_back,
            fallback_reason=" | ".join(errors), escalated=escalated,
            sensitive=decision.classification.sensitive, cloud_allowed=decision.cloud_allowed,
            tokens_saved_by_compression=saved, rules=decision.rules,
            **({"advisor_engine": advice.engine, "advisor_choice": advice.choice, "advisor_p": advice.p,
                "advisor_agreed": advice.agreed, "advisor_applied": advice.applied,
                "advisor_latency_ms": advice.latency_ms} if advice else {}),
        )
        self.ledger.record(record)
        self._observe(record, Trace(request_id=rid, ts=record.ts, prompt=prompt, output=result.text,
                                    route=decision.route, model=result.model, kind=record.kind,
                                    sensitive=record.sensitive, fallback=record.fallback))
        return ExecutionResult(decision=decision, text=result.text, record=record, sources=sources)

    def _observe(self, record: CallRecord, trace: Trace) -> None:
        # L'osservabilità non deve MAI abbattere il volo.
        for sink, call in ((self.metrics, lambda m: m.observe(record)),
                           (self.tracer, lambda t: t.trace(trace, record))):
            if sink is None:
                continue
            try:
                call(sink)
            except Exception:  # noqa: BLE001 — confine voluto
                pass

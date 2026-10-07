"""Contratto di ExecuteRequest: decisione → (compressione) → chiamata →
fallback/escalation → registro costi, metriche, trace.

È il percorso di OGNI richiesta: se uno di questi test si rompe, il talk
mente. FakeLLM inietta la turbolenza in modo deterministico.
"""
import pytest

from adapters.memory import (FakeLLM, FixedClock, HashEmbedder, InMemoryLedger, InMemoryTraceStore,
                             MemoryDocuments, MemoryIndex, RecordingMetrics, SequentialIds)
from core.domain.errors import ProviderError
from core.domain.models import CallRecord
from core.use_cases.execute_request import Budget, ExecuteRequest
from core.use_cases.rag import BuildRagIndex, RetrieveContext
from adapters.compression.extractive import ExtractiveCompressor

SIMPLE = "Classifica questo ticket in [accesso, bug]: 'non riesco a fare login'"
COMPLEX = ("Analizza i trade-off tra monolite modulare e microservizi per una piattaforma "
           "con vincoli di data residency, proponi una migrazione in 3 fasi con rischi. ") * 5
SENSITIVE_COMPLEX = "Documento riservato. " + COMPLEX


def make(llm=None, **kw):
    llm = llm or FakeLLM()
    ledger, traces, metrics = InMemoryLedger(), InMemoryTraceStore(), RecordingMetrics()
    uc = ExecuteRequest(llm=llm, ledger=ledger, clock=FixedClock(), ids=SequentialIds(),
                        tracer=traces, metrics=metrics, **kw)
    return uc, llm, ledger, traces, metrics


def test_simple_task_runs_local_and_is_recorded_everywhere():
    uc, llm, ledger, traces, metrics = make()
    res = uc.execute(SIMPLE)
    assert res.decision.route == "local"
    assert llm.calls_to("ollama/") == 1 and llm.calls_to("cloud/") == 0
    [rec] = ledger.records()
    assert rec.model.startswith("ollama/") and rec.route == "local"
    assert rec.cost_eur < rec.cost_if_cloud_eur
    assert metrics.seen == [rec]
    assert traces.traces()[0].request_id == rec.request_id == res.record.request_id


def test_complex_task_goes_cloud_when_healthy():
    uc, llm, ledger, *_ = make()
    res = uc.execute(COMPLEX)
    assert res.record.model.startswith("cloud/") and not res.record.fallback
    assert llm.calls_to("cloud/") == 1


def test_cloud_down_falls_back_to_local_for_real():
    uc, llm, ledger, *_ = make(FakeLLM({"cloud/": {"fail": True, "error": "401 no key"}}))
    res = uc.execute(COMPLEX)
    assert res.decision.route == "cloud"
    assert res.record.fallback and "401" in res.record.fallback_reason
    assert res.record.model.startswith("ollama/")
    assert llm.calls_to("cloud/") == 1 and llm.calls_to("ollama/") == 1


def test_cloud_too_slow_falls_back():
    uc, llm, *_ = make(FakeLLM({"cloud/": {"latency_ms": 9000}}), cloud_timeout_s=2)
    res = uc.execute(COMPLEX)
    assert res.record.fallback and "ms" in res.record.fallback_reason
    assert res.record.model.startswith("ollama/")


def test_everything_down_raises_domain_error():
    uc, *_ = make(FakeLLM({"cloud/": {"fail": True}, "ollama/": {"fail": True}}))
    with pytest.raises(ProviderError):
        uc.execute(COMPLEX)


def test_sensitive_data_never_reaches_cloud_even_if_local_fails_validation():
    uc, llm, ledger, *_ = make(FakeLLM({"ollama/": {"reply": ""}}))
    res = uc.execute(SENSITIVE_COMPLEX)
    assert llm.calls_to("cloud/") == 0
    assert res.record.sensitive and not res.record.cloud_allowed
    assert not res.record.escalated


def test_low_confidence_local_answer_escalates_to_cloud():
    llm = FakeLLM({"ollama/": {"reply": "boh"}, "cloud/": {"reply": "accesso"}})
    uc, *_ = make(llm)
    res = uc.execute(SIMPLE, validator=lambda t: t.strip() in ("accesso", "bug"))
    assert res.record.escalated and res.text == "accesso"
    assert res.record.model.startswith("cloud/")


def test_escalation_cost_includes_both_calls():
    llm = FakeLLM({"ollama/": {"reply": "boh"}, "cloud/": {"reply": "accesso"}})
    uc, *_ = make(llm)
    esc = uc.execute(SIMPLE, validator=lambda t: t == "accesso").record
    # due chiamate fatturate: i token in sono quelli di ENTRAMBI i prompt
    assert esc.tokens_in == 2 * (len(SIMPLE) // 4)
    assert len(llm.calls) == 2


def test_budget_guard_keeps_complex_task_local_when_budget_is_spent():
    uc, llm, ledger, *_ = make(budget=Budget(daily_limit_eur=0.001, guard_eur=0.0005))
    uc.execute(COMPLEX)                    # primo: va in cloud e consuma il budget
    second = uc.execute(COMPLEX)
    assert "budget_guard" in second.decision.rules
    assert second.record.model.startswith("ollama/")


def test_local_only_mode():
    uc, llm, *_ = make(local_only=True)
    uc.execute(COMPLEX)
    assert llm.calls_to("cloud/") == 0


def _rag(llm):
    docs = MemoryDocuments({
        "gateway.md": "Il gateway LiteLLM instrada le richieste. Il fallback locale usa ollama "
                      "quando il cloud non risponde entro il timeout.",
        "costi.md": "Il costo per token dei modelli locali dipende da energia e ammortamento.",
    })
    emb, idx = HashEmbedder(), MemoryIndex()
    BuildRagIndex(docs, emb, idx).execute()
    return make(llm, retriever=RetrieveContext(emb, idx, top_k=2))


def test_rag_injects_retrieved_context_into_the_model_prompt():
    """Regressione del difetto del legacy: i chunk venivano stampati ma NON
    passati al modello."""
    llm = FakeLLM({"ollama/": {"reply": "Usa ollama come fallback [1]"}})
    uc, *_ = _rag(llm)
    res = uc.execute("Nella documentazione, come funziona il fallback del gateway quando il cloud non risponde?")
    assert res.decision.route == "local_rag"
    sent_prompt = llm.calls[-1][1]
    assert "fallback locale usa ollama" in sent_prompt
    assert res.sources and res.sources[0].path == "gateway.md"
    assert "[1]" in sent_prompt


def test_rag_without_retriever_is_a_clear_error():
    uc, *_ = make()
    with pytest.raises(ProviderError):
        uc.execute("Nella documentazione del progetto, come configuro il gateway?")


def test_compression_applies_to_paid_route_and_is_recorded():
    long_complex = COMPLEX * 6
    uc, llm, *_ = make(compressor=ExtractiveCompressor(), compress_threshold_tokens=200, keep_ratio=0.5)
    res = uc.execute(long_complex)
    assert res.record.tokens_saved_by_compression > 0
    assert len(llm.calls[-1][1]) < len(long_complex)


def test_compression_skips_local_route():
    uc, llm, *_ = make(compressor=ExtractiveCompressor(), compress_threshold_tokens=1, keep_ratio=0.5)
    res = uc.execute(SIMPLE)
    assert res.record.tokens_saved_by_compression == 0
    assert llm.calls[-1][1] == SIMPLE


def test_broken_tracer_never_breaks_the_request():
    class Boom(InMemoryTraceStore):
        def trace(self, trace, record):
            raise RuntimeError("langfuse giù")
    uc = ExecuteRequest(llm=FakeLLM(), ledger=InMemoryLedger(), clock=FixedClock(),
                        ids=SequentialIds(), tracer=Boom())
    assert uc.execute(SIMPLE).text == "ok"


def test_record_roundtrip():
    uc, _, ledger, *_ = make()
    rec = uc.execute(SIMPLE).record
    assert CallRecord.from_dict(rec.to_dict()) == rec


def test_rag_without_index_degrades_to_local_and_says_why():
    from core.use_cases.rag import RetrieveContext
    uc, llm, *_ = make(retriever=RetrieveContext(HashEmbedder(), MemoryIndex()))
    res = uc.execute("Nella documentazione del progetto, come configuro il gateway?")
    assert res.record.model.startswith("ollama/") and not res.sources
    assert "RAG degradato" in res.record.fallback_reason
    assert llm.calls_to("cloud/") == 0

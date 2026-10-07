"""Contratti dei casi d'uso operativi: report costi (cockpit), stress test
di atterraggio, Data Flywheel, ingestione documenti (n8n)."""
import json

import pytest

from adapters.memory import (FakeLLM, FixedClock, HashEmbedder, InMemoryLedger, InMemoryTraceStore,
                             MemoryDocuments, MemoryIndex, SequentialIds)
from core.use_cases.execute_request import Budget, ExecuteRequest
from core.use_cases.flywheel import ExportFlywheel
from core.use_cases.ingest import IngestDocument
from core.use_cases.rag import BuildRagIndex, RetrieveContext
from core.use_cases.report import CostReport, percentile
from core.use_cases.stress import RunStressTest, landing_scenario


class ListSink:
    def __init__(self):
        self.written = {}

    def write(self, name, rows):
        self.written[name] = rows
        return f"mem://{name}"


def wired(llm=None, budget=None, docs=None):
    ledger, traces = InMemoryLedger(), InMemoryTraceStore()
    docs = docs or MemoryDocuments({"runbook.md": "Procedura di rilascio: tag, build, deploy canary, verifica."})
    emb, idx = HashEmbedder(), MemoryIndex()
    BuildRagIndex(docs, emb, idx).execute()
    ex = ExecuteRequest(llm=llm or FakeLLM(), ledger=ledger, clock=FixedClock(step=1), ids=SequentialIds(),
                        tracer=traces, retriever=RetrieveContext(emb, idx), budget=budget)
    return ex, ledger, traces, docs, emb, idx


# --- report -------------------------------------------------------------------

def test_percentile_basic():
    assert percentile([10, 20, 30, 40], 50) == 25
    assert percentile([5], 95) == 5
    assert percentile([], 50) == 0


def test_cost_report_aggregates_and_saving():
    ex, ledger, *_ = wired(FakeLLM({"cloud/": {"fail": True}}))
    ex.execute("Classifica: bug o accesso?")
    ex.execute("Analizza i trade-off di questa architettura distribuita. " * 20)
    rep = CostReport(ledger).execute()
    assert rep["calls"] == 2
    assert rep["fallbacks"] == 1
    assert rep["residency_violations"] == 0
    assert 0 < rep["saving_pct"] <= 100
    assert set(rep["by_route"]) == {"local", "cloud"}
    assert rep["latency_ms"]["p95"] >= rep["latency_ms"]["p50"]
    assert "| local |" in CostReport(ledger).markdown()


def test_residency_violation_is_detected_if_it_ever_happens():
    """Il contatore deve funzionare: se un record sensibile finisse in cloud lo vedremmo."""
    from core.domain.models import CallRecord
    ledger = InMemoryLedger()
    ledger.record(CallRecord(ts=0, request_id="x", route="cloud", model="cloud/gpt-4o", kind="reasoning",
                             tokens_in=1, tokens_out=1, latency_ms=1, cost_eur=0.1, cost_if_cloud_eur=0.1,
                             sensitive=True))
    assert CostReport(ledger).execute()["residency_violations"] == 1


# --- stress test --------------------------------------------------------------

def test_landing_scenario_is_deterministic_and_mixed():
    a, b = landing_scenario(100, seed=7), landing_scenario(100, seed=7)
    assert a == b and len(a) == 100
    kinds = {t["family"] for t in a}
    assert kinds == {"ticket", "extraction", "architecture", "kb_question", "sensitive"}
    assert sum(t["family"] == "sensitive" for t in a) == 10


def test_stress_test_lands_with_zero_residency_violations_under_turbulence():
    llm = FakeLLM({"cloud/": {"latency_ms": 300, "jitter_ms": 4000}}, jitter_seed=1)
    ex, ledger, *_ = wired(llm, budget=Budget(daily_limit_eur=0.008, guard_eur=0.002))
    ex.cloud_timeout_s = 2.5
    report = RunStressTest(ex).execute(landing_scenario(100, seed=1))
    assert report["total_tasks"] == 100
    assert report["completed"] == 100
    assert report["data_residency_violations"] == 0
    assert report["fallback_events"] > 0, "la turbolenza iniettata deve produrre fallback"
    assert report["budget_guard_hits"] > 0, "il budget deve finire durante il batch"
    assert report["routes_decided"]["local_rag"] > 0
    assert report["cost_real_eur"] < report["cost_if_all_cloud_eur"]
    assert len(report["timeline"]) == 100
    json.dumps(report)


def test_stress_counts_failures_instead_of_crashing():
    llm = FakeLLM({"cloud/": {"fail": True}, "ollama/": {"fail": True}})
    ex, *_ = wired(llm)
    rep = RunStressTest(ex).execute(landing_scenario(10, seed=2))
    assert rep["failed"] == 10 and rep["completed"] == 0


# --- flywheel -----------------------------------------------------------------

def test_flywheel_exports_scrubbed_chat_dataset():
    llm = FakeLLM({"ollama/": {"reply": "Scrivi a mario.rossi@example.com"}})
    ex, ledger, traces, *_ = wired(llm)
    ex.execute("Classifica il ticket di anna.bianchi@example.com: login rotto")
    ex.execute("Classifica il ticket di anna.bianchi@example.com: login rotto")   # duplicato
    sink = ListSink()
    stats = ExportFlywheel(traces, sink).execute()
    rows = sink.written["sft"]
    assert stats["exported"] == 1 and stats["duplicates_skipped"] == 1
    assert stats["pii_redactions"] >= 2
    blob = json.dumps(rows)
    assert "@example.com" not in blob and "<EMAIL>" in blob
    assert rows[0]["messages"][0]["role"] == "user"
    assert rows[0]["meta"]["route"] == "local"


def test_flywheel_marks_cloud_answers_as_distillation_candidates():
    ex, ledger, traces, *_ = wired(FakeLLM({"cloud/": {"reply": "analisi profonda"}}))
    ex.execute("Analizza i trade-off di questa architettura distribuita. " * 20)
    stats = ExportFlywheel(traces, ListSink()).execute()
    assert stats["distillation_candidates"] == 1


def test_flywheel_skips_empty_outputs():
    ex, ledger, traces, *_ = wired(FakeLLM({"ollama/": {"reply": "  "}, "cloud/": {"fail": True}}))
    ex.execute("Classifica: bug?")
    assert ExportFlywheel(traces, ListSink()).execute()["exported"] == 0


# --- ingest (n8n) -------------------------------------------------------------

def test_ingest_document_classifies_updates_kb_and_reports_cost():
    def reply(prompt):
        if "Classifica" in prompt:
            return "runbook"
        if "Estrai" in prompt:
            return '{"titolo": "Rollback DB", "parole_chiave": ["db", "rollback"]}'
        return "1. verifica backup\n2. prova rollback"
    ex, ledger, traces, docs, emb, idx = wired(FakeLLM(default_reply="", behaviours={"ollama/": {"reply": reply}}))
    uc = IngestDocument(ex, docs, BuildRagIndex(docs, emb, idx))
    out = uc.execute("rollback-db.md", "# Rollback DB\nIn caso di migrazione fallita ripristina lo snapshot.")
    assert out["category"] == "runbook"
    assert out["metadata"]["titolo"] == "Rollback DB"
    assert out["checklist"]
    assert "rollback-db.md" in docs.docs
    assert out["index"]["documents"] == 2
    assert out["cost_eur"] >= 0 and len(out["request_ids"]) == 3
    assert out["data_residency_violations"] == 0
    # il documento appena ingerito è subito interrogabile dal RAG
    assert RetrieveContext(emb, idx, top_k=1).retrieve("ripristina snapshot migrazione fallita")[0].path == "rollback-db.md"


def test_ingest_tolerates_bad_metadata_json():
    ex, ledger, traces, docs, emb, idx = wired(FakeLLM(default_reply="non json"))
    out = IngestDocument(ex, docs, BuildRagIndex(docs, emb, idx)).execute("x.md", "testo")
    assert out["metadata"] == {"raw": "non json"}
    assert out["category"] == "altro"

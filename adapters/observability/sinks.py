"""Osservabilità: Prometheus (→ Grafana) e Langfuse (trace per richiesta).

Entrambi assorbono i propri errori: il cockpit può spegnersi, l'aereo no.
"""
from __future__ import annotations

import base64
import datetime as dt
import uuid

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from core.ports import MetricsPort, TracerPort
from adapters.llm.http import post_json

LATENCY_BUCKETS = (100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000)


class PrometheusMetrics(MetricsPort):
    def __init__(self, registry: CollectorRegistry | None = None):
        self.registry = registry or CollectorRegistry()
        r = self.registry
        lbl = ("route", "model")
        self.requests = Counter("sai_requests_total", "Richieste servite", lbl, registry=r)
        self.tokens = Counter("sai_tokens_total", "Token contati dal motore", (*lbl, "direction"), registry=r)
        self.cost = Counter("sai_cost_eur_total", "Costo reale (EUR)", lbl, registry=r)
        self.cost_cloud = Counter("sai_cost_if_cloud_eur_total", "Costo se tutto-cloud (EUR)", lbl, registry=r)
        self.latency = Histogram("sai_latency_ms", "Latenza end-to-end (ms)", lbl, buckets=LATENCY_BUCKETS, registry=r)
        self.fallbacks = Counter("sai_fallbacks_total", "Fallback eseguiti", lbl, registry=r)
        self.escalations = Counter("sai_escalations_total", "Escalation al cloud", lbl, registry=r)
        self.violations = Counter("sai_residency_violations_total", "Dati sensibili finiti in cloud", registry=r)
        self.saved = Counter("sai_compression_tokens_saved_total", "Token risparmiati dalla compressione", registry=r)
        self.budget_guard = Counter("sai_budget_guard_total", "Richieste deviate dal budget guard", registry=r)
        self.advisor = Counter("sai_advisor_decisions_total", "Decisioni dell'advisor di rotta",
                               ("engine", "agreed", "applied"), registry=r)
        self.advisor_latency = Histogram("sai_advisor_latency_ms", "Latenza dell'advisor (ms)", ("engine",),
                                         buckets=(25, 50, 75, 100, 150, 250, 500, 1000, 2000), registry=r)
        self.violations.inc(0)

    def observe(self, rec):
        l = {"route": rec.route, "model": rec.model}
        self.requests.labels(**l).inc()
        self.tokens.labels(**l, direction="in").inc(rec.tokens_in)
        self.tokens.labels(**l, direction="out").inc(rec.tokens_out)
        self.cost.labels(**l).inc(rec.cost_eur)
        self.cost_cloud.labels(**l).inc(rec.cost_if_cloud_eur)
        self.latency.labels(**l).observe(rec.latency_ms)
        if rec.fallback:
            self.fallbacks.labels(**l).inc()
        if rec.escalated:
            self.escalations.labels(**l).inc()
        if rec.sensitive and rec.model.startswith("cloud/"):
            self.violations.inc()
        if rec.tokens_saved_by_compression:
            self.saved.inc(rec.tokens_saved_by_compression)
        if "budget_guard" in rec.rules:
            self.budget_guard.inc()
        if rec.advisor_engine:
            self.advisor.labels(engine=rec.advisor_engine, agreed=str(rec.advisor_agreed).lower(),
                                applied=str(rec.advisor_applied).lower()).inc()
            if rec.advisor_latency_ms:
                self.advisor_latency.labels(engine=rec.advisor_engine).observe(rec.advisor_latency_ms)

    def exposition(self) -> bytes:
        return generate_latest(self.registry)


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")


class LangfuseTracer(TracerPort):
    """Ingestion API pubblica di Langfuse v2 (niente SDK): una trace + una
    generation per richiesta, con rotta, fallback e costo nei metadati."""

    def __init__(self, host: str, public_key: str, secret_key: str, timeout_s: float = 3):
        self.url = host.rstrip("/") + "/api/public/ingestion"
        tok = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        self.headers = {"Authorization": f"Basic {tok}"}
        self.timeout_s = timeout_s
        self.last_error: str | None = None

    def trace(self, trace, record):
        start = _iso(record.ts - record.latency_ms / 1000)
        end = _iso(record.ts)
        meta = {"route": record.route, "fallback": record.fallback, "escalated": record.escalated,
                "rules": list(record.rules), "sensitive": record.sensitive,
                "cost_if_cloud_eur": record.cost_if_cloud_eur,
                "tokens_saved_by_compression": record.tokens_saved_by_compression}
        # il dato sensibile NON lascia la macchina nemmeno verso l'osservabilità
        shown_in = "[sensibile: contenuto non inviato]" if record.sensitive else trace.prompt
        shown_out = "[sensibile: contenuto non inviato]" if record.sensitive else trace.output
        batch = [
            {"id": str(uuid.uuid4()), "timestamp": end, "type": "trace-create",
             "body": {"id": trace.request_id, "name": f"route:{record.route}", "timestamp": start,
                      "input": shown_in, "output": shown_out, "metadata": meta,
                      "tags": [record.route, record.kind] + (["fallback"] if record.fallback else [])}},
            {"id": str(uuid.uuid4()), "timestamp": end, "type": "generation-create",
             "body": {"id": f"{trace.request_id}-gen", "traceId": trace.request_id, "name": record.kind,
                      "model": record.model, "startTime": start, "endTime": end,
                      "input": shown_in, "output": shown_out,
                      "usage": {"input": record.tokens_in, "output": record.tokens_out, "unit": "TOKENS",
                                "totalCost": record.cost_eur},
                      "metadata": meta}},
        ]
        try:
            post_json(self.url, {"batch": batch}, headers=self.headers, timeout_s=self.timeout_s)
            self.last_error = None
        except Exception as e:  # noqa: BLE001 — l'osservabilità non abbatte il volo
            self.last_error = str(e)


class FanoutTracer(TracerPort):
    def __init__(self, *tracers: TracerPort):
        self.tracers = tracers

    def trace(self, trace, record):
        for t in self.tracers:
            try:
                t.trace(trace, record)
            except Exception:  # noqa: BLE001
                pass

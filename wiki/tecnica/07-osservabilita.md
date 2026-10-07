# Osservabilità e persistenza

Regola: **l'osservabilità non abbatte mai il volo**. Ogni sink assorbe i propri errori e `ExecuteRequest._observe` li isola ancora.

## Persistenza locale (`adapters/storage/jsonl.py`)

Append-only, un JSON per riga, scritture protette da un lock di processo.

| File | Classe | Contenuto |
|---|---|---|
| `data/calls.jsonl` | `JsonlLedger` | `CallRecord.to_dict()` per ogni richiesta |
| `data/traces.jsonl` | `JsonlTraceStore` | `Trace`: `request_id`, `ts`, `prompt`, `output`, `route`, `model`, `kind`, `sensitive`, `fallback`, `feedback` |
| `data/flywheel/sft.jsonl` | `JsonlDatasetSink` | dataset di fine-tuning (sovrascritto a ogni export) |

Le righe malformate vengono saltate in lettura. Il ledger è anche la fonte del **budget giornaliero** (`cloud_spent_today`) e del report.

Esempio di riga del ledger:

```json
{"ts": 1791400000.1, "request_id": "flight-3f9c1a2b7d", "route": "cloud", "model": "ollama/qwen2.5:7b",
 "kind": "reasoning", "tokens_in": 214, "tokens_out": 300, "latency_ms": 5907,
 "cost_eur": 0.0001028, "cost_if_cloud_eur": 0.0023644, "fallback": true,
 "fallback_reason": "cloud/gpt-4o: nessuna chiave cloud (OPENAI_API_KEY vuota)", "escalated": false,
 "sensitive": false, "cloud_allowed": true, "tokens_saved_by_compression": 0, "rules": ["complexity"], ...}
```

Query utili:

```bash
# richieste in fallback
jq -c 'select(.fallback) | {request_id, route, model, fallback_reason}' data/calls.jsonl
# violazioni di residency (deve essere vuoto)
jq -c 'select(.sensitive and (.model | startswith("cloud/")))' data/calls.jsonl
# spesa cloud di oggi
jq -s '[.[] | select(.model | startswith("cloud/")) | .cost_eur] | add' data/calls.jsonl
```

## Report (`core/use_cases/report.py`)

`CostReport.execute()` ritorna: `calls`, `cost_eur`, `cost_if_cloud_eur`, `saving_pct`, `latency_ms.p50/p95`, `fallbacks`, `escalations`, `residency_violations`, `tokens_saved_by_compression`, `by_route`, `by_model` (ognuno con calls, costi, token, p50/p95). Percentili per interpolazione lineare.

`is_residency_violation(r) = r.sensitive and r.model.startswith("cloud/")`.

## Prometheus (`PrometheusMetrics`)

Registry dedicato, esposto su `GET /metrics` dell'API. Le metriche vivono **nel processo dell'API**: i comandi CLI (processi separati) non le alimentano.

| Metrica | Tipo | Label |
|---|---|---|
| `sai_requests_total` | counter | route, model |
| `sai_tokens_total` | counter | route, model, direction (`in`/`out`) |
| `sai_cost_eur_total` | counter | route, model |
| `sai_cost_if_cloud_eur_total` | counter | route, model |
| `sai_latency_ms` | histogram (100 … 64000 ms) | route, model |
| `sai_fallbacks_total` | counter | route, model |
| `sai_escalations_total` | counter | route, model |
| `sai_residency_violations_total` | counter (inizializzato a 0) | — |
| `sai_compression_tokens_saved_total` | counter | — |
| `sai_budget_guard_total` | counter | — |
| `sai_advisor_decisions_total` | counter | engine, agreed, applied |
| `sai_advisor_latency_ms` | histogram (25 … 2000 ms) | engine |

Scrape: `infra/prometheus.yml`, job `switchable_ai`, target `127.0.0.1:8088`, ogni 5 s.

PromQL di esempio:

```
sum(increase(sai_cost_eur_total[30m]))                                   # € reali
1 - sum(increase(sai_cost_eur_total[30m])) / sum(increase(sai_cost_if_cloud_eur_total[30m]))   # risparmio
histogram_quantile(0.95, sum by (le, route) (rate(sai_latency_ms_bucket[5m])))                # p95 per rotta
sum(sai_residency_violations_total)                                      # deve essere 0
```

## Grafana

Dashboard "Cockpit" in `infra/grafana/dashboards/cockpit.json`, **generata** da `tools/make_grafana_dashboard.py` (una sola fonte per i nomi delle metriche: rigenerala se aggiungi metriche). Provisioning in `infra/grafana/provisioning/` (datasource Prometheus `uid: prom`).

## Langfuse (`LangfuseTracer`)

Ingestion API pubblica v2 (`POST {host}/api/public/ingestion`, Basic auth `public:secret`), senza SDK. Per ogni richiesta un batch con:
- `trace-create`: id = `request_id`, nome `route:<rotta>`, tag `[rotta, kind, (fallback)]`, metadati (rotta, fallback, escalation, regole, sensibile, costo se cloud, token risparmiati);
- `generation-create`: modello, inizio e fine, `usage` (token in/out, `totalCost` in **euro**).

Se `record.sensitive`, input e output sono sostituiti da `[sensibile: contenuto non inviato]`: il dato non esce nemmeno verso l'osservabilità.

Timeout 3 s; errori salvati in `last_error` e ignorati. `FanoutTracer` manda a trace store locale **e** Langfuse.

## Test

`tests/test_adapters.py`: Prometheus espone rotta, costo e violazioni; Langfuse invia trace e generation senza contenuto sensibile; Langfuse giù non rompe niente. `tests/test_use_case_execute.py`: un tracer o una metrica che esplodono non fanno fallire la richiesta.

# Esecuzione di una richiesta (`core/use_cases/execute_request.py`)

`ExecuteRequest` è il caso d'uso attraversato da **ogni** richiesta: CLI, API, webhook n8n, tool MCP, stress test, ingest.

## Costruttore

```python
ExecuteRequest(
    llm: LLMPort, ledger: CostLedgerPort, clock: ClockPort, ids: IdGeneratorPort,
    catalog: ModelCatalog | None = None, tracer: TracerPort | None = None,
    metrics: MetricsPort | None = None, retriever=None,
    compressor: PromptCompressorPort | None = None, compress_threshold_tokens: int = 1500,
    keep_ratio: float = 0.5, budget: Budget | None = None, local_only: bool = False,
    cloud_timeout_s: float = 60.0, local_timeout_s: float = 300.0, advisor=None,
)
```

`Budget(daily_limit_eur, guard_eur)`.

## Passi di `execute(prompt, *, validator=None, max_tokens=None)`

1. **Decisione** — `decide_with_advice(prompt)`:
   - `routing_context()`: se c'è un budget, `remaining = daily_limit_eur − cloud_spent_today()`, dove `cloud_spent_today` somma `cost_eur` dei record di **oggi (giorno UTC)** con modello `cloud/…`;
   - `decide_route(prompt, ctx, catalog)`;
   - se c'è un advisor: `advisor.decide(prompt, base)` → `(decisione, Advice | None)`.
2. **Id** — `ids.new_id()` (in produzione `flight-<10 hex>`).
3. **Preparazione del prompt**:
   - `local_rag`: `retriever.retrieve(prompt)` (top-3) e `build_rag_prompt(prompt, sources)`. Se il retriever solleva un `DomainError` (es. `IndexNotReady`), il prompt resta quello originale e l'errore va in `fallback_reason` come `RAG degradato: …`. Se il retriever è `None` → `ProviderError`;
   - `cloud`: `_maybe_compress` comprime solo se c'è un compressore **e** `approx_tokens(prompt) > compress_threshold_tokens` (`keep_ratio` 0,5);
   - `local`: nessuna modifica.
4. **Catena** — `(decision.model, *decision.fallbacks)`: il primo che non solleva `ProviderError` vince. Timeout: `cloud_timeout_s` per `cloud/…`, `local_timeout_s` per gli altri. Se cadono tutti: `ProviderError("tutte le rotte sono cadute — …")`.
5. **Escalation** — se `decision.escalation` è valorizzata, il cloud è ammesso e `validator(result.text)` è falso (default: testo vuoto), si richiama `decision.escalation`. Se riesce, la risposta diventa quella del cloud e `escalated=True`; se fallisce, l'errore va in `fallback_reason` e resta la risposta locale.
6. **Fallback** — `fallback = result.model != decision.model and not escalated`. Se nessun errore registrato spiega il cambio di modello (caso tipico: LiteLLM ha fatto fallback per conto suo), si aggiunge `fallback eseguito dal gateway: servito da …`.
7. **Registro** — si costruisce il `CallRecord`, si scrive nel ledger, poi metriche e tracer. Metriche e tracer sono chiamati dentro `try/except Exception`: **l'osservabilità non può far fallire la richiesta**.

Ritorna `ExecutionResult(decision, text, record, sources)`; `to_dict()` serializza tutto.

## Prompt RAG

```
Rispondi in italiano usando SOLO il contesto qui sotto. Cita le fonti come [1], [2]. Se il contesto non basta, dillo esplicitamente.

CONTESTO:
[1] (percorso/file.md)
<chunk>

[2] (...)

DOMANDA: <prompt>
RISPOSTA:
```

## `CallRecord` (`core/domain/models.py`)

| Campo | Significato |
|---|---|
| `ts` | epoch secondi (fine richiesta) |
| `request_id` | id del volo |
| `route` | rotta **decisa** |
| `model` | modello che ha **risposto** |
| `kind` | tipo dal classificatore |
| `tokens_in`, `tokens_out` | contati dal motore; con escalation, somma delle due chiamate |
| `latency_ms` | somma delle chiamate fatturate + latenza dell'advisor |
| `cost_eur` | `Σ cost_of(model, in, out)` sulle chiamate fatturate |
| `cost_if_cloud_eur` | stessi token al prezzo del modello cloud di riferimento |
| `fallback`, `fallback_reason` | vedi sopra; `fallback_reason` raccoglie tutti gli errori, separati da ` \| ` |
| `escalated` | escalation riuscita |
| `sensitive`, `cloud_allowed` | dalla decisione |
| `tokens_saved_by_compression` | `tokens_before − tokens_after` stimati |
| `rules` | regole della decisione |
| `advisor_engine`, `advisor_choice`, `advisor_p`, `advisor_agreed`, `advisor_applied`, `advisor_latency_ms` | solo se c'è un advisor |

Nota: le chiamate fallite della catena **non** sono fatturate (non hanno prodotto token).

## Adapter LLM coinvolti (`adapters/llm/providers.py`)

| Adapter | Uso |
|---|---|
| `OllamaLLM` | `POST {base}/api/generate`, `stream=false`, `num_ctx=4096`, `temperature=0.2`, `keep_alive="10m"`; token da `prompt_eval_count` / `eval_count` |
| `OpenAICompatLLM` | `POST {base}/v1/chat/completions`; `model_name` traduce il nome interno (es. alias LiteLLM), `served_as` traduce il campo `model` della risposta per rilevare i fallback del gateway |
| `PrefixRouterLLM` | smista per prefisso del nome modello; prefisso sconosciuto → `ProviderError` |
| `UnavailableLLM` | solleva subito `ProviderError` (rotta senza credenziali: il fallback si esercita senza attendere un timeout) |
| `SimulatedCloudLLM` | cloud **simulato** per lo stress test: risponde un modello locale, si presenta col nome cloud (listino cloud), turbolenza programmata con `ProviderTimeout` |
| `post_json` (`http.py`) | client HTTP condiviso: errori di rete e HTTP mappati su `ProviderError` / `ProviderTimeout` |

## Esempio minimo, senza rete

```python
from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, SequentialIds
from core.use_cases.execute_request import ExecuteRequest

llm = FakeLLM({"cloud/": {"fail": True}, "ollama/": {"reply": "accesso"}})
uc = ExecuteRequest(llm=llm, ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds())
res = uc.execute("Analizza i trade-off tra monolite e microservizi. " * 20)
print(res.decision.route, res.record.model, res.record.fallback, res.record.fallback_reason)
# cloud ollama/qwen2.5:7b True cloud/gpt-4o: provider non disponibile
```

## Test

`tests/test_use_case_execute.py` (contratto completo) e `tests/test_use_case_ops.py` (report, stress, flywheel, ingest). Mutazioni: fallback mai eseguito, contesto RAG non passato al modello, escalation spenta.

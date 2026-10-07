# Configurazione (`app/composition.py`)

Tutta la configurazione arriva da **variabili d'ambiente**, lette da `Settings` (dataclass con `default_factory`, quindi valutate quando si crea l'oggetto). `./run.sh` carica `.env` prima di ogni comando; `python -m app.main` e `uvicorn` no: lì le variabili vanno esportate.

Template: `.env.example` (da copiare in `.env`, git-ignorato).

## Variabili

### Modelli e provider

| Variabile | Default | Effetto |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama per LLM ed embedding |
| `SAI_LOCAL_MODEL` | `ollama/qwen2.5:7b` | modello della rotta `local` e dei fallback |
| `SAI_RAG_MODEL` | `ollama/qwen2.5:7b` | modello della rotta `local_rag` |
| `SAI_CLOUD_MODEL` | `cloud/gpt-4o` | modello della rotta `cloud` e dell'escalation |
| `OPENAI_API_KEY` | vuota | chiave del provider cloud; **vuota ⇒ `UnavailableLLM`** sul prefisso `cloud/` |
| `OPENAI_BASE_URL` | `https://api.openai.com` | qualsiasi endpoint OpenAI-compatible (senza `/v1`) |
| `VLLM_BASE_URL` | vuota | server vLLM per i modelli `vllm/…`; vuota ⇒ `UnavailableLLM` |
| `SAI_EMBED_MODEL` | `nomic-embed-text` | modello di embedding in Ollama |
| `SAI_EMBED_DIM` | `768` | dimensione dei vettori (deve coincidere col modello) |

### Gateway LiteLLM

| Variabile | Default | Effetto |
|---|---|---|
| `SAI_GATEWAY_URL` | vuota | se valorizzata, **tutte** le rotte passano dal gateway |
| `SAI_GATEWAY_KEY` | vuota (`.env.example`: `sk-switchable-demo`) | `Authorization: Bearer` verso il gateway; deve coincidere con `LITELLM_MASTER_KEY` del compose |

### Policy

| Variabile | Default | Effetto |
|---|---|---|
| `SAI_LOCAL_ONLY` | `false` | regola `local_only`: cloud vietato (`1`, `true`, `yes`, `on` = attivo) |
| `SAI_BUDGET_EUR` | `0` | budget cloud giornaliero; `0` = nessun budget (budget guard spento) |
| `SAI_BUDGET_GUARD_EUR` | `0` | sotto questo residuo scatta `budget_guard` |
| `SAI_CLOUD_TIMEOUT_S` | `60` | timeout delle chiamate `cloud/…`; oltre ⇒ fallback |
| `SAI_COMPRESS` | `extractive` | `extractive` o qualsiasi altro valore (= nessuna compressione) |
| `SAI_COMPRESS_THRESHOLD` | `1500` | token stimati oltre i quali si comprime (solo rotta cloud) |

### Advisor

| Variabile | Default | Effetto |
|---|---|---|
| `SAI_ADVISOR` | vuota | `rizzo` o `openjev`; vuota = advisor spento |
| `SAI_ADVISOR_MODE` | `shadow` | `off`, `shadow`, `active`, `fallback` |
| `SAI_ADVISOR_MIN_P` | `0.6` | sotto questa probabilità vince la regola |
| `SAI_ADVISOR_URL` | vuota | sovrascrive l'endpoint di default del motore |
| `SAI_ADVISOR_BOTH_ORDERS` | `false` | doppia interrogazione con candidati invertiti |

### Osservabilità e dati

| Variabile | Default | Effetto |
|---|---|---|
| `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | vuote | se **tutte e tre** valorizzate, le trace vanno anche a Langfuse |
| `SAI_DATA_DIR` | `<repo>/data` | registro, trace, indice, kb, flywheel |
| `SAI_RAG_INDEX_DIR` | `<data>/rag_index` | indice RAG separato (i benchmark lo usano per isolare i run) |

### Solo `run.sh serve`

| Variabile | Default | Effetto |
|---|---|---|
| `SAI_HOST` | `0.0.0.0` | indirizzo d'ascolto dell'API (`python -m app.main serve` usa invece `127.0.0.1`) |
| `SAI_PORT` | `8088` | porta dell'API |

## Le due modalità di instradamento (`build_llm`)

### Diretta (default, `SAI_GATEWAY_URL` vuota)

`PrefixRouterLLM` con:

| Prefisso | Adapter |
|---|---|
| `ollama/` | `OllamaLLM(OLLAMA_BASE_URL)` |
| `vllm/` | `OpenAICompatLLM(VLLM_BASE_URL)` (toglie il prefisso) oppure `UnavailableLLM` |
| `cloud/` | `OpenAICompatLLM(OPENAI_BASE_URL, OPENAI_API_KEY)` (toglie il prefisso: `cloud/gpt-4o` → `gpt-4o`) oppure `UnavailableLLM` |

### Gateway (`SAI_GATEWAY_URL` valorizzata)

Un solo `OpenAICompatLLM` verso LiteLLM per tutti e tre i prefissi. I nomi interni diventano alias (`GATEWAY_ALIASES`, coerenti con `infra/litellm.yaml`):

| Nome interno | Alias LiteLLM |
|---|---|
| `SAI_CLOUD_MODEL` | `smart-cloud` |
| `vllm/…` | `fast-vllm` |
| `SAI_RAG_MODEL`, se diverso da `SAI_LOCAL_MODEL` | `rag-local` |
| tutto il resto | `fast-local` |

`served_as`: se si è chiesto un `cloud/…` e il campo `model` della risposta non contiene `gpt`, `claude`, `deepseek`, `smart-cloud`, `o1`, `o3`, il record riporta il modello locale ⇒ il fallback del gateway diventa visibile come `fallback=True`.

## Il `Container`

Costruito una volta per processo (l'API lo tiene in `lru_cache`). Grafo:

| Attributo | Oggetto |
|---|---|
| `ledger` | `JsonlLedger(data/calls.jsonl)` |
| `traces` | `JsonlTraceStore(data/traces.jsonl)` |
| `metrics` | `PrometheusMetrics()` (registry dedicato) |
| `langfuse` | `LangfuseTracer` o `None` |
| `llm` | `build_llm(settings)` |
| `embedder` | `OllamaEmbedder` |
| `index` | `HnswIndex(rag_index_dir, dim)` |
| `docs` | `FileSystemDocuments(README.md, MISSION.md, docs/, wiki/, infra/ + data/kb + git log)` |
| `retriever`, `build_index` | `RetrieveContext(top_k=3)`, `BuildRagIndex` |
| `execute` | `ExecuteRequest(...)` con budget, local-only, compressore, timeout, advisor |
| `report`, `stress`, `flywheel`, `ingest` | casi d'uso costruiti su `execute`, `ledger`, `traces` |

Nei test si passano `settings`, `llm` ed `embedder` al costruttore per sostituire i pezzi esterni (`tests/test_wiring.py`).

## Esempi

Solo locale, modello più piccolo, dati in una cartella temporanea:

```bash
export SAI_LOCAL_ONLY=true SAI_LOCAL_MODEL=ollama/qwen2.5:1.5b SAI_RAG_MODEL=ollama/qwen2.5:1.5b SAI_DATA_DIR=/tmp/sai
.venv/bin/python -m app.main demo --dry-run
```

Cloud tramite un endpoint compatibile diverso da OpenAI:

```
OPENAI_BASE_URL=https://api.example-provider.com
OPENAI_API_KEY=...
SAI_CLOUD_MODEL=cloud/nome-del-modello
```

Tutto via LiteLLM (dopo `./run.sh up core`):

```
SAI_GATEWAY_URL=http://localhost:4000
SAI_GATEWAY_KEY=sk-switchable-demo
```

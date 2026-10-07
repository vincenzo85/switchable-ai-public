# switchable_ai — Architettura AI "switchabile"

> **Local when possible. Cloud when needed. Observable always.**

Codice e numeri misurati del talk *"Architettura AI Switchabile: Routing Dinamico, RAG Locale e Ottimizzazione TCO tra Cloud e On-Premise"*.

Un gateway OpenAI-compatible decide dove vola ogni richiesta:
- **modello locale** (Ollama, vLLM) per il lavoro ripetitivo;
- **cloud** per il ragionamento complesso, sempre con fallback locale;
- **RAG locale** per la documentazione interna.

Le regole che proteggono dati e budget sono deterministiche e nessun modello le può scavalcare. Ogni richiesta lascia una traccia con token, costo reale, latenza e rotta.

Generato con lo scaffolder `hexainit`: architettura esagonale (il `core/` non conosce né rete né librerie), test prima del codice, mutation testing. Sostituisce un prototipo precedente (`router_llm_legacy`, non pubblicato).

## Avvio rapido

```bash
make setup                         # crea .venv e installa le dipendenze
cp .env.example .env               # le chiavi cloud sono OPZIONALI
./run.sh demo                      # la demo del talk: 4 richieste, 3 rotte, fallback reale
```

Serve Ollama con `qwen2.5:7b` e `nomic-embed-text`. Senza chiave cloud la rotta cloud fallisce subito e la richiesta passa al modello locale: è voluto, è la tesi del talk.

Lo stack completo (gateway, osservabilità, workflow) si avvia così:

```bash
./run.sh up                        # LiteLLM :4000 · Langfuse :3011 · Grafana :3012 · n8n :5678
./run.sh serve                     # API :8088 (OpenAI-compatible, webhook n8n, /metrics)
./run.sh rag-build                 # indice della knowledge base locale
./run.sh deck                      # la presentazione 3D (tasti: → ← F P D B ?)
```

Tutti i comandi: `./run.sh help`. La guida passo passo è in [docs/GUIDA-PER-NEGATI.md](docs/GUIDA-PER-NEGATI.md).

## Dall'abstract al codice

| Promessa dell'abstract | Dove | Prova misurata |
|---|---|---|
| AI Gateway LiteLLM, routing dinamico, fallback | `core/domain/policy.py`, `core/use_cases/execute_request.py`, `infra/litellm.yaml` | `benchmarks/results/tco.json` |
| Ollama / vLLM | `adapters/llm/providers.py`, `benchmarks/run_vllm.py` | `vllm_vs_ollama.json` |
| Docker self-hosted | `infra/docker-compose.yml` | healthcheck verdi |
| n8n | `infra/n8n/workflows/`, `core/use_cases/ingest.py` | `n8n_ingest.json` |
| RAG locale per l'SDLC | `core/use_cases/rag.py`, `docs/` | `rag.json` |
| MCP | `adapters/mcp/server.py` | `mcp.json` (handshake stdio reale) |
| Langfuse, Grafana | `adapters/observability/sinks.py`, `infra/grafana/` | `talk/assets/*.png` |
| Costo reale per token, TCO | `core/domain/pricing.py`, `core/use_cases/report.py` | `tco.json` (con TCO ammortizzato) |
| Token compression | `adapters/compression/extractive.py` | `compression.json` |
| Data Flywheel | `core/use_cases/flywheel.py` | `stress.json#flywheel` |
| Stress test (dagli appunti del talk) | `core/use_cases/stress.py`, `benchmarks/run_stress.py` | `stress.json` |
| Router appreso (Rizzo Flow, Open-Jev) | `core/use_cases/advisor.py`, `adapters/llm/systemone.py` | `advisor.json` |

## I numeri, onestamente

Ogni numero del talk viene da `benchmarks/results/*.json`. È aggregato in `talk/numbers.json`, con la sua fonte e la data di misura. Il deck e il canovaccio lo citano per chiave e i test falliscono se una cifra non ha fonte o è vecchia.

Alcuni risultati sono scomodi e restano scritti:
- **Il risparmio della demo è un rapporto di prezzi.** Il "−96%" conta solo l'energia del locale. Con l'ammortamento dell'hardware, il locale costa più del cloud se la GPU lavora meno del 12% del tempo (l'ipotesi hardware è dichiarata).
- **Le regole del router non generalizzano bene.** Fanno 100% sui casi scritti dall'autore, ma il 53% su un set di controllo scritto con parole diverse. Sbagliano sempre verso il risparmio.
- **Lo stress test usa un cloud simulato, dichiarato come tale.** Risponde un modello locale, pagato a listino cloud, con rallentamenti programmati.

## Struttura

```
core/        dominio, porte e casi d'uso puri (solo stdlib)
adapters/    Ollama, OpenAI-compatible/LiteLLM/vLLM, /v1/systemone, hnswlib, JSONL, Prometheus, Langfuse, MCP, compressione
app/         composition root (env), CLI, API FastAPI
infra/       docker compose, LiteLLM, Prometheus, Grafana, workflow n8n
benchmarks/  benchmark reali → results/*.json → build_numbers.py → talk/numbers.json
talk/        canovaccio, deck 3D, replay, screenshot
docs/        architettura, runbook, ADR, bibliografia verificata, guida
tools/       mutation testing, verifica bibliografia, screenshot e PDF del deck
```

## Cosa non c'è in questa versione pubblica

- Le risposte preparate per il Q&A del talk e gli appunti da cui è nata la bibliografia (`tools/verify_bibliography.py` li legge da `SAI_BIB_ANALISI`).
- I modelli Rizzo Flow / Open-Jev: `benchmarks/run_advisor.py` li cerca in `OPENJEV_BENCH_DIR`. Senza, l'advisor resta spento e i risultati misurati sono in `benchmarks/results/advisor.json`.
- I log grezzi dei server avviati dai benchmark.

Le credenziali in `infra/docker-compose.yml` sono di demo e i servizi ascoltano solo su `127.0.0.1`.

## Qualità

```bash
./run.sh test        # suite completa (core, adapter, cablaggio, deck in Chrome headless)
./run.sh mutation    # 15 sabotaggi deliberati: i test devono diventare rossi
```

Le scelte principali sono spiegate negli ADR in `docs/adr/`; il percorso di lavoro è in `docs/RCCV_LOG.md`.

## Licenza

Il codice è distribuito con licenza [MIT](LICENSE). I file di terze parti in `talk/deck/vendor/` mantengono la loro licenza: font sotto SIL Open Font License 1.1 (`vendor/fonts/OFL-*.txt`), icone Lucide sotto ISC (`vendor/icons/LICENSE`).

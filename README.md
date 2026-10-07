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

Tutti i comandi: `./run.sh help`.

## Documentazione

| Wiki | Per chi | Da dove partire |
|---|---|---|
| **Per negati** | parti da zero e vuoi far funzionare le cose | [wiki/per-negati](wiki/per-negati/00-inizia-qui.md) |
| **Tecnica** | sviluppi, integri o gestisci il sistema | [wiki/tecnica](wiki/tecnica/00-panoramica.md) |
| **Didattica** | vuoi capire i concetti, con esempi ed esercizi risolti | [wiki/didattica](wiki/didattica/00-percorso.md) |

Indice completo: [wiki/00_index.md](wiki/00_index.md).

## Comandi principali

| Comando | Cosa fa | Serve Ollama? |
|---|---|:---:|
| `./run.sh route "<prompt>"` | dice dove andrebbe la richiesta e perché (solo regole sul testo) | no |
| `./run.sh demo-dry` | le decisioni dei 4 task della demo, con le impostazioni del `.env` | no |
| `./run.sh demo` | la demo completa: decisione, esecuzione, fallback, costo | sì |
| `./run.sh ask "<prompt>" [--max-tokens N]` | esegue una richiesta end-to-end (JSON con risposta, rotta, costo) | sì |
| `./run.sh rag-build` | costruisce l'indice dei documenti (`docs/`, `wiki/`, `infra/`, `data/kb/`, git log) | sì |
| `./run.sh rag "<domanda>"` | mostra i 3 pezzi di documento più pertinenti | sì |
| `./run.sh ingest <file.md>` | aggiunge un documento: classifica, estrae metadati, checklist QA, reindicizza | sì |
| `./run.sh report [--json]` | costi reali vs tutto-cloud, latenze p50/p95, fallback, violazioni di residency | no |
| `./run.sh stress [N]` | stress test su N richieste miste (default 100) | sì |
| `./run.sh flywheel` | esporta le richieste anonimizzate in un dataset di fine-tuning | no |
| `./run.sh serve` | API OpenAI-compatible su `:8088` (+ webhook n8n, `/metrics`) | per rispondere |
| `./run.sh mcp` | server MCP stdio con 6 tool | per rispondere |
| `./run.sh up [core\|obs\|n8n]` / `down` | stack Docker: LiteLLM, Langfuse, Prometheus, Grafana, n8n | — |
| `./run.sh bench <nome>` / `numbers` | rifà un benchmark / rigenera `talk/numbers.json` | sì |
| `./run.sh test` · `make check` · `./run.sh mutation` | test · test + confini esagonali · mutation testing | no |
| `./run.sh deck` · `deck-redteam` | la presentazione 3D · la versione red team | no |

## Casi d'uso

| Se sei… | e ti serve… | la torre fa… | parti da |
|---|---|---|---|
| un team che classifica ticket, email, reclami | farlo in volume senza pagare il cloud | rotta `local`, escalation al cloud solo se la risposta non è valida | `./run.sh ask`, API `/v1/chat/completions` |
| un ufficio che estrae dati da fatture e ordini | estrazione ripetitiva, a costo quasi zero | rotta `local` anche per documenti lunghi (soglia ×5) | `./run.sh ask "Estrai …"` |
| un team di sviluppo con runbook e ADR | risposte sulla documentazione interna, con le fonti | rotta `local_rag`, i documenti non escono | `rag-build` + `ask "Nella documentazione…"` |
| un architetto o un analista | ragionamento lungo e complesso | rotta `cloud` con fallback locale | `.env` con `OPENAI_API_KEY` |
| un DPO o un'azienda regolamentata | garanzia che i dati personali non escano | regola `data_residency`: cloud vietato, anche per l'osservabilità | `./run.sh route` per verificare |
| FinOps / chi gestisce il budget | un tetto alla spesa cloud e il costo vero | `budget_guard`, registro costi, TCO ammortizzato | `SAI_BUDGET_EUR`, `./run.sh report` |
| MLOps | metriche, trace, dashboard | Prometheus, Grafana, Langfuse | `./run.sh up` + `./run.sh serve` |
| chi ha già un'app OpenAI | adottare il router senza riscrivere codice | API OpenAI-compatible: cambia solo il `base_url` | `./run.sh serve` |
| chi usa agenti AI | dare al proprio agente routing, RAG e costi | server MCP con 6 tool | `.mcp.json`, `./run.sh mcp` |
| chi automatizza flussi documentali | intake automatico dei documenti SDLC | workflow n8n → webhook → classifica, estrai, indicizza, QA | `infra/n8n/workflows/` |

## Hands-on: per fare questo, fai così

**Vedere dove andrebbe una richiesta (senza modelli)**
```bash
./run.sh route "Classifica questo ticket: non riesco a fare login"     # → local
./run.sh route "Analizza la pratica del cliente mario.rossi@example.com"   # → local, regola data_residency
```

**Far rispondere il modello locale**
```bash
ollama pull qwen2.5:7b && ollama pull nomic-embed-text
./run.sh ask "Classifica questo ticket in [accesso, fatturazione, bug, altro]: la fattura di marzo è doppia"
```

**Fare domande alla documentazione del progetto**
```bash
./run.sh rag-build
./run.sh ask "Nella documentazione, cosa faccio se il budget cloud è esaurito?"   # risposta con fonti [1], [2]
```

**Aggiungere i tuoi documenti alla knowledge base**
```bash
./run.sh ingest percorso/mio-runbook.md      # finisce in data/kb/ e l'indice viene ricostruito
```

**Vietare il cloud a tutti**
```bash
echo "SAI_LOCAL_ONLY=true" >> .env
./run.sh demo-dry                            # il Task B ora resta in locale: regola local_only
```

**Mettere un tetto di spesa giornaliero al cloud**
```bash
printf 'SAI_BUDGET_EUR=2.00\nSAI_BUDGET_GUARD_EUR=0.20\n' >> .env
```

**Usare un cloud vero**
```bash
printf 'OPENAI_API_KEY=sk-...\nSAI_CLOUD_MODEL=cloud/gpt-4o\n' >> .env     # o un endpoint compatibile con OPENAI_BASE_URL
```

**Collegare un'app che usa già l'SDK OpenAI**
```bash
./run.sh serve
```
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8088/v1", api_key="non-serve")
r = client.chat.completions.create(model="qualsiasi", messages=[{"role": "user", "content": "Classifica: login rotto"}])
print(r.choices[0].message.content, r.model)    # r.model = il modello che ha risposto davvero
```

**Vedere costi e latenze**
```bash
./run.sh report
```

**Vedere le dashboard**
```bash
./run.sh up && ./run.sh serve
curl -s -X POST localhost:8088/v1/stress -H 'Content-Type: application/json' -d '{"n": 10}'
# Grafana http://localhost:3012 · Langfuse http://localhost:3011 (demo@switchable.local / switchable-demo)
```

**Esportare un dataset per il fine-tuning**
```bash
./run.sh flywheel                            # data/flywheel/sft.jsonl, dati personali oscurati
```

**Controllare di non aver rotto niente**
```bash
make check && ./run.sh mutation
```

Altre ricette, con l'output atteso: [wiki/per-negati/03-ricette.md](wiki/per-negati/03-ricette.md).

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

# Infrastruttura (`infra/`)

## Porte

| Servizio | Porta | Dove gira | Ascolta su |
|---|---|---|---|
| API switchable_ai | 8088 | host (`./run.sh serve`) | `SAI_HOST` (default `0.0.0.0`) |
| Ollama | 11434 | host | — |
| vLLM (opzionale) | 8010 | host, venv `.venv-vllm` | 127.0.0.1 |
| LiteLLM | 4000 | Docker, rete host | 127.0.0.1 |
| Langfuse | 3011 → 3000 | Docker, bridge | 127.0.0.1 |
| Postgres di Langfuse | 5432 | Docker, bridge | solo rete interna |
| Prometheus | 9091 | Docker, rete host | 127.0.0.1 |
| Grafana | 3012 | Docker, rete host | 127.0.0.1 |
| n8n | 5678 | Docker, rete host | 127.0.0.1 |
| Rizzo Flow (opzionale) | 8017 | host | 127.0.0.1 |
| Open-Jev (opzionale) | 8791 | host | 127.0.0.1 |

## `docker-compose.yml`

Nome progetto `switchable-ai`. Profili:

| Profilo | Servizi |
|---|---|
| `core` | `litellm` (`ghcr.io/berriai/litellm:main-stable`) |
| `obs` | `langfuse-db` (postgres:16-alpine), `langfuse` (langfuse/langfuse:2), `prometheus` (v3.2.1), `grafana` (11.5.1) |
| `n8n` | `n8n` (n8nio/n8n:latest) |

Perché `network_mode: host`: sulla macchina di sviluppo il firewall scartava il traffico dalla rete bridge di Docker verso l'host, e i servizi che devono **chiamare** l'host (gateway → Ollama, Prometheus → API, n8n → API) non lo raggiungevano. Langfuse resta in bridge perché è l'host a chiamarlo. Vedi `wiki/lessons/docker-firewall-host-network.md`.

Ogni servizio ha un healthcheck. Volumi persistenti: `langfuse_pg`, `n8n_data`.

### Credenziali (solo demo)

| Servizio | Credenziale |
|---|---|
| LiteLLM | master key `${SAI_GATEWAY_KEY:-sk-switchable-demo}` |
| Langfuse | utente `demo@switchable.local` / `switchable-demo`; chiavi progetto `pk-lf-switchable-demo` / `sk-lf-switchable-demo`; `NEXTAUTH_SECRET` e `SALT` demo |
| Postgres | `langfuse` / `langfuse` |
| Grafana | `admin` / `switchable-demo`, anonimo in sola lettura |

Valgono perché tutto ascolta su 127.0.0.1. **Cambiale prima di esporre lo stack in rete.**

## LiteLLM (`litellm.yaml`)

| Alias | Modello | Endpoint |
|---|---|---|
| `fast-local` | `ollama/qwen2.5:7b` | `http://127.0.0.1:11434` |
| `rag-local` | `ollama/qwen2.5:7b` | `http://127.0.0.1:11434` |
| `smart-cloud` | `openai/gpt-4o` | chiave da `OPENAI_API_KEY` |
| `fast-vllm` | `openai/Qwen/Qwen2.5-1.5B-Instruct` | `http://127.0.0.1:8010/v1` |

Fallback del gateway: `smart-cloud → fast-local`, `fast-vllm → fast-local`. `num_retries: 0` (i retry li decide il core), `timeout: 60`, `drop_params: true`.

Per usarlo: `SAI_GATEWAY_URL=http://localhost:4000` (vedi [Configurazione](03-configurazione.md)).

## Prometheus e Grafana

`prometheus.yml`: un job, target `127.0.0.1:8088`, `scrape_interval: 5s`. Grafana: datasource e dashboard dal provisioning, home dashboard = Cockpit.

## n8n (`n8n/workflows/sdlc-document-intake.json`)

Workflow "SDLC document intake":

1. **Webhook** `POST /webhook/sdlc-document`, corpo `{"name", "text"}`;
2. **HTTP Request** a `{{$env.SAI_API}}/webhook/n8n/document` (timeout 10 minuti; `SAI_API=http://127.0.0.1:8088` nel compose);
3. **IF** `data_residency_violations == 0`;
4. sì → risposta JSON `status: landed` con categoria, documento, rotte, modelli, costi, checklist; no → **ALLARME residency** (HTTP 500, `residency_violation`).

Importazione: UI di n8n → *Import from file*, poi attivare il workflow. `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` serve a leggere `SAI_API` dall'ambiente.

Misura reale (`benchmarks/run_ingest.py` → `results/n8n_ingest.json`): 3 documenti, 0 violazioni.

## vLLM

Non è nel compose (Docker sulla macchina di sviluppo non aveva il runtime NVIDIA). `benchmarks/run_vllm.py` lo avvia da `.venv-vllm` sulla porta 8010, misura e lo spegne; prima scarica `qwen2.5:7b` dalla VRAM di Ollama. Per usarlo come rotta: `VLLM_BASE_URL=http://localhost:8010` e un modello `vllm/<nome>`.

## Avvio completo

```bash
./run.sh up                    # core + obs + n8n
docker compose -f infra/docker-compose.yml ps
./run.sh serve                 # in un terminale dedicato
./run.sh rag-build
```

Spegnimento: `./run.sh down` (aggiungi `-v` al comando docker per cancellare i volumi).

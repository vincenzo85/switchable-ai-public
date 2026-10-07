# CLI e MCP

## `run.sh`

Entrypoint unico. Fa `cd` nella cartella del repo, carica `.env` (se c'è) ed esegue con `.venv/bin/python`.

| Comando | Equivale a | Note |
|---|---|---|
| `demo` | `python -m app.main demo` | 4 task, decisione + esecuzione (`--max-tokens` default 300) |
| `demo-dry` | `python -m app.main demo --dry-run` | solo decisioni, **con** contesto |
| `route "<p>"` | `python -m app.main route` | solo regole sul testo, **senza** contesto |
| `ask "<p>" [--max-tokens N]` | `python -m app.main ask` | esecuzione end-to-end, JSON |
| `rag "<q>"` | `python -m app.main rag` | top-3 chunk con score |
| `rag-build` | `python -m app.main rag-build` | ricostruisce l'indice |
| `ingest <file.md>` | `python -m app.main ingest` | flusso n8n da CLI |
| `stress [N]` | `python -m app.main stress --n N --out benchmarks/results/stress_cli.json` | exit 3 se ci sono violazioni di residency |
| `report [--json]` | `python -m app.main report` | tabella markdown o JSON |
| `flywheel` | `python -m app.main flywheel` | `data/flywheel/sft.jsonl` |
| `bench <nome>` | `python benchmarks/run_<nome>.py` | `tco`, `compression`, `vllm`, `advisor`, `stress` (e gli altri `run_*.py`) |
| `numbers` | `python benchmarks/build_numbers.py` | rigenera `talk/numbers.json` |
| `test` | `pytest -q` | |
| `mutation` | `python tools/mutation_check.py` | |
| `check` | test + confini + mutation | il gate completo |
| `serve` | `python -m app.main serve --host $SAI_HOST --port $SAI_PORT` | default `0.0.0.0:8088` |
| `mcp` | `python -m app.main mcp` | server MCP stdio |
| `up [profili]` | `docker compose -f infra/docker-compose.yml --profile … up -d` | default `core obs n8n` |
| `down` | `docker compose … --profile '*' down` | |
| `deck`, `deck-redteam` | build se manca + `xdg-open` | `talk/deck/dist*/index.html` |

## `python -m app.main`

Sottocomandi argparse (`app/main.py`): `health`, `route`, `ask`, `demo`, `rag-build`, `rag`, `report`, `stress` (`--n`, `--seed`, `--out`), `flywheel`, `ingest`, `serve` (`--host`, `--port`), `mcp`. Ogni comando costruisce un `Container` nuovo (eccetto `route` e `health`).

I quattro task della demo sono in `DEMO_TASKS`: A classificazione, B reasoning complesso (testo ripetuto 4 volte per superare la soglia di complessità), C domanda sulla knowledge base, D documento "riservato" (ripetuto 3 volte: complesso **e** sensibile).

## Makefile

| Target | Cosa fa |
|---|---|
| `setup` | `python3 -m venv .venv && pip install -e '.[dev]'` |
| `check` / `test` | pytest + test dei confini |
| `lint-architecture` / `architecture` | solo i confini |
| `mutation` | mutation testing |
| `numbers` | `talk/numbers.json` |
| `deck` | numbers + build del deck |
| `deck-backup` | deck + screenshot + PDF di riserva (serve Chrome) |
| `clean-artifacts` | rimuove `__pycache__` e `.pytest_cache` |

## Server MCP (`adapters/mcp/server.py`)

Trasporto **stdio**. Compatibile con `mcp` 1.x (`FastMCP`) e 2.x (`MCPServer`).

| Tool | Parametri | Ritorna |
|---|---|---|
| `route_prompt` | `prompt: str` | decisione (con contesto) |
| `ask` | `prompt: str, max_tokens: int = 300` | `ExecutionResult.to_dict()` |
| `rag_search` | `question: str` | `{"results": [...]}` o `{"error": ...}` |
| `cost_report` | — | report costi |
| `stress_test` | `n: int = 20, seed: int = 42` | riepilogo senza timeline |
| `flywheel_export` | — | esito dell'export |

Descrizioni volutamente corte: le definizioni dei sei tool pesano circa 1.600 caratteri (~399 token) e viaggiano nel contesto di ogni richiesta dell'agente.

`build_tools(container)` restituisce le funzioni pure: si testano senza avviare il server.

Configurazione client (`.mcp.json` nella radice del repo):

```json
{
  "mcpServers": {
    "switchable-ai": {"command": "./.venv/bin/python", "args": ["-m", "app.main", "mcp"]}
  }
}
```

Il server non carica `.env`: le variabili vanno messe nella sezione `env` della configurazione del client, oppure esportate nella shell che lo avvia.

Smoke test reale (handshake stdio, elenco tool, due chiamate, peso delle definizioni):

```bash
.venv/bin/python tools/mcp_smoke.py      # scrive benchmarks/results/mcp.json
```

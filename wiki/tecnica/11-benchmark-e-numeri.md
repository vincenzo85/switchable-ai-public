# Benchmark e numeri del talk

Ogni numero del talk viene da un benchmark reale. Il percorso è sempre:

```
benchmarks/run_*.py  →  benchmarks/results/*.json  →  benchmarks/build_numbers.py  →  talk/numbers.json  →  deck e canovaccio ({{chiave}})
```

Ogni file di risultato ha un blocco `meta` con `benchmark`, `measured_at`, `git_commit` e `machine` (GPU, CPU, RAM).

## Gli script

| Script (`./run.sh bench <nome>`) | Cosa misura | Richiede | Risultato |
|---|---|---|---|
| `tco` | i 4 task della demo × N run (default 3) con i motori veri; throughput locale; costo ammortizzato | Ollama, indice RAG | `tco.json` |
| `compression` | 20 prompt "ago nel pagliaio": originale vs estrattiva 50%/30%, guidata dalla domanda o agnostica | Ollama | `compression.json` |
| `vllm` | stesso modello (Qwen2.5-1.5B) su Ollama (GGUF Q4_K_M) e vLLM (BF16): TTFT e throughput a concorrenza 1, 4, 16 | GPU, `.venv-vllm` | `vllm_vs_ollama.json` |
| `advisor` | regole vs Rizzo Flow vs Open-Jev sul batch di casa e sul set di controllo | server `/v1/systemone` locali | `advisor.json` |
| `router_tuning` | griglia sul dev, misura unica sul test | come sopra | `router_tuning.json` |
| `stress` | 100 task con budget che si esaurisce, turbolenza programmata, cloud **simulato** dichiarato; poi flywheel | Ollama | `stress.json` |
| `rag` | hit@3 e risposta corretta su 6 domande di riferimento | Ollama, indice | `rag.json` |
| `ingest` | il flusso n8n reale su 3 documenti | stack Docker + API | `n8n_ingest.json` |

Altri risultati: `mcp.json` (`tools/mcp_smoke.py`), `mutation.json` (`tools/mutation_check.py`), `bibliography.json` (`tools/verify_bibliography.py`), `legacy_tco_report_2026-07-03.md` (report storico).

Gli script avviano e spengono da soli i server che servono (vLLM, advisor) e scaricano i modelli dalla VRAM quando non ci stanno insieme (8 GB).

## Risultati principali

| Area | Numero | Chiave |
|---|---|---|
| Demo | €0,0011 reali vs €0,0256 se tutto-cloud (−96%, solo energia) | `tco.cost_real`, `tco.saving_energy_only` |
| TCO | pareggio al 12% di utilizzo GPU | `tco.breakeven_utilization` |
| Stress | 100/100 completati, 4 fallback, 40 budget guard, 0 violazioni, −82% | `stress.*` |
| Router | regole 53% sul controllo; Rizzo tarato 78% | `router.*` |
| RAG | hit@3 100%, risposta corretta 83% | `rag.*` |
| Compressione | guidata −68% token a 100%; agnostica −68% a 70% | `compression.*` |
| vLLM | 6,7× il throughput di Ollama a concorrenza 16; Ollama più veloce a richiesta singola | `vllm.*` |
| MCP | 6 tool, ~399 token di definizioni | `mcp.*` |
| Qualità | mutation 15/15 | `quality.*` |

## `talk/numbers.json`

Generato da `build_numbers.py`. Ogni voce:

```json
"tco.breakeven_utilization": {
  "value": 0.12, "display": "12%", "label": "...",
  "source": "benchmarks/results/tco.json#local_amortized_eur_per_mtok...", "measured_at": "2026-10-03..."
}
```

Le chiavi `lit.*` sono numeri della letteratura, presi solo dagli abstract verificati (`docs/BIBLIOGRAFIA.md`).

## I test che proteggono i numeri

- `tests/test_talk_numbers.py`: nel canovaccio ogni `{{chiave}}` esiste, e la cifra scritta accanto è il `display` attuale;
- `tests/test_deck.py`: ogni chiave nelle slide si risolve, nessuna cifra con unità scritta a mano (i parametri di esperimento sono marcati `data-param`), i numeri mostrati coincidono con `numbers.json`.

## Rifare i numeri

```bash
./run.sh bench tco
./run.sh bench stress
./run.sh numbers          # rigenera talk/numbers.json
./run.sh test             # se una cifra nel canovaccio è vecchia, il test lo dice
make deck                 # ricostruisce la presentazione
```

Note di onestà, scritte anche nei risultati:
- lo stress test usa un **cloud simulato** (`SimulatedCloudLLM`): risponde il modello locale, pagato a listino cloud, con rallentamenti programmati;
- il confronto vLLM/Ollama non è sulla stessa quantizzazione;
- il benchmark di compressione è un compito facile: misura il risparmio, non la qualità in generale.

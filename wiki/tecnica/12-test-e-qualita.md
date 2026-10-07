# Test e qualità

## Regole (da `AGENTS.md` e `DEFINITION_OF_DONE.md`)

- **Test-first**: nessuna feature senza un test che ne definisce il comportamento e che fallisce prima, per il motivo atteso.
- `make check` verde prima di ogni commit.
- **Anti-phantom-feature**: una feature non è completa se non è invocata a runtime, se i suoi test controllano solo stringhe statiche, se il benchmark è finto, o se è documentata ma non cablata. Ogni feature ha un test che fallisce se viene scollegata dalla composition root.
- Ogni classe/porta/adapter significativo ha una pagina in `wiki/classes/`; ogni step che ha insegnato qualcosa ha una voce in `wiki/lessons/`.

## La suite (`tests/`)

| File | Copre |
|---|---|
| `test_domain_policy.py` | classificatore e regole dure, casi limite (intento, confini di parola, documenti lunghi, PII) |
| `test_domain_pricing.py` | prezzario, linearità, TCO ammortizzato |
| `test_domain_text.py` | chunking per sezione, PII scrub, token approssimati |
| `test_use_case_execute.py` | il contratto di `ExecuteRequest`: fallback, timeout, escalation, budget, local-only, RAG, compressione, tracer rotto |
| `test_use_case_ops.py` | report, stress, flywheel, ingest |
| `test_route_advisor.py` | modalità dell'advisor, regole dure rispettate, doppio ordine |
| `test_adapters.py` | adapter reali contro un server HTTP finto locale (`conftest.py`): Ollama, OpenAI-compat, gateway, embedder, hnsw, JSONL, filesystem, compressione, Prometheus, Langfuse, SystemOne, cloud simulato |
| `test_wiring.py` | `Container`, CLI e API (TestClient) cablati davvero |
| `test_architecture_boundaries.py` | `core/` importa solo stdlib e `core/` |
| `test_talk_numbers.py` | numeri del canovaccio aggiornati |
| `test_deck.py`, `test_deck_redteam.py` | il deck in Chrome headless: nessun errore, nessuna rete, numeri con fonte, tempi = 30:00 |

Nessun test chiama servizi veri: Ollama, cloud, Langfuse e advisor sono sostituiti dal server stub di `conftest.py` o dagli adapter di `adapters/memory`.

```bash
./run.sh test                                   # tutta la suite
.venv/bin/python -m pytest tests/test_domain_policy.py -k residency    # un sottoinsieme
make check                                      # suite + confini
```

I test del deck si saltano se manca `google-chrome` (usano Playwright con `channel="chrome"`).

## Adapter in memoria (`adapters/memory`)

| Classe | Cosa fa |
|---|---|
| `FakeLLM(behaviours, default_reply, jitter_seed)` | per prefisso di modello: `fail`, `latency_ms` (oltre il timeout ⇒ `ProviderTimeout`), `reply` (stringa o funzione), `jitter_ms`; registra le chiamate (`calls`, `calls_to(prefix)`) |
| `InMemoryLedger`, `InMemoryTraceStore`, `RecordingMetrics` | sink in memoria |
| `FixedClock(t, step)`, `SequentialIds(prefix)` | tempo e id deterministici |
| `HashEmbedder` | bag-of-words con hashing md5, 256 dimensioni, senza rete |
| `MemoryIndex`, `MemoryDocuments` | indice e documenti in memoria |

Non sono solo mock: `FakeLLM` è anche il motore della turbolenza riproducibile.

## Confini esagonali

`test_architecture_boundaries.py` analizza con `ast` ogni file di `core/` e accetta solo moduli di `sys.stdlib_module_names` o `core.*`. Il confronto è **esatto** sul modulo di primo livello (il template originale confrontava per prefisso e faceva passare `requests` perché inizia con `re`).

Se il test fallisce: il codice che importa la libreria va in un adapter dietro una porta.

## Mutation testing (`tools/mutation_check.py`)

15 sabotaggi deliberati nei punti che reggono la tesi. Per ognuno: applica la modifica, lancia la suite (`pytest -x`), ripristina il file (sempre, `try/finally`). Una mutazione che sopravvive = un test cieco.

| File | Sabotaggio |
|---|---|
| `policy.py` | nulla è mai complesso · la rotta cloud sparisce · il cloud perde il fallback · data residency spenta · budget guard spento · l'intento torna a leggersi dal corpo |
| `pricing.py` | conteggio token rotto · tutto costa zero |
| `execute_request.py` | fallback mai eseguito · contesto RAG non passato · escalation spenta |
| `report.py` | contatore di violazioni cieco |
| `advisor.py` | cloud proposto per dati sensibili · modalità fallback che chiama sempre il modello |
| `text.py` | il flywheel esporta dati personali in chiaro |

```bash
./run.sh mutation         # ~15 run della suite: qualche minuto. Exit 0 = tutte uccise
```

Se rinomini una riga bersaglio, lo script stampa `SKIP … bersaglio non trovato` e la conta come sopravvissuta: aggiorna la mutazione.

## Il deck

`talk/deck/build.py` produce `talk/deck/dist/index.html` autocontenuto (CSS, JS, numeri e replay inline), `presenter.html`, asset e font. `--deck redteam` produce `dist-redteam`. Tempi e speaker notes vengono dal canovaccio (`talk/CANOVACCIO.md`, beat `## X.Y`).

Strumenti: `tools/deck_screens.py` (screenshot di ogni step), `tools/deck_pdf.py` (PDF di riserva), `make deck-backup`.

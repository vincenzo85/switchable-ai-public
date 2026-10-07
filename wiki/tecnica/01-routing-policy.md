# Routing policy (`core/domain/policy.py`)

Il router di base è **deterministico**: niente LLM nella decisione (ADR-001). Due funzioni pubbliche: `classify(prompt)` e `decide_route(prompt, context, catalog)`; più `reroute(...)` per l'advisor.

## Rotte e modelli

Costanti in `core/domain/models.py`:

| Costante | Valore | Modello (da `ModelCatalog`) |
|---|---|---|
| `ROUTE_LOCAL` | `"local"` | `catalog.local` (default `ollama/qwen2.5:7b`) |
| `ROUTE_CLOUD` | `"cloud"` | `catalog.cloud` (default `cloud/gpt-4o`) |
| `ROUTE_LOCAL_RAG` | `"local_rag"` | `catalog.rag` (default `ollama/qwen2.5:7b`) |

I nomi modello hanno un **prefisso di provider** (`ollama/`, `vllm/`, `cloud/`) che decide l'adapter (vedi [Esecuzione](02-esecuzione.md) e [Configurazione](03-configurazione.md)).

## `classify(prompt) → Classification`

### 1. Tipo di task (`kind`)

Si cerca **solo nell'intento**: il primo paragrafo (fino al primo `\n\n`), troncato a `INTENT_WINDOW = 240` caratteri, in minuscolo. Le parole chiave devono comparire **a inizio parola** (regex `(?<!\w)keyword`): `rag` non scatta dentro `paragrafo`, ma `classifica` scatta anche in `classificazione`.

| `kind` | Parole chiave (prefissi) |
|---|---|
| `rag_query` | documentazione, documentation, repository, progetto, docs, rag, runbook, procedura interna, knowledge base |
| `extraction` | estrai, extract, extraction, fattura, dati da, nome, data |
| `classification` | classifica, classify, classification, ticket, reclamo, categorizza, scegli |
| `reasoning` | analizza, analyze, trade-off, progetta, design, disaster recovery, migrazione, reasoning, strategia, ottimizza, valuta |

Se più tipi scattano, **vince la parola chiave che compare prima** nel testo (a parità di posizione, l'ordine della tabella). Se nessuna scatta, `keyword_hit = False` e il tipo è un default deciso dalla complessità (`reasoning` se alta, `classification` se bassa).

### 2. Complessità (`complexity`)

```
factor = 5 se kind ∈ {classification, extraction} altrimenti 1
high  se  len(prompt) > 400·factor  oppure  parole > 80·factor
low   altrimenti
```

Costanti: `COMPLEXITY_CHARS = 400`, `COMPLEXITY_WORDS = 80`, `SIMPLE_KIND_LENGTH_FACTOR = 5`. La lunghezza si misura su **tutto** il prompt.

### 3. Dato sensibile (`sensitive`)

Si cerca su **tutto** il testo (non solo l'intento):
- `SENSITIVE_KEYWORDS`: riservat, confidenzial, confidential, strettamente interno, dati personali di, cartella clinica, stipendi, buste paga;
- `PII_PATTERNS`: email, IBAN italiano, codice fiscale, numero di carta (13–16 cifre con spazi o trattini).

`reasons` raccoglie in italiano ogni indizio usato.

## `decide_route(prompt, context, catalog) → RouteDecision`

### Regole dure

Valutate tutte, in quest'ordine, e accumulate in `rules`:

| Regola | Condizione | Effetto |
|---|---|---|
| `data_residency` | `classification.sensitive` | cloud vietato |
| `local_only` | `context.local_only` | cloud vietato |
| `budget_guard` | `context.budget_remaining_eur is not None and ≤ context.budget_guard_eur` | cloud vietato |

`cloud_allowed = not rules`.

### Decisione

| Caso | Rotta | `fallbacks` | `escalation` | `rules` aggiunte |
|---|---|---|---|---|
| `kind == rag_query` | `local_rag` | `()` | `None` | `knowledge_base` |
| complessità alta e cloud ammesso | `cloud` | `(catalog.local,)` | `None` | `complexity` |
| complessità alta e cloud vietato | `local` | `()` | `None` | — (il motivo cita la prima regola dura) |
| altrimenti | `local` | `()` | `catalog.cloud` se cloud ammesso | — |

Nota: la rotta RAG viene scelta **anche** se il dato è sensibile (resta locale comunque).

### `RouteDecision`

| Campo | Tipo | Significato |
|---|---|---|
| `route` | str | `local` / `cloud` / `local_rag` |
| `model` | str | modello primario |
| `fallbacks` | tuple[str] | modelli da provare in ordine se il primario solleva `ProviderError` |
| `escalation` | str \| None | modello da usare se la risposta non supera il validatore |
| `estimated_cost_class` | str | `near_zero` (locale) / `metered` (cloud) |
| `cloud_allowed` | bool | esito delle regole dure |
| `reason` | str | spiegazione leggibile |
| `rules` | tuple[str] | regole scattate |
| `classification` | `Classification` | `kind`, `complexity`, `sensitive`, `reasons`, `keyword_hit` |

## `reroute(base, route, catalog)`

Ricostruisce la decisione sulla rotta scelta dall'advisor, aggiungendo `advisor` a `rules`. Solleva `ValueError` se si chiede `cloud` quando `base.cloud_allowed` è falso: le regole dure non sono negoziabili.

## Descrizioni delle rotte per l'advisor

`ROUTE_DESCRIPTIONS` (v2, default) e `ROUTE_DESCRIPTIONS_V1` sono i testi che l'advisor legge come "criteri" di scelta. La v2 è stata scelta sul set dev (vedi [Advisor](09-advisor.md)).

## Dove si usa

- `ExecuteRequest.decide_with_advice` costruisce il `RoutingContext` (local-only e budget residuo dal registro) e chiama `decide_route`.
- `./run.sh route` chiama `decide_route` **senza contesto**: mostra solo le regole sul testo.

## Limiti misurati

- 100% sul batch dello stress test, scritto con le stesse parole chiave delle regole: autoreferenziale.
- **53%** sul set di controllo `benchmarks/routing_heldout.py` (32 parafrasi senza parole chiave), con tutti gli errori verso la rotta più economica (12% di RAG riconosciuti, 0% di cloud).

## Test

`tests/test_domain_policy.py`. Mutazioni in `tools/mutation_check.py`: complessità mai alta, rotta cloud sparita, cloud senza fallback, data residency spenta, budget guard spento.

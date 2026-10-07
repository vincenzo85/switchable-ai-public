# Advisor di rotta (`core/use_cases/advisor.py`, `adapters/llm/systemone.py`)

Un modello piccolo e locale fa da "secondo controllore": sceglie tra le rotte **ammesse** dalle regole dure e restituisce una probabilità per ognuna. Decisione di progetto: ADR-003.

## Modalità (`SAI_ADVISOR_MODE`)

| Modalità | Il modello viene chiamato | Chi decide |
|---|---|---|
| `off` | mai | la regola |
| `shadow` (default) | sempre | la regola; l'advisor viene solo misurato |
| `active` | sempre | l'advisor, se la sua probabilità ≥ `SAI_ADVISOR_MIN_P` |
| `fallback` | solo se `classification.keyword_hit` è falso | come `active`, ma solo quando la regola tira a indovinare |

In ogni modalità:
- il cloud **non viene nemmeno offerto** se le regole dure lo vietano;
- se il server non risponde (`ProviderError`) o propone id non offerti, vince la regola e l'errore finisce in `Advice.error`;
- la latenza dell'advisor è sommata a quella della richiesta.

`both_orders` (`SAI_ADVISOR_BOTH_ORDERS`): due chiamate con i candidati in ordine inverso, probabilità mediate. Misurato: nessun guadagno, latenza doppia.

## Stato inviato al modello

```
Request: <prompt, troncato a 1200 caratteri + " …[truncated]">
Signals: <caratteri> chars, <parole> words, kind guess=<kind>, complexity guess=<complexity>
```

Domanda fissa: *"Which route should serve this request? Pick the cheapest route that can answer it well."* Candidati: `(id_rotta, ROUTE_DESCRIPTIONS[id])`.

## Contratto `/v1/systemone`

Richiesta:

```json
{
  "model": "rizzo-latest",
  "state": "Request: ...\nSignals: ...",
  "questions": {
    "decision": {
      "type": "choice",
      "instructions": "Which route should serve this request? ...",
      "criteria": {"local": "small local model: ...", "cloud": "large cloud model: ...", "local_rag": "local search over OUR internal documentation: ..."}
    }
  }
}
```

Risposta attesa:

```json
{"answers": {"decision": {"probabilities": {"local": 0.71, "cloud": 0.21, "local_rag": 0.08}}}}
```

Gli id restituiti devono coincidere **esattamente** con i candidati offerti, altrimenti `ProviderError`. Timeout di default 5 s.

## Motori (`ENGINES`)

| Nome | Endpoint | Modello |
|---|---|---|
| `rizzo` | `http://127.0.0.1:8017/v1/systemone` | `rizzo-latest` (Rizzo Flow accetta solo questo nome) |
| `openjev` | `http://127.0.0.1:8791/v1/systemone` | `open-jev` |

`SAI_ADVISOR_URL` sovrascrive l'endpoint. I due server non stanno insieme in 8 GB di VRAM. Non sono inclusi in questo repository: servono installazioni locali separate.

## Campi registrati

`CallRecord.advisor_engine`, `advisor_choice`, `advisor_p`, `advisor_agreed`, `advisor_applied`, `advisor_latency_ms`; metriche `sai_advisor_decisions_total{engine,agreed,applied}` e `sai_advisor_latency_ms{engine}`.

## Risultati misurati

| Router | Batch di casa (100) | Set di controllo (32) | Latenza aggiunta |
|---|---:|---:|---:|
| regole | 100% | 53% | 0 ms |
| Rizzo Flow (descrizioni v1) | 99% | 66% | 76 ms |
| Open-Jev (v1) | 88% | 66% | 204 ms |
| Rizzo Flow, descrizioni v2, `active` | — | **78%** (dev 86%) | ~90 ms |
| Open-Jev, descrizioni v2 | — | 56% | — |

Protocollo della messa a punto (`benchmarks/run_router_tuning.py`): griglia {active, fallback} × {ordine singolo, doppio} × {v1, v2} solo sul set **dev** (`routing_dev.py`, 42 richieste); la migliore misurata **una volta** sul **test** (`routing_heldout.py`, 32 richieste).

Raccomandazione (ADR-003): `SAI_ADVISOR=rizzo`, `SAI_ADVISOR_MODE=fallback` in produzione; `shadow` per misurare su traffico nuovo.

## Esempio

```bash
export SAI_ADVISOR=rizzo SAI_ADVISOR_MODE=shadow
.venv/bin/python -m app.main ask "Quale fra le due opzioni di deploy conviene per noi?"
# nel record: advisor_choice, advisor_p, advisor_agreed, advisor_latency_ms
```

## Test

`tests/test_route_advisor.py` (con un advisor scriptato) e `tests/test_adapters.py` (contratto, id non offerti, server giù, motore sconosciuto). Mutazioni: l'advisor può proporre il cloud per dati sensibili; la modalità fallback chiama il modello anche quando la regola è sicura.

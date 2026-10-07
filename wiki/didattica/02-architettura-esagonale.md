# 02 — Architettura esagonale

## Obiettivi

- Spiegare porte, adapter e composition root.
- Leggere il codice del progetto sapendo dove cercare ogni cosa.
- Scrivere un adapter nuovo e collegarlo a un caso d'uso senza toccare il core.

## Il concetto

Un sistema AI parla con molte cose esterne e inaffidabili: modelli locali, API cloud, database vettoriali, sistemi di monitoraggio. Se la logica importante (la decisione di rotta, il calcolo dei costi, il fallback) è mescolata alle chiamate HTTP, succede che:
- per testarla serve tutto acceso;
- cambiare fornitore significa riscrivere la logica;
- un errore di una libreria esterna può far crollare tutto.

L'**architettura esagonale** (o *ports and adapters*) separa in tre anelli:

```
  adapters/  ──implementano──▶  core/ports  ◀──usano──  core/use_cases, core/domain
      ▲                                                          ▲
      └──────────── app/composition.py li collega ───────────────┘
```

- **Dominio e casi d'uso** (`core/`): la logica pura. Non sa che esiste Ollama, né HTTP, né il filesystem.
- **Porte** (`core/ports`): le interfacce che il core dichiara. "Mi serve qualcuno che, dato un modello e un prompt, mi restituisca una risposta con i token contati": è `LLMPort`.
- **Adapter** (`adapters/`): le implementazioni concrete delle porte. `OllamaLLM`, `OpenAICompatLLM`, `FakeLLM` sono tutti `LLMPort`.
- **Composition root** (`app/composition.py`): l'unico posto che decide quale adapter concreto usare, a partire dalla configurazione.

## Come è fatto qui

Le porte (`core/ports/__init__.py`):

| Porta | Promessa | Adapter reale | Adapter di test |
|---|---|---|---|
| `LLMPort.complete(model, prompt, max_tokens, timeout_s)` | risposta + token contati dal motore; solo eccezioni di dominio | `OllamaLLM`, `OpenAICompatLLM` | `FakeLLM` |
| `EmbedderPort.embed / embed_query` | vettore normalizzato | `OllamaEmbedder` | `HashEmbedder` |
| `VectorIndexPort.build / search` | indice dei chunk | `HnswIndex` | `MemoryIndex` |
| `CostLedgerPort`, `TraceStorePort`, `MetricsPort`, `TracerPort` | registrare | JSONL, Prometheus, Langfuse | in memoria |
| `ClockPort`, `IdGeneratorPort` | tempo e id | `SystemClock`, `FlightIds` | `FixedClock`, `SequentialIds` |

Anche **l'orologio** è una porta: così un test può fissare "oggi" e verificare che il budget giornaliero si azzeri a mezzanotte, senza aspettare.

Due regole lo rendono vero, non solo un disegno:

1. **Il core importa solo la standard library.** Lo verifica un test (`tests/test_architecture_boundaries.py`) che legge ogni file di `core/` con `ast` e fallisce se trova `import requests`, `import hnswlib` o un import da `adapters`.
2. **Gli adapter traducono le eccezioni.** `adapters/llm/http.py` cattura gli errori di `urllib` e solleva `ProviderError` o `ProviderTimeout` (`core/domain/errors.py`). Il core non vedrà mai un `URLError`: vede solo "il provider non ha risposto", e sa cosa fare (fallback).

## Esempio svolto — un adapter in dieci righe

Un "modello" che risponde ripetendo il prompt in maiuscolo, collegato al vero caso d'uso `ExecuteRequest`:

```python
from core.ports import LLMPort
from core.domain.models import LLMResult
from adapters.memory import FixedClock, InMemoryLedger, SequentialIds
from core.use_cases.execute_request import ExecuteRequest

class EchoLLM(LLMPort):
    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        return LLMResult(text=prompt.upper()[:40], model=model,
                         tokens_in=len(prompt) // 4, tokens_out=10, latency_ms=1)

uc = ExecuteRequest(llm=EchoLLM(), ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds())
r = uc.execute("Classifica questo ticket: login rotto")
print(r.text, "|", r.record.model, r.record.cost_eur, r.record.cost_if_cloud_eur)
```

Output:

```
CLASSIFICA QUESTO TICKET: LOGIN ROTTO | ollama/qwen2.5:7b 3.8e-06 8.74e-05
```

Cosa è successo: la decisione di rotta, il calcolo del costo e la registrazione sono quelli veri. Abbiamo cambiato solo il "motore". Il core non se n'è accorto.

## Esercizi

1. ★ Apri `app/composition.py` e trova la classe `Container`. Elenca quali porte riceve `ExecuteRequest` e quale adapter concreto viene passato per ciascuna.
2. ★★ Scrivi un adapter `SlowLLM` che risponde dopo `latency_ms=5000` e solleva `ProviderTimeout` se `timeout_s` è più piccolo. Collegalo a `ExecuteRequest` con `cloud_timeout_s=1` e una richiesta complessa: cosa succede? (Suggerimento: guarda come lo fa `FakeLLM` in `adapters/memory/__init__.py`.)
3. ★★ Aggiungi temporaneamente `import requests` in cima a `core/domain/pricing.py` e lancia `make check`. Quale test fallisce e con quale messaggio? Poi togli la riga.
4. ★★★ Scrivi un `TracerPort` che stampa una riga per ogni richiesta (`request_id`, rotta, costo) e passalo come `tracer` a `ExecuteRequest`. Poi fallo sollevare un'eccezione: la richiesta fallisce? Perché? (Guarda `_observe`.)

## Da ricordare

- Il core dichiara **di cosa ha bisogno** (porte); gli adapter dicono **come**; solo la composition root decide **quale**.
- I confini sono verificati da un test, non solo dalla buona volontà.
- Gli adapter traducono gli errori esterni in errori di dominio: è così che il fallback diventa logica di business e non un `try/except` sparso.

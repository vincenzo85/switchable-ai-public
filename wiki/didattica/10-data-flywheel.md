# 10 — Data Flywheel

## Obiettivi

- Capire come le richieste di oggi diventano dati per migliorare il modello locale di domani.
- Anonimizzare un dataset prima di usarlo.
- Collegare il flywheel al TCO.

## Il concetto

Ogni richiesta lascia una **trace**: domanda e risposta complete, rotta, modello. Accumulate, sono un dataset prezioso:
- le risposte date dal **cloud** sono esempi di ciò che il modello locale oggi non sa fare: si possono usare per **insegnarglielo** (*distillazione*);
- le risposte locali corrette confermano cosa sa già fare.

Il ciclo (volano):

```
richieste → trace → dataset anonimizzato → fine-tuning del modello locale
    ▲                                                   │
    └──── il locale sa fare di più ◀── più rotte locali ┘
```

E il collegamento con i costi: più lavoro al locale = **più utilizzo** della GPU = TCO locale più basso ([lezione 06](06-costi-veri-e-tco.md)).

In letteratura: un modello addestrato sul proprio traffico che serve il 50% delle richieste di un'azienda (`lit.flywheel`).

### Prima regola: anonimizzare

Le trace contengono dati personali. Prima di farne un dataset bisogna sostituirli con segnaposto (`<EMAIL>`, `<IBAN>`, `<CF>`, `<CARD>`, `<PHONE>`), togliere i duplicati e le risposte vuote.

## Come è fatto qui

- `core/use_cases/flywheel.py`: `ExportFlywheel`.
- `core/domain/text.py`: `scrub_pii` (gli stessi pattern del router, più i telefoni).
- Formato di uscita: una riga JSON per esempio, formato chat (`messages`: utente, assistente) più `meta` (rotta, modello, `teacher` = la risposta viene dal cloud).
- Comando: `./run.sh flywheel` → `data/flywheel/sft.jsonl`.

Lo stato attuale, scritto nella roadmap: **il dataset esiste, l'addestramento no.**

## Esempio svolto

```python
from core.domain.text import scrub_pii
print(scrub_pii("Scrivi a anna@example.com, IBAN IT60X0542811101000000123456, tel +39 333 1234567"))

from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, InMemoryTraceStore, SequentialIds
from core.ports import DatasetSinkPort
from core.use_cases.execute_request import ExecuteRequest
from core.use_cases.flywheel import ExportFlywheel

class ListSink(DatasetSinkPort):
    def write(self, name, rows):
        self.rows = rows
        return f"memoria:{name}"

traces, sink = InMemoryTraceStore(), ListSink()
uc = ExecuteRequest(llm=FakeLLM({"ollama/": {"reply": "accesso"}, "cloud/": {"reply": "piano in 3 fasi"}}),
                    ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds(), tracer=traces)
uc.execute("Classifica il ticket di anna@example.com: login rotto")
uc.execute("Classifica il ticket di anna@example.com: login rotto")          # duplicato
uc.execute("Analizza i trade-off tra monolite e microservizi. " * 20)       # va in cloud
print(ExportFlywheel(traces, sink).execute())
print(sink.rows[0]["messages"][0]["content"])
```

Output:

```
('Scrivi a <EMAIL>, IBAN <IBAN>, tel <PHONE>', 3)
{'traces': 3, 'exported': 2, 'duplicates_skipped': 1, 'empty_skipped': 0, 'pii_redactions': 1, 'distillation_candidates': 1, 'path': 'memoria:sft'}
Classifica il ticket di <EMAIL>: login rotto
```

- 3 trace, 1 duplicato saltato, 2 esempi esportati;
- 1 dato personale oscurato (quello del duplicato non conta: è stato scartato);
- 1 candidato alla distillazione: la risposta del cloud.

Nello stress test reale: 100 trace → 49 esempi, 51 duplicati, 4 dati personali oscurati, 10 risposte cloud da insegnare al locale.

## Esercizi

1. ★ Prova `scrub_pii` su un testo con un codice fiscale (`RSSMRA80A01H501U`) e un numero di carta (`4111 1111 1111 1111`). Cosa esce?
2. ★ Perché i duplicati si riconoscono **dopo** l'anonimizzazione (l'hash è calcolato sul prompt già ripulito)? Cosa succederebbe con due ticket uguali di due clienti diversi?
3. ★★ Il campo `feedback` delle trace è sempre `None`. Proponi un modo per riempirlo (da dove arriverebbe il voto?) e come lo useresti per filtrare il dataset.
4. ★★ Perché le risposte "cloud" ottenute in **fallback** (risposta del locale, rotta cloud) **non** sono candidate alla distillazione? Guarda come si calcola `teacher`.
5. ★★★ Una mutazione del progetto sabota `scrub_pii` ("il flywheel esporta dati personali in chiaro"). Quale test la uccide? Scrivi un altro test che la ucciderebbe.

## Da ricordare

- Le trace sono il materiale per migliorare il modello locale; le risposte del cloud sono gli esempi più preziosi.
- Prima di tutto: anonimizzare, deduplicare, scartare il vuoto.
- Il flywheel e il TCO sono lo stesso argomento: più lavoro al locale, più utilizzo, meno costo.

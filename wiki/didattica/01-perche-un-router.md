# 01 — Perché un router

## Obiettivi

- Spiegare i tre assi su cui si sceglie dove far girare una richiesta AI: **costo, qualità, privacy**.
- Riconoscere quali richieste sono "da locale" e quali "da cloud".
- Sapere cosa dice la letteratura sul routing tra modelli, con numeri verificati.

## Il concetto

### Il jet per il latte

Un'azienda che usa l'AI riceve richieste molto diverse:
- "Questo ticket parla di login o di fatture?" (classificazione, una parola di risposta);
- "Estrai fornitore, data e importo da questa fattura" (estrazione);
- "Come si riavvia il servizio secondo il nostro runbook?" (domanda sui documenti interni);
- "Proponi un piano di migrazione in tre fasi con rischi e mitigazioni" (ragionamento lungo).

Mandarle tutte allo stesso modello grande in cloud è come usare un jet per comprare il latte: funziona, ma paghi la potenza anche quando non serve, e porti fuori casa dati che potevano restare dentro.

### I tre assi

| Asse | Locale | Cloud |
|---|---|---|
| **Costo** | quasi solo energia, ma l'hardware si paga anche quando è fermo | a consumo, per token |
| **Qualità** | ottima su compiti semplici e ripetitivi; limitata sul ragionamento lungo | migliore sul ragionamento complesso |
| **Privacy** | il dato non esce | il dato va da un fornitore esterno |

A questi si aggiungono **latenza** (un modello locale piccolo risponde in decine di millisecondi a un compito breve; il cloud ha la rete in mezzo) e **disponibilità** (il cloud può rallentare, avere limiti di frequenza, cadere).

### La risposta: una torre di controllo

Invece di scegliere una volta per tutte "tutto cloud" o "tutto in casa", si mette un componente in mezzo, il **router**, che decide richiesta per richiesta. Tre piste:

- `local` — modello locale per il lavoro ripetitivo;
- `cloud` — modello grande per il ragionamento complesso, **sempre con un piano B locale**;
- `local_rag` — ricerca nei documenti interni, che non escono.

E **regole dure** che vengono prima di tutto: un dato sensibile non va in cloud, mai; se il budget finisce, si resta in locale.

## Cosa dice la ricerca

Numeri presi solo dagli abstract verificati (`docs/BIBLIOGRAFIA.md`), aggregati in `talk/numbers.json`:

| Lavoro | Risultato | Chiave |
|---|---|---|
| FrugalGPT | fino a −98% di costo a parità di qualità con una cascata di modelli | `lit.frugalgpt` |
| RouteLLM | costi dimezzati con un router appreso | `lit.routellm` |
| Patil (economia dell'inferenza) | penalità di sottoutilizzo della GPU da 2,5× a 24× | `lit.patil` |
| LLMLingua | compressione dei prompt fino a 20× | `lit.llmlingua` |
| Data flywheel in produzione | un modello addestrato sul proprio traffico serve il 50% delle richieste | `lit.flywheel` |

E un avvertimento (Shafran et al. 2025, "Rerouting LLM Routers"): un router fatto con un LLM può essere **manipolato** con sequenze avversarie che spingono tutte le richieste verso il modello costoso. Per questo, in questo progetto, le regole dure non sono mai affidate a un modello (ADR-001).

## Come è fatto qui

- La decisione: `core/domain/policy.py` → [lezione 03](03-routing-deterministico.md).
- L'esecuzione con piano B: `core/use_cases/execute_request.py` → [lezione 04](04-fallback-e-resilienza.md).
- Il conto: `core/domain/pricing.py` → [lezione 06](06-costi-veri-e-tco.md).

## Esempio svolto

```bash
./run.sh demo-dry
```

Le quattro richieste della demo atterrano su tre piste diverse:

| Task | Rotta | Perché |
|---|---|---|
| A — classifica un ticket | `local` | parola chiave "classifica", testo breve |
| B — analisi lunga dei trade-off | `cloud` (fallback `local`) | "analizza", testo oltre 400 caratteri |
| C — domanda sulla documentazione | `local_rag` | "documentazione", "repository" nella prima frase |
| D — documento "riservato" | `local` | regola `data_residency`: il cloud è vietato |

## Esercizi

1. ★ Per ciascuna di queste richieste, scegli la pista che useresti e scrivi il perché in una riga: (a) tradurre in inglese un'etichetta di prodotto; (b) riassumere il verbale di un consiglio di amministrazione; (c) "come si fa il rilascio da noi?"; (d) scrivere la strategia commerciale per il prossimo anno.
2. ★★ Pensa a un'azienda reale che conosci. Elenca cinque tipi di richieste AI che potrebbe fare e classificale sui tre assi (costo, qualità necessaria, sensibilità del dato).
3. ★★ Perché il piano B della rotta cloud è il modello locale e non un secondo fornitore cloud? Elenca un vantaggio e uno svantaggio.

## Da ricordare

- Non esiste "il modello migliore" in assoluto: esiste il modello giusto per **quella** richiesta, sotto vincoli di costo, qualità e privacy.
- Il router sceglie richiesta per richiesta; le regole su privacy e budget vengono prima di qualsiasi ottimizzazione.
- Il cloud ha sempre un piano B locale: niente lock-in, niente blocchi se il fornitore cade.

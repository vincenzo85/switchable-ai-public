# Wiki didattica — il percorso

Questa wiki usa `switchable_ai` come **caso di studio** per imparare come si progetta un sistema AI che sceglie dove far girare ogni richiesta, quanto costa davvero e come si dimostra che funziona.

È diversa dalle altre due:
- la [wiki per negati](../per-negati/00-inizia-qui.md) ti dice **cosa digitare**;
- la [wiki tecnica](../tecnica/00-panoramica.md) ti dice **come è fatto**;
- questa ti spiega **perché** è fatto così, con esempi svolti ed esercizi.

## A chi serve

Sviluppatori, studenti, MLOps, architetti che vogliono capire:
- quando conviene un modello locale e quando il cloud;
- come si costruisce un router di richieste e quali sono i suoi limiti;
- come si misura un costo AI senza ingannarsi;
- come si scrive codice testabile attorno a componenti esterni inaffidabili (modelli, reti, API).

## Prerequisiti

- Python di base (classi, funzioni, dizionari);
- aver installato il progetto ([installazione](../per-negati/01-installazione.md)): servono solo `make setup` e `.venv`. **Nessun esercizio richiede Ollama o internet**: usano gli adapter in memoria di `adapters/memory`.

## Come funziona ogni lezione

1. **Obiettivi**: cosa saprai fare alla fine.
2. **Il concetto**, spiegato senza codice.
3. **Come è fatto qui**: i file e le righe che lo implementano.
4. **Esempio svolto**: codice eseguibile con l'output reale.
5. **Esercizi** (★ facile, ★★ medio, ★★★ difficile). Le soluzioni sono in [12 — Esercizi e soluzioni](12-esercizi-e-soluzioni.md).
6. **Da ricordare**: tre righe di riepilogo.

Per eseguire gli esempi, dalla cartella del progetto:

```bash
.venv/bin/python            # apre l'interprete con le librerie del progetto
```

e incolla il codice. Oppure salvalo in un file `prova.py` nella cartella del progetto e lancia `.venv/bin/python prova.py`.

## Le lezioni

| # | Lezione | Concetti chiave | Tempo |
|---|---|---|---|
| 01 | [Perché un router](01-perche-un-router.md) | costo, qualità, privacy; il problema del "jet per il latte" | 20' |
| 02 | [Architettura esagonale](02-architettura-esagonale.md) | porte, adapter, composition root, confini testati | 45' |
| 03 | [Routing deterministico](03-routing-deterministico.md) | classificatore a regole, regole dure, limiti misurati | 60' |
| 04 | [Fallback e resilienza](04-fallback-e-resilienza.md) | catena di fallback, timeout, escalation, fallback invisibili | 45' |
| 05 | [RAG locale](05-rag-locale.md) | embedding, similarità coseno, chunking, hit@k | 60' |
| 06 | [Costi veri e TCO](06-costi-veri-e-tco.md) | risparmio tautologico, ammortamento, punto di pareggio | 45' |
| 07 | [Compressione dei prompt](07-compressione.md) | compressione estrattiva, guidata vs agnostica, prompt caching | 30' |
| 08 | [Osservabilità](08-osservabilita.md) | registro costi, percentili, metriche, privacy delle trace | 40' |
| 09 | [Router appreso](09-router-appreso.md) | advisor, modalità shadow, dev/test, overfitting | 50' |
| 10 | [Data Flywheel](10-data-flywheel.md) | trace → dataset, anonimizzazione, distillazione | 30' |
| 11 | [Metodo: dimostrare che funziona](11-metodo.md) | test-first, mutation testing, set di controllo, numeri con fonte | 45' |
| 12 | [Esercizi e soluzioni](12-esercizi-e-soluzioni.md) | tutte le soluzioni | — |

Percorsi consigliati:
- **"Voglio solo capire l'idea"**: 01 → 03 → 06.
- **"Devo costruirne uno"**: 01 → 02 → 03 → 04 → 05 → 08 → 11.
- **"Mi interessa l'MLOps"**: 06 → 08 → 09 → 10 → 11.

## La tesi in una frase

> Non serve sempre un modello migliore: serve mandare ogni richiesta sul modello giusto, sotto vincoli di costo, qualità e privacy, e sapere perché.

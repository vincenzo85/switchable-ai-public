# Inizia qui — switchable_ai spiegato a chi parte da zero

> Questa è la **wiki per negati**: niente gergo dato per scontato, ogni comando spiegato, ogni risultato letto insieme.
> Se cerchi i dettagli interni vai alla [wiki tecnica](../tecnica/00-panoramica.md); se vuoi *capire i concetti* con esercizi vai alla [wiki didattica](../didattica/00-percorso.md).

## Il problema in una immagine

Immagina di dover comprare un litro di latte al supermercato sotto casa. Potresti andarci a piedi, oppure noleggiare un jet, decollare, atterrare nel parcheggio, comprare il latte e tornare. Ridicolo, no?

Con l'intelligenza artificiale succede proprio questo: molte aziende mandano **ogni** richiesta, anche la più banale ("questo ticket parla di login o di fatture?"), al modello più grande e più costoso che hanno, in cloud. Funziona, ma costa, e i dati escono dall'azienda.

## Cosa fa switchable_ai

`switchable_ai` è una **torre di controllo** per le richieste AI. Ogni volta che arriva una richiesta decide su quale "pista" farla atterrare:

| Pista (rotta) | Nome tecnico | Quando si usa | Costo |
|---|---|---|---|
| Il modello sul tuo computer | `local` | compiti semplici e ripetitivi: classificare, estrarre dati | quasi zero |
| Il modello grande in cloud | `cloud` | ragionamenti complessi: analisi, progetti, strategie | si paga a consumo |
| La ricerca nei documenti interni | `local_rag` | domande sulla documentazione del progetto | quasi zero, i documenti non escono |

E ci sono **regole che nessuno può scavalcare**:
- un dato sensibile (un'email, un IBAN, un codice fiscale, la parola "riservato") **non va mai in cloud**;
- se il budget del cloud sta finendo, si resta in locale;
- se il cloud non risponde, risponde il modello locale (si chiama *fallback*).

Ogni richiesta lascia una traccia: quanto è costata, quanto ci ha messo, dove è andata e perché.

## Le tre frasi da ricordare

> **Local when possible. Cloud when needed. Observable always.**
> (In locale quando si può. In cloud quando serve. Sempre misurabile.)

## Cosa ti serve sapere prima di cominciare

Niente di speciale. Ti basta saper:
- aprire un **terminale** (la finestra nera dove si scrivono i comandi);
- copiare e incollare un comando e premere Invio.

Ogni comando di questa wiki è in un riquadro così:

```bash
./run.sh help
```

Lo copi, lo incolli nel terminale **dentro la cartella del progetto** e premi Invio. Le righe che iniziano con `#` sono commenti: spiegano, non fanno niente.

## Da dove partire

Segui le pagine in ordine:

1. [Installazione passo passo](01-installazione.md) — prepari il computer (una volta sola).
2. [Primi passi](02-primi-passi.md) — i primi cinque comandi e come leggere quello che rispondono.
3. [Ricette "voglio fare X → fai così"](03-ricette.md) — i casi d'uso pratici, uno per uno.
4. [Lo stack completo con le dashboard](04-stack-completo.md) — Docker, Grafana, Langfuse, n8n.
5. [Problemi comuni](05-problemi-comuni.md) — cosa fare quando qualcosa non va.
6. [Glossario](06-glossario.md) — tutte le parole strane, spiegate in una riga.

## Cosa NON serve

- **Non serve una chiave del cloud** (OpenAI o simili). Senza chiave il sistema funziona lo stesso: le richieste "da cloud" ricadono sul modello locale, ed è proprio una delle cose che il progetto vuole mostrare.
- **Non serve Docker** per cominciare. Serve solo se vuoi vedere le dashboard.
- **Non serve una GPU potente** per provare i comandi di base: `route` e `demo-dry` non chiamano nessun modello. Per far rispondere davvero il modello locale serve un computer discreto (il modello pesa circa 4,7 GB).

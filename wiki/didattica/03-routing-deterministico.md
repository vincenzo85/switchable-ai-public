# 03 — Routing deterministico

## Obiettivi

- Capire come un classificatore **a regole** decide tipo, complessità e sensibilità di una richiesta.
- Prevedere a mano la rotta di una richiesta e verificarla.
- Conoscere i limiti misurati di questo approccio e perché lo si usa lo stesso.

## Il concetto

Per decidere la rotta servono tre informazioni sulla richiesta:

1. **Che tipo di compito è?** (classificare, estrarre, ragionare, chiedere ai documenti)
2. **Quanto è complesso?**
3. **Contiene dati sensibili?**

Si potrebbe chiedere tutto questo a un LLM. Qui si è scelto un **classificatore deterministico** (ADR-001):

| | Router a regole | Router con LLM |
|---|---|---|
| Costo per decisione | zero | token a ogni richiesta |
| Latenza | ~0 ms | decine o centinaia di ms |
| Prevedibilità | totale: stessa richiesta, stessa rotta | probabilistica |
| Verificabilità | si testa riga per riga, anche con mutation testing | serve un benchmark |
| Manipolabilità | bassa | attaccabile con prompt avversari |
| Accuratezza su richieste "strane" | **bassa** (vedi sotto) | migliore |

La scelta del progetto è a strati: **le regole dure** (privacy, budget, local-only) sono sempre deterministiche; un modello può al massimo **consigliare** tra le rotte ammesse ([lezione 09](09-router-appreso.md)).

## Come è fatto qui (`core/domain/policy.py`)

### Passo 1 — il tipo, letto dall'istruzione

Il tipo si cerca **solo nel primo paragrafo**, al massimo 240 caratteri. Perché? Lezione imparata dai dati veri: al primo run con n8n, il prompt "Classifica questo documento… <corpo di un ADR>" finiva sulla rotta documenti, perché nel **corpo** c'erano le parole "documentazione" e "repository". L'intento sta nell'istruzione, non nel documento allegato.

Parole chiave per tipo (match **a inizio parola**: "rag" non scatta in "paragrafo"):

| Tipo | Parole chiave |
|---|---|
| `rag_query` | documentazione, repository, progetto, docs, rag, runbook, procedura interna, knowledge base |
| `extraction` | estrai, extract, fattura, dati da, nome, data |
| `classification` | classifica, ticket, reclamo, categorizza, scegli |
| `reasoning` | analizza, trade-off, progetta, design, disaster recovery, migrazione, strategia, ottimizza, valuta |

Se ne scattano più di una vince quella che compare **prima**: "Classifica questo documento della documentazione" è una classificazione.

Se non ne scatta nessuna, il tipo è un default e `keyword_hit` è **falso**: la regola sta tirando a indovinare. Questo segnale serve all'advisor.

### Passo 2 — la complessità, dalla lunghezza

Complesso se il prompt supera **400 caratteri o 80 parole**. Per classificazioni ed estrazioni la soglia è **5 volte** più alta: classificare un documento lungo resta un compito semplice.

### Passo 3 — la sensibilità, su tutto il testo

Parole chiave (riservato, confidenziale, strettamente interno, cartella clinica, stipendi…) e pattern di dati personali (email, IBAN, codice fiscale, carta). Qui si guarda **tutto** il testo, non solo l'intento: un IBAN nel corpo del documento è comunque un IBAN.

### Passo 4 — le regole dure, poi la rotta

```
regole = []
se sensibile           → data_residency
se local_only          → local_only
se budget ≤ soglia     → budget_guard
cloud ammesso = nessuna regola

se tipo == rag_query                 → local_rag
se complesso e cloud ammesso         → cloud, con fallback locale
se complesso e cloud vietato         → local ("resta in locale per <regola>")
altrimenti                           → local, con escalation al cloud se ammesso
```

## Esempio svolto — prevedi, poi verifica

```python
from core.domain.policy import decide_route

prompts = [
    "Classifica questo reclamo: il corriere ha perso il pacco",
    "Estrai nome, data e importo da: Mario Bianchi, 03/04/2026, 120 EUR",
    "Nel runbook, come si riavvia Ollama?",
    "Progetta una strategia di disaster recovery multi-regione per il servizio pagamenti, con RPO e RTO, "
    "costi stimati, rischi principali, piano di test trimestrale e responsabilità dei team coinvolti, "
    "considerando vincoli normativi europei e dipendenze da fornitori esterni. " * 2,
    "Strettamente interno: progetta la riorganizzazione del team",
    "Quale database conviene per i nostri eventi, Postgres o Kafka?",
]
for p in prompts:
    d = decide_route(p)
    c = d.classification
    print(f"{d.route:<9} kw={c.keyword_hit!s:<5} {c.kind:<14} {c.complexity:<4} {list(d.rules)}")
```

Output:

```
local     kw=True  classification low  []
local     kw=True  extraction     low  []
local_rag kw=True  rag_query      low  ['knowledge_base']
cloud     kw=True  reasoning      high ['complexity']
local     kw=True  reasoning      low  ['data_residency']
local     kw=False classification low  []
```

Guarda l'ultima riga: "Quale database conviene…, Postgres o Kafka?" è una domanda che **richiede ragionamento**, ma non contiene parole chiave ed è corta. Il router la manda in locale come se fosse una classificazione. È il limite principale delle regole.

## I limiti, misurati

Il progetto ha due set di richieste:
- il **batch di casa** (stress test), scritto con le stesse parole delle regole: le regole fanno **100%**;
- un **set di controllo** (`benchmarks/routing_heldout.py`), 32 richieste scritte apposta **senza** quelle parole: le regole fanno **53%**. Riconoscono il 12% delle domande sui documenti e lo 0% di quelle da cloud.

Tutti gli errori vanno nella stessa direzione: verso la rotta più economica. È un errore "sicuro" per costi e privacy, ma costa qualità sulle domande difficili.

Lezione di metodo: il 100% sul batch di casa **si dà ragione da solo**. Senza il set di controllo, il numero sarebbe stato presentato come prova.

## Esercizi

1. ★ Prevedi la rotta (e le regole) di queste richieste, poi verifica con `decide_route`:
   (a) `"Categorizza questa email di un cliente: vorrei disdire l'abbonamento"`;
   (b) `"Nella documentazione: il cliente con IBAN IT60X0542811101000000123456 come chiede il rimborso?"`;
   (c) `"Riassumi questo paragrafo"`.
2. ★ Il risultato di (c) ha `keyword_hit` vero o falso? Perché "rag" non scatta dentro "paragrafo"?
3. ★★ Con `RoutingContext(budget_remaining_eur=0.1, budget_guard_eur=0.2)` la richiesta di disaster recovery dell'esempio dove va? E quale motivo (`reason`) viene dato?
4. ★★ Scrivi tre richieste che un umano manderebbe al cloud ma che il router manda in locale. Cosa hanno in comune?
5. ★★★ Proponi una modifica alle regole che corregga la richiesta "Postgres o Kafka". Poi spiega perché **non** bisogna verificarla sul set di controllo `routing_heldout.py` (suggerimento: [lezione 11](11-metodo.md)).

## Da ricordare

- Il tipo si legge dall'istruzione, la sensibilità da tutto il testo, la complessità dalla lunghezza.
- Le regole dure decidono **se** il cloud è ammesso; il resto decide **quale** pista.
- Un router a regole è gratuito, prevedibile e testabile, ma su richieste formulate in modo inatteso sbaglia spesso: misuralo su un set che non hai scritto pensando alle regole.

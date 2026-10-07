# Primi passi — cinque comandi e come leggerli

Tutti i comandi si danno dalla cartella del progetto. Per vedere l'elenco completo in qualsiasi momento:

```bash
./run.sh help
```

## 1. "Dove andrebbe questa richiesta?" — `route`

`route` chiede alla torre di controllo **solo la decisione**. Non chiama nessun modello, quindi funziona anche senza Ollama ed è istantaneo. Guarda solo il testo: le impostazioni `SAI_LOCAL_ONLY` e budget le applicano invece `demo-dry`, `ask` e l'API.

```bash
./run.sh route "Classifica questo ticket: non riesco a fare login"
```

Risposta (vera, accorciata):

```json
{
  "route": "local",
  "model": "ollama/qwen2.5:7b",
  "fallbacks": [],
  "escalation": "cloud/gpt-4o",
  "cloud_allowed": true,
  "reason": "task semplice e ripetitivo: modello locale",
  "rules": [],
  "classification": {
    "kind": "classification",
    "complexity": "low",
    "sensitive": false,
    "reasons": ["classification: parole chiave ['classifica', 'ticket']",
                "prompt breve (49 caratteri, 8 parole)"]
  }
}
```

Come leggerla, riga per riga:

| Campo | Significa | Qui |
|---|---|---|
| `route` | la pista scelta | `local`: il modello sul tuo computer |
| `model` | il modello che risponderà | `qwen2.5:7b` via Ollama |
| `fallbacks` | i modelli di riserva se il primo cade | nessuno (è già locale) |
| `escalation` | il modello a cui chiedere aiuto se la risposta locale è vuota o sbagliata | il cloud |
| `cloud_allowed` | il cloud è permesso per questa richiesta? | sì |
| `reason` | il perché, in italiano | compito semplice |
| `rules` | le regole "dure" scattate | nessuna |
| `classification.reasons` | gli indizi usati per decidere | ha trovato "classifica" e "ticket", il testo è corto |

Ora prova con un dato personale dentro:

```bash
./run.sh route "Il cliente mario.rossi@example.com chiede il rimborso: analizza la pratica"
```

Nella risposta vedrai `"rules": ["data_residency"]` e `"cloud_allowed": false`: c'è un'email, quindi **il cloud è vietato** e non c'è nemmeno l'escalation (`"escalation": null`).

E una domanda sui documenti:

```bash
./run.sh route "Nella documentazione del progetto, come funziona il fallback?"
```

Qui `route` è `local_rag`: la risposta verrà cercata nei documenti del progetto.

## 2. La demo senza modelli — `demo-dry`

```bash
./run.sh demo-dry
```

Mostra le decisioni per le quattro richieste della demo del talk:

| Task | Cosa chiede | Rotta attesa |
|---|---|---|
| A | classificare un ticket | `local` |
| B | un'analisi lunga e complessa | `cloud` (con riserva locale) |
| C | una domanda sulla documentazione | `local_rag` |
| D | un documento "riservato" | `local`, per regola |

## 3. La demo vera — `demo`

Serve Ollama acceso (`ollama serve`) e il modello scaricato.

```bash
./run.sh demo
```

Per ogni task vedi prima la decisione, poi una riga così:

```
→ eseguito su ollama/qwen2.5:7b (FALLBACK: cloud/gpt-4o: nessuna chiave cloud (OPENAI_API_KEY vuota)): 5907ms, 214→300 token, €0.000103 (se cloud €0.002364)
```

Cosa dice:
- **eseguito su**: il modello che ha risposto davvero;
- **FALLBACK**: il Task B doveva andare in cloud, ma non c'è la chiave, quindi ha risposto il locale. È voluto: mostra che il sistema non si blocca;
- **5907ms**: quanto ci ha messo;
- **214→300 token**: quanto testo è entrato e uscito (un token è circa 4 caratteri);
- **€0.000103 (se cloud €0.002364)**: quanto è costato davvero e quanto sarebbe costato in cloud.

> Al primo comando il modello si carica in memoria e la prima risposta è lenta: è normale.

Il Task C mostra anche le fonti trovate nei documenti, una per riga (per esempio `[1] 0.71 docs/RUNBOOK.md`: posizione, punteggio, file). Se dice che l'indice manca, fai prima il passo 5 qui sotto.

## 4. Una richiesta tua — `ask`

```bash
./run.sh ask "Classifica questo ticket in [accesso, fatturazione, bug, altro]: la fattura di marzo è doppia"
```

Ricevi un JSON con:
- `decision`: la decisione, come in `route`;
- `text`: la risposta del modello;
- `record`: la riga del registro costi (token, latenza, costo, fallback);
- `sources`: i documenti usati, solo per la rotta `local_rag`.

## 5. Le domande sui documenti — `rag-build` e `rag`

Prima si costruisce l'**indice** (una specie di catalogo della biblioteca):

```bash
./run.sh rag-build
```

Legge `README.md`, `MISSION.md`, `docs/`, `wiki/`, `infra/`, i documenti caricati con `ingest` e la storia git. Risponde con quanti pezzi (*chunk*) e quanti documenti ha indicizzato.

Poi si cerca:

```bash
./run.sh rag "Cosa succede se il cloud non risponde?"
```

Vedi i tre pezzi di documento più simili alla domanda, con un punteggio da 0 a 1 (più alto = più pertinente) e il file da cui vengono.

> `rag` cerca soltanto. Per avere una **risposta scritta** che cita le fonti usa `ask` con una domanda sulla documentazione: il router la manda sulla rotta `local_rag`.

## 6. Quanto ho speso? — `report`

```bash
./run.sh report
```

Una tabella per rotta (chiamate, euro reali, euro se tutto andasse in cloud, latenze p50 e p95) e una riga di totale con risparmio, fallback, escalation e **violazioni di residency** (deve essere sempre 0).

`p50` è la latenza "tipica" (metà delle richieste è più veloce). `p95` è quella dei casi lenti (solo 5 su 100 sono più lente).

Vuoi il JSON? `./run.sh report --json`.

## Dove finiscono i dati

Tutto resta nella cartella `data/` del progetto, che non viene caricata su git:

| File | Cosa contiene |
|---|---|
| `data/calls.jsonl` | il registro costi: una riga per richiesta |
| `data/traces.jsonl` | domanda e risposta complete di ogni richiesta |
| `data/rag_index/` | l'indice dei documenti |
| `data/kb/` | i documenti caricati con `ingest` |
| `data/flywheel/sft.jsonl` | il dataset esportato con `flywheel` |

Per ripartire da zero basta cancellare `data/`.

Prossima pagina: [Ricette](03-ricette.md).

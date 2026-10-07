# Ricette — "voglio fare X → fai così"

Ogni ricetta ha: **cosa serve**, **i comandi**, **cosa devi vedere**. Le ricette con 🟢 funzionano senza Ollama; quelle con 🟡 vogliono Ollama acceso; quelle con 🔵 vogliono anche Docker.

---

## R1 🟢 Voglio sapere dove andrebbe una richiesta, senza spendere niente

```bash
./run.sh route "Il testo della tua richiesta"
```

Guarda `route`, `reason` e `rules`. Nessun modello viene chiamato.

---

## R2 🟢 Voglio controllare che un dato sensibile non esca

```bash
./run.sh route "Analizza la pratica del cliente con IBAN IT60X0542811101000000123456"
```

Devi vedere `"rules": ["data_residency"]` e `"cloud_allowed": false`.

Cosa conta come sensibile:
- **parole chiave**: riservat…, confidenzial…, confidential, strettamente interno, dati personali di, cartella clinica, stipendi, buste paga;
- **pattern**: email, IBAN italiano, codice fiscale, numero di carta (13–16 cifre).

---

## R3 🟡 Voglio far rispondere il modello a una richiesta

```bash
./run.sh ask "Estrai fornitore, data e importo: Fattura n. 12 del 12/03/2026, importo 1.240 EUR, fornitore Alfa Srl"
```

La risposta è in `text`; il costo in `record.cost_eur`.

Per limitare la lunghezza della risposta (in token, circa 4 caratteri l'uno):

```bash
./run.sh ask "Riassumi in una riga cos'è un ADR" --max-tokens 60
```

---

## R4 🟡 Voglio fare domande alla documentazione del progetto

```bash
./run.sh rag-build                                                    # una volta, e dopo ogni modifica ai documenti
./run.sh ask "Nella documentazione, cosa faccio se il budget cloud è esaurito?"
```

La risposta cita le fonti come `[1]`, `[2]`; in `sources` trovi i file da cui vengono.

Per far scattare la rotta documenti, nella **prima frase** usa parole come: documentazione, repository, progetto, docs, runbook, procedura interna, knowledge base.

---

## R5 🟡 Voglio aggiungere un mio documento alla knowledge base

```bash
./run.sh ingest percorso/del/mio-documento.md
```

È il flusso automatico che fa anche n8n:
1. **classifica** il documento (requisiti, architettura, runbook, incident, release-note, altro);
2. **estrae** titolo e parole chiave in JSON;
3. **genera** una checklist QA di massimo 5 punti;
4. **copia** il documento in `data/kb/` e **ricostruisce** l'indice.

Alla fine vedi categoria, metadati, checklist, rotte usate, costo e `data_residency_violations` (deve essere 0).

---

## R6 🟢 Voglio vietare del tutto il cloud (per esempio per un cliente che lo chiede)

Nel file `.env` metti:

```
SAI_LOCAL_ONLY=true
```

Prova:

```bash
./run.sh demo-dry
```

Nel Task B (il ragionamento complesso) devi vedere `"rules": ["local_only"]`, `"route": "local"` e la spiegazione `task complesso ma modalità local-only: resta in locale`.

> `./run.sh route` guarda **solo il testo** della richiesta: non applica `SAI_LOCAL_ONLY` né il budget. Per vedere la decisione completa usa `demo-dry`, `ask` o l'API (`POST /v1/route`).

> `./run.sh` legge `.env` a ogni comando. `python -m app.main` invece no: se usi direttamente Python, esporta le variabili a mano (`export SAI_LOCAL_ONLY=true`).

---

## R7 🟡 Voglio un tetto di spesa giornaliero per il cloud

Nel file `.env`:

```
SAI_BUDGET_EUR=2.00          # massimo 2 euro al giorno di cloud
SAI_BUDGET_GUARD_EUR=0.20    # sotto 20 centesimi residui il cloud si spegne
```

Quando il residuo del giorno scende sotto la soglia, le richieste complesse restano in locale e nelle regole compare `budget_guard`. Il conto riparte ogni giorno (mezzanotte UTC). Il residuo si calcola dal registro `data/calls.jsonl`.

---

## R8 🟡 Voglio usare un vero modello cloud

Nel file `.env`:

```
OPENAI_API_KEY=sk-...la-tua-chiave...
SAI_CLOUD_MODEL=cloud/gpt-4o
```

Da ora le richieste complesse vanno davvero in cloud. Se il cloud non risponde entro `SAI_CLOUD_TIMEOUT_S` secondi (default 60), risponde comunque il locale.

Funziona con qualsiasi servizio compatibile con l'API OpenAI: cambia `OPENAI_BASE_URL`.

---

## R9 🟡 Voglio collegare un'app che già usa l'API OpenAI

Avvia l'API:

```bash
./run.sh serve        # resta in ascolto su http://localhost:8088 (lascia aperto il terminale)
```

Nella tua app cambia **solo** l'indirizzo base. Esempio in Python con la libreria `openai`:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8088/v1", api_key="non-serve")
r = client.chat.completions.create(
    model="qualsiasi",   # viene ignorato: decide la torre di controllo
    messages=[{"role": "user", "content": "Classifica questo ticket: non riesco a fare login"}],
)
print(r.choices[0].message.content)
```

Oppure con `curl`:

```bash
curl -s http://localhost:8088/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"x","messages":[{"role":"user","content":"Classifica questo ticket: non riesco a fare login"}]}'
```

Nella risposta, oltre ai campi standard, c'è `x_switchable` con rotta, fallback, regole e costo.

---

## R10 🟢 Voglio vedere quanto ho speso

```bash
./run.sh report          # tabella
./run.sh report --json   # per un altro programma
```

---

## R11 🟡 Voglio uno stress test (tante richieste di fila)

```bash
./run.sh stress 10       # 10 richieste miste: un paio di minuti
./run.sh stress          # 100 richieste: diversi minuti
```

Per ogni richiesta vedi una riga con ✓ o ✗, la famiglia (ticket, extraction, architecture, kb_question, sensitive), la rotta, il modello e la latenza. Alla fine c'è il riepilogo; il dettaglio va in `benchmarks/results/stress_cli.json`.

Il comando esce con codice 3 se anche **una sola** richiesta sensibile è finita in cloud.

---

## R12 🟡 Voglio un dataset per addestrare un modello dalle richieste fatte

```bash
./run.sh flywheel
```

Prende domande e risposte registrate, **oscura i dati personali** (email, IBAN, codice fiscale, carte, telefoni → `<EMAIL>`, `<IBAN>`…), toglie i doppioni e scrive `data/flywheel/sft.jsonl` nel formato chat usato per il fine-tuning.

---

## R13 🟢 Voglio usare switchable_ai da un agente AI (Claude, IDE…) — MCP

Il progetto ha già un file `.mcp.json`. Un client MCP che lo legge (per esempio Claude Code aperto nella cartella del progetto) trova sei strumenti:

| Strumento | Cosa fa |
|---|---|
| `route_prompt` | decide la rotta senza eseguire |
| `ask` | esegue la richiesta |
| `rag_search` | cerca nei documenti |
| `cost_report` | il report dei costi |
| `stress_test` | lancia lo stress test |
| `flywheel_export` | esporta il dataset |

Per avviare il server a mano: `./run.sh mcp` (parla via stdin/stdout, non ha un indirizzo web).

---

## R14 🔵 Voglio vedere le dashboard

Vedi [Lo stack completo](04-stack-completo.md).

---

## R15 🟢 Voglio vedere la presentazione del talk

```bash
./run.sh deck            # la presentazione 3D nel browser
./run.sh deck-redteam    # la versione "red team": la tesi sotto attacco
```

Tasti: → avanti, ← indietro, F schermo intero, P vista relatore, B schermo nero, A appendice.

Se il computer non regge il 3D: `make deck-backup` crea un PDF in `talk/screens/` (serve Google Chrome).

---

## R16 🟢 Voglio controllare di non aver rotto niente

```bash
./run.sh test        # i test (meno di un minuto)
make check           # test + controllo dell'architettura
./run.sh mutation    # più lento: rompe apposta il codice e controlla che i test se ne accorgano
```

---

## R17 🟢 Voglio ripartire da zero

```bash
rm -rf data/          # registro costi, tracce, indice, dataset: tutto cancellato
./run.sh rag-build    # se vuoi di nuovo le domande sui documenti
```

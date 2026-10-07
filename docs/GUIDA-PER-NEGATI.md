# Guida per negati

> Versione estesa, con ricette e soluzione dei problemi: [wiki per negati](../wiki/per-negati/00-inizia-qui.md).

Questa guida spiega come usare `switchable_ai` senza conoscere niente in anticipo. Ogni comando si scrive nel terminale, dentro la cartella del progetto:

```bash
git clone https://github.com/vincenzo85/switchable-ai-public.git
cd switchable-ai-public
```

## 1. Cosa fa, in una frase

Riceve una richiesta per un'intelligenza artificiale e decide dove mandarla:
- a un modello che gira su questo computer (gratis e privato);
- a un servizio cloud a pagamento (più potente);
- a una ricerca nei documenti del progetto.

Poi registra quanto è costata e quanto ci ha messo.

## 2. Prima volta

```bash
make setup                 # prepara l'ambiente Python (una volta sola, qualche minuto)
cp .env.example .env       # crea il file delle impostazioni
ollama pull qwen2.5:7b     # il modello locale (se non c'è già)
ollama pull nomic-embed-text
./run.sh test              # tutti i controlli: devono essere verdi
```

Nel file `.env` le chiavi del cloud possono restare vuote: il sistema funziona lo stesso e manda tutto in locale.

## 3. Provare la demo

```bash
./run.sh demo-dry          # mostra solo le DECISIONI, senza far lavorare i modelli
./run.sh demo              # le esegue davvero
```

Vedrai quattro richieste:
- **A:** una classificazione, va in locale;
- **B:** un'analisi complessa, va in cloud. Senza chiave c'è un *fallback* e risponde il locale;
- **C:** una domanda sui documenti, va al RAG locale e cita le fonti;
- **D:** un documento riservato, resta in locale per regola.

Per una richiesta tua:

```bash
./run.sh route "Classifica questo ticket: non riesco a fare login"    # dove andrebbe?
./run.sh ask "Classifica questo ticket: non riesco a fare login"      # eseguila
./run.sh report                                                       # quanto ho speso finora?
```

## 4. Le domande sui documenti (RAG)

```bash
./run.sh rag-build                                     # legge docs/, wiki/, infra/ e la storia git
./run.sh rag "Cosa succede se il cloud non risponde?"  # mostra i pezzi di documento trovati
```

Se aggiungi documenti in `docs/`, rilancia `rag-build`.

## 5. Tutto lo stack (facoltativo)

```bash
./run.sh up        # avvia in Docker: gateway, Langfuse, Grafana, Prometheus, n8n
./run.sh serve     # avvia l'API (lascia aperto questo terminale)
```

Poi apri nel browser:

| Indirizzo | Cosa vedi |
|---|---|
| http://localhost:3012 | Grafana, la dashboard "Cockpit": costi, latenze, fallback |
| http://localhost:3011 | Langfuse (utente `demo@switchable.local`, password `switchable-demo`): una traccia per ogni richiesta |
| http://localhost:5678 | n8n, il workflow che ingerisce documenti |

Per spegnere tutto: `./run.sh down`.

## 6. La presentazione

```bash
./run.sh deck
```

| Tasto | Effetto |
|---|---|
| → spazio | avanti |
| ← | indietro |
| F | schermo intero |
| P | apre la vista relatore (note, tempi, prossima slide) |
| D | demo dal vivo: le card dello step 9 chiamano davvero l'API; se l'API non risponde mostra il run registrato |
| B | schermo nero |

Se il computer della sala non regge il 3D: `make deck-backup` crea `talk/screens/deck-backup.pdf`.

## 7. Rifare i numeri

Ogni benchmark scrive un file in `benchmarks/results/`:

```bash
./run.sh bench tco           # costi e latenze della demo
./run.sh bench compression   # compressione dei prompt
./run.sh bench vllm          # Ollama contro vLLM (scarica il modello in VRAM, qualche minuto)
./run.sh bench advisor       # regole contro Rizzo Flow / Open-Jev
./run.sh bench stress        # stress test di 100 richieste (circa 4 minuti)
./run.sh numbers             # raccoglie tutto in talk/numbers.json
make deck                    # ricostruisce la presentazione con i numeri nuovi
```

## 8. Se qualcosa non va

| Problema | Soluzione |
|---|---|
| `nessun provider configurato` o tutte le rotte cadono | Ollama è spento: `ollama serve` |
| La rotta RAG risponde senza fonti | Manca l'indice: `./run.sh rag-build` |
| Grafana è vuoto | L'API non è avviata (`./run.sh serve`) o non ha ancora ricevuto richieste |
| La prima richiesta è lenta | Il modello si sta caricando in memoria: è normale, la seconda è veloce |
| vLLM non parte | La porta 8010 è occupata, oppure la VRAM è piena: chiudi gli altri modelli |

Per capire *perché* è fatto così: `docs/ARCHITETTURA.md` e gli ADR in `docs/adr/`.

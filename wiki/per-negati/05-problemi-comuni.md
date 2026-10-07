# Problemi comuni

Cerca il messaggio che vedi (o il sintomo) nella colonna di sinistra.

## Installazione

| Vedo | Perché | Cosa faccio |
|---|---|---|
| `python3: command not found` | Python non è installato | installa Python 3.11 o più recente |
| `make: command not found` | manca make | Linux: `sudo apt install make`; macOS: `xcode-select --install` |
| `.venv/bin/python: No such file or directory` | non hai fatto il setup | `make setup` |
| `./run.sh: Permission denied` | il file non è eseguibile | `chmod +x run.sh` |
| errori su `hnswlib` durante `make setup` | serve un compilatore C++ | Linux: `sudo apt install build-essential`; macOS: `xcode-select --install` |

## Modelli e Ollama

| Vedo | Perché | Cosa faccio |
|---|---|---|
| `tutte le rotte sono cadute — ollama/qwen2.5:7b: ... Connection refused` | Ollama è spento | `ollama serve` in un altro terminale |
| `HTTP 404 da http://localhost:11434/api/generate: … model "qwen2.5:7b" not found` | modello non scaricato | `ollama pull qwen2.5:7b` |
| `HTTP 404 da …/api/embed: … "nomic-embed-text" not found` (durante `rag-build` o `rag`) | manca il modello per i documenti | `ollama pull nomic-embed-text` |
| la prima risposta ci mette decine di secondi | il modello si sta caricando in memoria | normale; dalla seconda è veloce |
| tutte le risposte lentissime | il modello gira sul processore invece che sulla scheda video | usa un modello più piccolo: `SAI_LOCAL_MODEL=ollama/qwen2.5:1.5b` nel `.env` (dopo `ollama pull qwen2.5:1.5b`) |

## Rotte e risposte

| Vedo | Perché | Cosa faccio |
|---|---|---|
| `FALLBACK: cloud/gpt-4o: nessuna chiave cloud` | non c'è la chiave cloud | normale e voluto; se vuoi il cloud vero, ricetta R8 |
| la rotta RAG risponde senza fonti, `RAG degradato: indice assente` | l'indice non c'è | `./run.sh rag-build` |
| `rag` dà `IndexNotReady` | l'indice non c'è | `./run.sh rag-build` |
| una domanda sui documenti va su `local` invece di `local_rag` | nella prima frase mancano le parole chiave | scrivi "Nella documentazione…" o "Nel runbook…" all'inizio |
| una richiesta complessa ma corta va in `local` | il router a regole guarda la lunghezza: sotto i 400 caratteri e le 80 parole il compito è "semplice" | è un limite noto (vedi la [wiki didattica](../didattica/03-routing-deterministico.md)); allunga la richiesta o usa l'advisor |
| `SAI_LOCAL_ONLY=true` ma `./run.sh route` mostra ancora `cloud` | `route` guarda solo il testo, non le impostazioni | controlla con `./run.sh demo-dry` o con l'API `POST /v1/route` |

## Stack Docker

| Vedo | Perché | Cosa faccio |
|---|---|---|
| `./run.sh up` fallisce con "port is already allocated" | una porta è già usata da un altro programma | chiudi quel programma o cambia la porta in `infra/docker-compose.yml` |
| Grafana è vuoto | l'API non è accesa o non ha ricevuto richieste | `./run.sh serve`, poi manda richieste **all'API** (vedi [stack completo](04-stack-completo.md)) |
| Langfuse non riceve tracce | variabili `LANGFUSE_*` mancanti nel `.env` | aggiungile (passo 2 dello stack) e riavvia |
| i container non raggiungono Ollama | firewall tra Docker e il computer | il compose usa già `network_mode: host`; controlla che Ollama ascolti su `127.0.0.1:11434` |

## Test

| Vedo | Perché | Cosa faccio |
|---|---|---|
| molte `s` (skipped) nei test del deck | Google Chrome non c'è | normale; installalo se vuoi testare la presentazione |
| un test fallisce dopo che hai cambiato un benchmark | i numeri del talk non sono più aggiornati | `./run.sh numbers` e poi correggi il testo indicato dal test |
| `test_architecture_boundaries` fallisce | hai importato una libreria esterna dentro `core/` | sposta quel codice in `adapters/` (vedi la [wiki tecnica](../tecnica/12-test-e-qualita.md)) |

## Ancora bloccato?

1. `./run.sh test` è verde? Se no, il problema è nell'installazione.
2. `./run.sh route "ciao"` risponde? Se sì, il programma funziona e il problema è il modello (Ollama).
3. `curl http://localhost:11434/api/tags` elenca i modelli? Se no, Ollama è spento.

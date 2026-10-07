# Installazione passo passo

Si fa **una volta sola**. Tempo: 10–20 minuti, quasi tutti di download.

## Passo 0 — Cosa serve sul computer

| Cosa | Perché | Come controllare se c'è |
|---|---|---|
| Linux o macOS (su Windows: WSL) | i comandi sono pensati per una shell bash | — |
| Python 3.11 o più recente | il programma è scritto in Python | `python3 --version` |
| git | per scaricare il progetto | `git --version` |
| make | per l'installazione automatica | `make --version` |
| [Ollama](https://ollama.com) | fa girare il modello AI sul tuo computer | `ollama --version` |
| Docker (facoltativo) | solo per le dashboard | `docker --version` |

Se un comando di controllo risponde "command not found", quel programma manca: installalo dal sito ufficiale e riprova.

## Passo 1 — Scarica il progetto

```bash
git clone https://github.com/vincenzo85/switchable-ai-public.git
cd switchable-ai-public
```

Il secondo comando ti porta **dentro** la cartella del progetto. Da qui in poi tutti i comandi si danno da questa cartella. Se chiudi il terminale, quando lo riapri ricordati di rientrare con `cd`.

## Passo 2 — Prepara l'ambiente Python

```bash
make setup
```

Cosa fa: crea una cartella `.venv` con un Python "privato" del progetto e ci installa le librerie necessarie. Non tocca il Python del sistema.

Ci mette qualche minuto. Alla fine non deve comparire la parola `ERROR`.

## Passo 3 — Crea il file delle impostazioni

```bash
cp .env.example .env
```

Hai copiato il file di esempio in `.env`, il file che il programma legge all'avvio. **Va bene così com'è**: le chiavi del cloud sono vuote e devono restarlo finché non sai di volerle usare.

> Il file `.env` non viene mai caricato su git (è nel `.gitignore`): se un giorno ci metti una chiave vera, resta sul tuo computer.

## Passo 4 — Scarica i modelli locali

```bash
ollama pull qwen2.5:7b          # il modello che risponde (circa 4,7 GB)
ollama pull nomic-embed-text    # il modello che "capisce" i documenti per la ricerca (circa 270 MB)
```

Se Ollama non è avviato, avvialo in un altro terminale con `ollama serve`.

## Passo 5 — Controlla che tutto funzioni

```bash
./run.sh test
```

Cosa fa: lancia circa 150 controlli automatici. Non servono né Ollama né internet: i test usano modelli finti.

Risultato atteso: puntini `.` e alla fine una riga con `passed`. Alcune `s` (*skipped*, saltati) sono normali se non hai Google Chrome: sono i test della presentazione.

Se compare `failed`, guarda [Problemi comuni](05-problemi-comuni.md).

## Fatto

Il computer è pronto. Vai ai [Primi passi](02-primi-passi.md).

## Riepilogo (per la prossima volta)

```bash
git clone https://github.com/vincenzo85/switchable-ai-public.git
cd switchable-ai-public
make setup
cp .env.example .env
ollama pull qwen2.5:7b && ollama pull nomic-embed-text
./run.sh test
```

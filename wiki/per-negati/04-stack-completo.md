# Lo stack completo — Docker e le dashboard

Facoltativo. Serve per **vedere** i numeri in tempo reale: grafici di costi e latenze, la traccia di ogni richiesta, il flusso automatico dei documenti.

## Cosa si accende

| Servizio | Indirizzo | A cosa serve |
|---|---|---|
| LiteLLM | http://localhost:4000 | un "centralino" davanti ai modelli (facoltativo) |
| Langfuse | http://localhost:3011 | la **scatola nera**: una traccia per ogni richiesta |
| Prometheus | http://localhost:9091 | raccoglie i numeri ogni 5 secondi |
| Grafana | http://localhost:3012 | il **cockpit**: i grafici |
| n8n | http://localhost:5678 | il flusso automatico per i documenti |

Ollama e l'API di switchable_ai girano fuori da Docker, sul computer.

## Passo 1 — Accendi i servizi

```bash
./run.sh up
```

La prima volta scarica le immagini (qualche minuto). Controlla che siano tutti `healthy`:

```bash
docker compose -f infra/docker-compose.yml ps
```

Vuoi solo una parte?

```bash
./run.sh up core       # solo LiteLLM
./run.sh up obs        # solo Langfuse, Prometheus, Grafana
./run.sh up n8n        # solo n8n
```

## Passo 2 — Collega switchable_ai alle dashboard

Nel file `.env` metti:

```
LANGFUSE_HOST=http://localhost:3011
LANGFUSE_PUBLIC_KEY=pk-lf-switchable-demo
LANGFUSE_SECRET_KEY=sk-lf-switchable-demo
```

Sono le chiavi **di demo** che Langfuse crea da solo al primo avvio.

## Passo 3 — Accendi l'API

In un terminale dedicato (lascialo aperto):

```bash
./run.sh serve
```

Prometheus legge i numeri da http://localhost:8088/metrics.

## Passo 4 — Fai qualche richiesta

In un altro terminale:

```bash
./run.sh stress 10
```

oppure usa `curl` o la tua app contro http://localhost:8088 (ricetta R9).

> Attenzione: `./run.sh stress` e `./run.sh ask` girano in un processo separato dall'API, quindi **non** aggiornano i grafici di Grafana (che legge dall'API). Langfuse invece riceve le tracce da entrambi. Per vedere Grafana muoversi, manda le richieste all'API:
>
> ```bash
> curl -s -X POST http://localhost:8088/v1/stress -H 'Content-Type: application/json' -d '{"n": 10}'
> ```

## Passo 5 — Guarda

- **Grafana** → http://localhost:3012: si apre la dashboard "Cockpit". Accesso anonimo in sola lettura; per modificare usa `admin` / `switchable-demo`.
  - in alto: euro reali, euro se tutto-cloud, risparmio, richieste, fallback, **violazioni residency** (deve essere 0);
  - sotto: richieste per rotta, latenze p50/p95, costo cumulato, turbolenza (fallback, escalation, budget guard), token, compressione, advisor.
- **Langfuse** → http://localhost:3011, utente `demo@switchable.local`, password `switchable-demo`. Nella pagina *Traces* c'è una riga per richiesta: rotta, latenza, token, costo, tag (`cloud`, `fallback`…).
  - Per le richieste sensibili Langfuse **non riceve il testo**: vedi `[sensibile: contenuto non inviato]`.
  - Langfuse mostra il simbolo del dollaro, ma i valori sono in **euro**.

## Il flusso n8n dei documenti

1. Apri http://localhost:5678 e crea l'utente al primo accesso.
2. Importa il workflow: menu → *Import from file* → `infra/n8n/workflows/sdlc-document-intake.json`. Attivalo.
3. Manda un documento:

```bash
curl -s -X POST http://localhost:5678/webhook/sdlc-document \
  -H 'Content-Type: application/json' \
  -d '{"name":"adr-004.md","text":"# ADR-004\nUsiamo PostgreSQL per i dati transazionali..."}'
```

Risposta: `status: "landed"` con categoria, rotte, costi e checklist. Se un dato sensibile fosse finito in cloud, risponderebbe con codice 500 e `residency_violation`.

## Spegnere tutto

```bash
./run.sh down
```

I dati di Langfuse e n8n restano nei volumi Docker. Per cancellarli: `docker compose -f infra/docker-compose.yml --profile '*' down -v`.

## Sicurezza

Le password qui sopra sono **di demo** e funzionano solo perché tutti i servizi ascoltano su `127.0.0.1` (solo dal tuo computer). Se vuoi rendere lo stack raggiungibile da altri computer, cambiale tutte in `infra/docker-compose.yml`.

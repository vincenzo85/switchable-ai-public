# API HTTP (`app/api.py`)

FastAPI. Avvio:

```bash
./run.sh serve                                          # 0.0.0.0:8088 (SAI_HOST, SAI_PORT)
.venv/bin/python -m app.main serve --host 127.0.0.1 --port 8088
```

Documentazione interattiva generata da FastAPI: http://localhost:8088/docs.

CORS aperto (`*`) in GET/POST: serve al deck, che chiama l'API da `file://`. Se esponi l'API fuori da `localhost`, restringi CORS e metti un'autenticazione davanti: l'API non ne ha.

Gli errori di dominio (`DomainError`, per esempio tutte le rotte cadute) diventano **HTTP 503** con il messaggio nel campo `detail`.

## Endpoint

| Metodo | Percorso | Corpo | Risposta |
|---|---|---|---|
| GET | `/health` | — | `{"status": "ok"}` |
| GET | `/metrics` | — | esposizione Prometheus (`text/plain`) |
| POST | `/v1/route` | `{"prompt": str}` | `RouteDecision.to_dict()`, **con** contesto (local-only, budget, advisor) |
| POST | `/v1/ask` | `{"prompt": str, "max_tokens": int = 300}` | `ExecutionResult.to_dict()` |
| POST | `/v1/chat/completions` | formato OpenAI (`model`, `messages`, `max_tokens`) | formato OpenAI + `x_switchable` |
| POST | `/webhook/n8n/document` | `{"name": str, "text": str}` | esito di `IngestDocument` |
| GET | `/v1/report` | — | `CostReport.execute()` |
| POST | `/v1/stress` | `{"n": int = 20, "seed": int = 42}` | report dello stress test + `wall_s` |

## `/v1/chat/completions` in dettaglio

- Il campo `model` della richiesta è **ignorato di proposito**: decide la torre.
- I messaggi `system` sono scartati; i contenuti degli altri messaggi sono concatenati con `\n\n` in un solo prompt. Non c'è memoria di conversazione oltre a quello che il client manda.
- Niente streaming.

Risposta:

```json
{
  "id": "flight-3f9c1a2b7d",
  "object": "chat.completion",
  "created": 1791400000,
  "model": "ollama/qwen2.5:7b",
  "choices": [{"index": 0, "message": {"role": "assistant", "content": "accesso"}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 69, "completion_tokens": 3, "total_tokens": 72},
  "x_switchable": {"route": "local", "fallback": false, "rules": [], "cost_eur": 1.44e-05}
}
```

`model` è il modello che ha risposto davvero.

## Esempi

```bash
# decisione (con contesto)
curl -s -X POST localhost:8088/v1/route -H 'Content-Type: application/json' \
  -d '{"prompt":"Estrai fornitore, data e importo: Fattura n. 12 del 12/03/2026"}'

# esecuzione
curl -s -X POST localhost:8088/v1/ask -H 'Content-Type: application/json' \
  -d '{"prompt":"Classifica questo ticket: il pulsante salva va in errore 500","max_tokens":20}'

# client OpenAI esistente
curl -s localhost:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4o","messages":[{"role":"system","content":"ignorato"},{"role":"user","content":"Classifica: login rotto"}]}'

# costi
curl -s localhost:8088/v1/report | python3 -m json.tool

# stress test dentro il processo dell'API (aggiorna /metrics e quindi Grafana)
curl -s -X POST localhost:8088/v1/stress -H 'Content-Type: application/json' -d '{"n":10}'

# metriche
curl -s localhost:8088/metrics | grep '^sai_'
```

Python, SDK `openai`:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8088/v1", api_key="non-usata")
r = client.chat.completions.create(model="qualsiasi", messages=[{"role": "user", "content": "Classifica: login rotto"}])
print(r.choices[0].message.content, r.model)
```

## Comportamento senza modelli

Verificato: con Ollama spento `/health`, `/v1/route`, `/metrics` e `/v1/report` rispondono; `/v1/ask` e `/v1/chat/completions` rispondono **503** (`tutte le rotte sono cadute — …`).

## Test

`tests/test_wiring.py` usa `fastapi.testclient` con un `Container` costruito su adapter finti.

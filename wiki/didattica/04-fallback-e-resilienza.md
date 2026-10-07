# 04 — Fallback e resilienza

## Obiettivi

- Distinguere **fallback** (il provider non risponde) da **escalation** (risponde, ma male).
- Capire come un timeout diventa un fallback.
- Vedere perché un fallback "invisibile" è un problema e come lo si rende visibile.

## Il concetto

Un modello cloud può:
- non rispondere (rete, chiave mancante, errore 5xx, limite di frequenza);
- rispondere troppo tardi;
- rispondere, ma con qualcosa di inutile.

Un modello locale può rispondere velocemente ma sbagliare un compito troppo difficile per lui.

Due meccanismi diversi:

| | Fallback | Escalation |
|---|---|---|
| Quando | il modello scelto **non risponde** (errore o timeout) | il modello scelto **risponde**, ma la risposta non passa una validazione |
| Direzione | cloud → locale | locale → cloud |
| Condizione | sempre (la catena è nella decisione) | solo se il cloud è ammesso dalle regole dure |
| Costo registrato | solo la chiamata riuscita | **entrambe** le chiamate |

## Come è fatto qui

### La catena

La decisione di rotta porta con sé la catena: `model` più `fallbacks`. Per la rotta cloud è `("cloud/gpt-4o", "ollama/qwen2.5:7b")`. `ExecuteRequest` prova in ordine; il primo che non solleva `ProviderError` vince; se cadono tutti solleva `ProviderError("tutte le rotte sono cadute — …")` con tutti i motivi.

### Il timeout è un errore come gli altri

`SAI_CLOUD_TIMEOUT_S` (default 60) è il **budget di latenza** del cloud. L'adapter HTTP converte il timeout di rete in `ProviderTimeout`, che è un `ProviderError`: per il core "troppo lento" e "giù" sono la stessa cosa, e il fallback scatta.

### Senza chiave, fallimento immediato

Se manca la chiave cloud, la composition root mette `UnavailableLLM` sul prefisso `cloud/`: solleva subito `ProviderError`. Così il fallback si esercita **davvero** a ogni richiesta complessa, senza aspettare un timeout. È la demo del talk: "oggi il jet non ha carburante".

### L'escalation

Se la rotta è locale e la decisione prevede un modello di escalation (`escalation = cloud`, solo se il cloud è ammesso), dopo la risposta locale si chiama un **validatore** (default: "la risposta non è vuota"; l'ingest usa "la categoria è una di quelle ammesse"). Se fallisce, si ritenta in cloud.

### Il fallback invisibile

Con il gateway LiteLLM in mezzo, il gateway stesso può fare fallback (`smart-cloud → fast-local`). Il client riceve una risposta normale e **non sa** che ha risposto il locale. Nel registro risulterebbe una chiamata cloud, pagata a prezzo cloud. Il progetto lo rileva dal campo `model` della risposta (`OpenAICompatLLM.served_as`) e registra `fallback=True` con il motivo `fallback eseguito dal gateway`.

Questo bug è stato scoperto guardando il registro costi: "richieste cloud" eseguite da un modello locale.

## Esempio svolto

```python
from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, SequentialIds
from core.use_cases.execute_request import ExecuteRequest
from core.domain.errors import ProviderError

COMPLEX = "Analizza i trade-off tra monolite e microservizi. " * 20

def make(llm, **kw):
    return ExecuteRequest(llm=llm, ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds(), **kw)

# 1. il cloud è giù
r = make(FakeLLM({"cloud/": {"fail": True}})).execute(COMPLEX)
print(r.record.model, r.record.fallback, r.record.fallback_reason)

# 2. il cloud è lento: 5 secondi con un budget di 1
r = make(FakeLLM({"cloud/": {"latency_ms": 5000}}), cloud_timeout_s=1).execute(COMPLEX)
print(r.record.model, r.record.fallback, r.record.fallback_reason)

# 3. il locale risponde male: escalation
llm = FakeLLM({"ollama/": {"reply": "boh"}, "cloud/": {"reply": "accesso"}})
r = make(llm).execute("Classifica questo ticket in [accesso, bug]: login rotto",
                      validator=lambda t: t.strip() in ("accesso", "bug"))
print(r.text, r.record.model, r.record.escalated, r.record.tokens_in, r.record.tokens_out)

# 4. stessa cosa, ma con un dato personale: niente escalation
r = make(FakeLLM({"ollama/": {"reply": "boh"}, "cloud/": {"reply": "accesso"}})).execute(
    "Classifica questo ticket di mario@example.com in [accesso, bug]: login rotto",
    validator=lambda t: t.strip() in ("accesso", "bug"))
print(r.text, r.record.model, r.record.escalated, r.decision.escalation)

# 5. tutto giù
try:
    make(FakeLLM({"cloud/": {"fail": True}, "ollama/": {"fail": True}})).execute(COMPLEX)
except ProviderError as e:
    print(e)
```

Output:

```
ollama/qwen2.5:7b True cloud/gpt-4o: provider non disponibile
ollama/qwen2.5:7b True cloud/gpt-4o: 5000ms > 1000ms
accesso cloud/gpt-4o True 26 2
boh ollama/qwen2.5:7b False None
tutte le rotte sono cadute — cloud/gpt-4o: provider non disponibile | ollama/qwen2.5:7b: provider non disponibile
```

Osserva il caso 3: i token (26 in, 2 out) sono la **somma** delle due chiamate. Il caso 4: la regola di residency ha tolto l'escalation (`None`), quindi la risposta resta "boh". Meglio una risposta sbagliata in casa che un dato personale in cloud: è una scelta, ed è scritta nel codice.

## Nello stress test

`./run.sh bench stress` simula un cloud con una **finestra di turbolenza programmata** (`SimulatedCloudLLM`): alcune chiamate superano il timeout. Risultato misurato: 100 richieste su 100 completate, 4 fallback, 0 dati sensibili in cloud.

## Esercizi

1. ★ Nel caso 2, cambia `cloud_timeout_s` a 10. Cosa succede e perché?
2. ★ Perché il caso 1 non ha richiesto alcuna attesa, mentre in produzione un cloud giù potrebbe farti aspettare 60 secondi? Quale variabile abbasseresti nel runbook?
3. ★★ Scrivi un validatore per un'estrazione che deve restituire JSON con le chiavi `fornitore`, `data`, `importo`, e usalo con `FakeLLM` in due versioni: una che risponde JSON valido, una che risponde testo libero. Quale delle due va in escalation?
4. ★★ Quanto costa il caso 3 rispetto a una risposta locale corretta al primo colpo? Calcolalo con `core.domain.pricing.cost_of`.
5. ★★★ Leggi `test_gateway_side_fallback_is_reported_as_local_model` in `tests/test_adapters.py`. Spiega con parole tue cosa verifica e cosa succederebbe al report dei costi senza `served_as`.

## Da ricordare

- Fallback = il provider non risponde (o è troppo lento); escalation = risponde male. Sono due meccanismi con direzioni opposte.
- Il timeout è un budget di latenza: oltre, si tratta come un guasto.
- Le regole dure valgono anche qui: niente escalation al cloud per dati sensibili.
- Ogni fallback deve lasciare traccia; quelli fatti da un gateway vanno resi visibili apposta.

# 08 — Osservabilità

## Obiettivi

- Sapere **cosa** registrare di ogni richiesta AI e perché.
- Leggere percentili di latenza (p50, p95).
- Progettare un'osservabilità che non rompa il sistema e non faccia uscire dati.

## Il concetto

Un router che nessuno può controllare è una scatola nera. Per ogni richiesta servono risposte a domande precise:

| Domanda | Campo |
|---|---|
| Dove doveva andare e dove è andata davvero? | `route` (decisa), `model` (che ha risposto) |
| Perché? | `rules`, e la decisione completa |
| Quanto è costata, e quanto sarebbe costata in cloud? | `cost_eur`, `cost_if_cloud_eur` |
| Quanto ci ha messo? | `latency_ms` |
| È andato storto qualcosa? | `fallback`, `fallback_reason`, `escalated` |
| C'era un dato sensibile? È uscito? | `sensitive`, e se `model` è cloud: **violazione** |

### Tre livelli

| Livello | Strumento qui | Domanda tipica |
|---|---|---|
| **registro** (una riga per richiesta) | `data/calls.jsonl` | "cosa è successo alla richiesta X?", "quanto ho speso oggi?" |
| **metriche** (contatori aggregati nel tempo) | Prometheus + Grafana | "la latenza p95 sta salendo?", "quanti fallback negli ultimi 30 minuti?" |
| **trace** (contenuto completo) | `data/traces.jsonl` + Langfuse | "cosa ha chiesto l'utente e cosa ha risposto il modello?" |

### Percentili

La media inganna: 4 richieste da 100 ms e una da 4 secondi danno una media di ~900 ms, che non descrive nessuno.

- **p50** (mediana): metà delle richieste è più veloce;
- **p95**: 95 richieste su 100 sono più veloci. È quello che sentono gli utenti nei casi lenti.

### Due regole di progetto

1. **L'osservabilità non abbatte il volo.** Se Langfuse è giù o Prometheus esplode, la richiesta deve completarsi. Ogni sink assorbe i propri errori.
2. **Il dato sensibile non esce nemmeno verso il monitoraggio.** Mandare a Langfuse il testo di un documento riservato sarebbe una violazione di residency "dalla porta di servizio". Per le richieste sensibili Langfuse riceve `[sensibile: contenuto non inviato]`.

## Come è fatto qui

- `CallRecord` (`core/domain/models.py`) — il mattone di ogni numero.
- `CostReport` (`core/use_cases/report.py`) — aggregazioni e percentili.
- `PrometheusMetrics`, `LangfuseTracer`, `FanoutTracer` (`adapters/observability/sinks.py`).
- `ExecuteRequest._observe` — chiama metriche e tracer dentro un `try/except`.

La metrica più importante del cockpit: **violazioni di residency**, che deve restare a 0. Il contatore è inizializzato a 0 apposta, così Grafana mostra "0" e non "nessun dato".

## Esempio svolto

```python
from core.use_cases.report import CostReport, percentile
from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, SequentialIds
from core.use_cases.execute_request import ExecuteRequest

print(percentile([100, 120, 130, 150, 4000], 50), percentile([100, 120, 130, 150, 4000], 95))

COMPLEX = "Analizza i trade-off tra monolite e microservizi. " * 20
led = InMemoryLedger()
uc = ExecuteRequest(llm=FakeLLM({"cloud/": {"fail": True}}), ledger=led, clock=FixedClock(), ids=SequentialIds())
uc.execute("Classifica questo ticket: login rotto")
uc.execute(COMPLEX)
uc.execute("Documento riservato: " + COMPLEX)
rep = CostReport(led).execute()
print({k: rep[k] for k in ("calls", "fallbacks", "residency_violations")}, round(rep["saving_pct"], 2), list(rep["by_route"]))
```

Output:

```
130.0 3229.999999999999
{'calls': 3, 'fallbacks': 1, 'residency_violations': 0} 95.65 ['cloud', 'local']
```

Leggilo:
- p50 = 130 ms, p95 ≈ 3,2 s: un solo caso lento sposta il p95, non il p50;
- 3 richieste, 1 fallback (la complessa con il cloud giù), 0 violazioni (la riservata è rimasta in locale);
- risparmio 95,65%: tutto ha risposto il locale, quindi è il rapporto tautologico della [lezione 06](06-costi-veri-e-tco.md);
- la rotta della richiesta in fallback resta `cloud` nel report per rotta: la rotta è quella **decisa**, il modello quello che **ha risposto**.

## Un errore trovato grazie all'osservabilità

Nel talk: "Langfuse mostra il simbolo del dollaro, ma i miei valori sono euro. In un report a un CFO, quel dettaglio fa più danni di un bug." L'unità di misura fa parte del dato.

## Esercizi

1. ★ Calcola a mano p50 e p95 di `[200, 210, 220, 230, 240, 250, 260, 270, 280, 9000]` e verifica con `percentile`.
2. ★ Con `jq`, scrivi una query su `data/calls.jsonl` che elenchi le richieste in fallback con il motivo. (Soluzione in [tecnica/07](../tecnica/07-osservabilita.md).)
3. ★★ Scrivi un `TracerPort` che solleva sempre un'eccezione e verifica che `ExecuteRequest.execute` non fallisca. Quale test del progetto controlla già questo?
4. ★★ Perché `route` e `model` sono due campi separati? Fai un esempio in cui un report basato solo su `route` darebbe una conclusione sbagliata sui costi.
5. ★★★ Proponi una metrica Prometheus nuova che ti avviserebbe se il router comincia a mandare in cloud molte più richieste del solito. Scrivi la query PromQL.

## Da ricordare

- Registra sempre rotta decisa **e** modello che ha risposto, costo reale **e** costo di riferimento.
- Usa i percentili, non le medie, per la latenza.
- L'osservabilità non deve poter rompere le richieste né far uscire i dati che il router protegge.

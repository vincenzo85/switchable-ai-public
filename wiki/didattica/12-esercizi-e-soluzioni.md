# 12 — Esercizi e soluzioni

Le soluzioni con codice sono state eseguite sul progetto; gli output sono quelli reali. Per gli esercizi aperti c'è una traccia di risposta, non l'unica possibile.

Import comuni agli snippet:

```python
import json
from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, SequentialIds
from core.use_cases.execute_request import ExecuteRequest
from core.domain.policy import decide_route

COMPLEX = "Analizza i trade-off tra monolite e microservizi. " * 20
def make(llm, **kw):
    return ExecuteRequest(llm=llm, ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds(), **kw)
```

---

## Lezione 01 — Perché un router

**1.** (a) tradurre un'etichetta → `local`: breve, ripetitivo; (b) verbale del CdA → `local`: probabilmente riservato, e riassumere non richiede il modello più grande; (c) "come si fa il rilascio da noi?" → `local_rag`: è una domanda sulla documentazione interna; (d) strategia commerciale → `cloud`, se il contenuto non è riservato: ragionamento lungo e aperto.

**2.** Traccia: per ogni richiesta valuta costo per volume (quante al giorno?), qualità necessaria (un errore costa poco o tanto?), sensibilità (dati personali o riservati?). Le richieste ad alto volume e bassa difficoltà sono le prime candidate al locale.

**3.** Vantaggio del locale come piano B: funziona anche senza rete e senza un secondo contratto, e il dato non esce. Svantaggio: qualità più bassa sui compiti complessi. Un secondo cloud manterrebbe la qualità, ma ripeterebbe la dipendenza esterna e il problema della privacy.

---

## Lezione 02 — Architettura esagonale

**1.** In `Container.__init__`: `llm` → `build_llm(settings)` (`PrefixRouterLLM` con Ollama, OpenAI-compat o `UnavailableLLM`), `ledger` → `JsonlLedger`, `clock` → `SystemClock`, `ids` → `FlightIds`, `tracer` → `JsonlTraceStore` (o `FanoutTracer` con Langfuse), `metrics` → `PrometheusMetrics`, `retriever` → `RetrieveContext`, `compressor` → `ExtractiveCompressor` (o `None`), `advisor` → `AdvisedRouter` (o `None`).

**2.**

```python
from core.ports import LLMPort
from core.domain.models import LLMResult
from core.domain.errors import ProviderTimeout

class SlowLLM(LLMPort):
    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        if model.startswith("cloud/") and timeout_s is not None and 5000 > timeout_s * 1000:
            raise ProviderTimeout(f"{model}: 5000ms > {timeout_s * 1000:.0f}ms")
        return LLMResult("ok", model, 10, 2, 5000 if model.startswith("cloud/") else 50)

r = make(SlowLLM(), cloud_timeout_s=1).execute(COMPLEX)
print(r.record.model, r.record.fallback, r.record.fallback_reason)
# ollama/qwen2.5:7b True cloud/gpt-4o: 5000ms > 1000ms
```

Il cloud supera il budget di latenza, l'adapter solleva `ProviderTimeout`, il core passa al fallback locale.

**3.** Con `import requests` dopo `from __future__ import annotations` in `core/domain/pricing.py`:

```
FAILED tests/test_architecture_boundaries.py::test_core_does_not_import_unexpected_externals
E       AssertionError: core/ importa pacchetti esterni non attesi:
E         core/domain/pricing.py importa requests
```

(Attenzione: se lo metti dentro la docstring iniziale non è un import, e il test giustamente non scatta.)

**4.** La richiesta **non** fallisce: `_observe` chiama metriche e tracer dentro `try/except Exception`. Il test che lo garantisce è `test_broken_tracer_never_breaks_the_request` in `tests/test_use_case_execute.py`.

---

## Lezione 03 — Routing deterministico

**1.**

| Richiesta | Rotta | Regole | Tipo | `keyword_hit` |
|---|---|---|---|---|
| (a) "Categorizza questa email…" | `local` | — | classification | vero |
| (b) "Nella documentazione: il cliente con IBAN…" | `local_rag` | `data_residency`, `knowledge_base` | rag_query | vero |
| (c) "Riassumi questo paragrafo" | `local` | — | classification | **falso** |

In (b) il cloud è vietato (`cloud_allowed: false`) ma la rotta resta RAG: è locale comunque.

**2.** Falso: nessuna parola chiave, il tipo è il default per un testo breve. "rag" non scatta perché la regex richiede che la parola chiave **inizi** una parola (`(?<!\w)rag`): in "paragrafo" "rag" è preceduto da "pa".

**3.**

```python
from core.domain.models import RoutingContext
d = decide_route(DR, RoutingContext(budget_remaining_eur=0.1, budget_guard_eur=0.2))
# local ('budget_guard',) task complesso ma budget cloud sotto soglia: resta in locale
```

(`DR` è il prompt di disaster recovery dell'esempio della lezione.)

**4.** Esempi verificati: "Conviene passare a Kubernetes o restare su VM?", "Perché il nostro checkout è lento il venerdì sera?", "Scrivi un piano per ridurre il churn dei clienti business". Tutti: `local`, tipo `classification` di default, `keyword_hit` falso, complessità bassa. In comune: sono brevi e chiedono ragionamento **senza** usare le parole chiave del reasoning.

**5.** Traccia: aggiungere segnali come le domande comparative ("conviene", "o … ?", "perché") o affidare i casi `keyword_hit = False` all'advisor (modalità `fallback`). Non va verificata sul set di controllo perché quel set è già stato visto: ritoccare le regole finché passa lo trasforma in un set di casa e il numero diventa gonfiato. Serve un set dev nuovo per scegliere e il set di controllo per misurare una sola volta.

---

## Lezione 04 — Fallback e resilienza

**1.** Con `cloud_timeout_s=10` la latenza (5 s) sta nel budget: risponde il cloud, nessun fallback.

```
cloud/gpt-4o False 5000
```

**2.** `FakeLLM` con `fail` solleva subito, senza attendere. In produzione un cloud che non risponde ti fa aspettare fino al timeout: il runbook suggerisce di abbassare `SAI_CLOUD_TIMEOUT_S` se i fallback superano il 20% delle richieste cloud, e di passare a `SAI_LOCAL_ONLY=true` se il disservizio dura.

**3.**

```python
def valid_json(t):
    try:
        d = json.loads(t)
        return isinstance(d, dict) and {"fornitore", "data", "importo"} <= set(d)
    except json.JSONDecodeError:
        return False

P = "Estrai fornitore, data e importo: Fattura n. 12 del 12/03/2026, importo 1.240 EUR, fornitore Alfa Srl"
good = '{"fornitore": "Alfa Srl", "data": "12/03/2026", "importo": "1240"}'
for reply in (good, "Il fornitore è Alfa Srl"):
    r = make(FakeLLM({"ollama/": {"reply": reply}, "cloud/": {"reply": good}})).execute(P, validator=valid_json)
    print(r.record.model, r.record.escalated)
# ollama/qwen2.5:7b False
# cloud/gpt-4o True
```

La risposta in testo libero va in escalation.

**4.** Con `FakeLLM` (token = caratteri/4): escalation = 6,72·10⁻⁵ €; risposta locale corretta (13 token in, 1 out) = 2,8·10⁻⁶ €. L'escalation costa **24 volte** tanto: un validatore troppo severo si paga.

**5.** Il test simula un gateway che, chiesto `smart-cloud`, risponde con un modello locale nel campo `model`. Verifica che il `LLMResult` riporti il modello locale e quindi che `ExecuteRequest` registri `fallback=True`. Senza `served_as` il registro direbbe "cloud": costo cloud fatturato per un lavoro fatto in locale, fallback invisibili nel report e nella dashboard.

---

## Lezione 05 — RAG locale

**1.** `sim = 0,6·1 + 0,8·0 = 0,6`. Sì, sono normalizzati: `√(0,6² + 0,8²) = 1` e `|b| = 1`.

**2.** Con `HashEmbedder`:

```
0.27 infra.md '# Porte\n\nLangfuse ascolta sull'
0.13 runbook.md '## Budget esaurito\n\nLe richies'
```

Il chunk giusto è **secondo**. L'embedding giocattolo conta solo le parole uguali (e le collisioni dell'hashing): "budget" non basta. Un embedding addestrato capisce che "finisce il budget" e "budget esaurito" vogliono dire la stessa cosa. È esattamente il motivo per cui il progetto usa `nomic-embed-text` e misura hit@3.

**3.** Cinque paragrafi da ~300 caratteri con `target_size=800` → **3 chunk** (616, 616, 316 caratteri), e il titolo `## Sezione lunga` è in testa a **tutti** e tre.

**4.** Perché la rotta RAG è locale: modello locale, embedding locali, indice locale. Il dato non esce. Se la risposta la scrivesse un modello cloud, il **contesto recuperato** (pezzi di documenti interni) e la domanda con il dato sensibile andrebbero in cloud: violazione di residency.

**5.** `HashEmbedder` confronta parole identiche: "dashboard dei costi" e "cockpit" non hanno parole in comune. Un embedding addestrato su molti testi impara che parole diverse possono avere significati vicini e li mette vicini nello spazio dei vettori.

---

## Lezione 06 — Costi veri e TCO

**1.** 300 + 700 token: locale 0,0002 €, cloud 0,0046 €, risparmio 95,65%. Con 3.000 + 7.000: 0,002 € e 0,046 €, risparmio **ancora** 95,65%. È il rapporto tautologico.

**2.**

```python
from core.domain.pricing import local_cost_per_mtok, LocalTcoInputs

def breakeven(tps, cloud=4.6):
    total = lambda u: local_cost_per_mtok(LocalTcoInputs(2000, 36, 140, 0.30, tps, u))["total"]
    lo, hi = 0.001, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if total(mid) > cloud else (lo, mid)
    return hi

print(breakeven(42))    # 0.118…  → circa 11,8%
```

**3.** A 84 token/s e 5% di utilizzo: 5,24 €/Mtok (energia 0,14, hardware 5,10): ancora sopra il cloud. Il pareggio scende a circa **5,7%** (`breakeven(84)`). Raddoppiare il throughput dimezza sia l'energia sia l'hardware per token.

**4.** Nello stress test 15 richieste su 100 sono decise per il cloud e 11 vengono eseguite davvero in cloud, pagate a listino cloud; in più l'escalation e il cloud simulato fanno pagare token cloud. Il costo reale non è più solo "tutto a prezzo locale", quindi il risparmio scende a −82%. Il budget guard (40 richieste) limita la spesa cloud: senza, il risparmio sarebbe più basso.

**5.** Traccia: (1) risparmio rispetto a cosa, con quale prezzo per il locale? Include l'hardware? (2) Cambia se cambia il carico, o esce sempre uguale? (3) Qual è l'utilizzo della GPU, e qual è la qualità delle risposte rispetto al cloud sulle stesse richieste?

---

## Lezione 07 — Compressione

**1.** Con `keep_ratio=0.8` tornano le frasi sul backup, sui log (una sola volta) e sulla dashboard (una sola volta): i duplicati identici restano esclusi.

```
Il servizio pagamenti gira su tre nodi. I log vengono ruotati ogni notte. Il backup del database è alle 02:30 ogni giorno. La dashboard mostra le latenze. Il team on-call cambia il lunedì. Il certificato TLS scade il 14 novembre.
```

**2.** Sì: "Il certificato TLS scade il 14 novembre." resta (era già tra le frasi più rare).

**3.** `r.text[:40] == text[:40]` è vero. I provider con prompt caching fanno pagare meno i prefissi identici già visti: se la compressione cambia l'inizio, ogni richiesta paga il prefisso pieno.

**4.** Il prompt arriva come un blocco unico: istruzione e contesto non sono separati, quindi il core non sa quale parte sia "la domanda". Per questo in produzione la compressione è agnostica (e misurata come tale: 70–75% di risposte corrette). Una possibile evoluzione: separare istruzione e contesto e passare l'istruzione come `question`.

**5.** Traccia: un set di richieste di ragionamento con risposte di riferimento; giudizio di qualità alla cieca (umano o modello giudice) su originale e compresso; metriche: tasso di risposte giudicate equivalenti, token risparmiati, differenza di costo. Ripetere su più valori di `keep_ratio`.

---

## Lezione 08 — Osservabilità

**1.** p50 = 245 ms (media di 240 e 250); p95 ≈ 5.076 ms (interpolazione tra 280 e 9.000). Un solo valore estremo domina il p95.

**2.** Vedi [tecnica/07](../tecnica/07-osservabilita.md): `jq -c 'select(.fallback) | {request_id, route, model, fallback_reason}' data/calls.jsonl`.

**3.** Vedi la soluzione 02.4: la richiesta completa; il test è `test_broken_tracer_never_breaks_the_request`.

**4.** Esempio: 100 richieste decise `cloud` ma tutte servite in fallback dal locale. Un report per `route` direbbe "100 richieste cloud", e qualcuno concluderebbe che la spesa cloud è alta o che il cloud funziona. Il `model` dice che il cloud non ha risposto **mai**.

**5.** Traccia: la quota di richieste servite dal cloud.

```
sum(rate(sai_requests_total{model=~"cloud/.*"}[15m])) / sum(rate(sai_requests_total[15m]))
```

Avviso se supera, per esempio, il doppio della media degli ultimi 7 giorni (`avg_over_time` della stessa espressione su `[7d]` come riferimento).

---

## Lezione 09 — Router appreso

**1.** Con `min_confidence=0.95` il ticket resta `local`, `applied=False`, `note = "confidenza 0.90 < 0.95: vince la regola"`.

**2.** Con un advisor che solleva `ProviderError("server giù")`: la decisione è quella della regola (`local`), `Advice.error = "server giù"`, `applied=False`.

**3.** "Classifica questo ticket: login rotto" ha una parola chiave (`keyword_hit` vero): in modalità `fallback` l'advisor **non** viene chiamato (`Advice` è `None`). "Quale database conviene…" non ha parole chiave: l'advisor viene chiamato e, con `AlwaysCloud`, la rotta diventa `cloud`.

**4.** Scegliere la migliore tra 8 configurazioni guardando i risultati sul set di controllo è già "addestrare" su quel set: si sceglie anche la configurazione che per caso va meglio su **quelle** 32 richieste. Il numero riportato è ottimista. Per questo si sceglie sul dev e si misura una volta sul test.

**5.** Traccia: shadow per un periodo che copra il traffico tipico (es. due settimane); campi `advisor_choice`, `advisor_p`, `advisor_agreed`, `advisor_latency_ms`, più una revisione umana di un campione dei disaccordi per sapere chi aveva ragione. Decisione: passare ad `active` (o `fallback`) se, sui disaccordi rivisti, l'advisor ha ragione abbastanza spesso da giustificare la latenza media aggiunta e non manda in cloud richieste che non lo meritano.

---

## Lezione 10 — Data Flywheel

**1.** `('Cliente <CF>, carta <CARD>', 2)`.

**2.** Dopo l'anonimizzazione, due ticket identici di clienti diversi diventano lo stesso esempio (`Classifica il ticket di <EMAIL>: …`) e uno viene scartato come duplicato. È voluto: per l'addestramento conta il **modello** della richiesta, non chi l'ha fatta, e i duplicati sbilanciano il dataset.

**3.** Traccia: un pollice su/giù nell'interfaccia o un esito a valle (il ticket è stato riclassificato da un umano? la checklist QA è stata accettata?). Si salva nella trace (`feedback`) e si esportano solo gli esempi con feedback positivo, o si pesano.

**4.** `teacher = t.model.startswith("cloud/")`: conta il modello che **ha risposto**, non la rotta. Una risposta in fallback l'ha scritta il modello locale: non è un esempio da cui il locale può imparare qualcosa di nuovo.

**5.** La uccide `test_flywheel_exports_scrubbed_chat_dataset` (in `tests/test_use_case_ops.py`), oltre a `test_scrub_pii_replaces_email_iban_cf_phone`. Un altro test possibile: esportare una trace con un IBAN e verificare che nessuna riga del dataset contenga la sequenza `IT60X`.

---

## Lezione 11 — Metodo

**1.** Atteso: 15 mutazioni, 15 uccise (`💀 KILLED`), qualche minuto (la suite gira una volta per mutazione).

**2.** Mutazione proposta in `price_per_1k`: `return PRICING["local"] if _is_local(model) else PRICING[CLOUD_REFERENCE]` → `return PRICING["local"]`. La uccide `test_unknown_model_falls_back_to_conservative_cloud_price` in `tests/test_domain_pricing.py`.

**3.** Traccia: scrivile come le scriverebbe un collega, non pensando alle regole. Misurale con `decide_route` e confronta con la rotta che sceglieresti tu. Aspettati un risultato vicino al 53% del set di controllo.

**4.** Tre esempi: il −96% (smontato in TCO ammortizzato e −82% con rotte miste); il 100% del router (affiancato dal 53% sul set di controllo); lo stress test (cloud simulato dichiarato nel codice, nei risultati e sulle slide).

**5.** In `Container.__init__` sostituisci `compressor=ExtractiveCompressor() if s.compress == "extractive" else None` con `compressor=None` e lancia la suite.

Risultato reale (verificato il 2026-10-07): **150 passed**. Nessun test se ne accorge: la compressione è testata come unità (`test_adapters.py`) e dentro `ExecuteRequest` (`test_use_case_execute.py`), ma non come feature **cablata**. È esattamente il caso che la regola del test di scollegamento vuole evitare. Il test che manca, per esempio in `tests/test_wiring.py`: con il `Container` reale e un LLM finto, una richiesta cloud oltre `SAI_COMPRESS_THRESHOLD` deve registrare `tokens_saved_by_compression > 0`. È un buon primo contributo al progetto.

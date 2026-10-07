# Estendere il sistema — ricette per sviluppatori

Tutte seguono lo stesso schema: **test prima** (rosso per il motivo giusto), codice, `make check` verde, pagina in `wiki/classes/` se nasce una classe significativa, voce in `wiki/lessons/` se hai imparato qualcosa.

---

## E1 — Aggiungere una parola chiave a un tipo di task

Esempio: "triage" deve contare come classificazione.

1. Test in `tests/test_domain_policy.py`:
   ```python
   def test_triage_is_a_classification_by_keyword():
       c = classify("Fai il triage: login rotto")
       assert c.kind == "classification" and c.keyword_hit
   ```
   Oggi fallisce per il motivo giusto: il tipo è già `classification`, ma solo come default (`keyword_hit` è falso).
2. In `core/domain/policy.py` aggiungi `"triage"` a `CLASSIFICATION_KEYWORDS`.
3. Ricontrolla il set di controllo: `benchmarks/routing_heldout.py` **non va ritoccato** per far passare la regola (diventerebbe un set di casa). Misuralo e basta.

---

## E2 — Aggiungere una regola dura

Esempio: vietare il cloud fuori dall'orario d'ufficio.

1. Aggiungi il campo al contesto in `core/domain/models.py` (`RoutingContext.after_hours: bool = False`).
2. Test in `test_domain_policy.py`: con `after_hours=True` un task complesso resta locale e `rules` contiene `after_hours`.
3. In `decide_route` aggiungi `if ctx.after_hours: rules.append("after_hours")` dopo le altre regole, e la voce nel dizionario `why`.
4. In `ExecuteRequest.routing_context()` calcola il valore con `self.clock.now()` (mai `time` diretto: il clock è una porta, così il test è deterministico).
5. Test in `test_use_case_execute.py` con `FixedClock`.
6. Aggiungi una mutazione in `tools/mutation_check.py` che spegne la regola: deve morire.

---

## E3 — Aggiungere un provider LLM

Esempio: un endpoint con un'API non OpenAI-compatible, prefisso `acme/`.

1. Test in `tests/test_adapters.py` contro lo stub di `conftest.py`: token contati dal motore, HTTP 500 ⇒ `ProviderError`, lentezza ⇒ `ProviderTimeout`.
2. Crea `adapters/llm/acme.py` con una classe `AcmeLLM(LLMPort)`; usa `adapters/llm/http.post_json` (mappa già gli errori sulle eccezioni di dominio). Ritorna `LLMResult(text, model, tokens_in, tokens_out, latency_ms)` con il `model` **interno** (`acme/...`).
3. In `app/composition.py`, `build_llm`: `routes["acme/"] = AcmeLLM(...)` se configurato, altrimenti `UnavailableLLM("...")`.
4. Aggiungi le variabili a `Settings` e a `.env.example`; il prezzo in `PRICING` (vedi [Costi](10-costi-e-tco.md)).
5. Test di cablaggio in `tests/test_wiring.py`.

Se il provider è OpenAI-compatible non serve un adapter nuovo: basta `OpenAICompatLLM(base_url, key)` su un nuovo prefisso.

---

## E4 — Cambiare modello locale

Solo configurazione:

```
SAI_LOCAL_MODEL=ollama/llama3.1:8b
SAI_RAG_MODEL=ollama/llama3.1:8b
```

Aggiungi il prezzo in `PRICING` se vuoi un valore diverso dal `local` di default. Se usi il gateway, aggiorna anche `infra/litellm.yaml`.

---

## E5 — Aggiungere una sorgente al RAG

Cartelle markdown del repo: aggiungile a `roots` nel `Container` (`app/composition.py`). Altri formati: estendi `FileSystemDocuments.patterns` (es. `("*.md", "*.txt")`) o crea un nuovo `DocumentSourcePort` (es. Confluence) con il suo test, e passalo a `BuildRagIndex`. Poi `./run.sh rag-build`.

---

## E6 — Aggiungere un tool MCP

1. In `adapters/mcp/server.py`, dentro `build_tools`, aggiungi una funzione con parametri tipizzati e docstring breve; aggiungila alla tupla restituita.
2. Aggiungi la descrizione **corta** in `DESCRIPTIONS` (pesa a ogni richiesta dell'agente).
3. Test sulla funzione pura via `build_tools(container)`.
4. `tools/mcp_smoke.py` per verificare l'handshake reale e il nuovo peso delle definizioni.

---

## E7 — Aggiungere un endpoint HTTP

In `app/api.py`: modello pydantic per il corpo, funzione con `c=Depends(container)`, `DomainError` → `HTTPException(503)`. Test con `TestClient` in `tests/test_wiring.py`.

---

## E8 — Aggiungere una metrica

1. Test in `test_adapters.py`: dopo `observe(rec)` l'esposizione contiene la nuova serie.
2. In `PrometheusMetrics.__init__` crea la metrica sul registry dedicato; aggiornala in `observe`.
3. Rigenera la dashboard: `.venv/bin/python tools/make_grafana_dashboard.py`.

---

## E9 — Aggiungere un benchmark

1. `benchmarks/run_<nome>.py`: salva con `_common.save(name, data)`, che scrive `benchmarks/results/<nome>.json` aggiungendo `meta` con data, commit e macchina.
2. Se un numero va nel talk: aggiungilo in `build_numbers.py` con `display`, `label` e `source`; poi `./run.sh numbers`.
3. Si lancia con `./run.sh bench <nome>`.

---

## E10 — Un nuovo caso d'uso

1. Classe in `core/use_cases/` che riceve le porte nel costruttore e usa solo stdlib e `core`.
2. Test con gli adapter di `adapters/memory`.
3. Cablaggio nel `Container`; ingresso in CLI, API o MCP; test di cablaggio.
4. Pagina in `wiki/classes/`.

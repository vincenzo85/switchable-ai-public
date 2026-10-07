# ExecuteRequest (`core/use_cases/execute_request.py`)

Ogni richiesta, da qualsiasi ingresso (CLI, API, n8n, MCP, stress test), passa da qui:

1. `decide_with_advice`: `decide_route` con il contesto (budget residuo dal registro, local-only), poi l'`AdvisedRouter` se c'è.
2. **RAG**: `retriever.retrieve` → `build_rag_prompt` (contesto + richiesta di citare [n]). Se l'indice non c'è (`DomainError`), si degrada su risposta locale senza contesto e il motivo finisce in `fallback_reason`.
3. **Compressione**: solo sulla rotta `cloud` e oltre `compress_threshold_tokens`.
4. **Catena** `(modello, *fallbacks)`: il primo che non solleva `ProviderError` vince. Il timeout cloud è `cloud_timeout_s`.
5. **Escalation**: se la risposta locale non passa il `validator` (default: non vuota), il cloud è ammesso e c'è un modello di escalation, si ritenta in cloud. Il costo somma entrambe le chiamate.
6. `CallRecord` → ledger, metriche, trace. Metriche e tracer **non possono** far fallire la richiesta.

Fallback del gateway: se LiteLLM ha fatto fallback per conto suo, `OpenAICompatLLM.served_as` riporta il modello che ha risposto davvero e qui risulta `fallback=True`.

Test: `tests/test_use_case_execute.py`. Mutazioni che lo riguardano in `tools/mutation_check.py`: fallback mai eseguito, contesto RAG non passato, escalation spenta.

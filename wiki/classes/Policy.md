# Policy (`core/domain/policy.py`)

- `classify(prompt)` → `Classification(kind, complexity, sensitive, reasons)`.
  - **kind**: si legge solo dal primo paragrafo, al massimo 240 caratteri, con parole chiave a inizio parola; se scattano più tipi vince la parola chiave che compare prima.
  - **complexity**: dipende dalla lunghezza; per `classification` ed `extraction` la soglia è 5 volte più alta.
  - **sensitive**: si cerca su tutto il testo, con parole chiave e pattern PII (email, IBAN, codice fiscale, carta).
- `decide_route(prompt, context, catalog)`: le regole dure, in ordine `data_residency` > `local_only` > `budget_guard`, decidono se il cloud è ammesso; poi `rag_query` → RAG locale, complesso → cloud con fallback locale, il resto → locale con escalation possibile.
- `reroute(base, route)`: usata dall'advisor; solleva `ValueError` se si chiede il cloud quando le regole lo vietano.

Limite misurato: 53% sul set di controllo (`benchmarks/routing_heldout.py`), con tutti gli errori verso la rotta più economica. Vedi la lezione sul set di controllo.

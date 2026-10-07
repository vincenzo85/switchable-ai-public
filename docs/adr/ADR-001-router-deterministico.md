# ADR-001 — Router deterministico, non un LLM

Stato: accettata.

Contesto: si potrebbe chiedere a un modello linguistico di decidere la rotta di ogni richiesta.

Decisione: il router di base è deterministico (parole chiave, lunghezza, pattern di dati personali). È gratuito, prevedibile al 100%, testabile con mutation testing e non aggiunge latenza.

Conseguenze: un router fatto da un LLM costa token e latenza a ogni richiesta, e può essere manipolato con sequenze avversarie che spingono tutto verso il modello costoso (Shafran et al. 2025, "Rerouting LLM Routers"). Le regole dure (residency, budget, local-only) restano sempre deterministiche; un modello può al massimo consigliare tra le rotte ammesse (ADR-003).

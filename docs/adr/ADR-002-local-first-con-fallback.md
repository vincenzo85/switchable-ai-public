# ADR-002 — Local-first, cloud solo per il complesso, fallback sempre

Stato: accettata.

Decisione: i task semplici e ripetitivi (classificazione, estrazione) vanno sul modello locale. Il cloud serve solo il reasoning complesso e ha sempre un fallback locale. Le domande sulla documentazione interna vanno sul RAG locale. I dati sensibili non lasciano mai la macchina, nemmeno verso l'osservabilità.

Conseguenze: senza chiave cloud il sistema funziona comunque (il fallback si esercita davvero). Il costo per richiesta semplice è dell'ordine di centesimi di centesimo, misurato dal registro costi.

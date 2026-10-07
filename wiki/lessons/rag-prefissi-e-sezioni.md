# RAG: prefissi di task e chunk per sezione

Due correzioni misurate (`benchmarks/run_rag.py`), che hanno portato hit@3 dall'83% al 100%:

1. **Chunk per sezione markdown.** Spezzando solo per paragrafi, il titolo "## L'indice RAG è vuoto" finiva in un chunk e "Lanciare `./run.sh rag-build`" in un altro: il modello riceveva la domanda senza la risposta.
2. **Prefissi di task.** `nomic-embed-text` è addestrato con `search_document:` e `search_query:`. Senza prefissi, la domanda sulla porta di Langfuse non trovava la tabella giusta.

Resta un limite: la risposta contiene il dato atteso nell'83% dei casi anche con la fonte giusta in mano. Il modello locale a volte risponde a modo suo.

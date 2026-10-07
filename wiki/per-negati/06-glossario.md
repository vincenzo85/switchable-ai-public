# Glossario

Una riga per parola. In ordine alfabetico.

| Parola | Cosa vuol dire |
|---|---|
| **ADR** | *Architecture Decision Record*: una paginetta che spiega una scelta di progetto e il perché. Sono in `docs/adr/`. |
| **Adapter** | il pezzo di codice che parla con il mondo esterno (Ollama, un database, Langfuse). Sta in `adapters/`. |
| **Advisor** | un piccolo modello AI che "consiglia" la rotta. Facoltativo; le regole dure restano sopra di lui. |
| **API** | un indirizzo web a cui un programma manda richieste. Qui: http://localhost:8088. |
| **Budget guard** | la regola che spegne il cloud quando il budget giornaliero sta finendo. |
| **Chunk** | un pezzo di documento (qualche paragrafo) indicizzato per la ricerca. |
| **CLI** | *Command Line Interface*: i comandi da terminale (`./run.sh …`). |
| **Cloud** | un modello AI su server di altri, che si paga a consumo (es. GPT-4o). |
| **Data residency** | la regola "questi dati non devono uscire da qui". Qui: niente dati sensibili in cloud. |
| **Docker** | un programma che fa girare altri programmi in "scatole" isolate (container). |
| **Embedding** | la traduzione di un testo in una lista di numeri, così due testi simili hanno numeri vicini. Serve per la ricerca nei documenti. |
| **Escalation** | quando la risposta del modello locale è vuota o non valida, si richiede al cloud. |
| **Fallback** | il piano B: se il modello scelto non risponde, risponde un altro (qui sempre il locale). |
| **Fine-tuning** | addestrare ancora un modello su esempi propri per specializzarlo. |
| **Flywheel** (volano) | il ciclo "le richieste di oggi diventano esempi per migliorare il modello di domani". |
| **Gateway** | un "centralino" davanti ai modelli. Qui è LiteLLM, facoltativo. |
| **Grafana** | il programma che disegna i grafici (il cockpit). |
| **Indice** | il catalogo dei documenti già trasformati in embedding, in `data/rag_index/`. |
| **JSON** | un formato di testo per dati strutturati: `{"chiave": "valore"}`. |
| **JSONL** | un JSON per riga: comodo per i registri che crescono. |
| **Langfuse** | il programma che conserva la traccia di ogni richiesta (la scatola nera). |
| **Latenza** | quanto tempo passa tra la domanda e la risposta. |
| **LLM** | *Large Language Model*: un modello AI che legge e scrive testo. |
| **Locale** | un modello che gira sul tuo computer, gratis a parte l'elettricità. |
| **MCP** | *Model Context Protocol*: un modo standard per dare "strumenti" a un agente AI. |
| **Mutation testing** | rompere apposta il codice per controllare che i test se ne accorgano. |
| **n8n** | un programma per costruire flussi automatici con blocchi visivi. |
| **Ollama** | il programma che fa girare i modelli AI sul tuo computer. |
| **p50 / p95** | la latenza tipica (metà delle richieste è più veloce) / la latenza dei casi lenti (95 su 100 sono più veloci). |
| **PII** | *Personally Identifiable Information*: dati personali (email, IBAN, codice fiscale…). |
| **Porta** (di rete) | il "numero di interno" di un servizio sul computer: 8088, 3012… |
| **Porta** (nel codice) | un'interfaccia: il contratto che un adapter deve rispettare. Sta in `core/ports/`. |
| **Prometheus** | il programma che raccoglie i numeri ogni pochi secondi. |
| **Prompt** | il testo della richiesta che si manda al modello. |
| **RAG** | *Retrieval-Augmented Generation*: prima si cercano i pezzi di documento giusti, poi si chiede al modello di rispondere usando quelli. |
| **Rotta** | dove viene mandata la richiesta: `local`, `cloud` o `local_rag`. |
| **Router** | il pezzo che decide la rotta: la torre di controllo. |
| **Shadow** (modalità) | l'advisor viene interrogato e misurato, ma decide ancora la regola. |
| **TCO** | *Total Cost of Ownership*: il costo vero, compreso l'acquisto dell'hardware diviso negli anni, non solo la bolletta. |
| **Timeout** | il tempo massimo di attesa: oltre, si passa al fallback. |
| **Token** | il "pezzetto" di testo con cui ragionano e si pagano i modelli: circa 4 caratteri. |
| **Trace** | la registrazione completa di una richiesta: domanda, risposta, rotta, tempi, costo. |
| **vLLM** | un altro motore per modelli locali, più veloce di Ollama quando arrivano tante richieste insieme. |

# Architettura di switchable_ai

## Il percorso di una richiesta

Ogni richiesta, che arrivi dalla CLI, dall'API OpenAI-compatible, dal webhook di n8n o da un tool MCP, segue lo stesso percorso in `core/use_cases/execute_request.py`:

1. **Decisione di rotta** (`core/domain/policy.py`). Il classificatore è deterministico: legge l'intento dal primo paragrafo dell'istruzione, misura la lunghezza e cerca dati sensibili in tutto il testo. Le rotte sono tre: `local` (modello locale), `cloud` (modello a consumo, sempre con fallback locale) e `local_rag` (risposta dalla knowledge base locale).
2. **Regole dure**, in ordine di priorità: `data_residency` (un dato sensibile non va mai in cloud), `local_only`, `budget_guard` (sotto la soglia di budget giornaliero il cloud si spegne). Nessun modello, nemmeno l'advisor, può scavalcarle.
3. **Advisor opzionale** (Rizzo Flow o Open-Jev, vedi ADR-003): in modalità shadow viene solo misurato, in modalità active sceglie tra le rotte ammesse.
4. **Contesto RAG**: per la rotta `local_rag` i chunk recuperati vengono inseriti nel prompt e la risposta cita le fonti come [1], [2]. Se l'indice manca, la rotta degrada su risposta locale senza contesto e il motivo finisce nel registro.
5. **Compressione**: solo sulla rotta a pagamento (cloud) e solo oltre la soglia `SAI_COMPRESS_THRESHOLD`. Il prefisso stabile del prompt resta intatto per non invalidare il prompt caching del provider.
6. **Chiamata con fallback**: se il cloud risponde con errore, manca la chiave o supera il budget di latenza (`SAI_CLOUD_TIMEOUT_S`), la richiesta passa al modello locale. Se il gateway LiteLLM fa fallback per conto suo, lo rileviamo dal campo `model` della risposta.
7. **Escalation**: se la risposta locale non supera la validazione (per esempio una categoria fuori lista) e il cloud è ammesso, si ritenta in cloud. Il costo registrato comprende entrambe le chiamate.
8. **Registro e osservabilità**: ogni richiesta produce un `CallRecord` (token contati dal motore, costo reale, costo se tutto-cloud, rotta, fallback, regole), una metrica Prometheus e una trace locale; Langfuse riceve la trace senza il contenuto se il dato è sensibile.

## Esagonale

`core/` non importa nulla fuori dalla standard library (lo verifica `tests/test_architecture_boundaries.py`). Gli adapter in `adapters/` implementano le porte di `core/ports`. `app/composition.py` è l'unico punto che sceglie quali adapter usare, configurato da variabili d'ambiente.

## Componenti di infrastruttura

| Componente | Porta | Ruolo nel talk |
|---|---|---|
| API switchable_ai | 8088 | gate unico: OpenAI-compatible, webhook n8n, /metrics |
| LiteLLM | 4000 | torre di controllo: alias fast-local, smart-cloud, rag-local, fast-vllm, con fallback |
| Ollama (host) | 11434 | motore locale: qwen2.5:7b, nomic-embed-text |
| vLLM (host, opzionale) | 8010 | motore locale ad alto throughput per batch |
| Langfuse | 3011 | scatola nera: una trace per richiesta |
| Prometheus + Grafana | 9091, 3012 | cockpit: costi, latenze, fallback, violazioni residency |
| n8n | 5678 | equipaggio di cabina: intake automatico dei documenti SDLC |

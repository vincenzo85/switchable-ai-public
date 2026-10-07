# Porte e adapter

| Porta (`core/ports`) | Adapter reali | Adapter in memoria (test, stress) |
|---|---|---|
| `LLMPort` | `OllamaLLM`, `OpenAICompatLLM` (cloud, LiteLLM, vLLM), `PrefixRouterLLM`, `UnavailableLLM`, `SimulatedCloudLLM` | `FakeLLM` (latenza, errori, jitter iniettabili) |
| `EmbedderPort` (+ `embed_query`) | `OllamaEmbedder` (prefissi di task per nomic) | `HashEmbedder` |
| `VectorIndexPort` | `HnswIndex` | `MemoryIndex` |
| `DocumentSourcePort` | `FileSystemDocuments` (docs, wiki, infra, kb, git log) | `MemoryDocuments` |
| `CostLedgerPort`, `TraceStorePort`, `DatasetSinkPort` | JSONL in `data/` | `InMemoryLedger`, `InMemoryTraceStore` |
| `MetricsPort` | `PrometheusMetrics` | `RecordingMetrics` |
| `TracerPort` | `LangfuseTracer` (ingestion API, niente SDK; contenuto sensibile non inviato), `FanoutTracer` | — |
| `PromptCompressorPort` | `ExtractiveCompressor` (prefisso stabile), `NoCompressor` | — |
| `RouteAdvisorPort` | `SystemOneAdvisor` | `ScriptedAdvisor` nei test |

La scelta avviene **solo** in `app/composition.py`, da variabili d'ambiente (`.env.example`).

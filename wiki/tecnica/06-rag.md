# RAG locale

Tutto resta sulla macchina: documenti, embedding (Ollama) e indice (hnswlib su disco).

## Componenti

| Ruolo | Classe | File |
|---|---|---|
| sorgente documenti | `FileSystemDocuments` | `adapters/docs/filesystem.py` |
| chunking | `chunk_markdown` | `core/domain/text.py` |
| embedding | `OllamaEmbedder` | `adapters/embedding/ollama.py` |
| indice | `HnswIndex` | `adapters/index/hnsw.py` |
| costruzione | `BuildRagIndex` | `core/use_cases/rag.py` |
| recupero | `RetrieveContext(top_k=3, min_score=0.0)` | `core/use_cases/rag.py` |
| prompt | `build_rag_prompt` | `core/use_cases/execute_request.py` |

## Sorgenti indicizzate

Configurate nel `Container`:
- `README.md`, `MISSION.md`;
- tutti i `*.md` sotto `docs/`, `wiki/`, `infra/` (ricorsivo);
- tutti i `*.md` in `data/kb/` (documenti aggiunti con `ingest` o dal webhook n8n);
- la storia git: `git log -200 --date=short` come documento virtuale `git-log` (titolo "Storia del repository").

I percorsi sono relativi alla radice del repo. I duplicati (stesso file risolto) sono saltati.

`add(name, text)` salva in `data/kb/` con un nome ripulito (`[^\w.\-]` → `_`, estensione `.md` forzata): niente path traversal.

## Chunking (`chunk_markdown(text, target_size=800)`)

1. Si spezza per **sezioni markdown** (righe che iniziano con `#`…`######`).
2. Dentro una sezione si raggruppano i paragrafi (separati da riga vuota) fino a ~`target_size` caratteri.
3. Il titolo della sezione è **ripetuto** in testa a ogni chunk della sezione e non viene mai separato dal suo contenuto.
4. Sezioni diverse non si fondono.

Motivo: con il chunking per soli paragrafi un titolo ("## L'indice RAG è vuoto") finiva in un chunk e la sua risposta in un altro. La correzione ha portato hit@3 dall'83% al 100% (insieme ai prefissi di task).

## Embedding

`OllamaEmbedder` chiama `POST {OLLAMA_BASE_URL}/api/embed` e **normalizza** il vettore (norma 1).

Prefissi di task (`TASK_PREFIXES`): per `nomic-embed-text` i documenti sono preceduti da `search_document: ` e le domande da `search_query: `. Per modelli sconosciuti nessun prefisso. La porta lo esprime con due metodi: `embed` (documento) e `embed_query` (domanda).

Cambiare modello di embedding ⇒ aggiornare `SAI_EMBED_DIM` e **ricostruire** l'indice.

## Indice (`HnswIndex`)

- `build`: crea un indice hnswlib `space="cosine"`, `M=16`, `ef_construction=200`; scrive `index.bin` e `chunks.json` (`[{id, path, chunk}]`) nella cartella dell'indice. **Sovrascrive** l'indice precedente.
- `search`: carica da disco a ogni chiamata (semplice e coerente con più processi), `ef = max(2k, 50)`, ritorna `Source(path, chunk, score = 1 − distanza)` ordinate per score.
- Indice assente ⇒ `IndexNotReady` (eccezione di dominio).

Cartella: `SAI_RAG_INDEX_DIR` o `data/rag_index`.

## Comandi

```bash
./run.sh rag-build                         # {"chunks": N, "documents": M}
./run.sh rag "Che porta usa Langfuse?"     # top-3 con score e percorso
./run.sh ask "Nella documentazione, che porta usa Langfuse?"   # risposta con citazioni [n]
```

## Degrado

Se la rotta è `local_rag` ma l'indice manca, `ExecuteRequest` non fallisce: risponde in locale senza contesto e scrive `RAG degradato: …` in `fallback_reason`. Il dato non esce in nessun caso.

## Misure (`benchmarks/run_rag.py` → `results/rag.json`)

- 6 domande di riferimento con fonte attesa: **hit@3 100%**;
- risposta corretta con la fonte giusta in mano: **83%** (il modello locale a volte risponde a modo suo);
- la prima domanda non ha parole chiave apposta: il router a regole la manda su `local` e mostra il limite del routing per parole chiave.

## Test

`tests/test_adapters.py` (roundtrip hnsw, indice mancante, prefissi nomic, filesystem), `tests/test_domain_text.py` (chunking), `tests/test_use_case_execute.py` (contesto passato al modello). Mutazione: "il contesto RAG non arriva al modello".

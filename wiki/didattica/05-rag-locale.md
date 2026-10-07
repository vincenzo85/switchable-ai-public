# 05 — RAG locale

## Obiettivi

- Spiegare la *Retrieval-Augmented Generation* passo per passo.
- Capire embedding, similarità coseno e chunking.
- Misurare un RAG con hit@k e non solo "a occhio".

## Il concetto

Un modello linguistico non conosce i **tuoi** documenti (runbook, ADR, configurazioni). Due strade:
- addestrarlo sui documenti (costoso, da rifare a ogni modifica);
- **cercare** i pezzi giusti al momento della domanda e darglieli insieme alla domanda: è il RAG.

Il RAG ha due fasi.

**Indicizzazione** (una volta, e a ogni modifica dei documenti):
1. si spezzano i documenti in **chunk** (pezzi di qualche paragrafo);
2. ogni chunk diventa un **embedding**: un vettore di numeri (qui 768) tale che testi con significato simile hanno vettori vicini;
3. i vettori si salvano in un **indice** che sa trovare i più vicini velocemente.

**Interrogazione** (a ogni domanda):
1. la domanda diventa un embedding;
2. si prendono i *k* chunk più vicini (qui *k* = 3);
3. si costruisce un prompt: "rispondi **solo** con questo contesto e cita le fonti [1], [2]";
4. il modello risponde.

### Vicinanza: la similarità coseno

Due vettori normalizzati (lunghezza 1) sono tanto più simili quanto più il loro prodotto scalare è vicino a 1:

```
sim(a, b) = Σ a_i · b_i        (con |a| = |b| = 1)
```

1 = stessa direzione, 0 = nessuna relazione. L'indice hnswlib restituisce la distanza `1 − sim`; il progetto la riconverte in `score = 1 − distanza`.

### Perché "locale"

Documenti, embedding (Ollama, `nomic-embed-text`) e indice restano sulla macchina. Una domanda sulla documentazione interna non esce mai, anche se contiene dati sensibili.

## Come è fatto qui

| Fase | Codice |
|---|---|
| leggere i documenti | `adapters/docs/filesystem.py`: README, MISSION, `docs/`, `wiki/`, `infra/`, `data/kb/`, git log |
| chunking | `core/domain/text.py`: `chunk_markdown` |
| embedding | `adapters/embedding/ollama.py` (con prefissi di task) |
| indice | `adapters/index/hnsw.py` |
| orchestrazione | `core/use_cases/rag.py`: `BuildRagIndex`, `RetrieveContext` |
| prompt | `core/use_cases/execute_request.py`: `build_rag_prompt` |

### Due correzioni misurate (hit@3 dall'83% al 100%)

1. **Chunk per sezione.** Spezzando per paragrafi, il titolo "## L'indice RAG è vuoto" finiva in un chunk e la risposta "Lanciare `./run.sh rag-build`" in un altro. Ora si spezza per sezione markdown e il titolo viene ripetuto in ogni chunk della sezione.
2. **Prefissi di task.** `nomic-embed-text` è stato addestrato a distinguere `search_document: <testo>` da `search_query: <domanda>`. Senza prefissi, la domanda sulla porta di Langfuse non trovava la tabella giusta. Per questo la porta ha due metodi: `embed` (documento) e `embed_query` (domanda).

### Se l'indice manca

La rotta RAG non fallisce: risponde in locale senza contesto e lo scrive nel registro (`RAG degradato`). Il dato resta comunque in casa.

## Esempio svolto — un RAG in memoria

Con `HashEmbedder` (un embedding "giocattolo" a parole, senza rete) e `MemoryIndex`:

```python
from adapters.memory import HashEmbedder, MemoryIndex, MemoryDocuments
from core.use_cases.rag import BuildRagIndex, RetrieveContext
from core.domain.text import chunk_markdown

docs = MemoryDocuments({
    "runbook.md": "# Runbook\n\n## Il cloud non risponde\n\nOgni richiesta cloud viene ripetuta sul modello locale."
                  "\n\n## Budget esaurito\n\nLe richieste complesse restano in locale fino a mezzanotte UTC.",
    "infra.md": "# Porte\n\nLangfuse ascolta sulla porta 3011, Grafana sulla 3012.",
})
emb, idx = HashEmbedder(), MemoryIndex()
print(BuildRagIndex(docs, emb, idx).execute())
for s in RetrieveContext(emb, idx, top_k=2).retrieve("su che porta ascolta Langfuse?"):
    print(f"{s.score:.2f} {s.path} :: {s.chunk[:50]!r}")
for c in chunk_markdown(docs.docs["runbook.md"]):
    print("CHUNK", repr(c))
```

Output:

```
{'chunks': 4, 'documents': 2}
0.45 infra.md :: '# Porte\n\nLangfuse ascolta sulla porta 3011, Grafan'
0.00 runbook.md :: '# Runbook'
CHUNK '# Runbook'
CHUNK '## Il cloud non risponde\n\nOgni richiesta cloud viene ripetuta sul modello locale.'
CHUNK '## Budget esaurito\n\nLe richieste complesse restano in locale fino a mezzanotte UTC.'
```

Nota: ogni sezione è un chunk con il suo titolo; il chunk giusto ha lo score più alto. Con `HashEmbedder` contano solo le parole in comune ("Langfuse", "porta", "ascolta"); un embedding vero coglie anche i sinonimi.

## Come si misura un RAG

Due misure separate (`benchmarks/run_rag.py`):

| Misura | Domanda | Risultato |
|---|---|---|
| **hit@3** (recupero) | la fonte attesa è tra i primi 3 chunk? | 100% (6 domande) |
| **risposta** (percorso completo) | la risposta contiene il dato atteso e cita la fonte? | 83% |

Separarle dice **dove** sbaglia il sistema: se il recupero è al 100% e la risposta all'83%, il problema è il modello che legge il contesto, non la ricerca.

## Esercizi

1. ★ Calcola a mano la similarità coseno tra `a = (0.6, 0.8)` e `b = (1, 0)`. Sono normalizzati?
2. ★ Nell'esempio, chiedi "cosa succede quando finisce il budget?". Quale chunk vince?
3. ★★ Prova `chunk_markdown` su un documento con una sezione molto lunga (cinque paragrafi da 300 caratteri) e `target_size=800`. Quanti chunk escono? Il titolo c'è in tutti?
4. ★★ Perché il RAG si sceglie anche quando la domanda contiene un dato sensibile? Cosa cambierebbe se la rotta RAG usasse un modello cloud per scrivere la risposta?
5. ★★★ Con `HashEmbedder` la domanda "come si chiama la dashboard dei costi?" non trova un chunk che parla di "cockpit". Perché? Cosa fa diversamente un embedding addestrato?

## Da ricordare

- RAG = cercare i pezzi giusti, poi chiedere al modello di rispondere **solo** con quelli e di citarli.
- Il chunking conta: un titolo separato dal suo contenuto è una risposta persa.
- Misura recupero e risposta separatamente: sono due guasti diversi.

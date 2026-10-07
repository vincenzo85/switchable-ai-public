"""RAG locale per l'SDLC: indicizzazione e recupero del contesto.

I documenti, gli embedding e l'indice restano sulla macchina: è la rotta
"stiva" del talk (data residency totale).
"""
from __future__ import annotations

from core.domain.models import Source
from core.domain.text import chunk_markdown
from core.ports import DocumentSourcePort, EmbedderPort, VectorIndexPort


class BuildRagIndex:
    def __init__(self, docs: DocumentSourcePort, embedder: EmbedderPort, index: VectorIndexPort,
                 chunk_size: int = 800):
        self.docs, self.embedder, self.index, self.chunk_size = docs, embedder, index, chunk_size

    def execute(self) -> dict:
        items: list[tuple[str, str]] = []
        for path, text in self.docs.documents():
            items.extend((path, c) for c in chunk_markdown(text, self.chunk_size))
        vectors = [self.embedder.embed(c) for _, c in items]
        n = self.index.build(items, vectors)
        return {"chunks": n, "documents": len({p for p, _ in items})}


class RetrieveContext:
    def __init__(self, embedder: EmbedderPort, index: VectorIndexPort, top_k: int = 3,
                 min_score: float = 0.0):
        self.embedder, self.index, self.top_k, self.min_score = embedder, index, top_k, min_score

    def retrieve(self, question: str) -> list[Source]:
        hits = self.index.search(self.embedder.embed_query(question), self.top_k)
        return [h for h in hits if h.score >= self.min_score]

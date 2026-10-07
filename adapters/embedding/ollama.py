"""Embedder locale via Ollama (default nomic-embed-text, 768 dimensioni)."""
from __future__ import annotations

import math

from core.domain.errors import ProviderError
from core.ports import EmbedderPort
from adapters.llm.http import post_json


# prefissi di task con cui il modello è stato addestrato
TASK_PREFIXES = {"nomic-embed-text": ("search_document: ", "search_query: ")}


class OllamaEmbedder(EmbedderPort):
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434", dim: int = 768,
                 prefixes: tuple[str, str] | None = None):
        self.model, self.base_url, self.dim = model, base_url.rstrip("/"), dim
        self.doc_prefix, self.query_prefix = prefixes if prefixes is not None else TASK_PREFIXES.get(
            model.split(":")[0], ("", ""))

    def embed(self, text):
        return self._embed(self.doc_prefix + text)

    def embed_query(self, text):
        return self._embed(self.query_prefix + text)

    def _embed(self, text):
        data = post_json(f"{self.base_url}/api/embed", {"model": self.model, "input": text}, timeout_s=60)
        vecs = data.get("embeddings") or []
        if not vecs:
            raise ProviderError(f"ollama embed: nessun vettore per {self.model}")
        v = [float(x) for x in vecs[0]]
        n = math.sqrt(sum(x * x for x in v))
        return [x / n for x in v] if n else v

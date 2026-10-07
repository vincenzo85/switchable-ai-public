"""Indice vettoriale su disco: hnswlib (coseno) + chunks.json."""
from __future__ import annotations

import json
from pathlib import Path

import hnswlib
import numpy as np

from core.domain.errors import IndexNotReady
from core.domain.models import Source
from core.ports import VectorIndexPort


class HnswIndex(VectorIndexPort):
    def __init__(self, directory: str | Path, dim: int):
        self.dir, self.dim = Path(directory), dim

    def build(self, items, vectors):
        self.dir.mkdir(parents=True, exist_ok=True)
        idx = hnswlib.Index(space="cosine", dim=self.dim)
        idx.init_index(max_elements=max(len(items), 1), ef_construction=200, M=16)
        if items:
            idx.add_items(np.asarray(vectors, dtype=np.float32), np.arange(len(items)))
        idx.save_index(str(self.dir / "index.bin"))
        meta = [{"id": i, "path": p, "chunk": c} for i, (p, c) in enumerate(items)]
        (self.dir / "chunks.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        return len(items)

    def search(self, vector, top_k):
        bin_, meta_f = self.dir / "index.bin", self.dir / "chunks.json"
        if not bin_.exists() or not meta_f.exists():
            raise IndexNotReady(f"indice assente in {self.dir}: lancia `rag-build`")
        meta = json.loads(meta_f.read_text(encoding="utf-8"))
        if not meta:
            return []
        idx = hnswlib.Index(space="cosine", dim=self.dim)
        idx.load_index(str(bin_), max_elements=len(meta))
        k = min(top_k, len(meta))
        idx.set_ef(max(k * 2, 50))
        labels, dists = idx.knn_query(np.asarray([vector], dtype=np.float32), k=k)
        out = [Source(path=meta[int(l)]["path"], chunk=meta[int(l)]["chunk"], score=float(1 - d))
               for l, d in zip(labels[0], dists[0])]
        return sorted(out, key=lambda s: s.score, reverse=True)

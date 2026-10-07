"""Persistenza append-only in JSONL: registro costi, trace, dataset flywheel.

Tutto resta sul disco locale (data/, git-ignorata).
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from core.domain.models import CallRecord, Trace
from core.ports import CostLedgerPort, DatasetSinkPort, TraceStorePort

_lock = threading.Lock()


def _append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


class JsonlLedger(CostLedgerPort):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record(self, rec):
        _append(self.path, rec.to_dict())

    def records(self):
        return [CallRecord.from_dict(d) for d in _read(self.path)]


class JsonlTraceStore(TraceStorePort):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def trace(self, trace, record):
        _append(self.path, trace.to_dict())

    def traces(self):
        return [Trace.from_dict(d) for d in _read(self.path)]


class JsonlDatasetSink(DatasetSinkPort):
    def __init__(self, directory: str | Path):
        self.dir = Path(directory)

    def write(self, name, rows):
        self.dir.mkdir(parents=True, exist_ok=True)
        out = self.dir / f"{name}.jsonl"
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return str(out)

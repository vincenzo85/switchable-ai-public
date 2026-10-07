"""IngestDocument: il lavoro dell'equipaggio di cabina (n8n).

Nuovo documento → classifica SDLC → estrai metadati → aggiorna il RAG
locale → genera checklist QA → riporta costo e residency. Ogni passo è
una richiesta normale: è il router a decidere dove vola.
"""
from __future__ import annotations

import json

from core.domain.models import ROUTE_LOCAL_RAG
from core.ports import DocumentSourcePort
from core.use_cases.execute_request import ExecuteRequest
from core.use_cases.rag import BuildRagIndex
from core.use_cases.report import is_residency_violation

CATEGORIES = ("requisiti", "architettura", "runbook", "incident", "release-note", "altro")


class IngestDocument:
    def __init__(self, execute: ExecuteRequest, docs: DocumentSourcePort, build_index: BuildRagIndex,
                 excerpt_chars: int = 2000):
        self.ex, self.docs, self.build, self.excerpt = execute, docs, build_index, excerpt_chars

    def execute(self, name: str, text: str) -> dict:
        body = text[:self.excerpt]
        steps = []

        cls = self.ex.execute(
            f"Classifica questo documento SDLC in una categoria tra {list(CATEGORIES)}. "
            f"Rispondi SOLO con la categoria.\n\n{body}",
            validator=lambda t: t.strip().lower().strip(".") in CATEGORIES, max_tokens=8)
        steps.append(cls)
        category = cls.text.strip().lower().strip(".")
        category = category if category in CATEGORIES else "altro"

        meta = self.ex.execute(
            "Estrai titolo e 3 parole chiave in JSON con chiavi \"titolo\" e \"parole_chiave\". "
            f"Rispondi SOLO con il JSON.\n\n{body}", max_tokens=120)
        steps.append(meta)
        metadata = _parse_json(meta.text)

        qa = self.ex.execute(
            f"Genera una checklist QA di massimo 5 punti: cosa verificare per questo documento.\n\n{body}",
            max_tokens=200)
        steps.append(qa)

        path = self.docs.add(name, text)
        index = self.build.execute()
        records = [s.record for s in steps]
        return {
            "document": path,
            "category": category,
            "metadata": metadata,
            "checklist": [l.strip() for l in qa.text.splitlines() if l.strip()],
            "index": index,
            "routes": [s.decision.route for s in steps],
            "models": [r.model for r in records],
            "request_ids": [r.request_id for r in records],
            "cost_eur": sum(r.cost_eur for r in records),
            "cost_if_cloud_eur": sum(r.cost_if_cloud_eur for r in records),
            "data_residency_violations": sum(is_residency_violation(r) for r in records),
        }


def _parse_json(text: str) -> dict:
    s = text.strip()
    if "```" in s:
        s = s.split("```")[1].removeprefix("json").strip()
    start, end = s.find("{"), s.rfind("}")
    try:
        data = json.loads(s[start:end + 1]) if start >= 0 else None
    except json.JSONDecodeError:
        data = None
    return data if isinstance(data, dict) else {"raw": text.strip()}

#!/usr/bin/env python3
"""RAG SDLC: le domande di riferimento trovano la fonte giusta? La risposta la cita?

Due misure separate:
- RECUPERO: fonte attesa nei primi 3 chunk (hit@3), interrogando sempre l'indice;
- PERCORSO COMPLETO: rotta decisa dal router, citazione [n], valore atteso
  nella risposta. La prima domanda non contiene parole chiave di proposito:
  mostra il limite del router a regole (vedi benchmark advisor).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from _common import ROOT, pct, save

from app.composition import Container, Settings

GOLD = [
    ("Cosa succede quando il budget del cloud si esaurisce?", "docs/RUNBOOK.md|docs/ARCHITETTURA.md", "locale"),
    ("Nella documentazione, perché il router di base non usa un LLM per decidere?", "docs/adr/ADR-001-router-deterministico.md", "latenza"),
    ("Nella documentazione, su quale porta gira Langfuse?", "docs/ARCHITETTURA.md", "3011"),
    ("Nel runbook, come si ricostruisce l'indice RAG?", "docs/RUNBOOK.md", "rag-build"),
    ("Nella documentazione, in che modalità parte l'advisor di rotta?", "docs/adr/ADR-003-advisor-in-shadow.md", "shadow"),
    ("Nella documentazione, cosa fa il sistema se il cloud supera il budget di latenza?",
     "docs/ARCHITETTURA.md|docs/RUNBOOK.md", "locale"),
]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        c = Container(Settings(data_dir=Path(tmp), rag_index_dir=ROOT / "data/rag_index"))
        rows = []
        for q, src, expected in GOLD:
            paths = [x.path for x in c.retriever.retrieve(q)]
            res = c.execute.execute(q, max_tokens=200)
            rows.append({"question": q, "route": res.decision.route, "expected_source": src, "retrieved": paths,
                         "hit_at_3": any(p in paths for p in src.split("|")), "cites": "[" in res.text,
                         "expected_in_answer": expected.lower() in res.text.lower(),
                         "latency_ms": res.record.latency_ms, "answer": res.text.strip()[:300]})
            r = rows[-1]
            print(f"{r['route']:<9} {'✓' if r['hit_at_3'] else '✗'} hit  {'✓' if r['cites'] else '✗'} cita  "
                  f"{'✓' if r['expected_in_answer'] else '✗'} valore  {q[:60]}")
    n = len(rows)
    save("rag", {"questions": n, "hit_at_3": sum(r["hit_at_3"] for r in rows) / n,
                 "cites_rate": sum(r["cites"] for r in rows) / n,
                 "expected_in_answer_rate": sum(r["expected_in_answer"] for r in rows) / n,
                 "routed_to_rag": sum(r["route"] == "local_rag" for r in rows),
                 "latency_p50_ms": pct([r["latency_ms"] for r in rows], 50), "rows": rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Data Flywheel: ogni volo migliora il prossimo.

Le trace (prompt + risposta, rimaste in casa) diventano un dataset di
fine-tuning in formato chat (`messages`), anonimizzato. Le risposte date
dal cloud sono "candidate alla distillazione": insegnano al modello
locale a fare da solo ciò per cui oggi paghiamo (Tsymboi et al. 2026).
"""
from __future__ import annotations

import hashlib

from core.domain.text import scrub_pii
from core.ports import DatasetSinkPort, TraceStorePort


class ExportFlywheel:
    def __init__(self, traces: TraceStorePort, sink: DatasetSinkPort):
        self.traces, self.sink = traces, sink

    def execute(self) -> dict:
        rows, seen = [], set()
        redactions = dupes = skipped = distill = 0
        all_traces = self.traces.traces()
        for t in all_traces:
            if not t.output.strip():
                skipped += 1
                continue
            prompt, n1 = scrub_pii(t.prompt)
            output, n2 = scrub_pii(t.output)
            key = hashlib.sha256(prompt.encode()).hexdigest()
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            redactions += n1 + n2
            teacher = t.model.startswith("cloud/")
            distill += teacher
            rows.append({
                "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": output}],
                "meta": {"request_id": t.request_id, "route": t.route, "model": t.model, "kind": t.kind,
                         "fallback": t.fallback, "teacher": teacher, "feedback": t.feedback},
            })
        where = self.sink.write("sft", rows)
        return {"traces": len(all_traces), "exported": len(rows), "duplicates_skipped": dupes,
                "empty_skipped": skipped, "pii_redactions": redactions,
                "distillation_candidates": distill, "path": where}

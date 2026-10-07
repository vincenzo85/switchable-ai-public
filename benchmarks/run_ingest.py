#!/usr/bin/env python3
"""Il flusso n8n reale: POST al webhook del workflow importato in n8n, che
chiama l'API switchable_ai. Richiede `./run.sh up` e `./run.sh serve`."""
from __future__ import annotations

import json
import time
import urllib.request

from _common import ROOT, save

WEBHOOK = "http://127.0.0.1:5678/webhook/sdlc-document"
DOCS = {
    "adr-007-gateway.md": (ROOT / "data/adr-007-gateway.md").read_text(encoding="utf-8")
    if (ROOT / "data/adr-007-gateway.md").exists() else "# ADR-007\nRollback del gateway con deploy canary.",
    "incident-2026-09-30.md": "# Incident 2026-09-30\n\nAlle 10:42 il provider cloud ha risposto con errori 529 per "
                              "18 minuti. Il router ha eseguito 212 fallback sul modello locale; nessuna richiesta "
                              "persa. Azione: abbassare SAI_CLOUD_TIMEOUT_S a 20 secondi.",
    "nota-hr-riservata.md": "# Nota riservata HR\n\nDocumento riservato: elenco dei colloqui di fine anno con le "
                            "valutazioni individuali del team vendite.",
}


def main() -> int:
    rows = []
    for name, text in DOCS.items():
        body = json.dumps({"name": name, "text": text}).encode()
        t0 = time.monotonic()
        with urllib.request.urlopen(urllib.request.Request(WEBHOOK, data=body, headers={"Content-Type": "application/json"}),
                                    timeout=600) as r:
            d = json.loads(r.read())
        d["wall_ms"] = int((time.monotonic() - t0) * 1000)
        d["name"] = name
        rows.append(d)
        print(name, d["status"], d["category"], d["routes"], d["models"], f"€{d['cost_eur']:.5f}", d["wall_ms"], "ms")
    save("n8n_ingest", {"webhook": WEBHOOK, "workflow": "infra/n8n/workflows/sdlc-document-intake.json", "rows": rows,
                        "residency_violations": sum(r["data_residency_violations"] for r in rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

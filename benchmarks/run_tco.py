#!/usr/bin/env python3
"""TCO reale: i 4 task della demo × N run contro i motori VERI.

Senza chiave cloud la rotta cloud fa fallback locale MISURATO (è la tesi).
Il costo "se tutto-cloud" usa i token contati dal motore al listino gpt-4o.
Misura anche il throughput locale (eval_count / eval_duration di Ollama),
che serve al calcolo del costo ammortizzato.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import urllib.request
from pathlib import Path

from _common import ROOT, pct, save

from app.composition import Container, Settings
from app.main import DEMO_TASKS
from core.domain.pricing import PRICING, LocalTcoInputs, local_cost_per_mtok


def ollama_throughput(url: str, model: str, runs: int = 3) -> dict:
    tps = []
    for _ in range(runs):
        body = json.dumps({"model": model, "prompt": "Spiega in 150 parole cos'è un gateway per LLM.",
                           "stream": False, "options": {"num_predict": 200, "temperature": 0.2}}).encode()
        with urllib.request.urlopen(urllib.request.Request(f"{url}/api/generate", data=body,
                                                           headers={"Content-Type": "application/json"}), timeout=300) as r:
            d = json.loads(r.read())
        tps.append(d["eval_count"] / (d["eval_duration"] / 1e9))
    return {"model": model, "tokens_per_sec_p50": pct(tps, 50), "runs": tps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=300)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        # registro costi pulito (tmp), indice RAG reale del repo
        s = Settings(data_dir=Path(tmp), rag_index_dir=ROOT / "data/rag_index")
        c = Container(s)
        rows = []
        for title, prompt in DEMO_TASKS.items():
            for i in range(a.runs):
                res = c.execute.execute(prompt, max_tokens=a.max_tokens)
                r = res.record
                rows.append({"task": title, "run": i + 1, "route": res.decision.route, "model": r.model,
                             "fallback": r.fallback, "fallback_reason": r.fallback_reason[:120],
                             "tokens_in": r.tokens_in, "tokens_out": r.tokens_out, "latency_ms": r.latency_ms,
                             "cost_eur": r.cost_eur, "cost_if_cloud_eur": r.cost_if_cloud_eur,
                             "sources": [x.path for x in res.sources]})
                print(f"{title} run{i+1}: {r.route}→{r.model} {r.latency_ms}ms {r.tokens_in}/{r.tokens_out}"
                      f"{' FALLBACK' if r.fallback else ''}")
        report = c.report.execute()
    thr = ollama_throughput(s.ollama_url, s.local_model.split("/", 1)[1])
    assumption = {"hw_eur": 2000, "amort_months": 36, "watts": 140, "eur_kwh": 0.30}
    amort = {f"utilization_{round(u * 100)}pct": local_cost_per_mtok(LocalTcoInputs(**assumption,
                                                                    tokens_per_sec=thr["tokens_per_sec_p50"],
                                                                    utilization=u))
             for u in (0.05, 0.25, 0.8)}
    by_task = {}
    for t in DEMO_TASKS:
        rr = [x for x in rows if x["task"] == t]
        by_task[t] = {"route": rr[0]["route"], "model": rr[0]["model"], "fallback": rr[0]["fallback"],
                      "latency_p50_ms": pct([x["latency_ms"] for x in rr], 50),
                      "tokens_in": rr[0]["tokens_in"], "tokens_out_p50": pct([x["tokens_out"] for x in rr], 50),
                      "cost_eur": sum(x["cost_eur"] for x in rr), "cost_if_cloud_eur": sum(x["cost_if_cloud_eur"] for x in rr)}
    save("tco", {
        "runs_per_task": a.runs, "cloud_key_present": bool(s.openai_key),
        "pricing_eur_per_1k": PRICING,
        "totals": {"cost_eur": report["cost_eur"], "cost_if_cloud_eur": report["cost_if_cloud_eur"],
                   "saving_pct": report["saving_pct"], "fallbacks": report["fallbacks"],
                   "residency_violations": report["residency_violations"],
                   "latency_p50_ms": report["latency_ms"]["p50"], "latency_p95_ms": report["latency_ms"]["p95"]},
        "by_task": by_task, "rows": rows,
        "local_throughput": thr,
        "local_amortized_eur_per_mtok": {"assumption": assumption,
                                         "note": "IPOTESI dichiarata: quota hardware/potenza/energia non misurate; "
                                                 "throughput misurato", **amort},
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

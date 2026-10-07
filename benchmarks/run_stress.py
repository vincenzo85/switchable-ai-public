#!/usr/bin/env python3
"""Stress test di atterraggio, REALE sul locale, con cloud SIMULATO dichiarato.

100 task misti (40% ticket, 15% estrazioni, 20% architettura, 15% domande
alla knowledge base, 10% dati sensibili). Durante il batch:
- il budget cloud giornaliero si esaurisce (budget guard → local-first);
- una finestra di turbolenza programmata rallenta il cloud oltre il timeout
  (fallback reali sul modello locale);
- i dati sensibili non devono MAI finire sulla rotta cloud.
Alla fine esporta il Data Flywheel dalle trace del batch.

Cloud simulato (adapters/llm/simulated_cloud.py): risponde qwen2.5:7b
locale, prezzo di listino gpt-4o, turbolenza iniettata. Etichettato così
in ogni numero che ne deriva.
"""
from __future__ import annotations

import argparse
import shutil

from _common import ROOT, save

from adapters.llm.providers import OllamaLLM, PrefixRouterLLM
from adapters.llm.simulated_cloud import SimulatedCloudLLM
from app.composition import Container, Settings
from core.use_cases.execute_request import Budget
from core.use_cases.stress import landing_scenario


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--budget", type=float, default=0.02)
    ap.add_argument("--guard", type=float, default=0.004)
    ap.add_argument("--cloud-timeout", type=float, default=4.0)
    ap.add_argument("--max-tokens", type=int, default=120)
    a = ap.parse_args()

    run_dir = ROOT / "data/stress_run"
    shutil.rmtree(run_dir, ignore_errors=True)
    s = Settings(data_dir=run_dir, rag_index_dir=ROOT / "data/rag_index", cloud_timeout_s=a.cloud_timeout)
    ollama = OllamaLLM(s.ollama_url)
    sim = SimulatedCloudLLM(ollama, s.local_model)
    c = Container(s, llm=PrefixRouterLLM({"ollama/": ollama, "cloud/": sim}))
    c.execute.budget = Budget(a.budget, a.guard)
    c.stress.max_tokens = a.max_tokens

    def show(ev):
        if ev["status"] != "ok":
            print(f"  ✗ #{ev['i']:03d} {ev['error'][:80]}")
            return
        tag = " FALLBACK" if ev["fallback"] else (" ESCALATION" if ev["escalated"] else "")
        guard = " [budget_guard]" if "budget_guard" in ev["rules"] else ""
        print(f"  #{ev['i']:03d} {ev['family']:<12} {ev['route']:<9} {ev['model']:<18} {ev['latency_ms']:>6}ms"
              f" €{ev['cum_cost_eur']:.4f}{tag}{guard}")

    report = c.stress.execute(landing_scenario(a.n, seed=a.seed), on_event=show)
    fly = c.flywheel.execute()
    summary = {k: v for k, v in report.items() if k != "timeline"}
    save("stress", {
        "scenario": {"n": a.n, "seed": a.seed, "budget_eur": a.budget, "guard_eur": a.guard,
                     "cloud_timeout_s": a.cloud_timeout, "max_tokens": a.max_tokens},
        "cloud_simulation": "SIMULATO: risponde qwen2.5:7b locale, prezzo di listino gpt-4o, rallentamenti programmati "
                            f"sulle chiamate cloud {sim.slow_from}-{sim.slow_to - 1} (timeout simulati: {sim.timeouts})",
        "summary": summary, "flywheel": fly, "timeline": report["timeline"],
        "cost_report": c.report.execute(),
    })
    print({k: summary[k] for k in ("completed", "routes_decided", "executed_on", "fallback_events",
                                   "budget_guard_hits", "data_residency_violations", "cost_real_eur",
                                   "cost_if_all_cloud_eur", "saving_pct", "duration_s")})
    print("flywheel:", fly)
    return 0 if report["data_residency_violations"] == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())

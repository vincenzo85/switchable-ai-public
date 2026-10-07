#!/usr/bin/env python3
"""Messa a punto del secondo controllore, senza barare sul test.

1. Griglia sul set DEV (routing_dev.py) con Rizzo Flow:
   modalità {active, fallback} × doppio ordine {no, sì} × descrizioni {base, v2}.
2. Si sceglie la configurazione migliore SOLO sul dev (accuratezza, poi latenza).
3. Quella configurazione si valuta UNA volta sul TEST (routing_heldout.py),
   con Rizzo Flow e con Open-Jev. Le regole da sole sono il riferimento.
Le regole dure (residency, budget) restano sempre deterministiche.
"""
from __future__ import annotations

import os
import signal
import subprocess
from collections import Counter

from _common import ROOT, pct, save
from run_advisor import SERVERS, server_up, wait_up
from run_vllm import unload_ollama

from adapters.llm.systemone import ENGINES, SystemOneAdvisor
from core.domain.policy import ROUTE_DESCRIPTIONS, ROUTE_DESCRIPTIONS_V1, decide_route
from core.use_cases.advisor import AdvisedRouter
from routing_dev import DEV
from routing_heldout import HELDOUT

DESC_V2 = ROUTE_DESCRIPTIONS          # promossa a default in core/domain/policy.py dopo questa misura
DESCS = {"base": ROUTE_DESCRIPTIONS_V1, "v2": DESC_V2}
GRID = [(m, b, d) for m in ("active", "fallback") for b in (False, True) for d in ("base", "v2")]


def evaluate(items, router=None) -> dict:
    rows = []
    for gold, prompt in items:
        base = decide_route(prompt)
        if router is None:
            rows.append((gold, base.route, 0, False))
            continue
        d, adv = router.decide(prompt, base)
        rows.append((gold, d.route, adv.latency_ms if adv else 0, bool(adv)))
    by = {}
    for fam in ("local", "cloud", "local_rag"):
        fr = [r for r in rows if r[0] == fam]
        by[fam] = {"n": len(fr), "accuracy": sum(r[1] == fam for r in fr) / max(1, len(fr)),
                   "chosen": dict(Counter(r[1] for r in fr))}
    lat_all = [r[2] for r in rows]
    asked = [r for r in rows if r[3]]
    return {"accuracy": sum(r[0] == r[1] for r in rows) / len(rows), "per_family": by,
            "advisor_calls": len(asked), "requests": len(rows),
            "latency_mean_ms": sum(lat_all) / len(lat_all),                 # costo medio per richiesta (0 se non chiamato)
            "latency_p50_when_called_ms": pct([r[2] for r in asked], 50) if asked else 0,
            "cloud_when_not_gold": sum(r[1] == "cloud" and r[0] != "cloud" for r in rows)}


def router(adv, cfg):
    mode, both, desc = cfg
    return AdvisedRouter(adv, mode=mode, min_confidence=0.0, both_orders=both, descriptions=DESCS[desc])


def with_server(name, fn):
    endpoint, _ = ENGINES[name]
    proc = None
    if not server_up(endpoint):
        unload_ollama(os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        cmd, cwd = SERVERS[name]
        with open(ROOT / f"benchmarks/results/{name}_server.log", "w") as lf:
            proc = subprocess.Popen(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
        wait_up(endpoint, proc)
    try:
        adv = SystemOneAdvisor.engine(name, timeout_s=30)
        adv.choose("warm-up", "Which route?", [("local", "a"), ("cloud", "b")])
        return fn(adv)
    finally:
        if proc and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=60)


def label(cfg):
    return f"{cfg[0]}|{'2ordini' if cfg[1] else '1ordine'}|desc_{cfg[2]}"


def main() -> int:
    results = {"rules": {"dev": evaluate(DEV), "test": evaluate(HELDOUT)}}
    print(f"regole           dev={results['rules']['dev']['accuracy']:.0%}  test={results['rules']['test']['accuracy']:.0%}")

    def grid(adv):
        out = {}
        for cfg in GRID:
            r = evaluate(DEV, router(adv, cfg))
            out[label(cfg)] = r
            print(f"dev  {label(cfg):<28} acc={r['accuracy']:.0%}  latenza media={r['latency_mean_ms']:.0f} ms  "
                  f"chiamate={r['advisor_calls']}/{r['requests']}")
        return out
    dev_grid = with_server("rizzo", grid)
    best = max(GRID, key=lambda c: (dev_grid[label(c)]["accuracy"], -dev_grid[label(c)]["latency_mean_ms"]))
    print(f"scelta sul dev: {label(best)}")

    final = {}
    for name in ("rizzo", "openjev"):
        final[name] = with_server(name, lambda adv: {"dev": evaluate(DEV, router(adv, best)),
                                                     "test": evaluate(HELDOUT, router(adv, best))})
        print(f"test {name:<8} {label(best)}  acc={final[name]['test']['accuracy']:.0%}  "
              f"latenza media={final[name]['test']['latency_mean_ms']:.0f} ms")
    save("router_tuning", {"dev_size": len(DEV), "test_size": len(HELDOUT), "grid_engine": "rizzo",
                           "grid": dev_grid, "chosen": {"mode": best[0], "both_orders": best[1], "descriptions": best[2],
                                                        "label": label(best)},
                           "descriptions_v2": DESC_V2, "rules": results["rules"], "final": final,
                           "protocol": "configurazione scelta solo sul dev; test valutato una volta, a configurazione fissata"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

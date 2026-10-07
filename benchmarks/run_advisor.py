#!/usr/bin/env python3
"""Router a regole vs router appreso (Rizzo Flow, Open-Jev) sulle stesse richieste.

Rotta "giusta" per famiglia del batch di atterraggio (core/use_cases/stress.py):
  ticket, extraction → local · architecture → cloud · kb_question → local_rag
  sensitive          → local (il cloud non viene nemmeno offerto all'advisor)
Si misura accuratezza di rotta e latenza aggiunta dal router. I server
/v1/systemone vengono avviati uno alla volta (non stanno insieme in 8 GB) e
spenti a fine misura. Ollama viene scaricato dalla VRAM prima.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time
import urllib.request
from collections import Counter
from pathlib import Path

from _common import ROOT, pct, save
from run_vllm import unload_ollama

from adapters.llm.systemone import ENGINES, SystemOneAdvisor
from core.domain.errors import ProviderError
from core.domain.policy import ROUTE_DESCRIPTIONS_V1, decide_route
from core.use_cases.advisor import AdvisedRouter
from core.use_cases.stress import landing_scenario
from routing_heldout import HELDOUT

# checkout locale di Rizzo Flow / Open-Jev (non incluso in questo repository)
JEV = Path(os.environ.get("OPENJEV_BENCH_DIR", "../openjev-decision-bench"))
SERVERS = {
    "rizzo": (["uv", "run", "rizzo", "serve", "--device", "cuda", "--host", "127.0.0.1", "--port", "8017"],
              JEV / ".runtime/rizzo-flow"),
    "openjev": ([str(JEV / ".venv/bin/python"), "-m", "jev.server", "--checkpoint",
                 "../models/Open-Jev-2B/package/checkpoint", "--device", "cuda:0", "--max-length", "4096",
                 "--batch-size", "1", "--no-prefix-cache", "--host", "127.0.0.1", "--port", "8791"],
                JEV / ".runtime/Open-Jev"),
}
GOLD = {"ticket": "local", "extraction": "local", "architecture": "cloud", "kb_question": "local_rag",
        "sensitive": "local"}


def wait_up(endpoint: str, proc, timeout_s=300):
    health = endpoint.rsplit("/v1/", 1)[0] + "/health"
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"server uscito con codice {proc.returncode}")
        try:
            urllib.request.urlopen(health, timeout=2).read()
            return
        except Exception:  # noqa: BLE001
            time.sleep(2)
    raise TimeoutError("server non partito")


def evaluate(tasks, advisor=None, gold=None):
    gold = gold or GOLD
    rows = []
    # descrizioni V1: questo benchmark documenta la PRIMA misura (vedi run_router_tuning.py per la v2)
    router = AdvisedRouter(advisor, mode="active", min_confidence=0.0, descriptions=ROUTE_DESCRIPTIONS_V1) if advisor else None
    for t in tasks:
        base = decide_route(t["prompt"])
        if router:
            d, adv = router.decide(t["prompt"], base)
            rows.append({"family": t["family"], "route": d.route, "latency_ms": adv.latency_ms if adv else 0,
                         "p": adv.p if adv else 0.0, "error": adv.error if adv else "",
                         "applied": bool(adv and adv.applied)})
        else:
            rows.append({"family": t["family"], "route": base.route, "latency_ms": 0, "p": 1.0, "error": ""})
    ok = [r["route"] == gold[r["family"]] for r in rows]
    per_family = {}
    for fam in gold:
        fr = [r for r in rows if r["family"] == fam]
        per_family[fam] = {"n": len(fr), "accuracy": sum(r["route"] == gold[fam] for r in fr) / max(1, len(fr)),
                           "chosen": dict(Counter(r["route"] for r in fr))}
    lat = [r["latency_ms"] for r in rows if r["latency_ms"]]
    return {"accuracy": sum(ok) / len(ok), "per_family": per_family,
            "latency_p50_ms": pct(lat, 50), "latency_p95_ms": pct(lat, 95),
            "mean_confidence": sum(r["p"] for r in rows) / len(rows),
            "errors": sum(bool(r["error"]) for r in rows),
            "error_samples": sorted({r["error"] for r in rows if r["error"]})[:5]}


HELD_GOLD = {g: g for g in ("local", "cloud", "local_rag")}
HELD_TASKS = [{"family": g, "prompt": p} for g, p in HELDOUT]


def both(advisor=None) -> dict:
    return {"scenario": evaluate(SCENARIO, advisor), "heldout": evaluate(HELD_TASKS, advisor, HELD_GOLD)}


def server_up(endpoint: str) -> bool:
    try:
        urllib.request.urlopen(endpoint.rsplit("/v1/", 1)[0] + "/health", timeout=2).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def show(name: str, r: dict) -> None:
    sc, ho = r["scenario"], r["heldout"]
    print(f"{name:<8} scenario={sc['accuracy']:.0%} controllo={ho['accuracy']:.0%} "
          f"p50={ho['latency_p50_ms']:.0f}ms p95={ho['latency_p95_ms']:.0f}ms errori={sc['errors'] + ho['errors']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--engines", default="rizzo,openjev")
    a = ap.parse_args()
    global SCENARIO
    SCENARIO = landing_scenario(a.n, seed=42)
    results = {"deterministic": both()}
    show("regole", results["deterministic"])
    ollama = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    for name in a.engines.split(","):
        endpoint, _ = ENGINES[name]
        proc = None
        if not server_up(endpoint):
            unload_ollama(ollama)
            cmd, cwd = SERVERS[name]
            log = ROOT / f"benchmarks/results/{name}_server.log"
            with open(log, "w") as lf:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            if proc:
                wait_up(endpoint, proc)
            adv = SystemOneAdvisor.engine(name, timeout_s=30)
            adv.choose("warm-up", "Which route?", [("local", "a"), ("cloud", "b")])
            results[name] = both(adv)
            show(name, results[name])
        except (ProviderError, RuntimeError, TimeoutError) as e:
            results[name] = {"error": str(e)}
            print(name, "non misurato:", e)
        finally:
            if proc and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
    save("advisor", {"tasks": a.n, "heldout_tasks": len(HELDOUT), "gold": GOLD, "results": results,
                     "note": "Advisor in modalità active con min_confidence=0: misura la scelta grezza del modello. "
                             "Zero-shot: nessuna calibrazione sul dominio (rizzo calibrate non usato)."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

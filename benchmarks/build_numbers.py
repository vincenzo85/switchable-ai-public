#!/usr/bin/env python3
"""Aggrega benchmarks/results/*.json in talk/numbers.json: l'UNICA fonte dei
numeri del deck. Ogni voce porta valore, testo da mostrare, etichetta,
sorgente (file#percorso) e data di misura. Un numero che non passa da qui
non può comparire nelle slide (test in tests/test_talk_numbers.py).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
RES = ROOT / "benchmarks/results"
OUT = ROOT / "talk/numbers.json"


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def get(d: dict, path: str):
    for k in path.split("."):
        d = d[k] if not isinstance(d, list) else d[int(k)]
    return d


def eur(v):   return f"€{v:.4f}" if v < 1 else f"€{v:,.2f}"
def pctf(v):  return f"{v:.0f}%"
def ms(v):    return f"{v / 1000:.1f} s" if v >= 1000 else f"{v:.0f} ms"
def num(v):   return f"{v:,.0f}".replace(",", ".")
def ratio(v): return f"{v * 100:.0f}%"
def tps(v):   return f"{v:,.0f} tok/s".replace(",", ".")
def x(v):     return f"{v:.1f}×"


def main() -> int:
    n: dict[str, dict] = {}

    def put(key, bench, path, fmt, label, value=None):
        d = load(bench)
        v = get(d, path) if value is None else value
        n[key] = {"value": v, "display": fmt(v), "label": label,
                  "source": f"benchmarks/results/{bench}.json#{path}", "measured_at": d["meta"]["measured_at"]}

    # --- TCO demo (4 task × 3 run, motori veri, nessuna chiave cloud)
    put("tco.cost_real", "tco", "totals.cost_eur", eur, "costo reale demo (12 richieste)")
    put("tco.cost_if_cloud", "tco", "totals.cost_if_cloud_eur", eur, "stesso lavoro se tutto in cloud")
    put("tco.saving_energy_only", "tco", "totals.saving_pct", pctf,
        "risparmio se il locale costa solo energia (= rapporto di prezzo)")
    put("tco.fallbacks", "tco", "totals.fallbacks", num, "fallback reali (cloud senza chiave)")
    put("tco.local_tps", "tco", "local_throughput.tokens_per_sec_p50", tps, "throughput qwen2.5:7b su RTX 4070 Laptop")
    for u, label in (("5pct", "5%"), ("25pct", "25%"), ("80pct", "80%")):
        put(f"tco.amortized_eur_mtok_u{label[:-1]}", "tco", f"local_amortized_eur_per_mtok.utilization_{u}.total",
            lambda v: f"€{v:.2f}/Mtok", f"costo locale ammortizzato a utilizzo {label} (ipotesi hw dichiarata)")
    d = load("tco")
    a = d["local_amortized_eur_per_mtok"]["assumption"]
    n["tco.assumption"] = {"value": a, "label": "IPOTESI hardware/energia (non misurata)",
                           "display": f"{a['hw_eur']} € di hardware, {a['amort_months']} mesi, {a['watts']} W, "
                                      f"{a['eur_kwh']:.2f}".replace(".", ",") + " €/kWh",
                           "source": "benchmarks/results/tco.json#local_amortized_eur_per_mtok.assumption",
                           "measured_at": d["meta"]["measured_at"]}
    n["tco.cloud_price_eur_mtok"] = {"value": d["pricing_eur_per_1k"]["cloud/gpt-4o"] * 1000,
                                     "display": f"€{d['pricing_eur_per_1k']['cloud/gpt-4o'] * 1000:.2f}/Mtok",
                                     "label": "listino cloud di riferimento (gpt-4o, blended)",
                                     "source": "benchmarks/results/tco.json#pricing_eur_per_1k", "measured_at": d["meta"]["measured_at"]}
    for t, row in d["by_task"].items():
        key = t.split(" — ")[0].replace("Task ", "task_").lower()
        n[f"tco.{key}.latency"] = {"value": row["latency_p50_ms"], "display": ms(row["latency_p50_ms"]),
                                   "label": f"{t}: latenza p50 ({row['route']}→{row['model']})",
                                   "source": f"benchmarks/results/tco.json#by_task.{t}", "measured_at": d["meta"]["measured_at"]}

    # punto di pareggio: utilizzo GPU a cui il locale ammortizzato costa quanto il listino cloud
    # total(u) = energy + hw_80 * 0.8 / u   →   u* = hw_80 * 0.8 / (cloud - energy)
    a80 = d["local_amortized_eur_per_mtok"]["utilization_80pct"]
    cloud_mtok = d["pricing_eur_per_1k"]["cloud/gpt-4o"] * 1000
    be = a80["hardware"] * 0.8 / (cloud_mtok - a80["energy"])
    n["tco.breakeven_utilization"] = {"value": be, "display": f"{be * 100:.0f}%",
                                      "label": "utilizzo GPU a cui il locale costa quanto il cloud (con l'ipotesi hw)",
                                      "source": "benchmarks/results/tco.json#local_amortized_eur_per_mtok (calcolato)",
                                      "measured_at": d["meta"]["measured_at"]}

    # --- legacy (luglio 2026)
    n["legacy.cost"] = {"value": 0.00121, "display": "€0.00121 vs €0.02774", "label": "router_llm (legacy), 3×3 task",
                        "source": "benchmarks/results/legacy_tco_report_2026-07-03.md", "measured_at": "2026-07-03"}

    # --- compressione
    for v in ("estrattiva_50", "estrattiva_30", "agnostica_50", "agnostica_30"):
        put(f"compression.{v}.saving", "compression", f"summary.{v}.token_saving_pct", pctf, f"token risparmiati ({v})")
        put(f"compression.{v}.accuracy", "compression", f"summary.{v}.accuracy", ratio, f"risposte corrette ({v})")
    put("compression.originale.accuracy", "compression", "summary.originale.accuracy", ratio, "risposte corrette senza compressione")

    # --- vLLM vs Ollama
    vr = load("vllm_vs_ollama")["results"]
    for eng in ("ollama", "vllm"):
        for i, c in enumerate(vr[eng]["concurrency"]):
            put(f"vllm.{eng}.c{c['concurrency']}.tps", "vllm_vs_ollama", f"results.{eng}.concurrency.{i}.throughput_tok_s",
                tps, f"{eng} throughput a concorrenza {c['concurrency']}")
            put(f"vllm.{eng}.c{c['concurrency']}.ttft", "vllm_vs_ollama", f"results.{eng}.concurrency.{i}.ttft_p50_ms",
                ms, f"{eng} TTFT p50 a concorrenza {c['concurrency']}")
    top = max(c["concurrency"] for c in vr["vllm"]["concurrency"])
    put("vllm.max_concurrency", "vllm_vs_ollama", "levels", lambda v: str(max(v)), "concorrenza massima del test")
    n["vllm.max_concurrency"]["value"] = top
    sp = n[f"vllm.vllm.c{top}.tps"]["value"] / n[f"vllm.ollama.c{top}.tps"]["value"]
    n["vllm.speedup_batch"] = {"value": sp, "display": x(sp), "label": f"vLLM/Ollama throughput a concorrenza {top}",
                               "source": "benchmarks/results/vllm_vs_ollama.json#results", "measured_at": load("vllm_vs_ollama")["meta"]["measured_at"]}

    # --- router: regole vs advisor
    for eng in ("deterministic", "rizzo", "openjev"):
        put(f"router.{eng}.scenario", "advisor", f"results.{eng}.scenario.accuracy", ratio, f"{eng}: accuratezza sul batch di atterraggio")
        put(f"router.{eng}.heldout", "advisor", f"results.{eng}.heldout.accuracy", ratio, f"{eng}: accuratezza sul set di controllo")
        put(f"router.{eng}.latency", "advisor", f"results.{eng}.heldout.latency_p50_ms", ms, f"{eng}: latenza aggiunta p50")
    put("router.heldout_n", "advisor", "heldout_tasks", num, "richieste nel set di controllo")
    put("router.deterministic.heldout_rag", "advisor", "results.deterministic.heldout.per_family.local_rag.accuracy", ratio,
        "regole: domande sui documenti interni riconosciute (senza parole chiave)")
    put("router.deterministic.heldout_cloud", "advisor", "results.deterministic.heldout.per_family.cloud.accuracy", ratio,
        "regole: task complessi brevi riconosciuti")

    # --- qualità
    put("quality.mutation_killed", "mutation", "killed", num, "mutazioni uccise dai test")
    put("quality.mutation_total", "mutation", "total", num, "mutazioni applicate")

    # --- MCP
    put("mcp.tools", "mcp", "tools", lambda v: str(len(v)), "tool MCP esposti")
    n["mcp.tools"]["value"] = len(load("mcp")["tools"])
    put("mcp.definition_tokens", "mcp", "definitions_tokens_approx", lambda v: f"~{v} token",
        "peso delle definizioni dei tool in ogni richiesta")

    # --- messa a punto del router (dev → test)
    put("router.dev_n", "router_tuning", "dev_size", num, "richieste nel set dev")
    put("router.tuned.rizzo.test", "router_tuning", "final.rizzo.test.accuracy", ratio,
        "Rizzo Flow con descrizioni v2 (scelte sul dev): rotta giusta sul test")
    put("router.tuned.rizzo.dev", "router_tuning", "final.rizzo.dev.accuracy", ratio, "Rizzo Flow v2 sul dev")
    put("router.tuned.rizzo.latency", "router_tuning", "final.rizzo.test.latency_mean_ms", ms, "Rizzo Flow v2: latenza media aggiunta")
    put("router.tuned.rizzo.cloud", "router_tuning", "final.rizzo.test.per_family.cloud.accuracy", ratio,
        "Rizzo Flow v2: task complessi riconosciuti")
    put("router.tuned.rizzo.rag", "router_tuning", "final.rizzo.test.per_family.local_rag.accuracy", ratio,
        "Rizzo Flow v2: domande sui documenti interni riconosciute")
    put("router.tuned.rizzo.cloud_errors", "router_tuning", "final.rizzo.test.cloud_when_not_gold", num,
        "Rizzo Flow v2: richieste mandate in cloud senza motivo")
    put("router.tuned.openjev.test", "router_tuning", "final.openjev.test.accuracy", ratio, "Open-Jev con descrizioni v2 sul test")
    put("router.tuned.openjev.cloud_errors", "router_tuning", "final.openjev.test.cloud_when_not_gold", num,
        "Open-Jev v2: richieste mandate in cloud senza motivo")
    put("router.tuned.both_orders_dev", "router_tuning", "grid.active|2ordini|desc_v2.accuracy", ratio,
        "doppio ordine dei candidati (dev): nessun guadagno")
    put("router.rules.dev", "router_tuning", "rules.dev.accuracy", ratio, "regole sul set dev")

    # --- letteratura: SOLO numeri presenti nell'abstract dei paper VERIFICATI (docs/BIBLIOGRAFIA.md)
    bib = {r["arxiv_id"]: r for r in load("bibliography")["papers"]}
    LIT = [  # chiave, arXiv, numero nell'abstract, display, etichetta
        ("lit.frugalgpt", "2305.05176", "98%", "−98%", "FrugalGPT: costo in meno a parità di qualità (cascata di modelli)"),
        ("lit.routellm", "2406.18665", "2 volte", "costi ÷2", "RouteLLM: costi ridotti di oltre 2 volte senza perdere qualità"),
        ("lit.hybrid", "2404.14618", "40%", "−40%", "Hybrid LLM: chiamate al modello grande in meno"),
        ("lit.patil", "2606.11690", "24x", "fino a 24×", "Patil: penalità di costo per sottoutilizzo della GPU"),
        ("lit.inference_econ", "2607.13080", "88,6%", "−88,6%", "Inference Economics: costo API effettivo ridotto dal prompt caching"),
        ("lit.llmlingua", "2310.05736", "20x", "fino a 20×", "LLMLingua: compressione del prompt con poca perdita"),
        ("lit.capc", "2607.15516", "90%", "−90%", "CAPC: costo rispetto al prompt non compresso"),
        ("lit.mcp_cli", "2608.08654", "28x", "da 5× a 28×", "MCP vs CLI: quanto costano di più le definizioni esaustive dei tool"),
        ("lit.agent_tokens", "2604.22750", "1000 volte", "fino a 1000×", "token dei task agentici rispetto a una chat sul codice"),
        ("lit.flywheel", "2609.01572", "50%", "50%", "traffico aziendale assorbito dal modello self-hosted addestrato sul proprio traffico"),
        ("lit.continuity", "2607.15899", "99,20%", "99,2%", "ContinuityBench: continuità della conversazione con failover stateful"),
        ("lit.inference_econ_cloud", "2607.13080", "0,57", "$0.57/Mtok", "Inference Economics: costo API effettivo con prompt caching"),
        ("lit.inference_econ_local", "2607.13080", "2,83", "$2.83/Mtok", "Inference Economics: costo ammortizzato della quota GPU locale condivisa"),
        ("lit.fcr_local", "2607.13080", "74.9%", "74.9%", "Inference Economics: commit di riparazione col modello locale"),
        ("lit.fcr_cloud", "2607.13080", "45.9%", "45.9%", "Inference Economics: commit di riparazione col modello cloud"),
        ("lit.dedicated_more", "2607.13080", "43.8%", "+43.8%", "Inference Economics: costo in più del locale con GPU dedicata rispetto al cloud con caching"),
        ("lit.flywheel_volume", "2609.01572", "116", "116 M", "richieste al mese del traffico aziendale nel caso Tsymboi et al."),
    ]
    for key, aid, raw, disp, label in LIT:
        r = bib[aid]
        in_abs = raw in r["numbers_in_abstract"] or raw.replace(",", ".") in r["abstract"]
        if r["status"] != "VERIFICATO" or not in_abs:
            raise SystemExit(f"{key}: {raw} non è un numero citabile di {aid}")
        n[key] = {"value": raw, "display": disp, "label": label, "arxiv": aid, "title": r["real_title"],
                  "source": f"benchmarks/results/bibliography.json#{aid} (abstract)", "measured_at": r["date"]}

    # --- RAG
    put("rag.hit_at_3", "rag", "hit_at_3", ratio, "fonte giusta nei primi 3 chunk")
    put("rag.answer_ok", "rag", "expected_in_answer_rate", ratio, "risposte con il dato atteso")
    put("rag.questions", "rag", "questions", num, "domande di riferimento del benchmark RAG")

    # --- n8n
    ing = load("n8n_ingest")
    put("n8n.docs", "n8n_ingest", "rows", lambda v: str(len(v)), "documenti ingeriti via webhook n8n", value=ing["rows"])
    n["n8n.docs"]["value"] = len(ing["rows"])
    put("n8n.violations", "n8n_ingest", "residency_violations", num, "violazioni residency nell'intake n8n")
    wall = sorted(r["wall_ms"] for r in ing["rows"])[len(ing["rows"]) // 2]
    n["n8n.wall"] = {"value": wall, "display": ms(wall), "label": "tempo per documento (classifica+estrai+indicizza+QA)",
                     "source": "benchmarks/results/n8n_ingest.json#rows.wall_ms", "measured_at": ing["meta"]["measured_at"]}

    # --- stress test di atterraggio
    st = load("stress")
    for k, fmt, label in (("total_tasks", num, "task nel batch"), ("completed", num, "task completati"),
                          ("fallback_events", num, "fallback durante la turbolenza"),
                          ("budget_guard_hits", num, "richieste con budget guard attivo"),
                          ("data_residency_violations", num, "violazioni di data residency"),
                          ("cost_real_eur", eur, "costo reale del batch"), ("cost_if_all_cloud_eur", eur, "costo se tutto in cloud"),
                          ("saving_pct", pctf, "risparmio sul batch"), ("duration_s", lambda v: f"{v:.0f} s", "durata del batch")):
        put(f"stress.{k}", "stress", f"summary.{k}", fmt, label + " (cloud simulato)")
    for r in ("local", "cloud", "local_rag"):
        put(f"stress.decided.{r}", "stress", f"summary.routes_decided.{r}", num, f"rotte decise: {r}")
    put("stress.executed.cloud", "stress", "summary.executed_on.cloud", num, "eseguite davvero in cloud")
    put("stress.latency_p95", "stress", "cost_report.latency_ms.p95", ms, "latenza p95 del batch (richieste in sequenza)")
    for k in ("exported", "pii_redactions", "distillation_candidates", "duplicates_skipped"):
        put(f"flywheel.{k}", "stress", f"flywheel.{k}", num, f"flywheel: {k}")
    kept_local = sum(1 for e in st["timeline"] if e.get("family") == "architecture" and "budget_guard" in e.get("rules", []))
    n["stress.complex_kept_local_by_budget"] = {"value": kept_local, "display": num(kept_local),
                                                "label": "task complessi tenuti in locale dal budget guard",
                                                "source": "benchmarks/results/stress.json#timeline", "measured_at": st["meta"]["measured_at"]}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    meta = {"generated_from": sorted(p.name for p in RES.glob("*.json")),
            "cloud_simulation_note": st["cloud_simulation"]}
    OUT.write_text(json.dumps({"meta": meta, "numbers": n}, indent=1, ensure_ascii=False), encoding="utf-8")
    replay = [{k: e.get(k) for k in ("i", "family", "status", "route", "model", "fallback", "rules", "latency_ms",
                                     "cum_cost_eur", "cum_cost_if_cloud_eur")} for e in st["timeline"]]
    (ROOT / "talk/replays").mkdir(parents=True, exist_ok=True)
    (ROOT / "talk/replays/stress.json").write_text(json.dumps(replay, ensure_ascii=False), encoding="utf-8")
    # replay della demo "quattro destini": prima run misurata di ogni task (talk/replays/demo.json)
    tco = load("tco")
    from app.main import DEMO_TASKS
    demo = []
    for title, prompt in DEMO_TASKS.items():
        r = next(x for x in tco["rows"] if x["task"] == title)
        demo.append({"title": title, "prompt": prompt[:160] + ("…" if len(prompt) > 160 else ""), "prompt_full": prompt, **{k: r[k] for k in (
            "route", "model", "fallback", "fallback_reason", "tokens_in", "tokens_out", "latency_ms", "cost_eur",
            "cost_if_cloud_eur", "sources")}, "measured_at": tco["meta"]["measured_at"]})
    (ROOT / "talk/replays/demo.json").write_text(json.dumps(demo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(n)} numeri · talk/replays/stress.json: {len(replay)} eventi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI di switchable_ai — l'equivalente esagonale di run.sh del legacy.

    python -m app.main <comando> [argomenti]      (oppure ./run.sh <comando>)
"""
from __future__ import annotations

import argparse
import json
import sys

DEMO_TASKS = {
    "Task A — classificazione semplice": (
        "Classifica questo ticket in [accesso, fatturazione, bug, altro] e rispondi SOLO con la "
        "categoria: 'Non riesco a fare login da stamattina.'"),
    "Task B — reasoning complesso": (
        "Analizza i trade-off tra monolite modulare e microservizi per una piattaforma con vincoli "
        "di data residency, proponi una migrazione in 3 fasi con rischi e mitigazioni. " * 4),
    "Task C — domanda sulla knowledge base": (
        "Nella documentazione del repository, come funziona il fallback del gateway quando il cloud "
        "non risponde?"),
    "Task D — dato sensibile": (
        "Documento riservato: analizza i rischi del piano di riorganizzazione del team vendite e "
        "proponi le azioni per i prossimi 3 mesi. " * 3),
}


def _dump(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _container():
    from app.composition import Container
    return Container()


def cmd_health(a) -> int:
    print("OK")
    return 0


def cmd_route(a) -> int:
    from core.domain.policy import decide_route
    from app.composition import Settings
    _dump(decide_route(a.prompt, catalog=Settings().catalog).to_dict())
    return 0


def cmd_ask(a) -> int:
    res = _container().execute.execute(a.prompt, max_tokens=a.max_tokens)
    _dump({**res.to_dict(), "text": res.text})
    return 0


def cmd_demo(a) -> int:
    c = _container()
    for title, prompt in DEMO_TASKS.items():
        print(f"\n════ {title} ════")
        decision = c.execute.decide(prompt)
        _dump(decision.to_dict())
        if a.dry_run:
            continue
        res = c.execute.execute(prompt, max_tokens=a.max_tokens)
        r = res.record
        tag = " (FALLBACK: " + r.fallback_reason + ")" if r.fallback else ""
        print(f"→ eseguito su {r.model}{tag}: {r.latency_ms}ms, {r.tokens_in}→{r.tokens_out} token, "
              f"€{r.cost_eur:.6f} (se cloud €{r.cost_if_cloud_eur:.6f})")
        for i, s in enumerate(res.sources, 1):
            print(f"   [{i}] {s.score:.2f} {s.path}")
        print("→ risposta:", res.text.strip()[:300].replace("\n", " "), "…")
    return 0


def cmd_rag_build(a) -> int:
    _dump(_container().build_index.execute())
    return 0


def cmd_rag(a) -> int:
    for s in _container().retriever.retrieve(a.question):
        print(f"[{s.score:.2f}] {s.path}\n   {s.chunk[:200]}\n")
    return 0


def cmd_report(a) -> int:
    c = _container()
    print(c.report.markdown() if not a.json else json.dumps(c.report.execute(), indent=2))
    return 0


def cmd_stress(a) -> int:
    from core.use_cases.stress import landing_scenario
    c = _container()
    tasks = landing_scenario(a.n, seed=a.seed)

    def show(ev):
        if ev["status"] != "ok":
            print(f"  ✗ #{ev['i']:03d} {ev['family']}: {ev['error']}")
            return
        flag = " FALLBACK" if ev["fallback"] else (" ESCALATION" if ev["escalated"] else "")
        guard = " [budget_guard]" if "budget_guard" in ev["rules"] else ""
        print(f"  ✓ #{ev['i']:03d} {ev['family']:<12} {ev['route']:<9} {ev['model']:<22} "
              f"{ev['latency_ms']:>6}ms{flag}{guard}")
    report = c.stress.execute(tasks, on_event=show)
    if a.out:
        from pathlib import Path
        Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _dump({k: v for k, v in report.items() if k != "timeline"})
    return 0 if report["data_residency_violations"] == 0 else 3


def cmd_flywheel(a) -> int:
    _dump(_container().flywheel.execute())
    return 0


def cmd_ingest(a) -> int:
    from pathlib import Path
    p = Path(a.path)
    _dump(_container().ingest.execute(p.name, p.read_text(encoding="utf-8")))
    return 0


def cmd_serve(a) -> int:
    import uvicorn
    uvicorn.run("app.api:app", host=a.host, port=a.port, log_level="info")
    return 0


def cmd_mcp(a) -> int:
    from adapters.mcp.server import build_server
    build_server(_container()).run()
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="switchable_ai", description="Architettura AI switchabile")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health").set_defaults(fn=cmd_health)
    s = sub.add_parser("route", help="decisione di routing (nessuna chiamata)")
    s.add_argument("prompt"); s.set_defaults(fn=cmd_route)
    s = sub.add_parser("ask", help="esegue UNA richiesta end-to-end")
    s.add_argument("prompt"); s.add_argument("--max-tokens", type=int, default=None); s.set_defaults(fn=cmd_ask)
    s = sub.add_parser("demo", help='"one request, tre rotte" + dato sensibile')
    s.add_argument("--dry-run", action="store_true"); s.add_argument("--max-tokens", type=int, default=300)
    s.set_defaults(fn=cmd_demo)
    sub.add_parser("rag-build").set_defaults(fn=cmd_rag_build)
    s = sub.add_parser("rag"); s.add_argument("question"); s.set_defaults(fn=cmd_rag)
    s = sub.add_parser("report"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_report)
    s = sub.add_parser("stress", help="stress test di atterraggio")
    s.add_argument("--n", type=int, default=100); s.add_argument("--seed", type=int, default=42)
    s.add_argument("--out", default=""); s.set_defaults(fn=cmd_stress)
    sub.add_parser("flywheel").set_defaults(fn=cmd_flywheel)
    s = sub.add_parser("ingest"); s.add_argument("path"); s.set_defaults(fn=cmd_ingest)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8088)
    s.set_defaults(fn=cmd_serve)
    sub.add_parser("mcp").set_defaults(fn=cmd_mcp)
    return p


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(sys.argv[1:] if argv is None else argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

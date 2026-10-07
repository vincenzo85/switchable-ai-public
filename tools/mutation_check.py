#!/usr/bin/env python3
"""Mutation testing artigianale (porting da router_llm_legacy, esteso).

Sabota deliberatamente il codice nei punti che reggono la TESI del talk e
pretende che la suite diventi ROSSA. Una mutazione che sopravvive = un
test cieco. Ogni file viene sempre ripristinato (try/finally).

Uso:  .venv/bin/python tools/mutation_check.py      Exit 0 = tutte uccise.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
sys.path.insert(0, str(ROOT / "benchmarks"))

# (file, originale, mutato, cosa sabota)
MUTATIONS = [
    ("core/domain/policy.py", "if chars > COMPLEXITY_CHARS * factor or words > COMPLEXITY_WORDS * factor:",
     "if chars > COMPLEXITY_CHARS * 1000 or words > COMPLEXITY_WORDS * 1000:",
     "nulla è mai complesso: il reasoning non va più al cloud"),
    ("core/domain/policy.py", "return decision(ROUTE_CLOUD, cat.cloud, (cat.local,),",
     "return decision(ROUTE_LOCAL, cat.cloud, (cat.local,),", "la rotta cloud sparisce"),
    ("core/domain/policy.py", "return decision(ROUTE_CLOUD, cat.cloud, (cat.local,),",
     "return decision(ROUTE_CLOUD, cat.cloud, (),", "il cloud perde il fallback locale (lock-in)"),
    ("core/domain/policy.py", '    if c.sensitive:\n        rules.append("data_residency")',
     '    if False:\n        rules.append("data_residency")', "data residency spenta: il dato sensibile va in cloud"),
    ("core/domain/policy.py", "ctx.budget_remaining_eur <= ctx.budget_guard_eur",
     "ctx.budget_remaining_eur < -1e9", "budget guard spento"),
    ("core/domain/pricing.py", "return (tokens_in + tokens_out) / 1000.0 * price_per_1k(model)",
     "return (tokens_in - tokens_out) / 1000.0 * price_per_1k(model)", "conteggio token rotto"),
    ("core/domain/pricing.py", "return (tokens_in + tokens_out) / 1000.0 * price_per_1k(model)",
     "return 0.0 * price_per_1k(model)", "tutto costa zero: il TCO è una favola"),
    ("core/use_cases/execute_request.py", "chain = (decision.model, *decision.fallbacks)",
     "chain = (decision.model,)", "il fallback non viene mai eseguito"),
    ("core/use_cases/execute_request.py", "sent = build_rag_prompt(prompt, sources)",
     "sent = prompt", "RAG: il contesto non arriva al modello (bug del legacy)"),
    ("core/use_cases/execute_request.py", "if decision.escalation and decision.cloud_allowed and not check(result.text):",
     "if False:", "escalation spenta"),
    ("core/use_cases/report.py", 'return r.sensitive and r.model.startswith("cloud/")',
     "return False", "il contatore di violazioni residency è cieco"),
    ("core/use_cases/advisor.py", "if r != ROUTE_CLOUD or base.cloud_allowed]",
     "]", "l'advisor può proporre il cloud anche per dati sensibili"),
    ("core/domain/policy.py", "found = [(_position(intent, kws)", "found = [(_position(low, kws)",
     "l'intento torna a leggersi dal corpo del documento"),
    ("core/use_cases/advisor.py", 'if self.mode == "off" or (self.mode == "fallback" and base.classification.keyword_hit):',
     'if self.mode == "off":', "la modalità fallback chiama il modello anche quando la regola è sicura"),
    ("core/domain/text.py", 'text, n = pat.subn(f"<{label}>", text)',
     "n = 0", "il flywheel esporta dati personali in chiaro"),
]


def green() -> bool:
    p = subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT,
                       capture_output=True, text=True, timeout=600)
    return p.returncode == 0


def main() -> int:
    if not green():
        print("ERRORE: suite già rossa prima delle mutazioni.")
        return 2
    survived = []
    for path, old, new, what in MUTATIONS:
        f = ROOT / path
        src = f.read_text(encoding="utf-8")
        if old not in src:
            print(f"⚠ SKIP {path}: bersaglio non trovato — aggiorna la mutazione")
            survived.append((path, what))
            continue
        try:
            f.write_text(src.replace(old, new, 1), encoding="utf-8")
            ok = green()
        finally:
            f.write_text(src, encoding="utf-8")
        print(("🧟 SURVIVED " if ok else "💀 KILLED   ") + f"{path} — {what}")
        if ok:
            survived.append((path, what))
    if not green():
        print("ERRORE GRAVE: suite rossa dopo il ripristino")
        return 2
    print(f"\nEsito: {len(MUTATIONS) - len(survived)}/{len(MUTATIONS)} mutazioni uccise")
    from _common import save
    save("mutation", {"total": len(MUTATIONS), "killed": len(MUTATIONS) - len(survived),
                      "survived": [{"file": p, "what": w} for p, w in survived],
                      "mutations": [{"file": p, "what": w} for p, _, _, w in MUTATIONS]})
    return 1 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())

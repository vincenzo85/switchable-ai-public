#!/usr/bin/env python3
"""Token compression: quanti token si risparmiano e quanta qualità si perde?

20 prompt lunghi "ago nel pagliaio": contesto realistico (doc del repo +
log + verbali) con UN fatto da ritrovare e una domanda. Per ogni prompt:
originale vs compressione estrattiva al 50% e al 30%, sia guidata dalla
domanda (estrattiva_*) sia senza domanda (agnostica_*: il caso realistico
in cui il contesto si comprime una volta sola per molte domande).
ATTENZIONE: è un compito facile (un fatto, spesso con parole in comune con
la domanda): misura il risparmio, non è un benchmark generale di qualità. Il giudice è
deterministico: la risposta contiene il valore atteso? I token sono quelli
contati da Ollama (prompt_eval_count), non stimati.
"""
from __future__ import annotations

import argparse
import random
import time

from _common import ROOT, pct, save

from adapters.compression.extractive import ExtractiveCompressor
from adapters.llm.providers import OllamaLLM
from core.domain.text import chunk_markdown

FACTS = [
    ("Il codice di rilascio della versione 4.2 è ORCA-7731.", "Qual è il codice di rilascio della versione 4.2?", "ORCA-7731"),
    ("La finestra di manutenzione del database è il giovedì alle 03:40.", "In che giorno e a che ora è la finestra di manutenzione del database?", "03:40"),
    ("Il responsabile del servizio pagamenti è Ilaria Ventimiglia.", "Chi è il responsabile del servizio pagamenti?", "Ventimiglia"),
    ("Il limite di spesa cloud del team dati è di 740 euro al mese.", "Qual è il limite di spesa cloud mensile del team dati?", "740"),
    ("La chiave di partizione della tabella ordini è customer_region.", "Qual è la chiave di partizione della tabella ordini?", "customer_region"),
    ("Il timeout del gateway verso il provider cloud è fissato a 47 secondi.", "Quanti secondi è il timeout del gateway verso il provider cloud?", "47"),
    ("Il modello di riserva per il reparto legale è qwen2.5:14b.", "Quale modello di riserva usa il reparto legale?", "14b"),
    ("Il bucket dei backup notturni si chiama nightly-vault-eu3.", "Come si chiama il bucket dei backup notturni?", "nightly-vault-eu3"),
    ("Lo SLA di risposta per i ticket critici è di 25 minuti.", "Qual è lo SLA di risposta per i ticket critici?", "25"),
    ("La porta interna del servizio di embedding è 7319.", "Su quale porta interna gira il servizio di embedding?", "7319"),
]


def haystack(rng: random.Random, docs: list[str], n_chunks: int) -> list[str]:
    pool = docs[:]
    rng.shuffle(pool)
    logs = [f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d} INFO worker-{rng.randint(1, 9)} batch "
            f"{rng.randint(1000, 9999)} completato in {rng.randint(80, 900)} ms." for _ in range(12)]
    notes = ["Verbale: si è discusso del piano trimestrale senza decisioni operative.",
             "Promemoria: aggiornare la pagina wiki del team entro venerdì.",
             "Nota: la riunione di allineamento è spostata alla settimana prossima."]
    return pool[:n_chunks] + [" ".join(logs)] + notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--model", default="ollama/qwen2.5:7b")
    a = ap.parse_args()
    rng = random.Random(11)
    docs = []
    for f in sorted((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md"]:
        docs += chunk_markdown(f.read_text(encoding="utf-8"), 700)
    llm = OllamaLLM(num_ctx=8192, temperature=0.0)
    comp = ExtractiveCompressor()
    rows = []
    for i in range(a.n):
        fact, question, expected = FACTS[i % len(FACTS)]
        parts = haystack(rng, docs, 6)
        parts.insert(rng.randint(1, len(parts) - 1), fact)
        context = "\n\n".join(parts)
        for variant, ratio, q in (("originale", None, ""), ("estrattiva_50", 0.5, question),
                                  ("estrattiva_30", 0.3, question), ("agnostica_50", 0.5, ""), ("agnostica_30", 0.3, "")):
            ctx = context if ratio is None else comp.compress(context, keep_ratio=ratio, question=q).text
            prompt = (f"Rispondi in una riga usando SOLO il contesto.\n\nCONTESTO:\n{ctx}\n\nDOMANDA: {question}\nRISPOSTA:")
            t0 = time.monotonic()
            r = llm.complete(a.model, prompt, max_tokens=40, timeout_s=300)
            ok = expected.lower() in r.text.lower()
            rows.append({"i": i, "variant": variant, "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                         "latency_ms": int((time.monotonic() - t0) * 1000), "correct": ok,
                         "fact_kept": fact in ctx, "answer": r.text.strip()[:120]})
            print(f"#{i:02d} {variant:<14} in={r.tokens_in:5d} {'✓' if ok else '✗'} {r.text.strip()[:60]!r}")
    summary = {}
    base_tokens = {r["i"]: r["tokens_in"] for r in rows if r["variant"] == "originale"}
    for v in ("originale", "estrattiva_50", "estrattiva_30", "agnostica_50", "agnostica_30"):
        vr = [r for r in rows if r["variant"] == v]
        summary[v] = {"accuracy": sum(r["correct"] for r in vr) / len(vr),
                      "fact_kept_rate": sum(r["fact_kept"] for r in vr) / len(vr),
                      "tokens_in_mean": sum(r["tokens_in"] for r in vr) / len(vr),
                      "token_saving_pct": 100 * (1 - sum(r["tokens_in"] for r in vr) / sum(base_tokens.values())),
                      "latency_p50_ms": pct([r["latency_ms"] for r in vr], 50)}
    save("compression", {"model": a.model, "prompts": a.n, "compressor": "extractive (adapters/compression)",
                         "judge": "deterministico: valore atteso contenuto nella risposta",
                         "summary": summary, "rows": rows})
    for v, s in summary.items():
        print(f"{v:<14} acc={s['accuracy']:.0%} token={s['tokens_in_mean']:.0f} (−{s['token_saving_pct']:.0f}%) "
              f"fatto conservato={s['fact_kept_rate']:.0%} p50={s['latency_p50_ms']:.0f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

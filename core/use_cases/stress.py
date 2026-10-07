"""Stress test di atterraggio: il climax del talk.

100 task misti, budget cloud che si esaurisce durante il batch, cloud che
rallenta, 10% di documenti sensibili. Domanda: l'aereo atterra?
Risposta misurata: rotte, fallback, costo reale vs tutto-cloud e — il
numero che conta — violazioni di data residency.
"""
from __future__ import annotations

import random
import time
from collections import Counter

from core.domain.errors import DomainError
from core.use_cases.execute_request import ExecuteRequest
from core.use_cases.report import is_residency_violation

_TICKETS = ["non riesco a fare login da stamattina", "la fattura di marzo è doppia",
            "il pulsante salva va in errore 500", "come cambio la password?",
            "l'export CSV è vuoto", "non ricevo le email di notifica"]
_EXTRACT = ["Fattura n. {n} del 12/03/2026, importo 1.{n}40 EUR, fornitore Alfa Srl",
            "Ordine {n}: 3 licenze, consegna entro il 30/06, referente Ufficio Acquisti"]
_ARCH = ("Analizza i trade-off tra {a} e {b} per il servizio {s}, con vincoli di data residency "
         "europei, proponi una migrazione in 3 fasi con rischi, mitigazioni e criteri di successo misurabili. ")
_KB = ["Nella documentazione del progetto, come funziona il fallback del gateway?",
       "Nella documentazione, qual è la procedura di rilascio?",
       "Nel runbook, cosa faccio se il cloud non risponde?"]
_SENS = ["Documento riservato: valuta l'impatto del piano esuberi 2027 sul team {s}.",
         "Analizza la pratica del cliente con codice fiscale RSSMRA80A01H501U e IBAN IT60X0542811101000000123456.",
         "Strettamente interno: classifica la segnalazione disciplinare n. {n}."]


def landing_scenario(n: int = 100, seed: int = 42) -> list[dict]:
    """Batch deterministico: 40% ticket, 15% estrazioni, 20% architettura,
    15% domande alla knowledge base, 10% documenti sensibili."""
    rng = random.Random(seed)
    plan = (["ticket"] * 40 + ["extraction"] * 15 + ["architecture"] * 20 + ["kb_question"] * 15
            + ["sensitive"] * 10)
    plan = [plan[int(i * len(plan) / n)] for i in range(n)]
    rng.shuffle(plan)
    tasks = []
    for i, fam in enumerate(plan):
        if fam == "ticket":
            p = f"Classifica questo ticket in [accesso, fatturazione, bug, altro]: '{rng.choice(_TICKETS)}'"
        elif fam == "extraction":
            p = "Estrai fornitore, data e importo: " + rng.choice(_EXTRACT).format(n=i)
        elif fam == "architecture":
            a, b = rng.sample(["monolite modulare", "microservizi", "serverless", "event-driven"], 2)
            p = (_ARCH.format(a=a, b=b, s=rng.choice(["prenotazioni", "pagamenti", "anagrafica"]))) * 3
        elif fam == "kb_question":
            p = rng.choice(_KB)
        else:
            p = rng.choice(_SENS).format(n=i, s=rng.choice(["vendite", "IT", "HR"]))
        tasks.append({"id": i, "family": fam, "prompt": p})
    return tasks


class RunStressTest:
    def __init__(self, execute: ExecuteRequest, max_tokens: int | None = None):
        self.ex, self.max_tokens = execute, max_tokens

    def execute(self, tasks: list[dict], on_event=None) -> dict:
        t0 = time.monotonic()
        decided, executed = Counter(), Counter()
        fallbacks = escalations = guard_hits = violations = failed = 0
        cost = cost_cloud = saved = 0.0
        timeline = []
        for t in tasks:
            try:
                res = self.ex.execute(t["prompt"], max_tokens=self.max_tokens)
            except DomainError as e:
                failed += 1
                ev = {"i": t["id"], "family": t["family"], "status": "failed", "error": str(e)[:160]}
            else:
                r = res.record
                decided[res.decision.route] += 1
                executed["cloud" if r.model.startswith("cloud/") else "local"] += 1
                fallbacks += r.fallback
                escalations += r.escalated
                guard_hits += "budget_guard" in r.rules
                violations += is_residency_violation(r)
                cost += r.cost_eur
                cost_cloud += r.cost_if_cloud_eur
                saved += r.tokens_saved_by_compression
                ev = {"i": t["id"], "family": t["family"], "status": "ok", "route": res.decision.route,
                      "model": r.model, "fallback": r.fallback, "escalated": r.escalated,
                      "rules": list(r.rules), "latency_ms": r.latency_ms,
                      "cost_eur": r.cost_eur, "cost_if_cloud_eur": r.cost_if_cloud_eur,
                      "cum_cost_eur": cost, "cum_cost_if_cloud_eur": cost_cloud}
            timeline.append(ev)
            if on_event:
                on_event(ev)
        return {
            "total_tasks": len(tasks),
            "completed": len(tasks) - failed,
            "failed": failed,
            "routes_decided": {k: decided.get(k, 0) for k in ("local", "cloud", "local_rag")},
            "executed_on": {k: executed.get(k, 0) for k in ("local", "cloud")},
            "fallback_events": fallbacks,
            "escalations": escalations,
            "budget_guard_hits": guard_hits,
            "data_residency_violations": violations,
            "cost_real_eur": cost,
            "cost_if_all_cloud_eur": cost_cloud,
            "saving_pct": (1 - cost / cost_cloud) * 100 if cost_cloud else 0.0,
            "tokens_saved_by_compression": saved,
            "duration_s": round(time.monotonic() - t0, 2),
            "timeline": timeline,
        }

"""CostReport: il cockpit. Aggrega il registro costi in numeri da slide."""
from __future__ import annotations

from collections import defaultdict

from core.domain.models import CallRecord
from core.ports import CostLedgerPort


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0
    v = sorted(values)
    k = (len(v) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def _bucket(recs: list[CallRecord]) -> dict:
    lat = [r.latency_ms for r in recs]
    return {
        "calls": len(recs),
        "cost_eur": sum(r.cost_eur for r in recs),
        "cost_if_cloud_eur": sum(r.cost_if_cloud_eur for r in recs),
        "tokens_in": sum(r.tokens_in for r in recs),
        "tokens_out": sum(r.tokens_out for r in recs),
        "latency_p50_ms": percentile(lat, 50),
        "latency_p95_ms": percentile(lat, 95),
    }


def is_residency_violation(r: CallRecord) -> bool:
    return r.sensitive and r.model.startswith("cloud/")


class CostReport:
    def __init__(self, ledger: CostLedgerPort):
        self.ledger = ledger

    def execute(self) -> dict:
        recs = self.ledger.records()
        by_route, by_model = defaultdict(list), defaultdict(list)
        for r in recs:
            by_route[r.route].append(r)
            by_model[r.model].append(r)
        total = _bucket(recs)
        saving = (1 - total["cost_eur"] / total["cost_if_cloud_eur"]) * 100 if total["cost_if_cloud_eur"] else 0.0
        return {
            "calls": len(recs),
            "cost_eur": total["cost_eur"],
            "cost_if_cloud_eur": total["cost_if_cloud_eur"],
            "saving_pct": saving,
            "latency_ms": {"p50": total["latency_p50_ms"], "p95": total["latency_p95_ms"]},
            "fallbacks": sum(r.fallback for r in recs),
            "escalations": sum(r.escalated for r in recs),
            "residency_violations": sum(is_residency_violation(r) for r in recs),
            "tokens_saved_by_compression": sum(r.tokens_saved_by_compression for r in recs),
            "by_route": {k: _bucket(v) for k, v in sorted(by_route.items())},
            "by_model": {k: _bucket(v) for k, v in sorted(by_model.items())},
        }

    def markdown(self) -> str:
        rep = self.execute()
        lines = ["| Rotta | Chiamate | € reali | € se tutto-cloud | p50 ms | p95 ms |",
                 "|---|---:|---:|---:|---:|---:|"]
        for route, b in rep["by_route"].items():
            lines.append(f"| {route} | {b['calls']} | {b['cost_eur']:.6f} | {b['cost_if_cloud_eur']:.6f} | "
                         f"{b['latency_p50_ms']:.0f} | {b['latency_p95_ms']:.0f} |")
        lines.append(f"\n**Totale: €{rep['cost_eur']:.5f} vs €{rep['cost_if_cloud_eur']:.5f} se tutto-cloud "
                     f"→ risparmio {rep['saving_pct']:.1f}%** · fallback {rep['fallbacks']} · "
                     f"escalation {rep['escalations']} · violazioni residency {rep['residency_violations']}")
        return "\n".join(lines)

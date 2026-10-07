"""Genera infra/grafana/dashboards/cockpit.json dalle metriche sai_* esposte
da adapters/observability/sinks.py (una sola fonte di verità per i nomi)."""
import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "prom"}
panels, y = [], 0


def stat(title, expr, x, w=4, unit="none", decimals=None, thresholds=None, h=5):
    p = {"type": "stat", "title": title, "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
         "targets": [{"refId": "A", "expr": expr, "datasource": DS}],
         "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background", "graphMode": "area"},
         "fieldConfig": {"defaults": {"unit": unit, "thresholds": thresholds or
                                      {"mode": "absolute", "steps": [{"color": "blue", "value": None}]}}}}
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    panels.append(p)


def ts(title, targets, x, w=12, unit="none", h=8, stack=False):
    panels.append({"type": "timeseries", "title": title, "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
                   "targets": [{"refId": chr(65 + i), "expr": e, "legendFormat": l, "datasource": DS}
                               for i, (e, l) in enumerate(targets)],
                   "fieldConfig": {"defaults": {"unit": unit, "custom": {"stacking": {"mode": "normal" if stack else "none"},
                                                                          "fillOpacity": 20}}}})


green0 = {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 1}]}
stat("€ reali", "sum(sai_cost_eur_total)", 0, unit="currencyEUR", decimals=4)
stat("€ se tutto-cloud", "sum(sai_cost_if_cloud_eur_total)", 4, unit="currencyEUR", decimals=4)
stat("Risparmio", "100 * (1 - sum(sai_cost_eur_total) / sum(sai_cost_if_cloud_eur_total))", 8, unit="percent", decimals=1,
     thresholds={"mode": "absolute", "steps": [{"color": "orange", "value": None}, {"color": "green", "value": 50}]})
stat("Richieste", "sum(sai_requests_total)", 12)
stat("Fallback", "sum(sai_fallbacks_total) or vector(0)", 16,
     thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 1}]})
stat("Violazioni residency", "sum(sai_residency_violations_total)", 20, thresholds=green0)
y += 5
ts("Richieste per rotta (req/s)", [("sum by (route) (rate(sai_requests_total[1m]))", "{{route}}")], 0, stack=True, unit="reqps")
ts("Latenza p50 / p95 per rotta", [
    ("histogram_quantile(0.5, sum by (le, route) (rate(sai_latency_ms_bucket[2m])))", "p50 {{route}}"),
    ("histogram_quantile(0.95, sum by (le, route) (rate(sai_latency_ms_bucket[2m])))", "p95 {{route}}")], 12, unit="ms")
y += 8
ts("Costo cumulato: reale vs tutto-cloud", [("sum(sai_cost_eur_total)", "reale"),
                                             ("sum(sai_cost_if_cloud_eur_total)", "se tutto-cloud")], 0, unit="currencyEUR")
ts("Turbolenza: fallback, escalation, budget guard", [
    ("sum(sai_fallbacks_total) or vector(0)", "fallback"),
    ("sum(sai_escalations_total) or vector(0)", "escalation"),
    ("sum(sai_budget_guard_total)", "budget guard")], 12)
y += 8
ts("Token (in/out) per modello", [("sum by (model, direction) (rate(sai_tokens_total[1m]))", "{{model}} {{direction}}")], 0,
   unit="short")
stat("Token risparmiati (compressione)", "sum(sai_compression_tokens_saved_total)", 12, w=6, h=8)
stat("Accordo advisor (Rizzo/Open-Jev)",
     '100 * sum(sai_advisor_decisions_total{agreed="true"}) / sum(sai_advisor_decisions_total)', 18, w=6, h=8,
     unit="percent", decimals=0)

dash = {"title": "Switchable AI — Cockpit", "uid": "switchable-cockpit", "timezone": "browser", "refresh": "5s",
        "time": {"from": "now-30m", "to": "now"}, "schemaVersion": 39, "panels": panels,
        "tags": ["switchable-ai", "tco"]}
out = Path(__file__).resolve().parents[1] / "infra/grafana/dashboards/cockpit.json"
out.write_text(json.dumps(dash, indent=1, ensure_ascii=False))
print(out, len(panels), "pannelli")

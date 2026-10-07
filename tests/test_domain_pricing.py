"""Contratto del prezzario e del TCO (core/domain/pricing.py).

Porting dei test WP2 (cost_of) + costo locale ammortizzato ESPLICITO:
il talk dichiara da dove nasce ogni euro, niente "costo locale = 0".
"""
import pytest

from core.domain.pricing import PRICING, cost_of, local_cost_per_mtok, LocalTcoInputs


def test_pricing_has_local_and_cloud_tiers():
    assert any(k.startswith("ollama/") or k == "local" for k in PRICING)
    assert any(k.startswith("cloud/") for k in PRICING)


def test_local_cost_is_orders_of_magnitude_below_cloud():
    local = cost_of("ollama/qwen2.5:7b", 1000, 1000)
    cloud = cost_of("cloud/gpt-4o", 1000, 1000)
    assert local < cloud / 10, "la tesi TCO richiede almeno 10x di differenza"


def test_cost_is_linear_in_tokens():
    assert cost_of("cloud/gpt-4o", 2000, 0) == pytest.approx(2 * cost_of("cloud/gpt-4o", 1000, 0))
    assert cost_of("cloud/gpt-4o", 500, 500) == pytest.approx(cost_of("cloud/gpt-4o", 1000, 0))


def test_unknown_model_falls_back_to_conservative_cloud_price():
    assert cost_of("boh/unknown", 1000, 1000) == pytest.approx(cost_of("cloud/gpt-4o", 1000, 1000))


def test_unknown_local_model_uses_local_price():
    assert cost_of("ollama/qualsiasi", 1000, 0) == pytest.approx(PRICING["local"])


def test_local_amortized_cost_grows_when_utilization_drops():
    """Il sottoutilizzo è la trappola del TCO on-prem (Patil 2026): stessa GPU,
    meno lavoro ⇒ ogni token costa di più."""
    busy = LocalTcoInputs(hw_eur=2000, amort_months=36, watts=150, eur_kwh=0.30,
                          tokens_per_sec=40, utilization=0.8)
    idle = LocalTcoInputs(hw_eur=2000, amort_months=36, watts=150, eur_kwh=0.30,
                          tokens_per_sec=40, utilization=0.05)
    assert local_cost_per_mtok(idle)["total"] > 10 * local_cost_per_mtok(busy)["total"]


def test_local_amortized_cost_breakdown_sums():
    r = local_cost_per_mtok(LocalTcoInputs(hw_eur=2000, amort_months=36, watts=150,
                                           eur_kwh=0.30, tokens_per_sec=40, utilization=0.5))
    assert r["total"] == pytest.approx(r["energy"] + r["hardware"])
    assert r["energy"] > 0 and r["hardware"] > 0


def test_local_tco_rejects_zero_utilization():
    with pytest.raises(ValueError):
        local_cost_per_mtok(LocalTcoInputs(2000, 36, 150, 0.30, 40, 0.0))

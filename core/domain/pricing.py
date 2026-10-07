"""Prezzario e TCO. Da qui nasce ogni euro mostrato nel talk.

PRICING: EUR per 1k token (blended in+out), come in router_llm_legacy, per
confrontabilità con il report storico (€0.00121 vs €0.02774).
- locale: stima energetica conservativa (vedi `local_cost_per_mtok` per il
  calcolo esplicito energia + ammortamento hardware);
- cloud: listino pubblico, blended.
"""
from __future__ import annotations

from dataclasses import dataclass

PRICING: dict[str, float] = {
    "local": 0.0002,
    "ollama/qwen2.5:7b": 0.0002,
    "vllm/qwen2.5-1.5b": 0.0001,
    "cloud/gpt-4o": 0.0046,
    "cloud/gpt-4o-mini": 0.0004,
    "cloud/deepseek": 0.002,
}
CLOUD_REFERENCE = "cloud/gpt-4o"


def _is_local(model: str) -> bool:
    return model.startswith(("ollama/", "vllm/")) or model == "local"


def price_per_1k(model: str) -> float:
    if model in PRICING:
        return PRICING[model]
    return PRICING["local"] if _is_local(model) else PRICING[CLOUD_REFERENCE]


def cost_of(model: str, tokens_in: int, tokens_out: int) -> float:
    return (tokens_in + tokens_out) / 1000.0 * price_per_1k(model)


def cost_if_cloud(tokens_in: int, tokens_out: int) -> float:
    return cost_of(CLOUD_REFERENCE, tokens_in, tokens_out)


@dataclass(frozen=True)
class LocalTcoInputs:
    hw_eur: float            # costo hardware (quota GPU/workstation)
    amort_months: int        # ammortamento
    watts: float             # assorbimento medio sotto carico
    eur_kwh: float           # costo energia
    tokens_per_sec: float    # throughput misurato
    utilization: float       # frazione del tempo in cui la GPU lavora davvero (0..1]


def local_cost_per_mtok(x: LocalTcoInputs) -> dict[str, float]:
    """EUR per milione di token = energia + ammortamento.

    L'ammortamento si paga anche quando la GPU è ferma: è diviso solo per i
    token prodotti davvero (utilization). Da qui la penalità di sottoutilizzo.
    """
    if not 0 < x.utilization <= 1:
        raise ValueError("utilization deve stare in (0, 1]")
    if x.tokens_per_sec <= 0:
        raise ValueError("tokens_per_sec deve essere > 0")
    sec_per_mtok = 1_000_000 / x.tokens_per_sec
    energy = x.watts / 1000 * sec_per_mtok / 3600 * x.eur_kwh
    seconds_amort = x.amort_months * 30 * 24 * 3600
    tokens_amort = seconds_amort * x.tokens_per_sec * x.utilization
    hardware = x.hw_eur / tokens_amort * 1_000_000
    return {"energy": energy, "hardware": hardware, "total": energy + hardware}

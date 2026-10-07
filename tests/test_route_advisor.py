"""Contratto del router "appreso" attivabile (Rizzo Flow / Open-Jev).

Modalità:
- off     : solo regole deterministiche (default);
- shadow  : decide la regola, il modello viene interrogato e MISURATO
            (accordo, confidenza, latenza) senza influire;
- active  : decide il modello, ma solo tra le rotte AMMESSE dalle regole
            dure (residency, local-only, budget): il modello non può mai
            mandare in cloud un dato sensibile (difesa da "rerouting").
Se il modello cade o è incerto, vince la regola.
"""
import pytest

from adapters.memory import FakeLLM, FixedClock, InMemoryLedger, SequentialIds, RecordingMetrics
from core.domain.errors import ProviderError
from core.domain.models import RouteDecision
from core.domain.policy import ROUTE_DESCRIPTIONS, decide_route, reroute
from core.ports import RouteAdvisorPort
from core.use_cases.advisor import AdvisedRouter
from core.use_cases.execute_request import ExecuteRequest

SIMPLE = "Classifica: login rotto o fattura?"
COMPLEX = "Analizza i trade-off di questa architettura distribuita multi-region. " * 12
SENSITIVE = "Documento riservato: " + COMPLEX


class ScriptedAdvisor(RouteAdvisorPort):
    name = "scripted"

    def __init__(self, probs=None, fail=False, latency_ms=70):
        self.probs, self.fail, self.latency_ms = probs or {}, fail, latency_ms
        self.asked = []

    def choose(self, state, question, candidates):
        self.asked.append((state, question, [c for c, _ in candidates]))
        if self.fail:
            raise ProviderError("server systemone giù")
        ids = [c for c, _ in candidates]
        p = {c: self.probs.get(c, 0.0) for c in ids}
        s = sum(p.values()) or 1.0
        return {c: v / s for c, v in p.items()}, self.latency_ms


# --- dominio: reroute -----------------------------------------------------------

def test_reroute_to_cloud_adds_local_fallback():
    base = decide_route(SIMPLE)
    r = reroute(base, "cloud")
    assert r.route == "cloud" and r.fallbacks and r.fallbacks[0].startswith("ollama/")
    assert "advisor" in r.rules


def test_reroute_refuses_cloud_when_rules_forbid_it():
    base = decide_route(SENSITIVE)
    with pytest.raises(ValueError):
        reroute(base, "cloud")


def test_route_descriptions_cover_all_routes():
    assert set(ROUTE_DESCRIPTIONS) == {"local", "cloud", "local_rag"}


# --- AdvisedRouter -----------------------------------------------------------------

def test_off_mode_never_calls_the_model():
    adv = ScriptedAdvisor({"cloud": 1})
    d, a = AdvisedRouter(adv, mode="off").decide(SIMPLE, decide_route(SIMPLE))
    assert d.route == "local" and a is None and adv.asked == []


def test_shadow_mode_measures_but_does_not_change_route():
    adv = ScriptedAdvisor({"cloud": 0.9, "local": 0.1})
    d, a = AdvisedRouter(adv, mode="shadow").decide(SIMPLE, decide_route(SIMPLE))
    assert d.route == "local"
    assert a.choice == "cloud" and not a.agreed and not a.applied and a.latency_ms == 70


def test_active_mode_applies_confident_choice():
    adv = ScriptedAdvisor({"cloud": 0.95, "local": 0.05})
    d, a = AdvisedRouter(adv, mode="active", min_confidence=0.6).decide(SIMPLE, decide_route(SIMPLE))
    assert d.route == "cloud" and a.applied


def test_active_mode_ignores_low_confidence():
    adv = ScriptedAdvisor({"cloud": 0.55, "local": 0.45})
    d, a = AdvisedRouter(adv, mode="active", min_confidence=0.6).decide(SIMPLE, decide_route(SIMPLE))
    assert d.route == "local" and not a.applied and "confidenza" in a.note


def test_cloud_is_not_even_offered_when_forbidden():
    adv = ScriptedAdvisor({"cloud": 1.0, "local": 0.0})
    d, a = AdvisedRouter(adv, mode="active").decide(SENSITIVE, decide_route(SENSITIVE))
    offered = adv.asked[-1][2]
    assert "cloud" not in offered
    assert d.route == "local" and not d.cloud_allowed


def test_advisor_failure_falls_back_to_rules():
    adv = ScriptedAdvisor(fail=True)
    d, a = AdvisedRouter(adv, mode="active").decide(COMPLEX, decide_route(COMPLEX))
    assert d.route == "cloud" and a.error and not a.applied


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        AdvisedRouter(ScriptedAdvisor(), mode="yolo")


def test_state_contains_signals_but_question_is_fixed():
    adv = ScriptedAdvisor({"local": 1})
    AdvisedRouter(adv, mode="shadow").decide(SIMPLE, decide_route(SIMPLE))
    state, question, _ = adv.asked[-1]
    assert "Request:" in state and "chars" in state
    assert "route" in question.lower()


def test_long_prompt_is_truncated_in_state():
    adv = ScriptedAdvisor({"local": 1})
    AdvisedRouter(adv, mode="shadow", max_state_chars=300).decide(COMPLEX * 5, decide_route(COMPLEX * 5))
    assert len(adv.asked[-1][0]) < 700


# --- integrazione con ExecuteRequest ---------------------------------------------

def make(adv, mode):
    ledger, metrics = InMemoryLedger(), RecordingMetrics()
    ex = ExecuteRequest(llm=FakeLLM(), ledger=ledger, clock=FixedClock(), ids=SequentialIds(), metrics=metrics,
                        advisor=AdvisedRouter(adv, mode=mode))
    return ex, ledger


def test_execute_records_advisor_fields_and_router_latency():
    ex, ledger = make(ScriptedAdvisor({"local": 0.9, "cloud": 0.1}, latency_ms=72), "shadow")
    rec = ex.execute(SIMPLE).record
    assert rec.advisor_engine == "scripted" and rec.advisor_choice == "local"
    assert rec.advisor_agreed and rec.advisor_latency_ms == 72
    assert rec.latency_ms >= 72, "la latenza del router è parte del costo della richiesta"


def test_execute_active_routes_where_advisor_says():
    ex, ledger = make(ScriptedAdvisor({"cloud": 1.0}), "active")
    rec = ex.execute(SIMPLE).record
    assert rec.model.startswith("cloud/") and "advisor" in rec.rules


def test_execute_without_advisor_has_empty_advisor_fields():
    ex = ExecuteRequest(llm=FakeLLM(), ledger=InMemoryLedger(), clock=FixedClock(), ids=SequentialIds())
    rec = ex.execute(SIMPLE).record
    assert rec.advisor_engine == "" and rec.advisor_latency_ms == 0


# --- modalità "fallback": il secondo controllore solo quando la regola tira a indovinare ---

def test_fallback_mode_skips_the_model_when_a_keyword_decided():
    adv = ScriptedAdvisor({"cloud": 1.0})
    d, a = AdvisedRouter(adv, mode="fallback").decide(SIMPLE, decide_route(SIMPLE))
    assert adv.asked == [] and a is None and d.route == "local"


def test_fallback_mode_asks_and_applies_when_the_rule_defaulted():
    unsure = "Confronta Kafka e RabbitMQ per gli ordini con picchi alti: quali rischi vedi?"
    adv = ScriptedAdvisor({"cloud": 0.9, "local": 0.1})
    d, a = AdvisedRouter(adv, mode="fallback").decide(unsure, decide_route(unsure))
    assert adv.asked and a.applied and d.route == "cloud"


def test_fallback_mode_still_respects_hard_rules():
    unsure = "Riservato: confronta i due fornitori, chi conviene?"
    adv = ScriptedAdvisor({"cloud": 1.0, "local": 0.0})
    d, a = AdvisedRouter(adv, mode="fallback").decide(unsure, decide_route(unsure))
    assert "cloud" not in adv.asked[-1][2] and d.route != "cloud"


# --- doppio ordine dei candidati (bias di posizione) ---------------------------------

class PositionBiased(RouteAdvisorPort):
    """Sceglie sempre il PRIMO candidato: il caso peggiore di bias di posizione."""
    name = "biased"

    def __init__(self):
        self.orders = []

    def choose(self, state, question, candidates):
        ids = [c for c, _ in candidates]
        self.orders.append(ids)
        return {c: (0.9 if i == 0 else 0.1 / (len(ids) - 1)) for i, c in enumerate(ids)}, 50


def test_both_orders_asks_twice_with_reversed_candidates_and_sums_latency():
    adv = PositionBiased()
    d, a = AdvisedRouter(adv, mode="shadow", both_orders=True).decide(SIMPLE, decide_route(SIMPLE))
    assert adv.orders[0] == list(reversed(adv.orders[1]))
    assert a.latency_ms == 100


def test_both_orders_neutralises_a_pure_position_bias():
    adv = PositionBiased()
    _, a = AdvisedRouter(adv, mode="shadow", both_orders=True).decide(SIMPLE, decide_route(SIMPLE))
    assert a.p < 0.6, "un modello che sceglie solo per posizione non deve sembrare sicuro"


def test_custom_route_descriptions_are_sent():
    adv = ScriptedAdvisor({"local": 1})
    desc = {"local": "piccolo", "cloud": "grande", "local_rag": "documenti"}
    AdvisedRouter(adv, mode="shadow", descriptions=desc).decide(SIMPLE, decide_route(SIMPLE))
    assert adv.asked[-1][2] == ["local", "cloud", "local_rag"]

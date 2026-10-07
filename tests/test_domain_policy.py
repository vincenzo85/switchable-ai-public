"""Contratto della policy di routing (core/domain/policy.py).

Porting dei test WP1 di router_llm_legacy + le regole nuove dell'abstract:
data residency (dato sensibile ⇒ mai cloud), budget guard (soglia ⇒
local-first), escalation dichiarata per i task locali.
"""
import json

from core.domain.policy import classify, decide_route
from core.domain.models import ModelCatalog, RoutingContext

LONG_REASONING = ("Analizza i trade-off architetturali tra un monolite modulare e "
                  "microservizi per una piattaforma di prenotazioni con vincoli di "
                  "data residency, proponi una strategia di migrazione in 3 fasi "
                  "con rischi e mitigazioni per ciascuna fase. " * 6)
DR_PROMPT = ("Progetta una strategia completa di disaster recovery multi-region "
             "considerando RPO, RTO, costi e conformità GDPR, con analisi "
             "dettagliata dei compromessi tra le opzioni. " * 6)


# --- classify (porting WP1) --------------------------------------------------

def test_classify_short_classification_is_low():
    c = classify("Classifica questo ticket: 'non riesco a fare login'")
    assert c.complexity == "low"
    assert c.kind == "classification"


def test_classify_extraction_is_low():
    c = classify("Estrai nome, data e importo da questa fattura: ...")
    assert c.complexity == "low"
    assert c.kind == "extraction"


def test_classify_long_reasoning_is_high():
    c = classify(LONG_REASONING)
    assert c.complexity == "high"
    assert c.kind == "reasoning"


def test_classify_doc_question_is_rag():
    assert classify("Cosa dice la documentazione del repository sul fallback?").kind == "rag_query"


def test_classify_returns_reasons():
    c = classify("Riassumi questo testo breve")
    assert isinstance(c.reasons, tuple) and c.reasons


# --- sensitivity (nuovo) -----------------------------------------------------

def test_classify_flags_confidential_keyword():
    assert classify("Documento RISERVATO: piano esuberi 2027").sensitive


def test_classify_flags_pii_patterns():
    assert classify("Il cliente mario.rossi@example.com ha IBAN IT60X0542811101000000123456").sensitive
    assert classify("Codice fiscale RSSMRA80A01H501U, verifica la pratica").sensitive


def test_gdpr_word_alone_is_not_sensitive_data():
    """Parlare DI GDPR non significa contenere dati personali."""
    assert not classify(DR_PROMPT).sensitive


# --- decide_route (porting WP1) ----------------------------------------------

def test_route_low_goes_local_near_zero():
    r = decide_route("Classifica: reclamo o richiesta info?")
    assert r.route == "local"
    assert r.model.startswith("ollama/")
    assert r.estimated_cost_class == "near_zero"
    assert r.reason


def test_route_high_goes_cloud_with_local_fallback():
    r = decide_route(DR_PROMPT)
    assert r.route == "cloud"
    assert r.estimated_cost_class == "metered"
    # il fallback DEVE esistere e DEVE essere locale: è la tesi del talk
    assert r.fallbacks, "cloud senza fallback locale = lock-in"
    assert r.fallbacks[0].startswith("ollama/")


def test_route_doc_question_goes_local_rag():
    assert decide_route("Nella documentazione del progetto, come configuro il gateway?").route == "local_rag"


def test_route_local_only_mode_forces_local():
    r = decide_route("Analizza in profondità questa architettura distribuita. " * 20,
                     RoutingContext(local_only=True))
    assert r.route in ("local", "local_rag")
    assert r.model.startswith("ollama/")
    assert not r.cloud_allowed


def test_route_is_json_serializable():
    json.dumps(decide_route("test").to_dict())


# --- regole nuove -------------------------------------------------------------

def test_sensitive_complex_task_never_goes_cloud():
    prompt = "Documento riservato. " + LONG_REASONING
    r = decide_route(prompt)
    assert r.route == "local"
    assert not r.cloud_allowed
    assert "data_residency" in r.rules
    assert all(not m.startswith("cloud/") for m in r.fallbacks)
    assert r.escalation is None, "un dato sensibile non può nemmeno essere 'escalato' al cloud"


def test_sensitive_doc_question_goes_local_rag():
    r = decide_route("Nella documentazione interna riservata, qual è la procedura di rilascio?")
    assert r.route == "local_rag"
    assert not r.cloud_allowed


def test_budget_guard_switches_to_local_first():
    r = decide_route(DR_PROMPT, RoutingContext(budget_remaining_eur=0.01, budget_guard_eur=0.05))
    assert r.route == "local"
    assert "budget_guard" in r.rules
    assert not r.cloud_allowed


def test_budget_above_guard_keeps_cloud():
    r = decide_route(DR_PROMPT, RoutingContext(budget_remaining_eur=5.0, budget_guard_eur=0.05))
    assert r.route == "cloud"


def test_local_task_declares_cloud_escalation_when_allowed():
    r = decide_route("Classifica: reclamo o richiesta info?")
    assert r.escalation == ModelCatalog().cloud


def test_catalog_is_injectable():
    cat = ModelCatalog(local="ollama/qwen2.5:3b", cloud="cloud/claude", rag="ollama/qwen2.5:7b")
    r = decide_route(DR_PROMPT, catalog=cat)
    assert r.model == "cloud/claude" and r.fallbacks[0] == "ollama/qwen2.5:3b"


# --- regressioni dal primo run reale di n8n (2026-10-03) ----------------------

ADR_BODY = ("# ADR-007 — Rollback del gateway\nDecisione: ogni aggiornamento passa da un deploy canary; "
            "la documentazione del repository descrive gli smoke test. ") * 4


def test_intent_comes_from_the_instruction_not_from_the_document_body():
    c = classify("Classifica questo documento SDLC in una categoria. Rispondi SOLO con la categoria.\n\n" + ADR_BODY)
    assert c.kind == "classification"


def test_keywords_match_on_word_boundaries():
    assert classify("Riassumi il paragrafo sul coraggio").kind != "rag_query"


def test_long_document_to_classify_or_extract_stays_local():
    for instr in ("Classifica questo documento: ", "Estrai titolo e parole chiave in JSON: "):
        r = decide_route(instr + ADR_BODY)
        assert r.route == "local", instr


def test_very_long_extraction_is_still_complex():
    assert classify("Estrai i dati: " + "riga di tabella con valori. " * 400).complexity == "high"


def test_sensitivity_is_checked_on_the_whole_text():
    assert classify("Classifica questo documento:\n" + "testo neutro. " * 40 + "Documento riservato.").sensitive


def test_neutral_instruction_is_not_hijacked_by_body_keywords():
    """'Genera una checklist QA' + un documento che parla di documentazione:
    non è una domanda alla knowledge base."""
    c = classify("Genera una checklist QA di massimo 5 punti.\n\n" + ADR_BODY)
    assert c.kind != "rag_query"


# --- keyword_hit: la regola sa quando sta tirando a indovinare -----------------

def test_keyword_hit_true_when_a_keyword_decides_the_kind():
    assert classify("Classifica questo ticket: login rotto").keyword_hit


def test_keyword_hit_false_when_kind_is_a_default():
    c = classify("Confronta Kafka e RabbitMQ per gli ordini con picchi alti: rischi?")
    assert not c.keyword_hit and c.kind == "classification"

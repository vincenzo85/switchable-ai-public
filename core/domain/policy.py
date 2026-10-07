"""Policy di routing: la "torre di controllo" del talk.

DETERMINISTICA (niente LLM nel router): regole leggibili, auditabili,
modificabili. Un router LLM costa token e latenza a ogni richiesta ed è
attaccabile (Shafran et al. 2025, "Rerouting LLM Routers").

Ordine di priorità delle regole (la prima che scatta vince sul cloud):
  1. data_residency  — dato sensibile ⇒ il cloud non è ammesso, mai
  2. local_only      — modalità forzata (nessuna chiave, scelta aziendale)
  3. budget_guard    — budget cloud sotto soglia ⇒ local-first
  4. complexity      — task complesso ⇒ cloud con fallback locale
"""
from __future__ import annotations

import re

from core.domain.models import (
    ROUTE_CLOUD, ROUTE_LOCAL, ROUTE_LOCAL_RAG,
    Classification, ModelCatalog, RouteDecision, RoutingContext,
)

RAG_KEYWORDS = ("documentazione", "documentation", "repository", "progetto", "docs", "rag",
                "runbook", "procedura interna", "knowledge base")
EXTRACTION_KEYWORDS = ("estrai", "extract", "extraction", "fattura", "dati da", "nome, data")
CLASSIFICATION_KEYWORDS = ("classifica", "classify", "classification", "ticket", "reclamo",
                           "categorizza", "scegli")
REASONING_KEYWORDS = ("analizza", "analyze", "trade-off", "progetta", "design", "disaster recovery",
                      "migrazione", "reasoning", "strategia", "ottimizza", "valuta")

SENSITIVE_KEYWORDS = ("riservat", "confidenzial", "confidential", "strettamente interno",
                      "dati personali di", "cartella clinica", "stipendi", "buste paga")
PII_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),                                   # email
    re.compile(r"\bIT\d{2}[A-Z]\d{10}[0-9A-Z]{12}\b", re.IGNORECASE),        # IBAN italiano
    re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b", re.IGNORECASE),  # codice fiscale
    re.compile(r"\b(?:\d[ -]?){13,16}\b"),                                    # carta di credito
)

COMPLEXITY_CHARS = 400
COMPLEXITY_WORDS = 80
# Classificare o estrarre da un documento lungo resta un task semplice: la
# lunghezza pesa 5 volte meno (regressione dal primo run reale con n8n).
SIMPLE_KIND_LENGTH_FACTOR = 5
# L'intento sta nell'istruzione, non nel documento allegato: le parole chiave
# del TIPO di task si cercano solo qui (i dati sensibili invece ovunque).
INTENT_WINDOW = 240


def _first_match(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Match a inizio parola: 'rag' non deve scattare dentro 'paragrafo'."""
    return [k for k in keywords if re.search(r"(?<!\w)" + re.escape(k), text)]


def _position(text: str, keywords: tuple[str, ...]) -> int:
    hits = [m.start() for k in keywords for m in [re.search(r"(?<!\w)" + re.escape(k), text)] if m]
    return min(hits) if hits else -1


def _intent(low: str) -> str:
    """Primo paragrafo, al massimo INTENT_WINDOW caratteri."""
    return low.split("\n\n", 1)[0][:INTENT_WINDOW]


def classify(prompt: str) -> Classification:
    reasons: list[str] = []
    low = prompt.lower()
    intent = _intent(low)

    # se scattano più tipi vince la parola chiave che compare PRIMA:
    # "Classifica questo documento della documentazione…" è una classificazione
    kind = None
    found = [(_position(intent, kws), i, name, kws) for i, (name, kws) in enumerate(
        (("rag_query", RAG_KEYWORDS), ("extraction", EXTRACTION_KEYWORDS),
         ("classification", CLASSIFICATION_KEYWORDS), ("reasoning", REASONING_KEYWORDS)))]
    found = sorted(f for f in found if f[0] >= 0)
    if found:
        _, _, kind, kws = found[0]
        reasons.append(f"{kind}: parole chiave {_first_match(intent, kws)}")

    chars, words = len(prompt), len(prompt.split())
    factor = SIMPLE_KIND_LENGTH_FACTOR if kind in ("classification", "extraction") else 1
    if chars > COMPLEXITY_CHARS * factor or words > COMPLEXITY_WORDS * factor:
        complexity = "high"
        reasons.append(f"prompt lungo ({chars} caratteri, {words} parole)")
        kind = kind or "reasoning"
    else:
        complexity = "low"
        reasons.append(f"prompt breve ({chars} caratteri, {words} parole)")
        kind = kind or "classification"

    sensitive_kw = _first_match(low, SENSITIVE_KEYWORDS)
    pii = [p.pattern[:24] for p in PII_PATTERNS if p.search(prompt)]
    sensitive = bool(sensitive_kw or pii)
    if sensitive_kw:
        reasons.append(f"dato sensibile: parole chiave {sensitive_kw}")
    if pii:
        reasons.append(f"dato sensibile: {len(pii)} pattern PII")

    return Classification(kind=kind, complexity=complexity, sensitive=sensitive, reasons=tuple(reasons),
                          keyword_hit=bool(found))


def decide_route(prompt: str, context: RoutingContext | None = None,
                 catalog: ModelCatalog | None = None) -> RouteDecision:
    ctx = context or RoutingContext()
    cat = catalog or ModelCatalog()
    c = classify(prompt)

    rules: list[str] = []
    if c.sensitive:
        rules.append("data_residency")
    if ctx.local_only:
        rules.append("local_only")
    if ctx.budget_remaining_eur is not None and ctx.budget_remaining_eur <= ctx.budget_guard_eur:
        rules.append("budget_guard")
    cloud_allowed = not rules

    def decision(route: str, model: str, fallbacks: tuple[str, ...], reason: str) -> RouteDecision:
        local_route = route != ROUTE_CLOUD
        return RouteDecision(
            route=route, model=model, fallbacks=fallbacks,
            escalation=cat.cloud if (local_route and cloud_allowed and route == ROUTE_LOCAL) else None,
            estimated_cost_class="near_zero" if local_route else "metered",
            cloud_allowed=cloud_allowed, reason=reason, rules=tuple(rules), classification=c,
        )

    if c.kind == "rag_query":
        rules.append("knowledge_base")
        return decision(ROUTE_LOCAL_RAG, cat.rag, (), "domanda sulla knowledge base: RAG locale, i documenti non escono")

    if c.complexity == "high" and cloud_allowed:
        rules.append("complexity")
        return decision(ROUTE_CLOUD, cat.cloud, (cat.local,),
                        "task complesso: cloud, con fallback locale (niente lock-in)")

    if c.complexity == "high":
        why = {"data_residency": "dato sensibile", "local_only": "modalità local-only",
               "budget_guard": "budget cloud sotto soglia"}[rules[0]]
        return decision(ROUTE_LOCAL, cat.local, (), f"task complesso ma {why}: resta in locale")

    return decision(ROUTE_LOCAL, cat.local, (), "task semplice e ripetitivo: modello locale")


# Descrizioni delle rotte per l'advisor (Rizzo Flow / Open-Jev).
# V1: la prima versione. Default: v2, scelta sul set DEV (benchmarks/run_router_tuning.py)
# e poi misurata una volta sul TEST: Rizzo Flow 66% → 78% di rotte giuste.
ROUTE_DESCRIPTIONS_V1 = {
    ROUTE_LOCAL: "local small model: simple, repetitive, short tasks (classify, extract, summarize)",
    ROUTE_CLOUD: "cloud large model: complex multi-step reasoning, design, long analysis",
    ROUTE_LOCAL_RAG: "local retrieval over internal docs: questions about the repository, runbooks, procedures",
}
ROUTE_DESCRIPTIONS = {
    ROUTE_LOCAL: "small local model: short, repetitive or mechanical tasks — classify, label, translate, extract fields, "
                 "reformat, check a value, summarize a short text. Fast and almost free.",
    ROUTE_CLOUD: "large cloud model: open-ended reasoning — compare options, design, plan, diagnose, assess risks, write "
                 "a strategy or a proof. Use it whenever the answer needs real thinking, even if the question is short.",
    ROUTE_LOCAL_RAG: "local search over OUR internal documentation: architecture, runbook, ADRs, configuration, ports and "
                     "procedures of this project. Use it when the question asks how WE do things or about our own system.",
}


def reroute(base: RouteDecision, route: str, catalog: ModelCatalog | None = None) -> RouteDecision:
    """Ricostruisce la decisione su `route` scelta da un advisor, SENZA mai
    violare le regole dure già applicate in `base`."""
    cat = catalog or ModelCatalog()
    if route == base.route:
        return base
    if route == ROUTE_CLOUD and not base.cloud_allowed:
        raise ValueError(f"cloud vietato dalle regole {list(base.rules)}")
    rules = (*base.rules, "advisor")
    if route == ROUTE_CLOUD:
        return RouteDecision(route, cat.cloud, (cat.local,), None, "metered", True,
                             "scelto dall'advisor: cloud, con fallback locale", rules, base.classification)
    if route == ROUTE_LOCAL_RAG:
        return RouteDecision(route, cat.rag, (), None, "near_zero", base.cloud_allowed,
                             "scelto dall'advisor: RAG locale", rules, base.classification)
    if route == ROUTE_LOCAL:
        return RouteDecision(route, cat.local, (), cat.cloud if base.cloud_allowed else None, "near_zero",
                             base.cloud_allowed, "scelto dall'advisor: modello locale", rules, base.classification)
    raise ValueError(f"rotta sconosciuta: {route}")

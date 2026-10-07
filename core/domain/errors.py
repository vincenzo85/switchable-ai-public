"""Eccezioni di dominio.

Regola (vedi DEFINITION_OF_DONE.md): un adapter non deve mai lasciar
propagare le proprie eccezioni infrastrutturali (es. quelle di una libreria
HTTP o di un driver DB) oltre il proprio confine — le cattura e le mappa su
un'eccezione di dominio definita qui.
"""
from __future__ import annotations


class DomainError(Exception):
    """Classe base per tutte le eccezioni di dominio di questo progetto."""


class NotFoundError(DomainError):
    """Una entità richiesta non esiste."""


class ProviderError(DomainError):
    """Un provider LLM non ha risposto (rete, chiave mancante, 5xx, rate limit)."""


class ProviderTimeout(ProviderError):
    """Il provider ha superato il budget di latenza: turbolenza ⇒ fallback."""


class IndexNotReady(DomainError):
    """L'indice RAG non esiste ancora (va costruito con `rag-build`)."""

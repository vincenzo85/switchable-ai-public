"""Porte: i contratti che il core dichiara e gli adapter implementano.

Il core conosce SOLO queste interfacce. Quale motore c'è dietro (Ollama,
LiteLLM, vLLM, cloud, Langfuse, Prometheus, hnswlib…) lo decide
`app/composition.py`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from core.domain.models import CallRecord, CompressionResult, LLMResult, Source, Trace


class LLMPort(ABC):
    @abstractmethod
    def complete(self, model: str, prompt: str, *, max_tokens: int | None = None,
                 timeout_s: float | None = None) -> LLMResult:
        """Solleva ProviderError / ProviderTimeout, mai eccezioni di libreria."""


class EmbedderPort(ABC):
    dim: int

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Vettore normalizzato (norma 1) di un DOCUMENTO."""

    def embed_query(self, text: str) -> list[float]:
        """Vettore di una DOMANDA. Alcuni modelli (nomic, e5, bge) distinguono
        domanda e documento con prefissi di task; di default sono uguali."""
        return self.embed(text)


class VectorIndexPort(ABC):
    @abstractmethod
    def build(self, items: Sequence[tuple[str, str]], vectors: Sequence[list[float]]) -> int:
        """items = (path, chunk). Sovrascrive l'indice. Ritorna il numero di chunk."""

    @abstractmethod
    def search(self, vector: list[float], top_k: int) -> list[Source]:
        """Ordinati per score decrescente. IndexNotReady se l'indice manca."""


class DocumentSourcePort(ABC):
    @abstractmethod
    def documents(self) -> Iterable[tuple[str, str]]:
        """(path, testo) dei documenti da indicizzare."""

    @abstractmethod
    def add(self, name: str, text: str) -> str:
        """Aggiunge un documento alla knowledge base, ritorna il path."""


class CostLedgerPort(ABC):
    @abstractmethod
    def record(self, rec: CallRecord) -> None: ...

    @abstractmethod
    def records(self) -> list[CallRecord]: ...


class TracerPort(ABC):
    @abstractmethod
    def trace(self, trace: Trace, record: CallRecord) -> None:
        """Non deve MAI far fallire la richiesta: errori assorbiti dall'adapter."""


class TraceStorePort(TracerPort):
    @abstractmethod
    def traces(self) -> list[Trace]: ...


class MetricsPort(ABC):
    @abstractmethod
    def observe(self, rec: CallRecord) -> None: ...


class PromptCompressorPort(ABC):
    name: str

    @abstractmethod
    def compress(self, text: str, *, keep_ratio: float, question: str = "") -> CompressionResult: ...


class DatasetSinkPort(ABC):
    @abstractmethod
    def write(self, name: str, rows: list[dict]) -> str:
        """Scrive il dataset, ritorna dove."""


class ClockPort(ABC):
    @abstractmethod
    def now(self) -> float:
        """Epoch seconds."""


class IdGeneratorPort(ABC):
    @abstractmethod
    def new_id(self) -> str: ...


class RouteAdvisorPort(ABC):
    """Un modello che sceglie tra candidati e ritorna probabilità
    (contratto /v1/systemone di Rizzo Flow e Open-Jev)."""
    name: str

    @abstractmethod
    def choose(self, state: str, question: str,
               candidates: Sequence[tuple[str, str]]) -> tuple[dict[str, float], int]:
        """Ritorna ({id: probabilità}, latenza_ms). ProviderError se giù."""

"""Composition root: l'UNICO posto che sceglie gli adapter concreti.

Tutto è configurabile da variabili d'ambiente (vedi .env.example). Due
modalità per la rotta dei modelli:
- diretta (default): ollama/ → Ollama, vllm/ → server vLLM, cloud/ → API
  OpenAI-compatible se c'è la chiave, altrimenti ProviderError immediato
  (= fallback locale reale, la tesi del talk);
- gateway (SAI_GATEWAY_URL): tutte le rotte passano da LiteLLM con gli
  alias di infra/litellm.yaml; il gateway fa anche il suo fallback e noi lo
  rileviamo dal campo `model` della risposta.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from adapters.compression.extractive import ExtractiveCompressor
from adapters.docs.filesystem import FileSystemDocuments
from adapters.embedding.ollama import OllamaEmbedder
from adapters.index.hnsw import HnswIndex
from adapters.llm.providers import OllamaLLM, OpenAICompatLLM, PrefixRouterLLM, UnavailableLLM
from adapters.observability.sinks import FanoutTracer, LangfuseTracer, PrometheusMetrics
from adapters.storage.jsonl import JsonlDatasetSink, JsonlLedger, JsonlTraceStore
from adapters.system import FlightIds, SystemClock
from core.domain.models import ModelCatalog
from core.ports import LLMPort
from adapters.llm.systemone import ENGINES, SystemOneAdvisor
from core.use_cases.advisor import AdvisedRouter
from core.use_cases.execute_request import Budget, ExecuteRequest
from core.use_cases.flywheel import ExportFlywheel
from core.use_cases.ingest import IngestDocument
from core.use_cases.rag import BuildRagIndex, RetrieveContext
from core.use_cases.report import CostReport
from core.use_cases.stress import RunStressTest

ROOT = Path(__file__).resolve().parents[1]

GATEWAY_ALIASES = {"local": "fast-local", "cloud": "smart-cloud", "rag": "rag-local", "vllm": "fast-vllm"}


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _flag(name: str) -> bool:
    return _env(name).lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(_env("SAI_DATA_DIR", str(ROOT / "data"))))
    rag_index_dir: Path | None = field(default_factory=lambda: Path(_env("SAI_RAG_INDEX_DIR")) if _env("SAI_RAG_INDEX_DIR") else None)
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_BASE_URL", "http://localhost:11434"))
    local_model: str = field(default_factory=lambda: _env("SAI_LOCAL_MODEL", "ollama/qwen2.5:7b"))
    cloud_model: str = field(default_factory=lambda: _env("SAI_CLOUD_MODEL", "cloud/gpt-4o"))
    rag_model: str = field(default_factory=lambda: _env("SAI_RAG_MODEL", "ollama/qwen2.5:7b"))
    gateway_url: str = field(default_factory=lambda: _env("SAI_GATEWAY_URL"))
    gateway_key: str = field(default_factory=lambda: _env("SAI_GATEWAY_KEY"))
    openai_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_url: str = field(default_factory=lambda: _env("OPENAI_BASE_URL", "https://api.openai.com"))
    vllm_url: str = field(default_factory=lambda: _env("VLLM_BASE_URL"))
    embed_model: str = field(default_factory=lambda: _env("SAI_EMBED_MODEL", "nomic-embed-text"))
    embed_dim: int = field(default_factory=lambda: int(_env("SAI_EMBED_DIM", "768")))
    budget_eur: float = field(default_factory=lambda: float(_env("SAI_BUDGET_EUR", "0") or 0))
    budget_guard_eur: float = field(default_factory=lambda: float(_env("SAI_BUDGET_GUARD_EUR", "0") or 0))
    local_only: bool = field(default_factory=lambda: _flag("SAI_LOCAL_ONLY"))
    cloud_timeout_s: float = field(default_factory=lambda: float(_env("SAI_CLOUD_TIMEOUT_S", "60")))
    compress: str = field(default_factory=lambda: _env("SAI_COMPRESS", "extractive"))
    compress_threshold: int = field(default_factory=lambda: int(_env("SAI_COMPRESS_THRESHOLD", "1500")))
    advisor: str = field(default_factory=lambda: _env("SAI_ADVISOR"))          # rizzo | openjev | ""
    advisor_mode: str = field(default_factory=lambda: _env("SAI_ADVISOR_MODE", "shadow"))
    advisor_min_p: float = field(default_factory=lambda: float(_env("SAI_ADVISOR_MIN_P", "0.6")))
    advisor_url: str = field(default_factory=lambda: _env("SAI_ADVISOR_URL"))  # override endpoint
    advisor_both_orders: bool = field(default_factory=lambda: _flag("SAI_ADVISOR_BOTH_ORDERS"))
    langfuse_host: str = field(default_factory=lambda: _env("LANGFUSE_HOST"))
    langfuse_pk: str = field(default_factory=lambda: _env("LANGFUSE_PUBLIC_KEY"))
    langfuse_sk: str = field(default_factory=lambda: _env("LANGFUSE_SECRET_KEY"))

    @property
    def catalog(self) -> ModelCatalog:
        return ModelCatalog(local=self.local_model, cloud=self.cloud_model, rag=self.rag_model)


def build_llm(s: Settings) -> LLMPort:
    if s.gateway_url:
        cat = s.catalog

        def alias(model: str) -> str:
            if model == cat.cloud:
                return GATEWAY_ALIASES["cloud"]
            if model.startswith("vllm/"):
                return GATEWAY_ALIASES["vllm"]
            return GATEWAY_ALIASES["rag"] if model == cat.rag and model != cat.local else GATEWAY_ALIASES["local"]

        def served_as(requested: str, served: str) -> str:
            # LiteLLM riporta il modello che ha risposto davvero: se chiedevamo
            # il cloud e ha risposto un locale, è un fallback del gateway.
            if requested.startswith("cloud/") and served and not any(
                    k in served for k in ("gpt", "claude", "deepseek", "smart-cloud", "o1", "o3")):
                return cat.local
            return requested

        gw = OpenAICompatLLM(s.gateway_url, s.gateway_key, model_name=alias, served_as=served_as)
        return PrefixRouterLLM({"ollama/": gw, "vllm/": gw, "cloud/": gw})

    routes: dict[str, LLMPort] = {"ollama/": OllamaLLM(s.ollama_url)}
    routes["vllm/"] = (OpenAICompatLLM(s.vllm_url, model_name=lambda m: m.split("/", 1)[1])
                       if s.vllm_url else UnavailableLLM("VLLM_BASE_URL non configurato"))
    routes["cloud/"] = (OpenAICompatLLM(s.openai_url, s.openai_key)
                        if s.openai_key else UnavailableLLM("nessuna chiave cloud (OPENAI_API_KEY vuota)"))
    return PrefixRouterLLM(routes)


def build_advisor(s: Settings) -> AdvisedRouter | None:
    """SAI_ADVISOR=rizzo|openjev attiva il router appreso; SAI_ADVISOR_MODE
    sceglie shadow (default, solo misura) o active."""
    if not s.advisor or s.advisor_mode == "off":
        return None
    endpoint, model = ENGINES.get(s.advisor, ("", s.advisor))
    port = SystemOneAdvisor(s.advisor, s.advisor_url or endpoint, model)
    return AdvisedRouter(port, mode=s.advisor_mode, min_confidence=s.advisor_min_p, catalog=s.catalog,
                         both_orders=s.advisor_both_orders)


class Container:
    """Grafo degli oggetti, costruito una volta per processo."""

    def __init__(self, settings: Settings | None = None, llm: LLMPort | None = None, embedder=None):
        s = self.settings = settings or Settings()
        d = s.data_dir
        self.ledger = JsonlLedger(d / "calls.jsonl")
        self.traces = JsonlTraceStore(d / "traces.jsonl")
        self.metrics = PrometheusMetrics()
        self.langfuse = (LangfuseTracer(s.langfuse_host, s.langfuse_pk, s.langfuse_sk)
                         if s.langfuse_host and s.langfuse_pk and s.langfuse_sk else None)
        tracer = FanoutTracer(self.traces, self.langfuse) if self.langfuse else self.traces
        self.llm = llm or build_llm(s)
        self.embedder = embedder or OllamaEmbedder(s.embed_model, s.ollama_url, s.embed_dim)
        self.index = HnswIndex(s.rag_index_dir or d / "rag_index", self.embedder.dim)
        self.docs = FileSystemDocuments(
            roots=[ROOT / "README.md", ROOT / "MISSION.md", ROOT / "docs", ROOT / "wiki", ROOT / "infra"],
            kb_dir=d / "kb", git_repo=ROOT, base=ROOT)
        self.retriever = RetrieveContext(self.embedder, self.index, top_k=3)
        self.build_index = BuildRagIndex(self.docs, self.embedder, self.index)
        budget = Budget(s.budget_eur, s.budget_guard_eur) if s.budget_eur > 0 else None
        self.execute = ExecuteRequest(
            llm=self.llm, ledger=self.ledger, clock=SystemClock(), ids=FlightIds(), catalog=s.catalog,
            tracer=tracer, metrics=self.metrics, retriever=self.retriever,
            compressor=ExtractiveCompressor() if s.compress == "extractive" else None,
            compress_threshold_tokens=s.compress_threshold, budget=budget, local_only=s.local_only,
            cloud_timeout_s=s.cloud_timeout_s, advisor=build_advisor(s))
        self.report = CostReport(self.ledger)
        self.stress = RunStressTest(self.execute)
        self.flywheel = ExportFlywheel(self.traces, JsonlDatasetSink(d / "flywheel"))
        self.ingest = IngestDocument(self.execute, self.docs, self.build_index)

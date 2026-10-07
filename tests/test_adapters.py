"""Adapter reali contro un server HTTP finto: protocollo giusto, token dal
motore, errori di rete mappati su eccezioni di dominio."""
import json

import pytest

from adapters.compression.extractive import ExtractiveCompressor, NoCompressor
from adapters.docs.filesystem import FileSystemDocuments
from adapters.embedding.ollama import OllamaEmbedder
from adapters.index.hnsw import HnswIndex
from adapters.llm.providers import OllamaLLM, OpenAICompatLLM, PrefixRouterLLM, UnavailableLLM
from adapters.memory import HashEmbedder
from adapters.observability.sinks import LangfuseTracer, PrometheusMetrics
from adapters.storage.jsonl import JsonlDatasetSink, JsonlLedger, JsonlTraceStore
from core.domain.errors import IndexNotReady, ProviderError, ProviderTimeout
from core.domain.models import CallRecord, Trace


def rec(**kw):
    base = dict(ts=1_790_000_000.0, request_id="flight-1", route="local", model="ollama/qwen2.5:7b",
                kind="classification", tokens_in=10, tokens_out=2, latency_ms=300, cost_eur=0.1,
                cost_if_cloud_eur=1.0)
    return CallRecord(**{**base, **kw})


# --- LLM ------------------------------------------------------------------------

def test_ollama_counts_tokens_from_engine(stub):
    r = OllamaLLM(stub.url).complete("ollama/qwen2.5:7b", "ciao", max_tokens=5)
    path, body, _ = stub.requests[-1]
    assert path == "/api/generate" and body["model"] == "qwen2.5:7b"
    assert body["options"]["num_predict"] == 5
    assert (r.tokens_in, r.tokens_out, r.model) == (42, 3, "ollama/qwen2.5:7b")


def test_http_error_becomes_provider_error(stub):
    stub.status = 429
    with pytest.raises(ProviderError, match="429"):
        OllamaLLM(stub.url).complete("ollama/x", "ciao")


def test_slow_provider_becomes_provider_timeout(stub):
    stub.delay_s = 1.0
    with pytest.raises(ProviderTimeout):
        OpenAICompatLLM(stub.url).complete("cloud/gpt-4o", "ciao", timeout_s=0.2)


def test_unreachable_provider_is_provider_error():
    with pytest.raises(ProviderError):
        OllamaLLM("http://127.0.0.1:9").complete("ollama/x", "ciao", timeout_s=1)


def test_openai_compat_uses_alias_and_bearer(stub):
    llm = OpenAICompatLLM(stub.url, "sk-test", model_name=lambda m: "smart-cloud")
    r = llm.complete("cloud/gpt-4o", "ciao")
    _, body, headers = stub.requests[-1]
    assert body["model"] == "smart-cloud" and headers["Authorization"] == "Bearer sk-test"
    assert (r.tokens_in, r.tokens_out) == (11, 5)


def test_gateway_side_fallback_is_reported_as_local_model(stub):
    """LiteLLM ha fatto fallback da solo: lo vediamo dal campo model."""
    from app.composition import Settings, build_llm
    stub.chat_model_served = "ollama/qwen2.5:7b"
    s = Settings(gateway_url=stub.url)
    r = build_llm(s).complete(s.cloud_model, "ciao")
    assert r.model == s.local_model
    assert stub.requests[-1][1]["model"] == "smart-cloud"


def test_prefix_router_and_unavailable():
    llm = PrefixRouterLLM({"cloud/": UnavailableLLM("nessuna chiave")})
    with pytest.raises(ProviderError, match="nessuna chiave"):
        llm.complete("cloud/gpt-4o", "x")
    with pytest.raises(ProviderError, match="nessun provider"):
        llm.complete("altro/x", "x")


# --- embedding + index ------------------------------------------------------------

def test_ollama_embedder_normalizes(stub):
    v = OllamaEmbedder(base_url=stub.url, dim=4).embed("ciao")
    assert abs(sum(x * x for x in v) - 1) < 1e-6


def test_nomic_embedder_uses_task_prefixes(stub):
    e = OllamaEmbedder(base_url=stub.url, dim=4)
    e.embed("doc"); e.embed_query("domanda")
    sent = [b["input"] for p, b, _ in stub.requests if p == "/api/embed"]
    assert sent == ["search_document: doc", "search_query: domanda"]


def test_embedder_without_known_prefixes_sends_plain_text(stub):
    OllamaEmbedder(model="bge-m3", base_url=stub.url, dim=4).embed_query("x")
    assert stub.requests[-1][1]["input"] == "x"


def test_hnsw_roundtrip_and_ordering(tmp_path):
    emb = HashEmbedder()
    idx = HnswIndex(tmp_path / "idx", emb.dim)
    items = [("a.md", "fallback locale ollama quando il cloud non risponde"),
             ("b.md", "costo energia ammortamento gpu")]
    assert idx.build(items, [emb.embed(c) for _, c in items]) == 2
    hits = HnswIndex(tmp_path / "idx", emb.dim).search(emb.embed("fallback ollama cloud"), 2)
    assert hits[0].path == "a.md" and hits[0].score >= hits[1].score


def test_hnsw_missing_index_is_domain_error(tmp_path):
    with pytest.raises(IndexNotReady):
        HnswIndex(tmp_path / "nope", 8).search([0.0] * 8, 1)


# --- storage --------------------------------------------------------------------

def test_jsonl_ledger_and_traces_roundtrip(tmp_path):
    led = JsonlLedger(tmp_path / "calls.jsonl")
    r = rec(rules=("data_residency",))
    led.record(r)
    assert led.records() == [r]
    ts = JsonlTraceStore(tmp_path / "t.jsonl")
    t = Trace("flight-1", 1.0, "p", "o", "local", "ollama/x", "classification", False, False)
    ts.trace(t, r)
    assert ts.traces() == [t]


def test_dataset_sink_writes_jsonl(tmp_path):
    path = JsonlDatasetSink(tmp_path).write("sft", [{"a": 1}, {"b": 2}])
    assert [json.loads(l) for l in open(path)] == [{"a": 1}, {"b": 2}]


# --- docs -----------------------------------------------------------------------

def test_filesystem_docs_reads_roots_kb_and_adds(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "adr-001.md").write_text("# ADR 1")
    fs = FileSystemDocuments([tmp_path / "docs"], kb_dir=tmp_path / "kb", base=tmp_path)
    rel = fs.add("../../etc/passwd", "tentativo di path traversal")
    assert rel == "kb/passwd.md"
    paths = [p for p, _ in fs.documents()]
    assert paths == ["docs/adr-001.md", "kb/passwd.md"]


# --- compressione -----------------------------------------------------------------

def test_extractive_compression_keeps_question_relevant_sentence():
    text = ("Il meteo di oggi è variabile. " * 8 + "Il fallback del gateway usa il modello locale. "
            + "Le riunioni sono il martedì. " * 8)
    r = ExtractiveCompressor().compress(text, keep_ratio=0.3, question="come funziona il fallback del gateway?")
    assert "fallback del gateway" in r.text
    assert r.tokens_after < r.tokens_before and r.saved > 0


def test_extractive_preserves_stable_prefix_for_prompt_caching():
    prefix = "SYSTEM: sei un assistente. Regole fisse. "
    text = prefix + "Frase uno importante. Frase due ripetuta. Frase due ripetuta. Frase tre."
    r = ExtractiveCompressor(stable_prefix_chars=len(prefix)).compress(text, keep_ratio=0.5)
    assert r.text.startswith(prefix)


def test_no_compressor_is_identity():
    assert NoCompressor().compress("abc def", keep_ratio=0.1).text == "abc def"


# --- osservabilità ----------------------------------------------------------------

def test_prometheus_exposes_route_cost_and_violations():
    m = PrometheusMetrics()
    m.observe(rec(fallback=True, rules=("budget_guard",)))
    out = m.exposition().decode()
    assert 'sai_requests_total{model="ollama/qwen2.5:7b",route="local"} 1.0' in out
    assert "sai_fallbacks_total" in out and "sai_budget_guard_total 1.0" in out
    assert "sai_residency_violations_total 0.0" in out


def test_langfuse_sends_trace_and_generation_without_sensitive_content(stub):
    lf = LangfuseTracer(stub.url, "pk-lf", "sk-lf")
    t = Trace("flight-9", 1.0, "codice fiscale RSSMRA80A01H501U", "ok", "local", "ollama/x", "reasoning", True, False)
    lf.trace(t, rec(request_id="flight-9", sensitive=True))
    path, body, headers = stub.requests[-1]
    assert path == "/api/public/ingestion" and headers["Authorization"].startswith("Basic ")
    types = [e["type"] for e in body["batch"]]
    assert types == ["trace-create", "generation-create"]
    assert "RSSMRA" not in json.dumps(body), "il dato sensibile non deve lasciare la macchina"
    assert body["batch"][1]["body"]["usage"]["input"] == 10


def test_langfuse_down_is_swallowed():
    lf = LangfuseTracer("http://127.0.0.1:9", "pk", "sk", timeout_s=0.5)
    lf.trace(Trace("x", 1.0, "p", "o", "local", "m", "k", False, False), rec())
    assert lf.last_error


# --- advisor /v1/systemone ----------------------------------------------------------

def test_systemone_advisor_speaks_the_contract(stub):
    from adapters.llm.systemone import SystemOneAdvisor
    stub.systemone_probs = {"local": 0.8, "cloud": 0.2}
    adv = SystemOneAdvisor("rizzo", stub.url + "/v1/systemone", "rizzo-latest")
    probs, ms = adv.choose("Request: x", "Which route?", [("local", "piccolo"), ("cloud", "grande")])
    _, body, _ = stub.requests[-1]
    assert body["model"] == "rizzo-latest"
    assert body["questions"]["decision"]["type"] == "choice"
    assert body["questions"]["decision"]["criteria"] == {"local": "piccolo", "cloud": "grande"}
    assert probs == {"local": 0.8, "cloud": 0.2} and ms >= 0


def test_systemone_rejects_ids_not_offered(stub):
    from adapters.llm.systemone import SystemOneAdvisor
    stub.systemone_probs = {"local": 0.5, "banana": 0.5}
    adv = SystemOneAdvisor("openjev", stub.url + "/v1/systemone", "open-jev")
    with pytest.raises(ProviderError, match="candidati"):
        adv.choose("s", "q", [("local", "a"), ("cloud", "b")])


def test_systemone_down_is_provider_error():
    from adapters.llm.systemone import SystemOneAdvisor
    with pytest.raises(ProviderError):
        SystemOneAdvisor("rizzo", "http://127.0.0.1:9/v1/systemone", "rizzo-latest", 0.5).choose(
            "s", "q", [("local", "a")])


def test_systemone_unknown_engine():
    from adapters.llm.systemone import SystemOneAdvisor
    with pytest.raises(ValueError):
        SystemOneAdvisor.engine("gpt-router")


def test_prometheus_tracks_advisor_agreement():
    m = PrometheusMetrics()
    m.observe(rec(advisor_engine="rizzo", advisor_choice="local", advisor_agreed=True, advisor_latency_ms=72))
    out = m.exposition().decode()
    assert 'sai_advisor_decisions_total{agreed="true",applied="false",engine="rizzo"} 1.0' in out
    assert "sai_advisor_latency_ms_bucket" in out


# --- cloud simulato per lo stress test ------------------------------------------------

def test_simulated_cloud_prices_as_cloud_and_injects_scheduled_turbulence():
    from adapters.llm.simulated_cloud import SimulatedCloudLLM
    from adapters.memory import FakeLLM
    slept = []
    inner = FakeLLM(default_reply="risposta")
    sim = SimulatedCloudLLM(inner, "ollama/qwen2.5:7b", base_delay_ms=100, slow_from=1, slow_to=2,
                            slow_delay_ms=(5000, 5000), sleep=slept.append)
    r = sim.complete("cloud/gpt-4o", "ciao", timeout_s=2)
    assert r.model == "cloud/gpt-4o" and inner.calls[-1][0] == "ollama/qwen2.5:7b"
    assert r.latency_ms >= 100
    with pytest.raises(ProviderTimeout):
        sim.complete("cloud/gpt-4o", "ciao", timeout_s=2)
    assert slept[-1] == 2 and sim.timeouts == 1
    assert sim.complete("cloud/gpt-4o", "ciao", timeout_s=2).text == "risposta"

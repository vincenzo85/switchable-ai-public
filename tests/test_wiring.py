"""Test di cablaggio (DoD, "test di scollegamento"): la composition root,
la CLI, l'API e i tool MCP usano DAVVERO i casi d'uso. Se si scollega un
pezzo, qui si diventa rossi."""
import json

import pytest
from fastapi.testclient import TestClient

from adapters.memory import FakeLLM, HashEmbedder
from app import api
from app.composition import Container, Settings, build_llm
from app.main import main as cli
from adapters.mcp.server import build_tools


@pytest.fixture
def container(tmp_path):
    s = Settings(data_dir=tmp_path, compress="extractive", compress_threshold=50)
    return Container(s, llm=FakeLLM({"cloud/": {"fail": True, "error": "nessuna chiave"}},
                                    default_reply="accesso"), embedder=HashEmbedder())


def test_container_executes_and_persists(container, tmp_path):
    res = container.execute.execute("Classifica: login rotto")
    assert res.record.route == "local"
    assert (tmp_path / "calls.jsonl").exists() and (tmp_path / "traces.jsonl").exists()
    assert b"sai_requests_total" in container.metrics.exposition()


def test_container_rag_end_to_end(container):
    info = container.build_index.execute()
    assert info["chunks"] > 0
    res = container.execute.execute("Nella documentazione, cosa contiene il git log del repository?")
    assert res.decision.route == "local_rag" and res.sources


def test_direct_mode_without_key_falls_back_for_real(tmp_path):
    """Composizione reale (niente FakeLLM): senza chiave il cloud dà
    ProviderError subito, senza toccare la rete."""
    from core.domain.errors import ProviderError
    llm = build_llm(Settings(openai_key="", vllm_url=""))
    with pytest.raises(ProviderError, match="nessuna chiave"):
        llm.complete("cloud/gpt-4o", "x")
    with pytest.raises(ProviderError, match="VLLM_BASE_URL"):
        llm.complete("vllm/qwen", "x")


def test_cli_route_prints_decision(capsys):
    assert cli(["route", "Classifica: reclamo o richiesta info?"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "local" and out["model"].startswith("ollama/")


def test_cli_demo_dry_run_shows_four_routes(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("SAI_DATA_DIR", str(tmp_path))
    assert cli(["demo", "--dry-run"]) == 0
    out = capsys.readouterr().out
    routes = [json.loads("{" + b.split("{", 1)[1].rsplit("}", 1)[0] + "}")["route"]
              for b in out.split("════")[2::2]]
    assert routes == ["local", "cloud", "local_rag", "local"]


@pytest.fixture
def client(container, monkeypatch):
    api.app.dependency_overrides[api.container] = lambda: container
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_api_openai_compatible_chat(client):
    r = client.post("/v1/chat/completions", json={"model": "qualsiasi",
                                                  "messages": [{"role": "user", "content": "Classifica: login rotto"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "accesso"
    assert body["x_switchable"]["route"] == "local"


def test_api_cloud_fallback_visible(client):
    r = client.post("/v1/ask", json={"prompt": "Analizza i trade-off di questa architettura distribuita. " * 20})
    rec = r.json()["record"]
    assert rec["fallback"] and "nessuna chiave" in rec["fallback_reason"]


def test_api_metrics_and_report(client):
    client.post("/v1/ask", json={"prompt": "Classifica: bug?"})
    assert "sai_requests_total" in client.get("/metrics").text
    assert client.get("/v1/report").json()["calls"] == 1


def test_api_n8n_webhook_ingests(client, container):
    r = client.post("/webhook/n8n/document", json={"name": "adr-007.md", "text": "# ADR 7\nUsiamo LiteLLM come gateway."})
    assert r.status_code == 200
    body = r.json()
    assert body["document"].endswith("adr-007.md") and body["index"]["chunks"] > 0
    assert body["data_residency_violations"] == 0


def test_api_stress_endpoint(client):
    rep = client.post("/v1/stress", json={"n": 10, "seed": 3}).json()
    assert rep["total_tasks"] == 10 and rep["data_residency_violations"] == 0


def test_mcp_tools_are_wired(container):
    tools = build_tools(container)
    assert set(tools) == {"route_prompt", "ask", "rag_search", "cost_report", "stress_test", "flywheel_export"}
    assert tools["route_prompt"]("Classifica: bug?")["route"] == "local"
    tools["ask"]("Classifica: bug?")
    assert tools["cost_report"]()["calls"] == 1
    assert "error" in tools["rag_search"]("x")        # indice non costruito: errore pulito
    assert tools["flywheel_export"]()["exported"] == 1


def test_mcp_server_registers_tools(container):
    import asyncio
    from adapters.mcp.server import build_server
    names = {t.name for t in asyncio.run(build_server(container).list_tools())}
    assert "stress_test" in names and "flywheel_export" in names


def test_advisor_is_off_by_default_and_activatable(tmp_path, stub):
    from app.composition import build_advisor
    assert build_advisor(Settings(advisor="")) is None
    assert build_advisor(Settings(advisor="rizzo", advisor_mode="off")) is None
    stub.systemone_probs = {"local": 0.1, "cloud": 0.9, "local_rag": 0.0}
    s = Settings(data_dir=tmp_path, advisor="rizzo", advisor_mode="active",
                 advisor_url=stub.url + "/v1/systemone")
    c = Container(s, llm=FakeLLM(), embedder=HashEmbedder())
    rec = c.execute.execute("Classifica: login rotto").record
    assert rec.advisor_engine == "rizzo" and rec.advisor_applied
    assert rec.model.startswith("cloud/")
    [(path, body, _)] = stub.requests
    assert path == "/v1/systemone" and body["model"] == "rizzo-latest"

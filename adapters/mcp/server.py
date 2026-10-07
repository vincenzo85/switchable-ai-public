"""Server MCP (stdio): la "radio di bordo".

Espone pochi tool, con descrizioni corte: le definizioni dei tool viaggiano
nel contesto di ogni richiesta dell'agente, e definizioni verbose costano
token (Alier Forment et al. 2026, MCP vs CLI).
"""
from __future__ import annotations

try:                                   # mcp >= 2: FastMCP rinominato in MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:                    # mcp 1.x
    from mcp.server.fastmcp import FastMCP


def build_tools(c) -> dict:
    """Funzioni pure sul container: testabili senza avviare il server."""

    def route_prompt(prompt: str) -> dict:
        return c.execute.decide(prompt).to_dict()

    def ask(prompt: str, max_tokens: int = 300) -> dict:
        return c.execute.execute(prompt, max_tokens=max_tokens).to_dict()

    def rag_search(question: str) -> dict:
        try:
            return {"results": [s.to_dict() for s in c.retriever.retrieve(question)]}
        except Exception as e:  # noqa: BLE001 — risposta tool, non crash
            return {"error": str(e)}

    def cost_report() -> dict:
        return c.report.execute()

    def stress_test(n: int = 20, seed: int = 42) -> dict:
        from core.use_cases.stress import landing_scenario
        rep = c.stress.execute(landing_scenario(n, seed=seed))
        return {k: v for k, v in rep.items() if k != "timeline"}

    def flywheel_export() -> dict:
        return c.flywheel.execute()

    return {f.__name__: f for f in (route_prompt, ask, rag_search, cost_report, stress_test, flywheel_export)}


DESCRIPTIONS = {
    "route_prompt": "Decide la rotta (local/cloud/local_rag) di un prompt, senza eseguirlo.",
    "ask": "Esegue un prompt sulla rotta decisa, con fallback; ritorna testo, costo, rotta.",
    "rag_search": "Cerca nella knowledge base SDLC locale; ritorna chunk e fonti.",
    "cost_report": "Costi, latenze p50/p95, fallback e violazioni di residency dal registro.",
    "stress_test": "Lancia lo stress test di atterraggio su n task e ritorna il riepilogo.",
    "flywheel_export": "Esporta le trace anonimizzate in un dataset di fine-tuning.",
}


def build_server(container) -> FastMCP:
    mcp = FastMCP("switchable-ai")
    for name, fn in build_tools(container).items():
        mcp.tool(name=name, description=DESCRIPTIONS[name])(fn)
    return mcp

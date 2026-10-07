"""Smoke test reale del server MCP: avvia `python -m app.main mcp` in stdio,
fa l'handshake, elenca i tool e ne chiama due. Misura anche quanto pesano
le definizioni dei tool (caratteri inviati al modello a ogni richiesta)."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from _common import save  # noqa: E402


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.main", "mcp"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            size = len(json.dumps([t.model_dump(mode="json", exclude_none=True) for t in tools]))
            print("tool:", [t.name for t in tools], f"· definizioni: {size} caratteri (~{size // 4} token)")
            res = await s.call_tool("route_prompt", {"prompt": "Classifica: login rotto o fattura?"})
            print("route_prompt →", res.content[0].text[:120].replace("\n", " "))
            res = await s.call_tool("cost_report", {})
            print("cost_report →", res.content[0].text[:120].replace("\n", " "))
            save("mcp", {"tools": [t.name for t in tools], "definitions_chars": size,
                         "definitions_tokens_approx": size // 4, "transport": "stdio", "handshake": "ok"})


asyncio.run(main())

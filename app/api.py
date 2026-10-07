"""API HTTP: OpenAI-compatible per le app, webhook per n8n, /metrics per
Prometheus, endpoint di demo per il deck.

"Cambia solo il base_url": un client OpenAI esistente punta qui e il router
decide la rotta (il nome modello richiesto viene ignorato di proposito).
"""
from __future__ import annotations

import time
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from core.domain.errors import DomainError

app = FastAPI(title="switchable_ai", version="0.1.0")
# il deck gira da file:// o da un altro localhost: CORS aperto solo in lettura demo
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


@lru_cache(maxsize=1)
def container():
    from app.composition import Container
    return Container()


class RouteIn(BaseModel):
    prompt: str


class AskIn(BaseModel):
    prompt: str
    max_tokens: int | None = 300


class IngestIn(BaseModel):
    name: str
    text: str


class ChatIn(BaseModel):
    model: str | None = None
    messages: list[dict]
    max_tokens: int | None = None


class StressIn(BaseModel):
    n: int = 20
    seed: int = 42


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics(c=Depends(container)):
    return Response(c.metrics.exposition(), media_type="text/plain; version=0.0.4")


@app.post("/v1/route")
def route(body: RouteIn, c=Depends(container)):
    return c.execute.decide(body.prompt).to_dict()


@app.post("/v1/ask")
def ask(body: AskIn, c=Depends(container)):
    try:
        return c.execute.execute(body.prompt, max_tokens=body.max_tokens).to_dict()
    except DomainError as e:
        raise HTTPException(503, str(e)) from e


@app.post("/v1/chat/completions")
def chat(body: ChatIn, c=Depends(container)):
    prompt = "\n\n".join(str(m.get("content", "")) for m in body.messages if m.get("role") != "system")
    try:
        res = c.execute.execute(prompt, max_tokens=body.max_tokens)
    except DomainError as e:
        raise HTTPException(503, str(e)) from e
    r = res.record
    return {
        "id": r.request_id, "object": "chat.completion", "created": int(r.ts), "model": r.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": res.text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": r.tokens_in, "completion_tokens": r.tokens_out,
                  "total_tokens": r.tokens_in + r.tokens_out},
        "x_switchable": {"route": r.route, "fallback": r.fallback, "rules": list(r.rules), "cost_eur": r.cost_eur},
    }


@app.post("/webhook/n8n/document")
def n8n_document(body: IngestIn, c=Depends(container)):
    try:
        return c.ingest.execute(body.name, body.text)
    except DomainError as e:
        raise HTTPException(503, str(e)) from e


@app.get("/v1/report")
def report(c=Depends(container)):
    return c.report.execute()


@app.post("/v1/stress")
def stress(body: StressIn, c=Depends(container)):
    from core.use_cases.stress import landing_scenario
    t0 = time.monotonic()
    rep = c.stress.execute(landing_scenario(body.n, seed=body.seed))
    rep["wall_s"] = round(time.monotonic() - t0, 2)
    return rep

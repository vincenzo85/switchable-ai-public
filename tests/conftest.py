"""Fixture condivise: un server HTTP finto e locale (stdlib) che recita la
parte di Ollama, di un endpoint OpenAI-compatible e di Langfuse."""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


class StubState:
    def __init__(self):
        self.requests: list[tuple[str, dict, dict]] = []   # (path, json, headers)
        self.status = 200
        self.delay_s = 0.0
        self.chat_model_served = None
        self.reply = "accesso"
        self.systemone_probs = None       # dict id->p, oppure None = uniforme


@pytest.fixture
def stub():
    state = StubState()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            state.requests.append((self.path, data, dict(self.headers)))
            if state.delay_s:
                time.sleep(state.delay_s)
            if state.status != 200:
                return self._send(state.status, {"error": "rate limit"})
            if self.path == "/api/generate":
                return self._send(200, {"response": state.reply, "prompt_eval_count": 42, "eval_count": 3})
            if self.path == "/api/embed":
                text = data["input"]
                return self._send(200, {"embeddings": [[float(len(text) % 7 + 1), 1.0, 0.0, 2.0]]})
            if self.path == "/v1/chat/completions":
                return self._send(200, {"model": state.chat_model_served or data["model"],
                                        "choices": [{"message": {"content": state.reply}}],
                                        "usage": {"prompt_tokens": 11, "completion_tokens": 5}})
            if self.path == "/v1/systemone":
                crit = data["questions"]["decision"]["criteria"]
                probs = state.systemone_probs or {k: 1 / len(crit) for k in crit}
                return self._send(200, {"answers": {"decision": {"probabilities": probs}}})
            if self.path == "/api/public/ingestion":
                return self._send(207, {"successes": [], "errors": []})
            return self._send(404, {"error": "?"})

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    state.url = f"http://127.0.0.1:{srv.server_address[1]}"
    yield state
    srv.shutdown()

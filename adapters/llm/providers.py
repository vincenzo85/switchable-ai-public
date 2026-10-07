"""Adapter LLM reali.

- OllamaLLM: API nativa di Ollama (/api/generate), token contati dal motore.
- OpenAICompatLLM: qualsiasi endpoint /v1/chat/completions — il gateway
  LiteLLM, un server vLLM, o un provider cloud diretto.
- PrefixRouterLLM: smista per prefisso (`ollama/`, `vllm/`, `cloud/`).
- UnavailableLLM: rotta senza credenziali → ProviderError immediato
  (così il fallback si esercita DAVVERO, senza attendere un timeout).
"""
from __future__ import annotations

import time
from typing import Callable

from core.domain.errors import ProviderError
from core.domain.models import LLMResult
from core.ports import LLMPort
from adapters.llm.http import post_json


def _strip_prefix(model: str) -> str:
    return model.split("/", 1)[1] if "/" in model else model


class OllamaLLM(LLMPort):
    def __init__(self, base_url: str = "http://localhost:11434", num_ctx: int = 4096,
                 temperature: float = 0.2, keep_alive: str = "10m"):
        self.base_url, self.num_ctx, self.temperature, self.keep_alive = base_url.rstrip("/"), num_ctx, temperature, keep_alive

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        opts = {"num_ctx": self.num_ctx, "temperature": self.temperature}
        if max_tokens:
            opts["num_predict"] = max_tokens
        t0 = time.monotonic()
        data = post_json(f"{self.base_url}/api/generate",
                         {"model": _strip_prefix(model), "prompt": prompt, "stream": False,
                          "options": opts, "keep_alive": self.keep_alive},
                         timeout_s=timeout_s or 300)
        if "error" in data:
            raise ProviderError(f"ollama: {data['error']}")
        return LLMResult(text=data.get("response", ""), model=model,
                         tokens_in=int(data.get("prompt_eval_count", 0)),
                         tokens_out=int(data.get("eval_count", 0)),
                         latency_ms=int((time.monotonic() - t0) * 1000))


class OpenAICompatLLM(LLMPort):
    """`model_name` traduce il nome interno (es. `cloud/gpt-4o`) nel nome che
    l'endpoint si aspetta (es. alias LiteLLM `smart-cloud`).

    `served_as` fa il contrario sul campo `model` della risposta: se il
    gateway ha fatto fallback per conto suo (cloud → ollama), il nome interno
    restituito cambia e il core lo registra come fallback. Senza questo, un
    fallback del gateway sarebbe invisibile nel registro costi.
    """

    def __init__(self, base_url: str, api_key: str = "", model_name: Callable[[str], str] = _strip_prefix,
                 temperature: float = 0.2, served_as: Callable[[str, str], str] | None = None):
        self.base_url, self.api_key, self.model_name, self.temperature = base_url.rstrip("/"), api_key, model_name, temperature
        self.served_as = served_as or (lambda requested, served: requested)

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        payload = {"model": self.model_name(model), "temperature": self.temperature,
                   "messages": [{"role": "user", "content": prompt}]}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        t0 = time.monotonic()
        data = post_json(f"{self.base_url}/v1/chat/completions", payload, headers=headers, timeout_s=timeout_s or 120)
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"risposta senza choices da {self.base_url}: {str(data)[:200]}") from e
        usage = data.get("usage") or {}
        served = data.get("model") or ""
        return LLMResult(text=text, model=self.served_as(model, served),
                         tokens_in=int(usage.get("prompt_tokens", 0)),
                         tokens_out=int(usage.get("completion_tokens", 0)),
                         latency_ms=int((time.monotonic() - t0) * 1000))


class UnavailableLLM(LLMPort):
    def __init__(self, why: str):
        self.why = why

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        raise ProviderError(f"{model}: {self.why}")


class PrefixRouterLLM(LLMPort):
    def __init__(self, routes: dict[str, LLMPort]):
        self.routes = routes

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        for prefix, llm in self.routes.items():
            if model.startswith(prefix):
                return llm.complete(model, prompt, max_tokens=max_tokens, timeout_s=timeout_s)
        raise ProviderError(f"nessun provider configurato per {model}")

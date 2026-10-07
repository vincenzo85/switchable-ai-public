"""Cloud SIMULATO per lo stress test, dichiarato come tale.

Senza una chiave cloud la demo non potrebbe mostrare né costi cloud né
rallentamenti. Questo adapter:
- fa rispondere un modello locale reale (token contati dal motore);
- si presenta col nome del modello cloud, così il prezzo applicato è il
  listino cloud (core/domain/pricing.py);
- inietta una turbolenza PROGRAMMATA e riproducibile: nella finestra
  [slow_from, slow_to) delle chiamate cloud aggiunge un ritardo; se il
  ritardo supera il timeout del chiamante, attende il timeout e solleva
  ProviderTimeout, come un client vero.
Ogni numero prodotto con questo adapter va etichettato "cloud simulato".
"""
from __future__ import annotations

import random
import time
from dataclasses import replace

from core.domain.errors import ProviderTimeout
from core.ports import LLMPort


class SimulatedCloudLLM(LLMPort):
    def __init__(self, inner: LLMPort, inner_model: str, *, base_delay_ms: int = 300,
                 slow_from: int = 5, slow_to: int = 12, slow_delay_ms: tuple[int, int] = (1500, 9000),
                 seed: int = 7, sleep=time.sleep):
        self.inner, self.inner_model = inner, inner_model
        self.base_delay_ms, self.slow_from, self.slow_to, self.slow_delay_ms = base_delay_ms, slow_from, slow_to, slow_delay_ms
        self.rng, self.sleep = random.Random(seed), sleep
        self.calls = 0
        self.timeouts = 0

    def complete(self, model, prompt, *, max_tokens=None, timeout_s=None):
        n = self.calls
        self.calls += 1
        delay = self.base_delay_ms
        if self.slow_from <= n < self.slow_to:
            delay += self.rng.randint(*self.slow_delay_ms)
        if timeout_s is not None and delay > timeout_s * 1000:
            self.sleep(timeout_s)
            self.timeouts += 1
            raise ProviderTimeout(f"{model}: turbolenza simulata, {delay}ms > {timeout_s * 1000:.0f}ms")
        self.sleep(delay / 1000)
        r = self.inner.complete(self.inner_model, prompt, max_tokens=max_tokens, timeout_s=timeout_s)
        return replace(r, model=model, latency_ms=r.latency_ms + delay)

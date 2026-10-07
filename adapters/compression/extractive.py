"""Compressione estrattiva leggera (zero dipendenze, zero GPU).

Tiene le frasi più informative finché non raggiunge keep_ratio dei
caratteri, nell'ordine originale. Punteggio = rarità delle parole nel
testo (le frasi ripetute valgono poco) + sovrapposizione con la domanda.

Cache-aware (idea di CAPC, Song 2026): i primi `stable_prefix_chars`
caratteri NON si toccano, così il prefisso resta identico tra richieste e
il prompt caching del provider continua a funzionare.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from core.domain.models import CompressionResult
from core.domain.text import approx_tokens
from core.ports import PromptCompressorPort

_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"\w{3,}", re.UNICODE)


class ExtractiveCompressor(PromptCompressorPort):
    name = "extractive"

    def __init__(self, stable_prefix_chars: int = 0):
        self.stable_prefix_chars = stable_prefix_chars

    def compress(self, text, *, keep_ratio, question=""):
        prefix, body = text[:self.stable_prefix_chars], text[self.stable_prefix_chars:]
        sentences = [s.strip() for s in _SENT.split(body) if s.strip()]
        if len(sentences) <= 1:
            return CompressionResult(text, approx_tokens(text), approx_tokens(text), self.name)

        words = [Counter(w.lower() for w in _WORD.findall(s)) for s in sentences]
        df = Counter(w for c in words for w in c)
        seen_exact: set[str] = set()
        q = {w.lower() for w in _WORD.findall(question)}
        scores = []
        for s, c in zip(sentences, words):
            if s in seen_exact:              # frase identica già vista: duplicato puro
                scores.append(-1.0)
                continue
            seen_exact.add(s)
            n = sum(c.values()) or 1
            rarity = sum(cnt * math.log(1 + len(sentences) / df[w]) for w, cnt in c.items()) / n
            overlap = len(q & set(c)) * 2.0
            scores.append(rarity + overlap)

        budget = keep_ratio * len(body)
        keep, used = set(), 0
        for i in sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True):
            if scores[i] < 0:
                continue
            if used + len(sentences[i]) > budget and keep:
                continue
            keep.add(i)
            used += len(sentences[i])
        out = prefix + " ".join(sentences[i] for i in sorted(keep))
        return CompressionResult(out, approx_tokens(text), approx_tokens(out), self.name)


class NoCompressor(PromptCompressorPort):
    name = "none"

    def compress(self, text, *, keep_ratio, question=""):
        t = approx_tokens(text)
        return CompressionResult(text, t, t, self.name)

"""Funzioni pure sul testo: chunking, conteggio token approssimato, PII scrub.

Il conteggio token qui è solo per decisioni interne (soglie, compressione):
i token FATTURATI vengono sempre dal motore (LLMResult), mai da qui.
"""
from __future__ import annotations

import re

from core.domain.policy import PII_PATTERNS


def approx_tokens(text: str) -> int:
    """~4 caratteri per token (euristica standard per testo latino)."""
    return max(1, len(text) // 4) if text else 0


def _pack(paragraphs: list[str], target_size: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for p in paragraphs:
        if current and length + len(p) + 2 > target_size:
            chunks.append("\n\n".join(current))
            current, length = [p], len(p)
        else:
            current.append(p)
            length += len(p) + (2 if len(current) > 1 else 0)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


_HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)


def chunk_markdown(text: str, target_size: int = 800) -> list[str]:
    """Chunk per SEZIONI markdown, poi per paragrafi di ~target_size caratteri.

    Un titolo non viene mai separato dal suo contenuto e non si fondono
    sezioni diverse; se una sezione è lunga, ogni pezzo riporta il titolo
    come contesto. (Il chunking per soli paragrafi del legacy staccava
    "## L'indice RAG è vuoto" da "Lanciare ./run.sh rag-build".)
    """
    starts = [m.start() for m in _HEADING.finditer(text)]
    if not starts or starts[0] != 0:
        starts = [0, *starts]
    sections = [text[a:b] for a, b in zip(starts, [*starts[1:], len(text)])]
    chunks: list[str] = []
    for sec in sections:
        paragraphs = [p.strip() for p in sec.split("\n\n") if p.strip()]
        if not paragraphs:
            continue
        heading = paragraphs[0] if _HEADING.match(paragraphs[0]) else ""
        body = paragraphs[1:] if heading else paragraphs
        if not body:
            chunks.append(heading)
            continue
        room = max(target_size - len(heading) - 2, target_size // 2) if heading else target_size
        for piece in _pack(body, room):
            chunks.append(f"{heading}\n\n{piece}" if heading else piece)
    return chunks


_PII_LABELS = ("EMAIL", "IBAN", "CF", "CARD")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d ]{8,}\d(?!\w)")


def scrub_pii(text: str) -> tuple[str, int]:
    """Sostituisce i dati personali con segnaposto. Ritorna (testo, n_sostituzioni)."""
    total = 0
    for label, pat in zip(_PII_LABELS, PII_PATTERNS):
        text, n = pat.subn(f"<{label}>", text)
        total += n
    text, n = _PHONE.subn("<PHONE>", text)
    return text, total + n

"""Il canovaccio cita numeri solo con la
loro chiave ({{chiave}}), e la cifra scritta accanto è quella attuale di
talk/numbers.json. Se un benchmark viene rifatto, il testo vecchio diventa
rosso qui invece di arrivare sul palco."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NUMBERS = json.loads((ROOT / "talk/numbers.json").read_text(encoding="utf-8"))["numbers"]
DOCS = [ROOT / "talk/CANOVACCIO.md"]
KEY = re.compile(r"\{\{([\w.]+)\}\}")


def _norm(t: str) -> str:
    return re.sub(r"[\s.,]", "", t).lower()


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_every_key_exists(doc):
    keys = KEY.findall(doc.read_text(encoding="utf-8"))
    assert keys, "nessun numero citato?"
    assert [k for k in keys if k not in NUMBERS] == []


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_written_value_matches_current_number(doc):
    text = doc.read_text(encoding="utf-8")
    stale = []
    for m in KEY.finditer(text):
        key = m.group(1)
        before = text[:m.start()].rstrip()
        disp = NUMBERS[key]["display"]
        # la cifra accanto alla chiave (se c'è) deve essere il display attuale
        tail = re.search(r"([~€]?[\d][\d.,]*\s?(?:%|×|ms|s|tok/s|/Mtok|token)?)$", before)
        if tail and not _norm(before).endswith(_norm(disp)) and _norm(tail.group(1)) not in _norm(disp):
            stale.append(f"{key}: scritto '{tail.group(1)}', attuale '{disp}'")
    assert stale == []

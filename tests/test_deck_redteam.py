"""Il deck red team (deck separato) gira offline, senza errori, senza numeri
senza fonte, e ogni attacco ha la sua risposta."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "talk/deck/dist-redteam/index.html"
pw = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not shutil.which("google-chrome"), reason="Chrome non installato")


@pytest.fixture(scope="module")
def deck():
    subprocess.run([sys.executable, str(ROOT / "talk/deck/build.py"), "--deck", "redteam"], check=True, capture_output=True)
    with pw.sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        errors, external = [], []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: external.append(r.url) if not r.url.startswith(("file://", "data:")) else None)
        page.goto(DIST.as_uri())
        page.wait_for_timeout(800)
        yield page, errors, external
        b.close()


def test_navigable_offline_and_clean(deck):
    page, errors, external = deck
    total = page.evaluate("window.__deck.total")
    for i in range(total):
        page.evaluate(f"window.__deck.go({i})")
        page.wait_for_timeout(80)
    assert page.evaluate("[...window.__deck.missing]") == []
    assert errors == [] and external == []


def test_every_attack_has_an_answer_and_notes(deck):
    page, *_ = deck
    steps = page.evaluate("STEPS.map(s => [s.beat, !!s.notes])")
    attacks = [b for b, _ in steps if re.fullmatch(r"T\d+a", b)]
    answers = [b for b, _ in steps if re.fullmatch(r"T\d+b", b)]
    assert len(attacks) == 10 and [a[:-1] for a in attacks] == [b[:-1] for b in answers]
    assert all(has for _, has in steps)


def test_no_hand_written_metric_numbers(deck):
    page, *_ = deck
    offenders = page.evaluate(r"""() => {
      const out = [];
      const w = document.createTreeWalker(document.getElementById('slides'), NodeFilter.SHOW_TEXT);
      let n; while ((n = w.nextNode())) {
        if (n.parentElement.closest('[data-num],[data-param],.cite')) continue;
        if (/\d[\d.,]*\s?(%|€|ms\b|s\b|×|tok|token|W\b|mesi|kWh)/.test(n.textContent)) out.push(n.textContent.trim().slice(0, 80));
      }
      return out;
    }""")
    assert offenders == []


def test_total_time_is_thirty_minutes(deck):
    page, *_ = deck
    assert abs(page.evaluate("stepMinutes().reduce((a, b) => a + b, 0)") - 30) < 0.01

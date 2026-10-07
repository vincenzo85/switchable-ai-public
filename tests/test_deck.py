"""Il deck 3D gira davvero (Chrome headless via Playwright, da file://).

Si salta se Chrome/Playwright non ci sono. Controlli: nessun errore in
console, nessuna richiesta di rete fuori da file:// (offline-first), ogni
{{numero}} risolto da numbers.json, nessuna cifra "metrica" scritta a mano
nel testo delle slide, tutti gli step navigabili, FPS accettabili.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "talk/deck/dist/index.html"
pw = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not shutil.which("google-chrome"), reason="Chrome non installato")

# cifra seguita da un'unità di misura: deve venire da numbers.json (data-num)
METRIC = re.compile(r"\d[\d.,]*\s?(%|€|ms\b|s\b|×|tok|token|W\b|mesi|kWh)")


@pytest.fixture(scope="module")
def deck():
    subprocess.run([sys.executable, str(ROOT / "talk/deck/build.py")], check=True, capture_output=True)
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


def test_no_missing_numbers_and_no_console_errors(deck):
    page, errors, _ = deck
    assert page.evaluate("[...window.__deck.missing]") == []
    assert errors == []


def test_every_step_renders_and_is_navigable(deck):
    page, errors, external = deck
    total = page.evaluate("window.__deck.total")
    for i in range(total):
        page.evaluate(f"window.__deck.go({i})")
        page.wait_for_timeout(120)
        assert page.evaluate("window.__deck.cur") == i
        visible = page.locator(f'.slide[data-step="{i}"]')
        assert visible.evaluate("e => e.classList.contains('on')")
    assert errors == []
    assert external == [], f"richieste di rete non locali: {external[:3]}"


def test_no_hand_written_metric_numbers(deck):
    page, *_ = deck
    offenders = page.evaluate(r"""() => {
      const out = [];
      const walker = document.createTreeWalker(document.getElementById('slides'), NodeFilter.SHOW_TEXT);
      let n; while ((n = walker.nextNode())) {
        const el = n.parentElement;
        // [data-param]: parametri dell'esperimento (es. "GPU al 5%"), non risultati misurati
        if (el.closest('[data-num],[data-param],.counters,#demo-cards,.cite,pre code,.workflow')) continue;
        if (/\d[\d.,]*\s?(%|€|ms\b|s\b|×|tok|token|W\b|mesi|kWh)/.test(n.textContent)) out.push(n.textContent.trim().slice(0, 80));
      }
      return out;
    }""")
    assert offenders == []


def test_numbers_on_slides_match_numbers_json(deck):
    import json
    page, *_ = deck
    nums = json.loads((ROOT / "talk/numbers.json").read_text())["numbers"]
    shown = page.evaluate("[...document.querySelectorAll('[data-num]')].map(e => [e.dataset.num, e.textContent])")
    assert shown
    for key, text in shown:
        assert text == nums[key]["display"], key


def test_fps_is_acceptable(deck):
    page, *_ = deck
    page.evaluate("window.__deck.go(7)")          # globo con archi: la scena più pesante
    page.wait_for_timeout(2500)
    assert page.evaluate("Engine.fps") >= 30


def test_every_step_has_a_canovaccio_beat_and_the_timing_adds_up():
    import json, re
    built = DIST.read_text(encoding="utf-8")
    beats = json.loads(re.search(r"window.BEATS=(\{.*?\});window.ICONS=", built, re.S).group(1))
    src = (ROOT / "talk/deck/src/slides.js").read_text(encoding="utf-8")
    steps = re.findall(r"beat: '([\w.]+)'", src)
    assert [s for s in steps if s != "qa" and not s.startswith("A.") and s not in beats] == []
    assert set(beats) <= set(steps), "beat del canovaccio senza slide"
    assert all(b["notes"] for b in beats.values())
    qa = float(re.search(r"beat: 'qa', title: 'Domande', min: ([\d.]+)", src).group(1))
    total = sum(b["min"] for b in beats.values()) + qa
    assert len(beats) == 23, "racconto principale: 23 beat (V2)"
    assert abs(total - 30) < 0.01


def test_flight_indicator_follows_the_journey(deck):
    """Il viaggio è anche grafico: fasi in ordine, aereo a terra al boarding,
    in quota in crociera, di nuovo a terra agli arrivi."""
    page, *_ = deck
    phases = page.evaluate("[...document.querySelectorAll('#flight .ph')].map(e => e.dataset.ph)")
    assert phases == ["boarding", "briefing", "gate", "decollo", "crociera", "turbolenza", "atterraggio", "arrivi"]
    assert "appendice" not in phases
    def plane_top(i):
        page.evaluate(f"window.__deck.go({i})")
        page.wait_for_timeout(1100)
        return page.evaluate("parseFloat(document.getElementById('plane').style.top)")
    total = page.evaluate("window.__deck.total")
    phase_of = page.evaluate("STEPS.map(s => s.phase)")
    ground, cruise, arrival = plane_top(0), plane_top(phase_of.index("crociera") + 3), plane_top(phase_of.index("arrivi"))
    assert cruise < ground - 30 and abs(arrival - ground) < 1
    assert page.evaluate("document.querySelector('#flight .ph.cur').dataset.ph") == "arrivi"


def test_semantic_3d_routing_and_turbulence(deck):
    """Il 3D è il sistema: la pista cloud si chiude per residency nelle regole
    dure e per budget durante lo stress test; i pacchetti partono davvero."""
    page, errors, _ = deck
    steps = page.evaluate("STEPS.map(s => s.beat)")
    page.evaluate(f"window.__deck.go({steps.index('3.3')})"); page.wait_for_timeout(300)
    routes = {r["name"]: r for r in page.evaluate("Engine.routes")}
    assert routes["cloud"]["state"] == "closed" and routes["cloud"]["reason"] == "RESIDENCY"
    page.evaluate(f"window.__deck.go({steps.index('3.2')})"); page.wait_for_timeout(5600)
    assert page.evaluate("document.querySelectorAll('#reqs li.in').length") == 4
    i = steps.index("5.2")
    page.evaluate(f"window.__deck.go({i})"); page.wait_for_timeout(14500)
    routes = {r["name"]: r for r in page.evaluate("Engine.routes")}
    assert routes["cloud"]["state"] == "closed" and routes["cloud"]["reason"] == "BUDGET"
    assert page.evaluate(f"document.querySelector('.slide[data-step=\"{i}\"] .l-final').classList.contains('hidden')") is False
    assert errors == []


def test_appendix_is_after_qa_and_reachable_with_a(deck):
    page, *_ = deck
    phases = page.evaluate("STEPS.map(s => s.phase)")
    assert phases.index("arrivi") < phases.index("appendice")
    page.keyboard.press("a"); page.wait_for_timeout(200)
    assert phases[page.evaluate("window.__deck.cur")] == "appendice"

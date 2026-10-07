#!/usr/bin/env python3
"""Build del deck: un index.html autocontenuto (CSS, JS, numeri e replay
inline) + presenter.html + assets/ + fonts/ in talk/deck/dist/.

Offline-first: i font vengono scaricati UNA volta in talk/deck/vendor/fonts
(se manca la rete si usano i font di sistema e il build lo dice).
"""
from __future__ import annotations

import json
import re
import shutil
import urllib.request
from pathlib import Path

DECK = Path(__file__).resolve().parent
TALK = DECK.parent
SRC, DIST, FONTS = DECK / "src", DECK / "dist", DECK / "vendor" / "fonts"
GOOGLE = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500"
          "&family=Instrument+Sans:wght@400;600&display=swap")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def vendor_fonts() -> str:
    css_file = FONTS / "fonts.css"
    if not css_file.exists():
        try:
            FONTS.mkdir(parents=True, exist_ok=True)
            css = urllib.request.urlopen(urllib.request.Request(GOOGLE, headers={"User-Agent": UA}), timeout=20).read().decode()
            blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S)
            out = []
            for subset, block in blocks:
                if subset not in ("latin", "latin-ext"):
                    continue
                url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
                name = re.sub(r"[^\w.-]", "_", url.rsplit("/", 1)[1])
                (FONTS / name).write_bytes(urllib.request.urlopen(url, timeout=20).read())
                out.append(block.replace(url, f"fonts/{name}"))
            css_file.write_text("\n".join(out), encoding="utf-8")
            print(f"font scaricati: {len(out)} facce → {FONTS}")
        except Exception as e:  # noqa: BLE001 — il deck funziona anche con i font di sistema
            print(f"⚠ font non scaricati ({e}): uso i font di sistema")
            return ""
    return f"<style>{css_file.read_text(encoding='utf-8')}</style>"


def parse_beats(md: str) -> dict:
    """`## X.Y · mm:ss–mm:ss · titolo` → tempi, speaker notes e transizione."""
    beats = {}
    parts = re.split(r"^## (\d\.\d+) · (\d\d):(\d\d)–(\d\d):(\d\d) · (.+)$", md, flags=re.M)
    for i in range(1, len(parts), 7):
        bid, m1, s1, m2, s2, title, body = parts[i:i + 7]
        body = body.split("\n# ", 1)[0]
        notes = re.search(r"\*\*Speaker notes \(parlato\):\*\*\s*\n((?:>.*\n?)+)", body)
        trans = re.search(r"\*\*Transizione:\*\*\s*(.+)", body)
        clean = lambda t: re.sub(r"\s?\{\{[\w.]+\}\}", "", t).strip()
        beats[bid] = {"title": title.strip(), "start": f"{m1}:{s1}", "end": f"{m2}:{s2}",
                      "min": ((int(m2) * 60 + int(s2)) - (int(m1) * 60 + int(s1))) / 60,
                      "notes": clean(re.sub(r"^>\s?", "", notes.group(1), flags=re.M)) if notes else "",
                      "transition": clean(trans.group(1)) if trans else ""}
    return beats


ICONS_DIR = DECK / "vendor" / "icons"
IMG_DIR = TALK / "assets" / "img"


def load_icons() -> dict:
    """Lucide (ISC): SVG ripuliti e incorporati, dimensionati in em dal CSS."""
    out = {}
    for f in sorted(ICONS_DIR.glob("*.svg")):
        svg = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S).strip()
        svg = re.sub(r'\s(width|height)="24"', "", svg)
        svg = svg.replace('stroke-width="2"', 'stroke-width="1.6"')
        out[f.stem] = re.sub(r"\s+", " ", svg)
    return out


def load_images() -> dict:
    """Fondali generati: talk/assets/img/<id>.(webp|jpg|jpeg|png)."""
    if not IMG_DIR.exists():
        return {}
    return {f.stem: f.name for f in sorted(IMG_DIR.iterdir()) if f.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png")}


def write_image_plan(slides_js: str, images: dict) -> None:
    """talk/IMMAGINI.md: per ogni slide l'immagine prevista (da slides.js, unica fonte)."""
    import subprocess
    js = slides_js + "\nconsole.log(JSON.stringify(STEPS.map(s => ({phase: s.phase, beat: s.beat, title: s.title, img: s.img || null}))));"
    try:
        rows = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    except Exception as e:  # noqa: BLE001
        print(f"⚠ IMMAGINI.md non generato (serve node): {e}")
        return
    L = ["# Immagini del deck, slide per slide", "",
         "Generato da `talk/deck/build.py` leggendo il campo `img` di ogni slide in `talk/deck/src/slides.js`.",
         "Per usare un'immagine: salvarla come `talk/assets/img/<id>.webp` (o .jpg/.png), 16:9, almeno 1920×1080,",
         "lato sinistro scuro e vuoto (lì va il titolo). Poi `make deck`: il deck la usa come fondale da solo.", "",
         "Stile comune (già incluso nei prompt): notte, blu quasi nero, luci avorio, accenti verde acqua / arancio / blu,",
         "composizione minimale, molto spazio negativo a sinistra, niente testo, niente loghi, niente volti.", "",
         "| # | Fase | Slide | id | Stato | Cosa mostrare | Alternativa SVG/3D |", "|---|---|---|---|---|---|---|"]
    prompts = []
    for i, r in enumerate(rows, 1):
        im = r["img"] or {}
        iid = im.get("id", "—")
        state = "✅ presente" if iid in images else ("—" if not im.get("prompt") else "da generare")
        L.append(f"| {i} | {r['phase']} | {r['title']} | `{iid}` | {state} | {im.get('idea', '')} | {im.get('alt', '')} |")
        if im.get("prompt"):
            prompts.append(f"### {i}. {r['title']} — `{iid}`\n\n```\n{im['prompt']}\n```\n")
    L += ["", "## Prompt per la generazione", ""] + prompts
    (TALK / "IMMAGINI.md").write_text("\n".join(L) + "\n", encoding="utf-8")


DECKS = {  # nome → (sorgente slide, cartella di uscita, titolo pagina, piano immagini)
    "main": ("slides.js", "dist", "Non serve sempre un modello migliore", True),
    "redteam": ("slides_redteam.js", "dist-redteam", "Red team: provo a far cadere la mia tesi", False),
}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", choices=sorted(DECKS) + ["all"], default="all")
    a = ap.parse_args(argv)
    for name in (sorted(DECKS) if a.deck == "all" else [a.deck]):
        build_one(*DECKS[name])
    return 0


def build_one(slides_file: str, out_dir: str, page_title: str, image_plan: bool) -> None:
    DIST = DECK / out_dir
    numbers = json.loads((TALK / "numbers.json").read_text(encoding="utf-8"))
    demo = json.loads((TALK / "replays/demo.json").read_text(encoding="utf-8"))
    stress = json.loads((TALK / "replays/stress.json").read_text(encoding="utf-8"))
    beats = parse_beats((TALK / "CANOVACCIO.md").read_text(encoding="utf-8"))
    data = (f"window.NUMBERS={json.dumps(numbers, ensure_ascii=False)};"
            f"window.BEATS={json.dumps(beats, ensure_ascii=False)};"
            f"window.ICONS={json.dumps(load_icons())};"
            f"window.IMAGES={json.dumps(load_images())};"
            f"window.REPLAY_DEMO={json.dumps(demo, ensure_ascii=False)};"
            f"window.REPLAY_STRESS={json.dumps(stress, ensure_ascii=False)};").replace("</", "<\\/")
    src = {n: (SRC / n).read_text(encoding="utf-8") for n in ("engine.js", "deck.js", "deck.css")}
    src["slides.js"] = (SRC / slides_file).read_text(encoding="utf-8")
    fonts = vendor_fonts()
    if image_plan:
        write_image_plan(src["slides.js"], load_images())

    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir(parents=True)
    page = (SRC / "index.html").read_text(encoding="utf-8")
    page = (page.replace("<title>Architettura AI switchabile</title>", f"<title>{page_title}</title>").replace("<!--FONTS-->", fonts).replace("/*CSS*/", src["deck.css"]).replace("/*DATA*/", data)
                .replace("/*ENGINE*/", src["engine.js"]).replace("/*SLIDES*/", src["slides.js"])
                .replace("/*DECK*/", src["deck.js"]))
    (DIST / "index.html").write_text(page, encoding="utf-8")
    pres = (SRC / "presenter.html").read_text(encoding="utf-8")
    (DIST / "presenter.html").write_text(pres.replace("/*DATA*/", data).replace("/*SLIDES*/", src["slides.js"]), encoding="utf-8")
    shutil.copytree(TALK / "assets", DIST / "assets")
    if FONTS.exists():
        shutil.copytree(FONTS, DIST / "fonts")
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"deck → {DIST.relative_to(TALK.parent)}/index.html ({size / 1e6:.1f} MB con assets)")


if __name__ == "__main__":
    raise SystemExit(main())

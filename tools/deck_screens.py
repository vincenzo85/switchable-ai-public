"""Screenshot di ogni step del deck (talk/screens/NN.png) + provini a 6 per
foglio (talk/screens/sheet-N.png) per la revisione visiva."""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REDTEAM = "--redteam" in sys.argv
OUT = ROOT / ("talk/screens-redteam" if REDTEAM else "talk/screens")
OUT.mkdir(parents=True, exist_ok=True)
PAGE = ROOT / ("talk/deck/dist-redteam/index.html" if REDTEAM else "talk/deck/dist/index.html")
wait = 2200

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto(PAGE.as_uri())
    total = pg.evaluate("window.__deck.total")
    enters = pg.evaluate("STEPS.map(s => s.enter || '')")
    for i in range(total):
        pg.evaluate(f"window.__deck.go({i})")
        waits = {"demo": 17000, "stress": 17000, "routing": 7000, "finale": 10500, "boarding": 3600}
        pg.wait_for_timeout(waits.get(enters[i], wait))                    # sequenze: fotogramma finale
        pg.screenshot(path=str(OUT / f"{i + 1:02d}.png"))
    # filmine dei quattro WOW: più fotogrammi nel tempo
    WOW = {"boarding": [400, 1300, 3600], "routing": [900, 2400, 4600, 6800], "stress": [2500, 7000, 14500], "finale": [1500, 4300, 6500, 10500]}
    for name, times in ({} if REDTEAM else WOW).items():
        i = enters.index(name)
        frames = []
        for t in times:
            pg.evaluate("window.__deck.go(0)"); pg.wait_for_timeout(200)
            pg.evaluate(f"window.__deck.go({i})"); pg.wait_for_timeout(t)
            f = OUT / f"wow-{name}-{t}.png"; pg.screenshot(path=str(f)); frames.append(f)
        strip = Image.new("RGB", (960 * 2, 540 * ((len(frames) + 1) // 2)), "#000")
        for k, f in enumerate(frames):
            strip.paste(Image.open(f).resize((960, 540)), ((k % 2) * 960, (k // 2) * 540))
        strip.save(OUT / f"wow-{name}.png")
    b.close()

for old in OUT.glob("sheet-*.png"):
    old.unlink()
shots = sorted(OUT.glob("[0-9][0-9].png"))[:total]
for s in range(0, len(shots), 6):
    sheet = Image.new("RGB", (1920, 1620), "#000")
    for k, f in enumerate(shots[s:s + 6]):
        im = Image.open(f).resize((960, 540))
        sheet.paste(im, ((k % 2) * 960, (k // 2) * 540))
    sheet.save(OUT / f"sheet-{s // 6 + 1}.png")
print(len(shots), "step")

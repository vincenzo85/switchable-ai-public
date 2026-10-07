"""PDF di riserva del deck (piano B se il PC della sala non regge il 3D):
uno step per pagina, dagli screenshot di tools/deck_screens.py."""
from pathlib import Path

from PIL import Image

import sys
ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / ("talk/screens-redteam" if "--redteam" in sys.argv else "talk/screens")
shots = sorted(SHOTS.glob("[0-9][0-9].png"))
pages = [Image.open(p).convert("RGB") for p in shots]
out = SHOTS / "deck-backup.pdf"
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=144)
print(out, len(pages), "pagine", f"{out.stat().st_size / 1e6:.1f} MB")

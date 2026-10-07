"""QR del repository per l'ultima slide (SVG, offline)."""
from pathlib import Path

import qrcode
import qrcode.image.svg

URL = "https://github.com/vincenzo85/switchable-ai-public"
OUT = Path(__file__).resolve().parents[1] / "talk/assets/qr-repo.svg"
img = qrcode.make(URL, image_factory=qrcode.image.svg.SvgPathFillImage, border=2)
OUT.write_bytes(img.to_string())
print(OUT, URL)

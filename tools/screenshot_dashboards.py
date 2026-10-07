"""Screenshot del cockpit Grafana e delle trace Langfuse per il deck (talk/assets)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "talk/assets"

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1.5, color_scheme="dark")
    pg.goto("http://127.0.0.1:3012/d/switchable-cockpit?orgId=1&from=now-30m&to=now&kiosk&theme=dark")
    pg.wait_for_timeout(6000)
    pg.screenshot(path=str(OUT / "grafana-cockpit.png"))
    # Langfuse: login demo, lista trace
    pg.goto("http://localhost:3011/auth/sign-in")   # = NEXTAUTH_URL, altrimenti il cookie non vale
    pg.fill("input[name=email]", "demo@switchable.local")
    pg.fill("input[name=password]", "switchable-demo")
    pg.get_by_role("button", name="Sign in").last.click()
    pg.wait_for_timeout(4000)
    pg.goto("http://localhost:3011/project/switchable-ai/traces")
    pg.wait_for_timeout(5000)
    pg.screenshot(path=str(OUT / "langfuse-traces.png"))
    b.close()
print("ok")

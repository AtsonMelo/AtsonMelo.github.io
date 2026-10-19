"""Regenerates assets/img/og.png from tools/og.html (needs: pip install playwright && playwright install chromium)."""
import pathlib
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width": 1200, "height": 630})
    p.goto((root / "tools" / "og.html").as_uri()); p.screenshot(path=str(root / "assets" / "img" / "og.png")); b.close()
print("og.png written")

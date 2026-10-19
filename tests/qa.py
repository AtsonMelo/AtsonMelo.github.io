"""Local QA: serves the site, checks console errors, overflow, links, i18n, dialogs, a11y basics, external requests.
Run: python tests/qa.py [--shots DIR]   (needs: pip install playwright && playwright install chromium)"""
import functools, http.server, pathlib, re, sys, threading, json
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
shots = pathlib.Path(sys.argv[sys.argv.index("--shots") + 1]) if "--shots" in sys.argv else None
if shots: shots.mkdir(parents=True, exist_ok=True)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=str(ROOT)))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{httpd.server_address[1]}/"
ok = bad = 0
def check(name, cond, extra=""):
    global ok, bad
    if cond: ok += 1
    else: bad += 1; print("FAIL:", name, extra)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    for label, vp in (("desktop", {"width": 1440, "height": 900}), ("tablet", {"width": 820, "height": 1100}), ("mobile", {"width": 390, "height": 844})):
        ctx = br.new_context(viewport=vp, locale="en-US"); pg = ctx.new_page()
        errs, reqs = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("requestfailed", lambda r: errs.append("reqfail " + r.url))
        pg.on("request", lambda r: reqs.append(r.url))
        pg.goto(base); pg.wait_for_load_state("networkidle")
        check(f"{label}: no console errors", not errs, str(errs))
        check(f"{label}: only same-origin requests", all(u.startswith(base) or u.startswith("data:") for u in reqs), str([u for u in reqs if not u.startswith(base)]))
        check(f"{label}: no horizontal scroll", pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), str(pg.evaluate("document.documentElement.scrollWidth")))
        check(f"{label}: exactly one h1", pg.locator("h1").count() == 1)
        check(f"{label}: all images have alt attr", pg.evaluate("[...document.images].every(i => i.hasAttribute('alt'))"))
        check(f"{label}: all images loaded", pg.evaluate("[...document.images].every(i => i.complete && i.naturalWidth > 0)"))
        if shots:
            pg.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('in'))")
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(shots / f"{label}-full.png"), full_page=True)
        if label == "mobile":
            check("mobile: menu hidden then opens", not pg.locator("#nav").is_visible())
            pg.locator("#burger").click(); check("mobile: menu opens", pg.locator("#nav").is_visible())
            pg.locator("#nav a[href='#projects']").click(); check("mobile: menu closes on nav", not pg.locator("#nav").is_visible())
        if label == "desktop":
            # internal anchors resolve
            ids = set(pg.evaluate("[...document.querySelectorAll('[id]')].map(e => e.id)"))
            hrefs = pg.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].map(a => a.getAttribute('href').slice(1))")
            check("anchors resolve", all(h in ids or h == "" for h in hrefs), str([h for h in hrefs if h not in ids]))
            # external links: https + rel noopener, none fake
            ext = pg.evaluate("[...document.querySelectorAll('a[href^=\"http\"]')].map(a => [a.href, a.rel])")
            check("external links https + noopener", all(h.startswith("https://") and "noopener" in r for h, r in ext), str(ext))
            print("external links:", sorted({h for h, _ in ext}))
            # contact: no invented channels while config is empty
            cfg = pg.evaluate("window.SITE_CONFIG")
            labels = pg.evaluate("[...document.querySelectorAll('#channels small')].map(e => e.textContent)")
            check("contact renders only configured channels", ("Discord" in labels) == bool(cfg["discordUrl"] or cfg["discordHandle"]) and ("E-mail" in labels) == bool(cfg["email"]), str(labels))
            # dialogs
            for d in ("dlg-phone", "dlg-char", "dlg-core", "dlg-oss"):
                pg.locator(f"[data-open={d}]").first.click(); check(f"{d} opens", pg.evaluate(f"document.getElementById('{d}').open"))
                if shots and d == "dlg-phone": pg.screenshot(path=str(shots / "dialog.png"))
                pg.keyboard.press("Escape"); check(f"{d} closes with Esc", not pg.evaluate(f"document.getElementById('{d}').open"))
            # i18n
            en = pg.locator("h2").first.inner_text()
            pg.locator("#lang").click()
            check("PT toggle sets lang + text", pg.evaluate("document.documentElement.lang") == "pt-BR" and pg.locator("h2").first.inner_text() != en)
            missing = pg.evaluate("[...document.querySelectorAll('[data-i18n]')].map(n => n.getAttribute('data-i18n')).filter(k => !(k in window.I18N_PT))")
            check("every data-i18n key has PT", not missing, str(missing))
            if shots: pg.screenshot(path=str(shots / "desktop-pt-top.png"))
            pg.locator("#lang").click(); check("EN restored", pg.locator("h2").first.inner_text() == en)
            # keyboard: first Tab lands on skip link
            pg.reload(); pg.keyboard.press("Tab")
            check("first Tab focuses skip link", pg.evaluate("document.activeElement.className") == "skip")
        ctx.close()
    # reduced motion: content visible without scroll reveals
    ctx = br.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce"); pg = ctx.new_page(); pg.goto(base)
    check("reduced-motion: no hidden reveal blocks", pg.evaluate("[...document.querySelectorAll('.card')].every(c => getComputedStyle(c).opacity === '1')"))
    ctx.close()
    # JS disabled: content present
    ctx = br.new_context(java_script_enabled=False); pg = ctx.new_page(); pg.goto(base)
    check("no-JS: hero + projects visible", pg.locator("h1").is_visible() and pg.locator(".card").first.is_visible())
    ctx.close(); br.close()

# static hygiene
text = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix in {".html", ".js", ".css", ".md", ".xml", ".txt", ".svg", ".py"} and p.name != "qa.py")
for pat, why in ((r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+(?:\.\d+)?\b", "private IP"), (r"(?i)sv_licensekey|secrets\.cfg|server\.cfg|api[_-]?key|password|token\s*[:=]", "secret-like"), (r"[A-Z]:\Atson", "local path")):
    hit = re.findall(pat, text)
    check(f"static scan: no {why}", not hit, str(hit[:3]))
print(f"QA: {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)

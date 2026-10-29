
"""Regression: Light surfaces, dark theme isolation and readable contrast.

Tests rendered CSS in Chromium at mobile/tablet/desktop widths. Photo pixels are
not treated as dark UI surfaces; the already approved Hero is not modified.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import re
import shutil

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "tests" / "_screenshots" / "theme-surfaces"
SHOTS.mkdir(parents=True, exist_ok=True)
SECTIONS = [
    "#mission", "#formats", "#studio", "#about", "#nutrition",
    "#results", "#reviews", "#pricing", "#faq", ".final-section", ".yf-footer",
]
# Photo-backed program cards intentionally retain a dark CSS shade for white
# labels; these are photographs, not dark section surfaces.
LIGHT_CARDS = [
    "#pricing .price", "#reviews .review", "#mission .benefit",
]
INK = ["#formats .heading", "#results .heading", "#pricing .heading",
       ".yf-footer-info h2",
       "#pricing .price h3"]
PHOTO_AREA = ["#formats .program-card", ".final-section"]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

def components(color):
    values = re.findall(r"[\d.]+", color)
    return [float(value) for value in values[:3]]

def luminance(rgb):
    channels = [v / 255 for v in rgb]
    corrected = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
                 for c in channels]
    return .2126 * corrected[0] + .7152 * corrected[1] + .0722 * corrected[2]

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        chrome = shutil.which("google-chrome") or shutil.which("chromium")
        browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        for width, height in ((320,740), (375,812), (768,1024), (1024,768), (1440,900), (1920,1080)):
            for theme in ("light", "dark"):
                page = browser.new_page(viewport={"width":width,"height":height}, reduced_motion="reduce")
                page.add_init_script(f"localStorage.setItem('fitness-theme','{theme}');localStorage.setItem('yuliia-language','uk')")
                page.goto(f"http://127.0.0.1:{server.server_port}/",wait_until="domcontentloaded")
                page.wait_for_function("window.YF_I18N && document.getElementById('yf-socials').children.length > 0")
                assert page.locator("html").get_attribute("data-theme") == theme
                for selector in SECTIONS:
                    element = page.locator(selector).first
                    bg = components(element.evaluate("el=>getComputedStyle(el).backgroundColor"))
                    if selector == ".final-section":
                        # Photo-first closing section intentionally matches the dark first screen in all themes.
                        assert max(bg) < 75, (width, selector, "closing hero dark palette lost", bg)
                    elif theme == "light":
                        assert min(bg) > 223, (width, selector, "light surface remains dark", bg)
                    elif selector in ("#formats", "#results", "#pricing", ".yf-footer"):
                        assert max(bg) < 75, (width, selector, "dark theme regressed", bg)
                if theme == "light":
                    for selector in LIGHT_CARDS:
                        bg = components(page.locator(selector).first.evaluate("el=>getComputedStyle(el).backgroundColor"))
                        assert min(bg) > 227, (width, selector, "dark card", bg)
                    for selector in INK:
                        el = page.locator(selector).first
                        color = components(el.evaluate("el=>getComputedStyle(el).color"))
                        assert luminance(color) < .17, (width, selector, "low ink contrast", color)
                    for selector in ("#pricing .price p", "#results p"):
                        rgb = components(page.locator(selector).first.evaluate("el=>getComputedStyle(el).color"))
                        assert luminance(rgb) < .25, (width, selector, "muted text too pale", rgb)
                    for selector in (".final-section .heading", ".final-section p"):
                        rgb = components(page.locator(selector).first.evaluate("el=>getComputedStyle(el).color"))
                        assert luminance(rgb) > .7, (width, selector, "closing photographic text must remain bright", rgb)
                    for selector in ("#formats .program-card::after", ".final-section::after"):
                        element, pseudo = selector.split("::")
                        gradient = page.locator(element).first.evaluate(
                            "(el, pseud)=>getComputedStyle(el,'::'+pseud).backgroundImage", pseudo
                        )
                        assert "linear-gradient" in gradient, (width, selector, gradient)
                    if width in (375,768,1440):
                        page.locator(".reveal").evaluate_all("(items)=>items.forEach(el=>el.classList.add('visible'))")
                        page.screenshot(path=str(SHOTS/f"light-{width}.png"),full_page=True,animations="disabled")
                overflow=page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow <= 2, (width,theme,"horizontal overflow",overflow)
                page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print("PASS: light surfaces/cards/ink and dark-theme isolation at 320–1920px.")

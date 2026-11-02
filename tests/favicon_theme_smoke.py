"""Verify the FT favicon follows the selected theme on desktop and mobile."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        binary = shutil.which("google-chrome") or shutil.which("chromium")
        browser = p.chromium.launch(headless=True, executable_path=binary) if binary else p.chromium.launch(headless=True)
        for width, height in ((375, 812), (1440, 900)):
            for theme in ("light", "dark", "mixed"):
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="domcontentloaded")
                page.evaluate("(theme) => localStorage.setItem('fitness-theme', theme)", theme)
                page.reload(wait_until="domcontentloaded")
                link = page.locator('link[rel="icon"]')
                expected = lambda mode: f"assets/images/fitness-trener-favicon-{mode}.svg"
                assert page.locator("html").get_attribute("data-theme") == theme
                assert link.get_attribute("href") == expected("light" if theme == "light" else "dark")
                assert page.evaluate('document.querySelectorAll("link[rel=icon]").length') == 1
                next_theme = ("light", "dark", "mixed")[(("light", "dark", "mixed").index(theme) + 1) % 3]
                page.locator("#theme-button").click()
                page.wait_for_function("theme => document.documentElement.dataset.theme === theme", arg=next_theme)
                page.wait_for_function('icon => document.querySelector("link[rel=icon]").getAttribute("href") === icon',
                                       arg=expected("light" if next_theme == "light" else "dark"))
                assert page.evaluate("localStorage.getItem(\'fitness-theme\')") == next_theme
                page.reload(wait_until="domcontentloaded")
                assert page.locator("html").get_attribute("data-theme") == next_theme
                assert link.get_attribute("href") == expected("light" if next_theme == "light" else "dark")
                for mode in ("light", "dark"):
                    response = page.request.get(f"http://127.0.0.1:{server.server_port}/assets/images/fitness-trener-favicon-{mode}.svg")
                    assert response.ok and "image/svg+xml" in response.headers["content-type"]
                    assert "<svg" in response.text() and "FT" in response.text()
                page.close()
        browser.close()
finally:
    server.shutdown()
print("PASS: dynamic Light/Dark/Mixed favicon switching at mobile and desktop widths")

"""Premium Motion regression: geometry, progressive enhancement and reduced motion.
Runs in the CI Chromium used to publish the GitHub Pages frontend.
"""
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
URL = f"http://127.0.0.1:{server.server_port}/"

try:
    with sync_playwright() as playwright:
        chrome = shutil.which('google-chrome') or shutil.which('chromium')
        launch = {"headless": True, "args": ["--no-sandbox"]}
        if chrome:
            launch["executable_path"] = chrome
        browser = playwright.chromium.launch(**launch)
        for width, height in ((375, 812), (768, 1024), (1440, 900)):
            page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="no-preference")
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.add_init_script("localStorage.setItem('fitness-theme','dark');localStorage.setItem('yuliia-language','uk')")
            page.goto(URL, wait_until='domcontentloaded', timeout=45000)
            page.locator('.fhero-photo').scroll_into_view_if_needed(timeout=5000)
            page.wait_for_function("document.querySelectorAll('.yf-motion-item').length >= 14")
            assert page.locator('#formats .yf-motion-item').count() == 4, width
            assert page.locator('#reviews .yf-motion-item').count() == 3, width
            assert page.locator('#faq .yf-motion-item').count() == 5, width
            assert page.locator('.fhero-photo').evaluate(
                "el => getComputedStyle(el).animationName.includes('yf-motion-hero-breathe')"
            ), (width, 'missing hero motion')
            for section in ('mission', 'formats', 'reviews', 'faq'):
                page.locator(f'#{section}').scroll_into_view_if_needed()
                page.locator(f'#{section} .yf-motion-item').first.wait_for(state='visible')
                page.wait_for_function(
                    "id => [...document.querySelectorAll('#' + id + ' .yf-motion-item')].some(el => el.classList.contains('yf-motion-visible'))",
                    arg=section
                )
            page.locator('#faq summary').first.click()
            assert page.locator('#faq details').first.evaluate('el => el.open'), (width, 'FAQ broken')
            if width >= 768:
                page.locator('#about .yf-about-media').scroll_into_view_if_needed()
                page.wait_for_function("document.querySelector('#about .yf-about-media img').classList.contains('yf-motion-portrait')")
                assert page.locator('#about .yf-about-media').evaluate(
                    "el => !!el.style.getPropertyValue('--yf-motion-parallax')"
                ), (width, 'portrait parallax not updated')
            assert page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') <= 3, (width, 'overflow')
            assert not errors, (width, errors)
            page.close()

        for scripting in (True, False):
            page = browser.new_page(viewport={"width": 375, "height": 812}, reduced_motion='reduce', java_script_enabled=scripting)
            page.goto(URL, wait_until='domcontentloaded')
            assert page.locator('.yf-motion-item').count() == 0, ('reduced/no-js must not hide elements', scripting)
            assert page.locator('#formats .program-card').first.evaluate(
                "el => getComputedStyle(el).opacity === '1'"
            ), ('card hidden without motion', scripting)
            assert page.locator('.fhero-photo').evaluate(
                "el => getComputedStyle(el).animationName === 'none'"
            ), ('hero not respecting reduced motion', scripting)
            page.close()
        browser.close()
finally:
    server.shutdown()
print('PASS: premium motion, progressive reveal, parallax, FAQ, reduced motion and no-JS')

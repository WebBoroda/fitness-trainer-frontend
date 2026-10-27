"""Visual and interaction smoke test of the GitHub Pages frontend, not WordPress."""
import pathlib
from functools import partial
import shutil
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parents[1]
SHOTS = BASE / "tests" / "_screenshots"
SHOTS.mkdir(exist_ok=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(BASE)))
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
url = f"http://127.0.0.1:{server.server_port}/"
checks = []
try:
    with sync_playwright() as playwright:
        chrome = shutil.which('google-chrome') or shutil.which('chromium')
        browser = playwright.chromium.launch(headless=True, executable_path=chrome) if chrome else playwright.chromium.launch(headless=True)
        for width, height in [(320, 740), (375, 812), (480, 850), (768, 1024),
                              (1024, 768), (1440, 900), (1536, 1024), (1920, 1080)]:
            for scheme in ("dark", "light"):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    color_scheme=scheme,
                    device_scale_factor=1
                )
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.add_init_script("localStorage.setItem('fitness-theme','" + scheme + "')")
                response = page.goto(url, wait_until="networkidle", timeout=45000)
                assert response and response.ok, (width, response.status if response else None)
                assert page.locator("main section").count() == 11, width
                assert page.locator("#formats .program-card").count() == 4
                assert page.locator("#formats .program-card .ico svg").count() == 4
                assert page.locator("#about .quote blockquote").count() == 1
                assert page.locator("#mission .quote").count() == 0
                assert page.locator("#pricing .price-action").count() == 3
                assert page.locator("img[src^='data:']").count() == 0
                assert page.locator("html").get_attribute("data-theme") == scheme
                assert page.locator(".studio-gallery .gallery-photo").count() == 3
                assert page.locator(".yf-consultation-modal").count() == 1

                for img in page.locator("main img:visible").all():
                    img.scroll_into_view_if_needed(timeout=10000)
                    img.evaluate("(el) => el.decode().catch(()=>{})")
                bad_images = page.locator("main img:visible").evaluate_all(
                    "(items) => items.filter(img=>!img.complete || img.naturalWidth===0).map(img=>img.src)"
                )
                assert not bad_images, (width, bad_images)
                page.evaluate("scrollTo(0,0)")
                page.wait_for_timeout(100)

                overflow = page.evaluate(
                    "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)-innerWidth"
                )
                assert overflow <= 2, ("horizontal overflow", width, overflow)
                sections = page.locator("main section")
                for section in sections.all():
                    box = section.bounding_box()
                    assert box and box["height"] > 40, (width, section.get_attribute("id"), box)
                if width >= 1024:
                    program = page.locator("#formats .program-top").bounding_box()
                    cards = page.locator("#formats .program-cards").bounding_box()
                    if width >= 1024:
                        assert program and cards and cards["x"] > program["x"], (width, program, cards)

                # Gallery: first CTA must open an actual keyboard-accessible dialog.
                gallery = page.locator('a[href="#studio-gallery"]')
                gallery.click()
                assert page.locator(".yf-gallery-modal").evaluate("(el)=>el.open"), width
                photo_first = page.locator(".yf-gallery-modal img").get_attribute("src")
                page.locator('.yf-gallery-controls button[aria-label="Наступне фото"]').click()
                photo_next = page.locator(".yf-gallery-modal img").get_attribute("src")
                assert photo_first != photo_next
                page.keyboard.press("Escape")
                assert not page.locator(".yf-gallery-modal").evaluate("(el)=>el.open")

                # Locally generated consultation text, never a fake "sent" action.
                page.locator('.fhero-button-primary').click()
                assert page.locator("#consultation").evaluate("(el)=>el.open")
                page.locator('#consultation textarea[name="goal"]').fill("Покращити витривалість і силу")
                page.locator("#consultation button[type=submit]").click()
                page.wait_for_timeout(150)
                note = page.locator(".yf-planner-status").inner_text()
                assert "надісл" in note.lower() or "скопій" in note.lower(), note
                page.keyboard.press("Escape")
                assert not page.locator("#consultation").evaluate("(el)=>el.open")

                # Accordions, mobile menu and animation fallback.
                faq = page.locator("#faq details")
                assert faq.count() == 5
                faq.first.locator("summary").click()
                assert faq.first.evaluate("(el)=>el.open")
                faq.nth(1).locator("summary").click()
                page.wait_for_timeout(60)
                assert not faq.first.evaluate("(el)=>el.open")
                if width <= 1100:
                    menu = page.locator("#menu-button")
                    menu.click()
                    assert menu.get_attribute("aria-expanded") == "true"
                    page.keyboard.press("Escape")
                    assert menu.get_attribute("aria-expanded") == "false"

                assert not errors, (width, errors)
                if width in (375, 768, 1536) and scheme in ("light", "dark"):
                    # Use actual rendered full-page captures for manual comparison.
                    page.locator(".reveal").evaluate_all(
                        "(els)=>els.forEach(el=>el.classList.add('visible'))"
                    )
                    page.screenshot(
                        path=str(SHOTS / f"frontend-{width}-{scheme}.png"),
                        full_page=True, animations="disabled", timeout=30000
                    )
                checks.append(f"{width}px {scheme}")
                page.close()

        default = browser.new_page(viewport={"width": 375, "height": 812})
        default.goto(url, wait_until="domcontentloaded")
        assert default.locator("html").get_attribute("data-theme") == "mixed", "Approved mixed mode must be the initial visual"
        default.close()
        reduced = browser.new_page(viewport={"width": 375, "height": 812}, reduced_motion="reduce")
        reduced.goto(url, wait_until="networkidle")
        assert reduced.locator(".reveal").first.evaluate(
            "(el)=>getComputedStyle(el).opacity"
        ) == "1", "reduced motion hides content"
        reduced.close()
        browser.close()
    print("PASS: frontend responsive, assets, dialogs, FAQ, gallery, nav, consultation and motion; " + ", ".join(checks))
finally:
    server.shutdown()
    server.server_close()

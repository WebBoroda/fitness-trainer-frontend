"""Language, unified CTAs, handwritten annotation and footer layout regression.
Uses actual Chromium with UA/EN browser locales and persistence scenarios.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "_screenshots" / "bilingual-system"
OUT.mkdir(parents=True, exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"
cases = [(320,740), (375,812), (768,1024), (974,1374), (1440,900), (1920,1080)]
errors = []
try:
    with sync_playwright() as p:
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
        browser = p.chromium.launch(headless=True, executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch(headless=True, args=["--no-sandbox"])
        for locale, expected in (("en-US","en"),("uk-UA","uk"),("pl-PL","uk")):
            for width,height in cases:
                page = browser.new_page(viewport={"width":width,"height":height},locale=locale, reduced_motion="reduce")
                page.goto(url,wait_until="domcontentloaded")
                page.wait_for_function("window.YF_I18N && document.querySelector('#yf-socials .yf-social-link')", timeout=15000)
                assert page.locator("html").get_attribute("lang")==expected,(locale,width,"wrong initial lang")
                assert page.locator("html").get_attribute("data-language")==expected,(locale,width,"wrong data lang")
                nav = page.locator(".fhero-navigation a").first.inner_text()
                assert nav==("About" if expected=="en" else "Про мене"),(locale,width,nav)
                assert page.locator("main > section").count()==11,(locale,width,"missing sections")
                assert page.locator("#yf-socials .yf-social-link").count()==7,(locale,width,"social icons")
                assert page.locator("#yf-map").count()==1,(locale,width,"map missing")
                assert page.locator("#yf-directions").get_attribute("aria-disabled")=="true",(locale,width,"demo route should not point to a fake gym")
                assert page.locator(".fhero-curve").count()==1,(locale,width,"curved video-to-handwriting arrow missing")
                assert page.locator(".fhero-curve").is_visible(),(locale,width,"curved arrow must remain visible")
                note = page.locator(".fhero-handwrite")
                assert note.is_visible(),(locale,width,"handwriting must always be visible")
                assert note.bounding_box()["height"]>8,(locale,width,"annotation has no height")
                overflow = page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow<=3,(locale,width,"horizontal overflow",overflow)
                buttons=page.locator('.section .btn .arrow,.fhero-actions .fhero-cta-circle,.fhero-actions .fhero-button-secondary .fhero-svg,.yf-footer .btn .arrow')
                for button in buttons.all():
                    child=button.bounding_box()
                    parent=button.locator("xpath=..").bounding_box()
                    assert child is not None and parent is not None
                    assert child["x"]>=parent["x"]-2 and child["x"]+child["width"]<=parent["x"]+parent["width"]+2,(locale,width,"arrow out of button",child,parent)
                if expected=="en":
                    assert "A Stronger You" in page.title(),(locale,width,"English page title")
                    assert page.locator("#pricing .heading").inner_text()=="CHOOSE YOUR PLAN",(locale,width,"untranslated pricing")
                    assert page.locator("#faq .heading").inner_text().startswith("FREQUENTLY"),(locale,width,"untranslated FAQ")
                if width in (375,974,1920) and locale in ("en-US","uk-UA"):
                    page.screenshot(path=str(OUT / f"hero-{expected}-{width}.png"),full_page=False,animations="disabled")
                    page.locator(".yf-footer").screenshot(path=str(OUT / f"footer-{expected}-{width}.png"),animations="disabled",timeout=20000)
                page.close()

        page=browser.new_page(locale="en-US",viewport={"width":375,"height":812})
        page.goto(url,wait_until="domcontentloaded")
        page.wait_for_function("window.YF_I18N")
        assert page.locator("html").get_attribute("lang")=="en"
        page.locator('[data-language-choice="uk"]').click()
        assert page.locator("html").get_attribute("lang")=="uk"
        assert page.locator(".fhero-navigation a").first.inner_text()=="Про мене"
        assert page.evaluate("localStorage.getItem('yuliia-language')")=="uk"
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.YF_I18N")
        assert page.locator("html").get_attribute("lang")=="uk","manual choice not persisted"
        page.locator('[data-language-choice="en"]').click()
        assert page.locator(".fhero-navigation a").first.inner_text()=="About"
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.YF_I18N")
        assert page.locator("html").get_attribute("lang")=="en","English choice not persisted"
        page.locator("#pricing .btn").click()
        page.wait_for_timeout(150)
        assert page.locator(".yf-consultation-modal").is_visible(),"Booking modal not opening"
        assert "Your future program" in page.locator("#yf-planner-title").inner_text(),"Dynamically generated modal not translated"
        assert "Copy request" in page.locator(".yf-planner-copy").inner_text(),"Modal CTA not translated"
        page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print("PASS: device language, persisted preference, translated sections and modal, 7 social icons, demo map, responsive buttons and visible handwritten cue.")

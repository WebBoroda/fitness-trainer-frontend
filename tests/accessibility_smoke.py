"""Browser-based accessibility regression checks (not a full WCAG certification).
Chromium validates keyboard, dialog focus, headings, responsive reflow, and
representative foreground/background contrast for both light/dark modes.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"
try:
    with sync_playwright() as playwright:
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
        browser = playwright.chromium.launch(headless=True, executable_path=chrome, args=["--no-sandbox"]) if chrome else playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height in ((320,740),(375,812),(768,1024),(1440,900)):
            for theme in ("light","dark"):
                page = browser.new_page(viewport={"width":width,"height":height}, reduced_motion="reduce")
                page.add_init_script(f"localStorage.setItem('fitness-theme','{theme}');localStorage.setItem('yuliia-language','uk')")
                errors=[]
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_function("window.YF_I18N && document.querySelector('.yf-carousel-controls')", timeout=15000)
                page.keyboard.press("Tab")
                assert page.evaluate("document.activeElement.classList.contains('skip-link')"),(width,theme,"skip link not first focus")
                page.keyboard.press("Enter")
                assert page.evaluate("document.activeElement.id == 'main-content' or location.hash == '#main-content'"),(width,theme,"skip link inaccessible")
                assert page.locator("main h1").count()==1,(width,theme,"main H1")
                assert page.locator("html").get_attribute("lang")=="uk",(width,theme,"document language")
                assert page.locator("#reviews .yf-demo-review-note").is_visible(),(width,theme,"demo reviews not disclosed")
                assert page.locator(".yf-demo-flag").count()==1,(width,theme,"demo statistics not disclosed")
                missing=page.evaluate("""() => [...document.querySelectorAll('a,button,summary')]
                  .filter(el => {
                    const cs=getComputedStyle(el);
                    if (cs.visibility==='hidden' || cs.display==='none' || !el.getClientRects().length) return false;
                    return !(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') ||
                      el.textContent.trim() || el.getAttribute('title') || el.querySelector('img[alt]'));
                  }).map(el=>el.outerHTML.slice(0,200))""")
                assert not missing,(width,theme,"interactive controls without a name",missing)
                sizing=page.evaluate("""() => ['.fhero-button-primary','#about .yf-about-action',
                  '#faq summary','.yf-footer-bottom .btn'].map(selector => {
                    const r=document.querySelector(selector).getBoundingClientRect();
                    return {selector,width:r.width,height:r.height};
                  })""")
                assert all(v["height"]>=24 and v["width"]>=24 for v in sizing),(width,theme,"target below 24px",sizing)
                contrast=page.evaluate("""() => {
                  const lum=rgb => {
                    const c=rgb.match(/[\\d.]+/g).slice(0,3).map(Number)
                      .map(v=>{v=v/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});
                    return c[0]*.2126+c[1]*.7152+c[2]*.0722;
                  };
                  return [['#mission .lead','#mission'],
                    ['#about .yf-about-lead','#about'],
                    ['#reviews .review p','#reviews'],
                    ['#faq .faq-list summary','#faq']].map(([fg,bg])=>{
                      const foreground=lum(getComputedStyle(document.querySelector(fg)).color);
                      const background=lum(getComputedStyle(document.querySelector(bg)).backgroundColor);
                      const ratio=(Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05);
                      return {fg,bg,ratio};
                    });
                }""")
                assert all(x["ratio"]>=4.5 for x in contrast),(width,theme,"text contrast below AA",contrast)
                page.locator("#about [data-about-open]").click()
                assert page.locator("#yf-about-details").evaluate("(el)=>el.open"),(width,theme,"About modal")
                page.keyboard.press("Escape")
                assert not page.locator("#yf-about-details").evaluate("(el)=>el.open"),(width,theme,"Escape About")
                page.locator(".fhero-button-primary").click()
                assert page.locator("#consultation").evaluate("(el)=>el.open"),(width,theme,"consultation dialog")
                assert page.evaluate("document.activeElement.matches('#consultation select')"),(width,theme,"consultation focus")
                page.keyboard.press("Escape")
                assert not page.locator("#consultation").evaluate("(el)=>el.open"),(width,theme,"Escape consultation")
                page.locator("[data-faq-open]").click()
                assert page.locator("#faq details").first.evaluate("(el)=>el.open"),(width,theme,"FAQ destination")
                assert page.evaluate("document.activeElement.matches('#faq summary')"),(width,theme,"FAQ focus")
                page.locator("[data-results-next]").click()
                assert page.evaluate("document.activeElement.id==='results-track'"),(width,theme,"results focus")
                page.locator("[data-language-toggle]").click()
                assert page.locator("html").get_attribute("lang")=="en",(width,theme,"English lang for screen readers")
                assert page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")<=3,(width,theme,"reflow overflow")
                assert not errors,(width,theme,"uncaught JS",errors)
                page.close()
        browser.close()
finally:
    server.shutdown()
print("PASS: browser accessibility basics at mobile/tablet/desktop with light/dark and keyboard")

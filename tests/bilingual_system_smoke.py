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
        for locale, expected in (("en-US","uk"),("uk-UA","uk"),("pl-PL","uk")):
            for width,height in cases:
                page = browser.new_page(viewport={"width":width,"height":height},locale=locale, reduced_motion="reduce")
                page.goto(url,wait_until="domcontentloaded")
                page.wait_for_function("window.YF_I18N && document.querySelector('#yf-socials .yf-social-link')", timeout=15000)
                assert page.locator("html").get_attribute("lang")==expected,(locale,width,"wrong initial lang")
                assert page.locator("html").get_attribute("data-language")==expected,(locale,width,"wrong data lang")
                assert page.locator('[data-language-toggle]').count()==1,(locale,width,"single language control")
                assert page.locator('[data-language-indicator]').count()==2,(locale,width,"two visual halves")
                assert page.locator('[data-language-indicator].is-active').get_attribute('data-language-indicator')==expected,(locale,width,"active language half")
                assert "Записатися на тренування" in page.locator(".fhero-button-primary").inner_text()
                assert "Обрати програму" in page.locator(".fhero-button-secondary").inner_text()
                # Measure both boxes in the same layout frame so reveal/
                # header movement cannot introduce inter-call coordinate drift.
                centering = page.locator(".yf-language-toggle").evaluate("""el => {
                    const text = el.querySelector('.yf-language-half.is-active');
                    if (!text) return null;
                    const a=el.getBoundingClientRect(), b=text.getBoundingClientRect();
                    return [a.left+a.width/2-b.left-b.width/2,
                            a.top+a.height/2-b.top-b.height/2];
                }""")
                assert centering and abs(centering[0]) < 1 and abs(centering[1]) < 1, (locale,width,centering)
                nav = page.locator(".fhero-navigation a").first.inner_text()
                assert nav==("About" if expected=="en" else "Про мене"),(locale,width,nav)
                assert page.locator("main > section").count()==11,(locale,width,"missing sections")
                assert page.locator("#yf-socials .yf-social-link").count()==7,(locale,width,"social icons")
                assert page.locator("#yf-map").count()==1,(locale,width,"map missing")
                pads = page.evaluate("""() => ['mission','formats','studio','about','nutrition','results','reviews','pricing','faq']
                  .map(id => {
                    const st = getComputedStyle(document.getElementById(id));
                    return {id,top:parseFloat(st.paddingTop),bottom:parseFloat(st.paddingBottom)};
                  })""")
                assert all(abs(x['top']-x['bottom']) < 1 for x in pads), (locale,width,"asymmetric section padding",pads)
                shared = [x for x in pads if x['id'] != 'about' or height > 800 or width < 992]
                assert max(x['top'] for x in shared)-min(x['top'] for x in shared) < 2, (locale,width,"inconsistent section spacing",pads)
                assert page.locator('[data-results-next]').get_attribute('href') == '#results-track', (locale,width,"wrong results CTA")
                assert page.locator('#reviews .btn').get_attribute('href') == '#reviews-list', (locale,width,"wrong reviews CTA")
                assert page.locator('[data-faq-open]').get_attribute('href') == '#faq-list', (locale,width,"wrong FAQ CTA")
                assert page.locator('link[rel="canonical"]').count() == 1, (locale,width,"canonical missing")
                assert page.locator('script[type="application/ld+json"]').count() == 1, (locale,width,"structured data missing")
                route = page.locator("#yf-directions")
                assert route.get_attribute("aria-disabled") is None,(locale,width,"route remains disabled")
                assert "google.com/maps/dir/" in (route.get_attribute("href") or ""),(locale,width,"route URL missing")
                assert "50.449855" in (route.get_attribute("href") or ""),(locale,width,"route location does not match the map")
                assert page.locator("#yf-address").inner_text().strip()==("22 Khreshchatyk St, Kyiv" if expected=="en" else "м. Київ, вул. Хрещатик, 22"),(locale,width,"demo address / locale")
                assert page.locator(".yf-map-badge").is_visible(),(locale,width,"demo address disclosure hidden")
                assert page.locator(".yf-footer-socials .yf-demo-caption").count()==0,(locale,width,"obsolete social placeholder remains")
                assert page.locator(".yf-map-bottom .yf-demo-caption").count()==0,(locale,width,"obsolete route placeholder remains")
                # The two footer pills sit on independent rows above their content.
                contact_pill = page.locator(".yf-footer-info > .eyebrow").bounding_box()
                brand = page.locator(".yf-footer-brand").bounding_box()
                assert contact_pill and brand and contact_pill["y"]+contact_pill["height"]<=brand["y"]+2,(locale,width,"contact pill overlaps brand")
                # On desktop both pills must share the same top edge and height;
                # when the layout stacks, each pill stays above its content.
                # Read both rectangles in one layout frame: late font/layout
                # settlement must not make positions from different frames incomparable.
                map_pill, map_box = page.evaluate("""() => {
                  const selectors=['.yf-footer-map > .eyebrow','.yf-map-frame'];
                  return selectors.map(selector => {
                    const rect=document.querySelector(selector).getBoundingClientRect();
                    return {x:rect.x,y:rect.y,width:rect.width,height:rect.height};
                  });
                }""")
                assert map_pill and map_box, (locale,width,"map label or frame missing")
                assert abs(contact_pill["height"]-map_pill["height"])<=1, (locale,width,"different footer pill heights")
                assert map_box["y"]+1>=map_pill["y"]+map_pill["height"],(locale,width,"map overlaps its pill")
                if width > 1024:
                    assert abs(contact_pill["y"]-map_pill["y"])<=1,(locale,width,"footer pills not on one horizontal line",contact_pill,map_pill)
                    assert map_box["height"]<=302,(locale,width,"desktop map not compact",map_box)
                elif width <= 624:
                    assert 180<=map_box["height"]<=220,(locale,width,"mobile map proportions",map_box)
                else:
                    assert map_box["height"]<=230,(locale,width,"tablet map not compact",map_box)
                assert map_box["width"]>0 and map_box["height"]>0,(locale,width,"collapsed map")
                # The text-only return-to-top link must not inherit the
                # compact right padding reserved for CTAs with round icons.
                back_top = page.locator(".yf-footer-bottom > a.btn.outline")
                assert back_top.get_attribute("href")=="#top",(locale,width,"back-to-top target changed")
                padding = back_top.evaluate("""el => {
                    const css = getComputedStyle(el);
                    return {
                        left: parseFloat(css.paddingLeft),
                        right: parseFloat(css.paddingRight),
                        height: el.getBoundingClientRect().height
                    };
                }""")
                assert abs(padding["left"]-padding["right"])<=.5,(locale,width,"unequal back-to-top padding",padding)
                assert padding["left"]>=15 and padding["right"]>=15,(locale,width,"insufficient back-to-top padding",padding)
                assert padding["height"]>=43,(locale,width,"back-to-top tap target too short",padding)
                # One inter-word rhythm for all major headings. All primary
                # buttons have identical fill/edge; secondary variants only
                # differ between light and dark surfaces for contrast.
                style_audit = page.evaluate("""() => {
                    const headings = [...document.querySelectorAll(
                      '.hero.fhero h1.fhero-title, .section h2.heading, #about h2.yf-about-heading, #final-cta h2.heading'
                    )];
                    const primary = [...document.querySelectorAll(
                      '.section .btn.fill, .yf-consultation-form .btn.fill, .yf-about-dialog .btn.fill, .yf-footer .btn.fill, .fhero-header-cta, .fhero-button-primary, #final-cta .yf-final-button-primary, #pricing .price .price-action'
                    )];
                    const secondary = [...document.querySelectorAll(
                      '.section .btn.outline, .yf-footer .btn.outline, .fhero-button-secondary, #final-cta .yf-final-button-secondary'
                    )];
                    const finish = el => {
                        const s = getComputedStyle(el);
                        return [s.backgroundImage, s.borderTopColor, s.borderTopWidth, s.borderTopStyle].join('|');
                    };
                    return {
                        headingSpaces: headings.map(el => getComputedStyle(el).wordSpacing),
                        primaryFinishes: [...new Set(primary.map(finish))],
                        secondaryFinishes: [...new Set(secondary.map(finish))],
                        primaryCount: primary.length,
                        secondaryCount: secondary.length
                    };
                }""")
                assert style_audit["headingSpaces"] and all(
                    float(v.removesuffix("px")) >= 2 for v in style_audit["headingSpaces"]
                ), (locale,width,"unclear word spacing in headings",style_audit["headingSpaces"])
                assert style_audit["primaryCount"]>=12 and len(style_audit["primaryFinishes"])==1,(
                    locale,width,"primary CTA fills/borders are inconsistent",style_audit)
                assert "|1px|solid" in style_audit["primaryFinishes"][0],(
                    locale,width,"primary border missing",style_audit)
                assert style_audit["secondaryCount"]>=5 and len(style_audit["secondaryFinishes"])<=2,(
                    locale,width,"secondary CTA finishes inconsistent",style_audit)
                assert all("|1px|solid" in f for f in style_audit["secondaryFinishes"]),(
                    locale,width,"secondary border missing",style_audit)
                assert page.locator(".fhero-curve").count()==1,(locale,width,"curved video-to-handwriting arrow missing")
                assert page.locator(".fhero-curve").is_visible(),(locale,width,"curved arrow must remain visible")
                note = page.locator(".fhero-handwrite")
                assert note.is_visible(),(locale,width,"handwriting must always be visible")
                assert note.bounding_box()["height"]>8,(locale,width,"annotation has no height")
                overflow = page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow<=3,(locale,width,"horizontal overflow",overflow)
                buttons=page.locator('.section .btn .arrow,.fhero-actions .fhero-cta-circle,.fhero-actions .fhero-button-secondary .fhero-svg,.yf-footer .btn .arrow')
                # Every text-arrow circle across sections, prices, carousels and footer
                # uses a real SVG, not a font glyph that drifts with line-height.
                circles = page.locator('.section .btn .arrow, .yf-footer .btn .arrow, #pricing .price-action, .yf-carousel-controls:not([hidden]) button')
                assert circles.count() >= 15, (locale,width,"missing shared arrow circles")
                for circle in circles.all():
                    # Measure both rectangles within one animation frame.
                    # Separate browser round-trips can sample a moving reveal
                    # at two different times and report false displacement.
                    centers = circle.evaluate("""el => {
                      const icon = el.querySelector('svg.yf-arrow-svg');
                      if (!icon) return null;
                      const outer = el.getBoundingClientRect();
                      const inner = icon.getBoundingClientRect();
                      return {
                        dx: (outer.left + outer.width / 2) - (inner.left + inner.width / 2),
                        dy: (outer.top + outer.height / 2) - (inner.top + inner.height / 2)
                      };
                    }""")
                    assert centers is not None, (locale,width,"arrow missing vector icon")
                    assert abs(centers["dx"]) <= 1, (locale,width,"horizontal arrow center",centers)
                    assert abs(centers["dy"]) <= 1, (locale,width,"vertical arrow center",centers)
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
        assert page.locator("html").get_attribute("lang")=="uk"
        assert page.locator('[data-language-toggle]').count()==1,"single UA/EN button"
        assert page.locator('[data-language-indicator]').count()==2,"two language halves"
        page.locator('[data-language-toggle]').click()
        assert page.locator("html").get_attribute("lang")=="en"
        assert page.locator(".fhero-navigation a").first.inner_text()=="About"
        assert "Book a training session" in page.locator(".fhero-button-primary").inner_text()
        assert "Choose a program" in page.locator(".fhero-button-secondary").inner_text()
        assert page.evaluate("localStorage.getItem('yuliia-language')")=="en"
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.YF_I18N")
        assert page.locator("html").get_attribute("lang")=="en","English choice not persisted"
        page.locator('[data-language-toggle]').click()
        assert page.locator("html").get_attribute("lang")=="uk"
        assert "Записатися на тренування" in page.locator(".fhero-button-primary").inner_text()
        assert "Обрати програму" in page.locator(".fhero-button-secondary").inner_text()
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.YF_I18N")
        assert page.locator("html").get_attribute("lang")=="uk","Ukrainian choice not persisted"
        page.locator('[data-language-toggle]').click()
        assert page.locator("html").get_attribute("lang")=="en"
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
print("PASS: device language, persisted preference, translated sections and modal, 7 social icons, mapped demo address and active directions, responsive buttons and visible handwritten cue.")

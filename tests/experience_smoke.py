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
                              (1024, 768), (1366, 768), (1440, 900), (1536, 1024), (1920, 1080)]:
            for scheme in ("dark", "light"):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    color_scheme=scheme,
                    device_scale_factor=1
                )
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.add_init_script("if (!localStorage.getItem('fitness-theme')) localStorage.setItem('fitness-theme','" + scheme + "');localStorage.setItem('yuliia-language','uk');")
                response = page.goto(url, wait_until="networkidle", timeout=45000)
                assert response and response.ok, (width, response.status if response else None)
                assert page.locator("main section").count() == 11, width
                assert page.locator("#formats .program-card").count() == 4
                assert page.locator("#formats .program-card .ico svg").count() == 4
                assert page.locator("#about .yf-about-heading").count() == 1
                assert page.locator("#about .yf-about-kicker").evaluate('(el)=>getComputedStyle(el,"::before").content') == 'none', (width,"old label line")
                label_radius = page.locator('#about .yf-about-kicker').evaluate('(el)=>parseFloat(getComputedStyle(el).borderRadius)')
                assert label_radius > 20, (width,"About label should be pill")
                about_button = page.locator('#about [data-about-open]')
                assert about_button.count() == 1 and about_button.is_visible(), (width,"About CTA missing")
                weights = page.locator('#about .yf-about-heading span').evaluate_all('(els)=>els.map(el=>parseFloat(getComputedStyle(el).fontWeight))')
                assert len(weights) == 3 and weights[0] >= 700 and weights[1] < 400 and weights[2] < 400, (width, scheme, weights)
                assert page.locator("#about .yf-about-benefits li").count() == 3
                assert page.locator("#about .yf-about-quote blockquote").count() == 0
                assert page.locator("#about blockquote.yf-about-quote").count() == 1
                about_image = page.locator('#about img[data-media-field="about.portrait"]')
                about_frame = page.locator('#about .yf-about-media')
                quote_box = page.locator('#about .yf-about-quote')
                assert about_image.count() == 1, (width, "missing replaceable portrait")
                assert about_image.get_attribute('src') == "assets/images/about-trainer-editorial.webp", width
                assert about_image.get_attribute('alt'), width
                assert float(about_frame.evaluate("(el)=>getComputedStyle(el).borderTopLeftRadius.replace('px','')")) >= 10, (width, "unrounded photo frame")
                assert quote_box.count() == 1 and quote_box.locator('cite').count() == 0, (width, 'removed signature must not reappear')
                quote_text = quote_box.inner_text()
                assert "правильну підтримку" in quote_text, width
                assert not quote_box.evaluate('(el)=>el.closest(".yf-about-media") !== null'), (width, "quote must be beside photo, not over it")
                if width >= 1024 and height >= 700:
                    page.locator('#about .reveal').evaluate_all('(els)=>els.forEach(el=>{el.style.transition="none";el.classList.add("visible")})')
                    geometry = page.evaluate("""() => {
                      const a=document.querySelector('#about').getBoundingClientRect();
                      const im=document.querySelector('#about .yf-about-media').getBoundingClientRect();
                      const q=document.querySelector('#about .yf-about-quote').getBoundingClientRect();
                      const btn=document.querySelector('#about .yf-about-action').getBoundingClientRect();
                      return {sectionHeight:a.height, photoBottom:im.bottom, quoteBottom:q.bottom, buttonBottom:btn.bottom, sectionBottom:a.bottom};
                    }""")
                    assert geometry['sectionHeight'] <= height + 2, (width,height,"About exceeds viewport",geometry)
                    assert max(geometry['photoBottom'],geometry['quoteBottom'],geometry['buttonBottom']) <= geometry['sectionBottom'] - 5, (width,height,"About content clipped",geometry)
                about_button.click()
                assert page.locator('#yf-about-details').evaluate('(el)=>el.open'), (width,"About details did not open")
                assert page.locator('#yf-about-details h2').is_visible(), width
                page.keyboard.press('Escape')
                assert not page.locator('#yf-about-details').evaluate('(el)=>el.open'), (width,"Escape close failed")
                original_src = about_image.get_attribute('src')
                about_image.evaluate("(el)=>el.setAttribute('src','assets/images/gym-01-main.webp')")
                assert quote_box.inner_text() == quote_text, (width, "quote changed on photo replacement")
                assert float(about_frame.evaluate("(el)=>getComputedStyle(el).borderTopLeftRadius.replace('px','')")) >= 10, (width, "radius changed on photo replacement")
                about_image.evaluate("(el,src)=>el.setAttribute('src',src)",original_src)
                assert page.locator("#mission .quote").count() == 0
                assert page.locator("#pricing .price-action").count() == 3
                assert page.locator("img[src^='data:']").count() == 0
                assert page.locator("html").get_attribute("data-theme") == scheme
                assert page.locator(".studio-gallery .gallery-photo").count() == 5
                assert page.locator(".studio-gallery .gallery-photo:visible").count() == 3
                expected = ["gym-01-main.webp","gym-02-dumbbells.webp","gym-03-cardio.webp","gym-04-strength.webp","gym-05-stretching.webp"]
                paths = page.locator("#studio .studio-gallery img").evaluate_all("(items)=>items.map(img=>img.getAttribute('src').split('/').pop())")
                assert paths == expected, (width,paths)
                nutrition = page.locator("#nutrition")
                assert nutrition.locator(".nutrition-copy .eyebrow").inner_text() == "ХАРЧУВАННЯ", (width, "nutrition eyebrow")
                assert nutrition.locator(".nutrition-aside li").count() == 5, (width, "nutrition checklist")
                assert nutrition.locator(".nutrition-note").count() == 1, width
                nutrition_photo = nutrition.locator("img.nutrition-photo")
                assert nutrition_photo.get_attribute("src") == "assets/images/formats-nutrition.webp", (width, "low-res source remains")
                assert nutrition_photo.get_attribute("width") == "1086", width
                assert nutrition_photo.get_attribute("alt"), width
                nutrition_photo.scroll_into_view_if_needed()
                nutrition_photo.evaluate("(el)=>el.decode()")
                assert nutrition_photo.evaluate("(el)=>el.naturalWidth === 1086 && el.naturalHeight === 1448"), (width, "high-res nutrition photo not loaded")
                assert nutrition.locator('.btn[href="#consultation"]').count() == 1, (width, "nutrition CTA")
                assert nutrition.evaluate('(el)=>el.scrollWidth <= el.clientWidth + 2'), (width, "nutrition horizontal overflow")
                nutrition_boxes = nutrition.evaluate("""el=>{
                  const rect=q=>{const r=el.querySelector(q).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height};};
                  return {section:el.getBoundingClientRect().toJSON(),copy:rect('.nutrition-copy'),photo:rect('.nutrition-visual'),aside:rect('.nutrition-aside'),note:rect('.nutrition-note')};
                }""")
                if 672 <= width < 1024:
                    assert nutrition_boxes["copy"]["y"] <= nutrition_boxes["photo"]["y"] + 3, (width, "tablet heading must precede image and checklist", nutrition_boxes)
                    assert nutrition_boxes["copy"]["right"] <= nutrition_boxes["photo"]["x"] + 3, (width, "tablet columns overlap", nutrition_boxes)
                    assert nutrition_boxes["aside"]["y"] >= max(nutrition_boxes["copy"]["bottom"],nutrition_boxes["photo"]["bottom"]) - 3, (width, "tablet benefits must follow first row", nutrition_boxes)
                if width >= 1024:
                    assert nutrition_boxes["section"]["height"] <= height + 2, (width,height,"nutrition exceeds one desktop viewport",nutrition_boxes)
                    assert nutrition_boxes["copy"]["right"] < nutrition_boxes["photo"]["x"] + 2, (width,"nutrition columns collide",nutrition_boxes)
                    assert nutrition_boxes["photo"]["right"] < nutrition_boxes["aside"]["x"] + 2, (width,"nutrition column order",nutrition_boxes)
                elif width <= 670:
                    assert nutrition_boxes["photo"]["y"] >= nutrition_boxes["copy"]["bottom"] - 2, (width,"mobile photo overlaps description",nutrition_boxes)
                    assert nutrition_boxes["aside"]["y"] >= nutrition_boxes["photo"]["bottom"] - 2, (width,"mobile benefits overlap photo",nutrition_boxes)
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
                assert page.locator(".yf-gallery-modal").evaluate("(el)=>el.open"), (width,errors,page.evaluate("""() => ({markup: document.querySelector('.yf-gallery-modal')?.innerHTML.slice(0,1000), hasTrack: !!document.querySelector('.yf-gallery-mobile-track'), scriptType: typeof window.matchMedia})"""))
                buttons = page.locator(".yf-gallery-controls button")
                def bounds():
                    return [button.bounding_box() for button in buttons.all()]
                is_mobile = width < 768
                assert all(button.is_visible() != is_mobile for button in buttons.all()), (width, "gallery arrow visibility")

                def swipe(start_x, start_y, end_x, end_y):
                    # Real Chromium touch input; assert the slide follows the
                    # finger BEFORE release, then returns to centered position.
                    devtools = page.context.new_cdp_session(page)
                    devtools.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})
                    devtools.send("Input.dispatchTouchEvent", {
                        "type": "touchStart",
                        "touchPoints": [{"x": start_x, "y": start_y, "id": 1}]
                    })
                    mid_x, mid_y = (start_x + end_x)//2, (start_y + end_y)//2
                    for px,py in [(mid_x,mid_y),(end_x,end_y)]:
                        devtools.send("Input.dispatchTouchEvent", {
                            "type": "touchMove",
                            "touchPoints": [{"x": px, "y": py, "id": 1}]
                        })
                    strip = page.locator(".yf-gallery-mobile-track")
                    if abs(end_x-start_x) > abs(end_y-start_y)*1.4:
                        assert "calc(" in strip.evaluate("(el)=>el.style.transform"), (width,"image not following finger")
                    devtools.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    devtools.detach()
                    page.wait_for_function("""() => {
                      const el = document.querySelector('.yf-gallery-mobile-track');
                      if (!el || el.style.transition !== 'none') return false;
                      const width = el.getBoundingClientRect().width;
                      const x = new DOMMatrixReadOnly(getComputedStyle(el).transform).m41;
                      return Math.abs(x + width) < 2;
                    }""",timeout=2400)

                if not is_mobile:
                    fixed_boxes = bounds()
                    for control, box in zip(buttons.all(), fixed_boxes):
                        vector = control.locator(".yf-arrow-svg").bounding_box()
                        assert box and vector and abs((box["x"]+box["width"]/2)-(vector["x"]+vector["width"]/2))<=1, ("arrow x centered",width)
                        assert abs((box["y"]+box["height"]/2)-(vector["y"]+vector["height"]/2))<=1, ("arrow y centered",width)
                        assert abs((box["y"]+box["height"]/2)-height/2)<=2, ("arrows must be viewport-fixed vertically",width,box)
                    assert fixed_boxes[0]["x"] < width * .12 and fixed_boxes[1]["x"] > width * .80, (width,fixed_boxes)

                photo_first = page.locator(".yf-gallery-modal figure > img").get_attribute("src")
                assert photo_first.endswith("gym-01-main.webp"), (width,photo_first)
                viewport = page.locator(".yf-gallery-mobile-viewport")
                if is_mobile:
                    assert viewport.is_visible() and page.locator(".yf-gallery-mobile-track img").count()==3, width
                    stage = viewport.bounding_box()
                    assert abs(stage["height"]-min(stage["width"]*9/16,height*.65))<=3,(width,"mobile gallery must remain compact",stage)
                    assert page.locator(".yf-gallery-modal figure>img").is_hidden(), width
                fig_box = (viewport if is_mobile else page.locator(".yf-gallery-modal figure")).bounding_box()
                for photo_index in range(1,5):
                    if is_mobile:
                        swipe(int(fig_box["x"]+fig_box["width"]*.70),
                              int(fig_box["y"]+fig_box["height"]*.5),
                              int(fig_box["x"]+fig_box["width"]*.25),
                              int(fig_box["y"]+fig_box["height"]*.5))
                    else:
                        buttons.nth(1).click()
                    current = page.locator(".yf-gallery-modal figure > img").get_attribute("src")
                    assert current.endswith(expected[photo_index]), (width,photo_index,current)
                    assert f"{photo_index+1} / 5" in page.locator(".yf-gallery-modal figcaption").inner_text()
                    if not is_mobile:
                        for original, current_box in zip(fixed_boxes, bounds()):
                            assert abs(original["x"]-current_box["x"])<1 and abs(original["y"]-current_box["y"])<1, (width,"arrows moved with image",original,current_box)
                if is_mobile:
                    # A largely vertical gesture must never change the selected photo.
                    before_vertical = page.locator(".yf-gallery-modal figure > img").get_attribute("src")
                    swipe(int(fig_box["x"]+fig_box["width"]*.5),
                          int(fig_box["y"]+fig_box["height"]*.25),
                          int(fig_box["x"]+fig_box["width"]*.53),
                          int(fig_box["y"]+fig_box["height"]*.75))
                    assert page.locator(".yf-gallery-modal figure > img").get_attribute("src") == before_vertical, (width,"vertical gesture incorrectly changed photo")
                    swipe(int(fig_box["x"]+fig_box["width"]*.25),
                          int(fig_box["y"]+fig_box["height"]*.5),
                          int(fig_box["x"]+fig_box["width"]*.70),
                          int(fig_box["y"]+fig_box["height"]*.5))
                    assert page.locator(".yf-gallery-modal figure > img").get_attribute("src").endswith(expected[3]), (width,"right swipe should go back")
                    swipe(int(fig_box["x"]+fig_box["width"]*.70),
                          int(fig_box["y"]+fig_box["height"]*.5),
                          int(fig_box["x"]+fig_box["width"]*.25),
                          int(fig_box["y"]+fig_box["height"]*.5))
                    assert page.locator(".yf-gallery-modal figure > img").get_attribute("src").endswith(expected[4]), (width,"forward swipe should restore fifth photo")
                    # Moving forward once more wraps the last photo to the first.
                    swipe(int(fig_box["x"]+fig_box["width"]*.70),
                          int(fig_box["y"]+fig_box["height"]*.5),
                          int(fig_box["x"]+fig_box["width"]*.25),
                          int(fig_box["y"]+fig_box["height"]*.5))
                else:
                    buttons.nth(1).click()
                assert page.locator(".yf-gallery-modal figure > img").get_attribute("src") == photo_first, (width,"gallery navigation wrap")
                if width in (375, 768, 1440):
                    page.locator(".yf-gallery-modal").screenshot(path=str(SHOTS / f"gallery-controls-{width}-{scheme}.png"), animations="disabled")
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
                if width in (375, 768, 1024, 1366, 1440) and scheme in ("light", "dark"):
                    page.evaluate("document.activeElement?.blur()")
                    nutrition.scroll_into_view_if_needed()
                    nutrition.locator('.reveal').evaluate_all("(els)=>els.forEach(el=>{el.style.transition='none';el.classList.add('visible')})")
                    nutrition.screenshot(path=str(SHOTS / f"nutrition-{width}-{scheme}.png"), animations="disabled", timeout=30000)
                if width in (375, 768, 1440) and scheme in ("light", "dark"):
                    about_section = page.locator('#about')
                    about_section.scroll_into_view_if_needed()
                    about_section.locator('.reveal').evaluate_all("(els)=>els.forEach(el=>el.classList.add('visible'))")
                    about_image.evaluate("(el)=>el.decode().catch(()=>{})")
                    about_section.screenshot(path=str(SHOTS / f"about-{width}-{scheme}.png"), animations="disabled")
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

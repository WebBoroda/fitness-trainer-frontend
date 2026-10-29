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
                # Closing hero: generated photographic asset, without old FAQ pixels, crop masks or transforms.
                closing = page.locator(".final-section")
                final_image = closing.locator("img.final-photo")
                assert final_image.count() == 1, (width, "closing photo absent")
                assert final_image.get_attribute("src") == "assets/images/final-cta-trainer.webp", (width, "old screenshot crop remains")
                assert final_image.get_attribute("loading") == "lazy", width
                final_image.scroll_into_view_if_needed()
                final_image.evaluate("(img)=>img.decode()")
                assert final_image.evaluate("(img)=>img.naturalWidth===1600 && img.naturalHeight===900"), (width, "new hero photo failed to decode")
                style = final_image.evaluate("(img)=>({mask:getComputedStyle(img).maskImage,transform:getComputedStyle(img).transform})")
                assert style["mask"] == "none" and style["transform"] == "none", (width, "legacy photo crop effect remains",style)
                # Closing actions reuse first-screen hero button styling.
                for href, variant in (("#consultation","yf-final-button-primary"),("#formats","yf-final-button-secondary")):
                    action = closing.locator(f'.actions a[href="{href}"]')
                    assert action.count()==1 and action.is_visible(), (width, "closing CTA missing",href)
                    assert "yf-final-button" in (action.get_attribute("class") or "").split(), (width,scheme,"missing hero CTA component",href)
                    assert variant in (action.get_attribute("class") or "").split(), (width,scheme,"closing CTA reference variant",href)
                    assert action.locator(".yf-final-circle .yf-final-svg").count()==1, (width,scheme,"hero CTA arrow missing",href)
                closing_theme = closing.evaluate("""(el)=>({
                    bg:getComputedStyle(el).backgroundColor,
                    fg:getComputedStyle(el).color,
                    gradient:getComputedStyle(el,"::after").backgroundImage.replace(/\\s/g,""),
                    photoOpacity:getComputedStyle(el.querySelector(".final-photo")).opacity,
                    heading:getComputedStyle(el.querySelector(".heading")).color,
                    label:getComputedStyle(el.querySelector(".final-benefits strong")).color,
                    subtitle:getComputedStyle(el.querySelector(".final-content>p")).color,
                    cta:getComputedStyle(el.querySelector(".yf-final-button-secondary")).color
                })""")
                expected_background = "rgb(246, 240, 234)" if scheme=="light" else "rgb(18, 18, 16)"
                expected_foreground = "rgb(27, 23, 21)" if scheme=="light" else "rgb(255, 255, 255)"
                assert closing_theme["bg"] == expected_background, (width,scheme,"closing theme background",closing_theme)
                assert closing_theme["fg"] == expected_foreground, (width,scheme,"closing theme foreground",closing_theme)
                assert closing_theme["heading"] == expected_foreground, (width,scheme,"closing headline contrast",closing_theme)
                assert closing_theme["label"] == expected_foreground, (width,scheme,"closing feature contrast",closing_theme)
                assert closing_theme["photoOpacity"] == "1", (width,scheme,"closing photograph dimmed",closing_theme)
                curve=closing_theme["gradient"]
                assert "linear-gradient(" in curve and ("transparent" in curve or "rgba(0,0,0,0)" in curve), (width,scheme,"closing gradient absent",curve)
                if width > 670:
                    expected_tint = "rgba(246,240,234,0.3)" if scheme=="light" else "rgba(18,18,16,0.77)"
                    expected_end = "65%" if scheme=="light" else "75%"
                    assert expected_tint in curve and expected_end in curve, (width,scheme,"wrong photo-studio reference gradient strength",curve)
                    assert "90deg" in curve and "180deg" not in curve, (width,scheme,"desktop gradient must be horizontal",curve)
                else:
                    expected_tint = "rgba(246,240,234,0.88)" if scheme=="light" else "rgba(18,18,16,0.91)"
                    assert expected_tint in curve and "90deg" not in curve, (width,scheme,"mobile gradient strength or direction",curve)
                # No opaque matte over the image in any theme.
                assert "rgb(18,18,16)49%" not in curve and "#121210" not in curve, (width,scheme,"legacy solid veil remains",curve)
                assert closing.locator(".final-benefits li").count() == 3, (width, "closing advantages")
                assert closing.locator(".final-benefit-icon svg").count() == 3, (width, "missing vector feature icons")
                assert "Персональний план" in closing.locator(".final-content > p").inner_text(), (width,"closing reference copy")
                geometry = closing.evaluate("""(el)=>{
                    const rect=(q)=>{const r=(q===':scope'?el:el.querySelector(q)).getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
                    const photo=el.querySelector('.final-photo');
                    const css=getComputedStyle(photo);
                    return {section:rect(':scope'),content:rect('.final-content'),features:rect('.final-benefits'),
                      heading:rect('.heading'),photoWidth:parseFloat(css.width),overflow:el.scrollWidth-el.clientWidth,
                      items:[...el.querySelectorAll('.final-benefits li')].map(li=>{const r=li.getBoundingClientRect();return {left:r.left,top:r.top,bottom:r.bottom}})};
                }""")
                assert geometry["overflow"] <= 2, (width,scheme,"closing overflow",geometry)
                assert geometry["content"]["bottom"] < geometry["features"]["top"]+4, (width,scheme,"closing copy/benefits overlap",geometry)
                if width >= 1120:
                    assert geometry["section"]["height"] <= height + 2, (width,scheme,"closing exceeds viewport",geometry)
                    assert geometry["features"]["bottom"] <= geometry["section"]["bottom"]-max(48,height*.08), (width,scheme,"closing benefits too low or clipped",geometry)
                    assert geometry["items"][0]["left"] < geometry["items"][1]["left"] < geometry["items"][2]["left"], (width,scheme,"closing benefits must run horizontally",geometry)
                    assert abs(geometry["photoWidth"]-width) <= 2, (width,scheme,"final photo must fill section as first hero",geometry)
                elif width <= 670:
                    assert geometry["items"][0]["top"] < geometry["items"][1]["top"] < geometry["items"][2]["top"], (width,scheme,"mobile closing benefits must stack",geometry)
                if width in (375,768,1024,1440,1536,1920):
                    closing.locator(".reveal").evaluate("(el)=>{el.style.transition='none';el.classList.add('visible')}")
                    closing.screenshot(path=str(SHOTS / f"final-cta-{width}-{scheme}.png"), animations="disabled", timeout=30000)

                # Secondary actions explain more content, not conversion.
                for selector in ("#results .btn", "#reviews .btn", "#faq .btn"):
                    cta = page.locator(selector)
                    assert cta.count() == 1, (width, scheme, selector, "missing CTA")
                    assert "outline" in (cta.get_attribute("class") or "").split(), (width, scheme, selector, "secondary CTA must be outlined")
                    assert "fill" not in (cta.get_attribute("class") or "").split(), (width, scheme, selector, "secondary CTA wrongly accented")
                    paint = cta.evaluate("(el)=>({bg:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderTopWidth})")
                    assert paint["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), (width, scheme, selector, paint)
                    assert float(paint["border"].replace("px", "")) >= 1, (width, scheme, selector, paint)
                for selector in ("#mission .btn.fill", "#nutrition .btn.fill"):
                    assert page.locator(selector).count() == 1, (width, scheme, selector, "conversion CTA accidentally changed")

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
                nutrition_frame_style = nutrition.locator('.nutrition-visual').evaluate("""el=>{
                    const cs=getComputedStyle(el),box=el.getBoundingClientRect();
                    return {radii:[cs.borderTopLeftRadius,cs.borderTopRightRadius,cs.borderBottomRightRadius,cs.borderBottomLeftRadius].map(v=>parseFloat(v)),
                            ratio:box.width/box.height,overflow:cs.overflow};
                }""")
                assert all(abs(r - nutrition_frame_style['radii'][0]) < .1 for r in nutrition_frame_style['radii']), (width, "nutrition corners must have equal radius", nutrition_frame_style)
                assert 8 <= nutrition_frame_style['radii'][0] <= 16, (width, "nutrition corner radius differs from site photo cards", nutrition_frame_style)
                assert abs(nutrition_frame_style['ratio'] - 4/3) <= .025, (width, "nutrition photo must be rectangular 4:3", nutrition_frame_style)
                assert nutrition_photo.evaluate("(el)=>getComputedStyle(el).clipPath") == 'none', (width, "legacy circle clip still applies")
                assert nutrition.locator('.btn[href="#consultation"]').count() == 1, (width, "nutrition CTA")
                assert nutrition.evaluate('(el)=>el.scrollWidth <= el.clientWidth + 2'), (width, "nutrition horizontal overflow")
                nutrition_boxes = nutrition.evaluate("""el=>{
                  const rect=q=>{const r=el.querySelector(q).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height};};
                  return {section:el.getBoundingClientRect().toJSON(),copy:rect('.nutrition-copy'),photo:rect('.nutrition-visual'),aside:rect('.nutrition-aside'),note:rect('.nutrition-note')};
                }""")
                if 672 <= width < 1024:
                    assert nutrition_boxes["copy"]["y"] < nutrition_boxes["photo"]["bottom"] - 4, (width, "tablet heading must precede image and checklist", nutrition_boxes)
                    assert nutrition_boxes["copy"]["right"] <= nutrition_boxes["photo"]["x"] + 3, (width, "tablet columns overlap", nutrition_boxes)
                    assert nutrition_boxes["aside"]["y"] >= max(nutrition_boxes["copy"]["bottom"],nutrition_boxes["photo"]["bottom"]) - 3, (width, "tablet benefits must follow first row", nutrition_boxes)
                if width >= 1024:
                    assert nutrition_boxes["section"]["height"] <= height + 2, (width,height,"nutrition exceeds one desktop viewport",nutrition_boxes)
                    assert nutrition_boxes["copy"]["right"] < nutrition_boxes["photo"]["x"] + 2, (width,"nutrition columns collide",nutrition_boxes)
                    assert nutrition_boxes["photo"]["right"] < nutrition_boxes["aside"]["x"] + 2, (width,"nutrition column order",nutrition_boxes)
                elif width <= 670:
                    assert nutrition_boxes["photo"]["y"] >= nutrition_boxes["copy"]["bottom"] - 2, (width,"mobile photo overlaps description",nutrition_boxes)
                    assert nutrition_boxes["aside"]["y"] >= nutrition_boxes["photo"]["bottom"] - 2, (width,"mobile benefits overlap photo",nutrition_boxes)
                results_section = page.locator("#results")
                demo_cards = results_section.locator(".yf-result-card")
                assert demo_cards.count() == 6, (width, "six demo before/after images required")
                assert results_section.locator(".yf-results-disclaimer").count() == 0, (width, "duplicate disclaimer remains")
                for j, card in enumerate(demo_cards.all(), 1):
                    photo = card.locator("img")
                    assert photo.get_attribute("src") == f"assets/images/result-demo-{j:02d}.webp", (width, j, "missing generated image")
                    photo.scroll_into_view_if_needed()
                    photo.evaluate("(el)=>el.decode()")
                    assert photo.evaluate("(el)=>el.naturalWidth === 900 && el.naturalHeight === 1200"), (width,j,"wrong image dimensions")
                    assert "ШІ-візуалізація" in photo.get_attribute("alt"), (width,j,"missing illustrative alt")
                    assert card.locator("figcaption span").count() == 2, (width,j,"before/after labels")
                    assert card.locator(".yf-result-ai").count() == 1, (width,j,"on-photo AI badge missing")
                    assert card.locator(".yf-result-ai").inner_text().strip() == "AI-демо", (width,j,"incorrect AI label")
                result_track = results_section.locator("#results-track")
                assert result_track.get_attribute("tabindex") == "0", (width, "gallery keyboard navigation")
                assert result_track.evaluate("(el)=>el.scrollWidth > el.clientWidth"), (width, "gallery has no overflow")
                result_track.evaluate("(el)=>{el.style.scrollBehavior='auto';el.scrollLeft=0}")
                carousel_buttons = results_section.locator(".yf-carousel-controls button")
                assert carousel_buttons.count() == 2, (width, "existing carousel arrows missing")
                carousel_buttons.nth(1).click()
                page.wait_for_function("document.getElementById('results-track').scrollLeft > 0", timeout=3000)
                result_track.evaluate("(el)=>el.scrollLeft=0")
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
                if width in (375, 768, 1440) and scheme in ("light", "dark"):
                    results_section.scroll_into_view_if_needed()
                    results_section.locator(".reveal").evaluate_all("(els)=>els.forEach(el=>{el.style.transition='none';el.classList.add('visible')})")
                    result_track.evaluate("(el)=>el.scrollLeft=0")
                    results_section.screenshot(path=str(SHOTS / f"results-{width}-{scheme}.png"), animations="disabled", timeout=30000)
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

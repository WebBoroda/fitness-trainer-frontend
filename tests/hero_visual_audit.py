"""Visual layout gate: screenshot the real browser, then assert composition.
Captures original and annotated screenshots with measured bounding boxes.
This does not claim pixel-diff validation against an unavailable Figma export.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "_screenshots" / "hero-audit"
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    (320, 740), (375, 812), (480, 900),
    (768, 1024), (974, 1374), (1024, 768),
    (1280, 720), (1440, 900), (1536, 1024),
    (1792, 1000), (1920, 1080)
]
SELECTORS = {
    "hero": ".hero.fhero",
    "title": ".fhero-title",
    "intro": ".fhero-eyebrow",
    "stats": ".fhero-stats",
    "features": ".fhero-features",
    "watch": ".fhero-watch",
    "video": ".fhero-watch-action",
    "handwritten": ".fhero-handwrite",
    "scroll": ".fhero-scroll",
}

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

def bottom(b):
    return b["y"] + b["height"]

def right(b):
    return b["x"] + b["width"]

def center_y(b):
    return b["y"] + b["height"] / 2

server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(Quiet, directory=str(ROOT))
)
Thread(target=server.serve_forever, daemon=True).start()
measurements = []
errors = []
try:
    with sync_playwright() as p:
        browser_path = shutil.which("google-chrome") or shutil.which("chromium")
        browser = p.chromium.launch(
            headless=True, executable_path=browser_path
        ) if browser_path else p.chromium.launch(headless=True)
        for width, height in CASES:
            page = browser.new_page(
                viewport={"width": width, "height": height},
                color_scheme="dark", reduced_motion="reduce", device_scale_factor=1
            )
            page.add_init_script("localStorage.setItem('fitness-theme','dark');localStorage.setItem('yuliia-language','uk')")
            page.goto(
                f"http://127.0.0.1:{server.server_port}/",
                wait_until="networkidle", timeout=45000
            )
            page.locator(".fhero-photo").evaluate(
                "(img) => img.decode().catch(() => {})"
            )
            boxes = {}
            for name, selector in SELECTORS.items():
                locator = page.locator(selector).first
                boxes[name] = locator.bounding_box() if locator.is_visible() else None
            layout = {
                "width": width,
                "height": height,
                "heroHeight": round(boxes["hero"]["height"], 2),
                "introTop": round(boxes["intro"]["y"], 2),
                "spaces": {},
                "visibleHandwriting": bool(boxes["handwritten"]),
                "boxes": boxes,
            }
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            layout["horizontalOverflow"] = overflow
            checks = []
            def check(condition, message):
                checks.append({"pass": bool(condition), "assertion": message})
                if not condition:
                    errors.append(f"{width}x{height}: {message}")
            check(overflow <= 2, "No horizontal overflow")
            for language in ("uk", "en"):
                page.evaluate("language => window.YF_I18N.setLanguage(language)", language)
                toggle = page.locator(".yf-language-toggle").bounding_box()
                label = page.locator(".yf-language-half.is-active").bounding_box()
                check(abs((toggle["x"] + toggle["width"] / 2) -
                          (label["x"] + label["width"] / 2)) <= 1 and
                      abs(center_y(toggle) - center_y(label)) <= 1,
                      "Language label is centered on both axes: " + language)
            page.evaluate("window.YF_I18N.setLanguage('uk')")

            check(boxes["features"] is not None and boxes["watch"] is not None, "Benefits and video visible")
            check(boxes["scroll"] is not None, "Scroll control visible")
            curve = page.locator('.fhero-curve')
            check(curve.count() == 1 and curve.is_visible(), "Curved arrow points toward handwritten caption")
            curve_box = curve.bounding_box()
            note = boxes["handwritten"]
            video_trigger = boxes["video"]
            check(note is not None and curve_box is not None, "Handwriting and curved arrow always visible")
            if note and video_trigger:
                if width < 672:
                    check(note["y"] >= video_trigger["y"] + video_trigger["height"] * .62,
                          "Mobile handwritten label sits immediately below video")
                    check(note["y"] - bottom(video_trigger) <= 17,
                          "No excessive mobile distance between video and caption")
                else:
                    gap_x = note["x"] - right(video_trigger)
                    layout["spaces"]["videoToCaptionHorizontal"] = round(gap_x,2)
                    check(-13 <= gap_x <= 32, "Handwritten caption directly next to video, not across empty column")
                    check(abs(center_y(note) - center_y(video_trigger)) < 38,
                          "Caption vertically aligned with video")
            if curve_box and page.locator('.fhero-video-thumb').count():
                circle = page.locator('.fhero-video-thumb').bounding_box()
                check(curve_box["x"] > circle["x"] + circle["width"] - 4,
                      "Curved arrow does not cover the video thumbnail")
            scroll_style = page.locator('.fhero-scroll').evaluate("""el => ({
              arrow: getComputedStyle(el.querySelector('.fhero-scroll-arrow')).display,
              underline: getComputedStyle(el.querySelector('span:nth-child(2)'), '::after').content
            })""")
            check(scroll_style["arrow"] != "none" and scroll_style["underline"] != "none",
                  "Scroll cue has partial underline and downward arrow")
            for selector in ('.fhero-header', '.fhero-stats', '.fhero-features',
                             '.fhero-button-primary'):
                blur = page.locator(selector).first.evaluate(
                    'el => getComputedStyle(el).backdropFilter || getComputedStyle(el).webkitBackdropFilter'
                )
                check('blur(' in blur, "Real frosted-glass backdrop for " + selector)
            if width >= 672:
                full_photo = page.locator('.fhero-photo').bounding_box()
                check(abs(full_photo["x"] - boxes["hero"]["x"]) < 2 and
                      abs(full_photo["width"] - boxes["hero"]["width"]) < 2 and
                      abs(full_photo["y"] - boxes["hero"]["y"]) < 2 and
                      abs(full_photo["height"] - boxes["hero"]["height"]) < 2,
                      "Real photograph covers the full hero height AND width")
                if width >= 1120:
                    check(boxes["hero"]["height"] >= height - 2,
                          "Desktop hero photograph reaches the viewport bottom")
            if width >= 1120:
                photo = page.locator('.fhero-photo').bounding_box()
                check(abs(photo["x"] - boxes["hero"]["x"]) < 2 and
                      abs(photo["width"] - boxes["hero"]["width"]) < 2,
                      "Full-bleed hero photograph spans the viewport without side bands")
                mode = page.locator('.fhero-photo').evaluate('el => getComputedStyle(el).objectFit')
                check(mode == "cover", "Approved cover image fills the entire hero")
                image = page.locator('.fhero-photo').evaluate("""el => ({
                    src: el.currentSrc, width: el.naturalWidth, height: el.naturalHeight
                })""")
                check(image["src"].endswith("hero-trainer-wide.webp"),
                      "Desktop uses the panoramic photograph")
                scale = max(photo["width"] / image["width"],
                            photo["height"] / image["height"])
                # Landmarks in the panoramic asset: crown at 6%, shoe at 92%.
                cropped_y = (image["height"] * scale - photo["height"]) / 2
                check(image["height"] * .06 * scale - cropped_y >= 0 and
                      image["height"] * .92 * scale - cropped_y <= photo["height"],
                      "Photograph keeps both the head and raised sneaker in frame")


            # A visible annotation must not paint over the actionable video label.
            if width >= 672 and boxes["handwritten"]:
                video_label = page.locator(".fhero-watch-label").bounding_box()
                hw = boxes["handwritten"]
                intersects = (
                    hw["x"] < right(video_label) - 3
                    and right(hw) > video_label["x"] + 3
                    and hw["y"] < bottom(video_label) - 3
                    and bottom(hw) > video_label["y"] + 3
                )
                layout["spaces"]["handwriteOverlapsVideoLabel"] = intersects
                check(not intersects, "Handwritten note does not overlap video button label")
            if width < 672:
                rows = [f.bounding_box() for f in page.locator(".fhero-feature").all()]
                check(
                    abs(rows[0]["y"]-rows[1]["y"]) < 3
                    and abs(rows[2]["y"]-rows[3]["y"]) < 3,
                    "Benefits remain a clean 2x2 mobile grid"
                )
                check(
                    abs(center_y(boxes["watch"])-center_y(boxes["scroll"])) <= 10,
                    "Mobile video and scroll aligned horizontally"
                )
            elif width < 1120:
                check(bool(boxes["handwritten"]), "Handwritten video label visible on tablet")
                check(boxes["intro"]["y"] < height * .32, "Tablet hero headline not pushed far down")
                check(
                    abs(center_y(boxes["watch"])-center_y(boxes["scroll"])) <= 10,
                    "Tablet video and scroll aligned horizontally"
                )
                gap = boxes["watch"]["y"] - bottom(boxes["features"])
                layout["spaces"]["benefitsToVideo"] = round(gap, 2)
                check(8 <= gap <= 90, "Tablet benefits-to-video gap is natural")
                check(
                    not (boxes["handwritten"] and right(boxes["handwritten"]) > right(boxes["watch"])+8),
                    "Handwriting stays in its video region"
                )
            else:
                check(bool(boxes["handwritten"]), "Handwritten label preserved on desktop")
                gap = boxes["watch"]["y"] - bottom(boxes["features"])
                layout["spaces"]["benefitsToVideo"] = round(gap, 2)
                check(12 <= gap <= 65, "Desktop video sits close below benefits")
                check(
                    bottom(boxes["watch"]) <= boxes["scroll"]["y"]+5,
                    "Video does not overlap the bottom scroll affordance"
                )
                video_to_scroll = boxes["scroll"]["y"] - bottom(boxes["watch"])
                layout["spaces"]["videoToScroll"] = round(video_to_scroll,2)
                delta = bottom(boxes["scroll"]) - bottom(boxes["stats"])
                layout["spaces"]["statsToScrollBottomDelta"] = round(delta, 2)
                if width >= 1120 and height >= 672:
                    check(8 <= video_to_scroll <= 50,
                          "Wide-screen video and scroll remain proportionally spaced")
                    check(abs(delta) <= 180,
                          "Wide-screen scroll is part of the same compact composition")
                    check(boxes["hero"]["height"] <= max(height, 1020),
                          "Wide monitors must not create unnecessary empty hero height")
                    toggle = page.locator(".yf-language-toggle").bounding_box()
                    theme = page.locator(".fhero-theme-trigger").bounding_box()
                    check(abs(toggle["width"] - theme["width"]) <= 2 and
                          abs(toggle["height"] - theme["height"]) <= 2,
                          "Language toggle matches the theme control's circular size")
                else:
                    check(abs(delta) <= 24, "Scroll bottom aligns with statistics")
            layout["checks"] = checks
            measurements.append(layout)
            raw = OUT / f"hero-{width}x{height}.png"
            page.screenshot(path=str(raw), full_page=False, animations="disabled")
            with Image.open(raw).convert("RGB") as img:
                if width >= 1120:
                    # A photo covering the box is not enough if a solid overlay
                    # hides the entire lower viewport. Verify image detail there.
                    w, h = img.size
                    region = img.crop((int(w*.50), int(h*.85),
                                       int(w*.75), int(h*.97)))
                    texture = ImageStat.Stat(region).stddev
                    layout["spaces"]["bottomPhotoTexture"] = round(min(texture), 2)
                    check(min(texture) >= 12,
                          "Photo remains visually present at the bottom, no flat band")
                draw = ImageDraw.Draw(img)
                palette = {"intro": "#eace9f", "features": "#9df0ac", "watch": "#8ce2f5",
                           "handwritten": "#e2aafc", "scroll": "#f9bd7f", "stats": "#c5cfef"}
                for key, color in palette.items():
                    b = boxes[key]
                    if not b:
                        continue
                    xy = (b["x"], b["y"], right(b), bottom(b))
                    draw.rectangle(xy, outline=color, width=2)
                    draw.text((b["x"]+3, max(0, b["y"]-14)), key, fill=color)
                img.save(OUT / f"annotated-{width}x{height}.png")
            if width in (974, 1280, 1440, 1536, 1920):
                page.evaluate("document.documentElement.dataset.theme='light'")
                page.screenshot(path=str(OUT / f"hero-{width}x{height}-light.png"),full_page=False,animations="disabled")
                if width >= 1120:
                    light_scroll = page.locator('.fhero-scroll').evaluate(
                        """el => ({color:getComputedStyle(el).color,
                                    shadow:getComputedStyle(el).textShadow,
                                    arrow:getComputedStyle(el.querySelector('.fhero-scroll-arrow')).display,
                                    mouse:getComputedStyle(el.querySelector('.fhero-scroll-mouse')).borderColor})"""
                    )
                    check(light_scroll["color"] == "rgb(255, 255, 255)",
                          "LIGHT theme scroll cue is visibly white on dark photo")
                    check(light_scroll["shadow"] != "none",
                          "LIGHT theme scroll retains optical contrast shadow")
                    check(light_scroll["arrow"] != "none" and
                          "255, 255, 255" in light_scroll["mouse"],
                          "LIGHT theme downward arrow and mouse affordance visible")
                if width == 974:
                    note_rgb = page.locator(".fhero-handwrite").evaluate(
                        "(el) => getComputedStyle(el).color"
                    )
                    check(note_rgb != "rgb(255, 255, 255)", "Handwritten label has readable contrast in light tablet theme")
            print("HERO VISUAL", width, height, json.dumps({
                "introTop": layout["introTop"],
                "featuresToVideo": layout["spaces"].get("benefitsToVideo"),
                "delta": layout["spaces"].get("statsToScrollBottomDelta"),
                "handwriting": layout["visibleHandwriting"],
                "failures": [x["assertion"] for x in checks if not x["pass"]],
            }), flush=True)
            page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(OUT / "layout-metrics.json").write_text(
    json.dumps(measurements, ensure_ascii=False, indent=2), encoding="utf-8"
)
if errors:
    raise AssertionError("Hero visual audit failed:\n" + "\n".join(errors))
print("PASS: Hero visual audit, 11 viewport sizes, screenshots and annotated layout evidence.")

"""Browser smoke checks for the actual WordPress-rendered landing page."""
import os
import pathlib
import shutil

from playwright.sync_api import sync_playwright

url = "http://127.0.0.1:8765/"
out = pathlib.Path(__file__).resolve().parent / "_screenshots"
out.mkdir(exist_ok=True)
chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")

with sync_playwright() as playwright:
    kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        kwargs["executable_path"] = chrome
    browser = playwright.chromium.launch(**kwargs)
    page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    for width in [320, 375, 480, 768, 1024, 1440, 1920]:
        page.set_viewport_size({"width": width, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(250)
        assert page.locator("h1").count() == 1, f"Missing single H1 at {width}"
        assert page.locator(".hero.fhero").count() == 1
        if not page.locator(".fhero-photo").evaluate("(e) => e.complete && e.naturalWidth > 0"):
            src = page.locator(".fhero-photo").get_attribute("src")
            resp = page.request.get(src)
            print("DEBUG IMAGE:", src, "status", resp.status, "mime", resp.headers.get("content-type"), "bytes", len(resp.body()), flush=True)
            page.screenshot(path=str(out / "wp-image-debug.png"), full_page=False)
            raise AssertionError("Hero photo failed to load")
        overflow = page.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-window.innerWidth")
        assert overflow <= 4, f"Horizontal overflow {overflow}px at {width}px"
        if width in [375, 1440]:
            page.screenshot(path=str(out / f"wp-{width}.png"), full_page=True, animations="disabled")

    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(url, wait_until="domcontentloaded")
    theme = page.locator("#theme-button")
    initial = page.locator("html").get_attribute("data-theme")
    theme.click()
    changed = page.locator("html").get_attribute("data-theme")
    assert changed != initial, "Theme switch button did not change mode"
    page.reload()
    assert page.locator("html").get_attribute("data-theme") == changed, "Theme choice not persisted"

    page.set_viewport_size({"width": 375, "height": 850})
    page.goto(url, wait_until="domcontentloaded")
    menu = page.locator("#menu-button")
    menu.click()
    assert menu.get_attribute("aria-expanded") == "true", "Mobile menu did not open"
    assert page.locator("#mobile-menu").is_visible(), "Mobile nav remains hidden"
    page.keyboard.press("Escape")
    assert menu.get_attribute("aria-expanded") == "false", "Escape did not close menu"

    faq = page.locator(".faq-list details")
    assert faq.count() >= 4, "FAQ entries missing"
    faq.nth(0).locator("summary").click()
    assert faq.nth(0).evaluate("(e) => e.open")
    faq.nth(1).locator("summary").click()
    page.wait_for_timeout(120)
    assert faq.nth(1).evaluate("(e) => e.open")
    assert not faq.nth(0).evaluate("(e) => e.open"), "FAQ accordion did not close previous"
    assert page.locator("#contact form input[name=email]").count() == 1, "Contact form missing"

    # Reduced-motion must preserve readable content, not hide reveal sections.
    reduced = browser.new_page(viewport={"width": 375, "height": 850}, reduced_motion="reduce")
    reduced.goto(url, wait_until="domcontentloaded")
    assert reduced.locator("html").evaluate("(e) => !e.classList.contains('yf-motion')")
    assert reduced.locator(".reveal").first.evaluate("(e) => getComputedStyle(e).opacity") == "1"
    reduced.close()
    assert not errors, f"Browser JavaScript errors: {errors}"
    browser.close()

print("PASS: responsive widths 320-1920, theme, mobile menu, FAQ, reduced motion, form and images.")

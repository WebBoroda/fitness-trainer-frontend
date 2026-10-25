"""Smoke-тести першого етапу (Chromium + Playwright).
Run: python -m pip install playwright && python tests/smoke.py
For systems with system Chromium: CHROMIUM_PATH=/usr/bin/chromium python tests/smoke.py
Note: page.set_content is used because sandbox browser navigation may be blocked.
Persistence is checked with a session localStorage shim, not against a production origin.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
HTML = (BASE / 'index.html').read_text(encoding='utf-8')
CSS = (BASE / 'assets/css/styles.css').read_text(encoding='utf-8')
JS = (BASE / 'assets/js/main.js').read_text(encoding='utf-8')
SHOTS = BASE / 'tests' / '_screenshots'
SHOTS.mkdir(exist_ok=True)

with sync_playwright() as p:
    launch_args = {'headless': True}
    if os.environ.get('CHROMIUM_PATH'):
        launch_args['executable_path'] = os.environ['CHROMIUM_PATH']
    browser = p.chromium.launch(**launch_args)
    for width, height in ((375, 812), (768, 1024), (1024, 768), (1440, 900)):
        page = browser.new_page(viewport={'width': width, 'height': height})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(HTML, wait_until='load')
        page.evaluate("""Object.defineProperty(window, 'localStorage', {
          configurable:true, value: { items:{}, getItem(k){return this.items[k]??null},
          setItem(k,v){this.items[k]=v} }
        })""")
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=JS)
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), width
        assert not errors, errors
        assert page.get_by_role('heading', name='СИЛЬНІША ВЕРСІЯ ТЕБЕ').count() == 1
        if width < 900:
            page.get_by_role('button', name='Відкрити меню').click()
            assert page.locator('#mobile-nav').is_visible()
            page.keyboard.press('Escape')
            assert not page.locator('#mobile-nav').is_visible()
        theme = page.get_by_role('button', name='Вибрати оформлення')
        theme.click()
        page.get_by_role('button', name='Темна', exact=True).click()
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        page.set_content(HTML, wait_until='load')
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=JS)
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        theme.click()
        page.get_by_role('button', name='Світла', exact=True).click()
        assert page.locator('html').get_attribute('data-theme') == 'light'
        for section in page.locator('main section').all():
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(250)
        page.evaluate('scrollTo(0, 0)')
        page.wait_for_timeout(700)
        page.screenshot(path=str(SHOTS / f'light-{width}.png'), full_page=True)
        if width == 1440:
            theme.click()
            page.get_by_role('button', name='Контрастна', exact=True).click()
            assert page.locator('html').get_attribute('data-theme') == 'mixed'
            page.screenshot(path=str(SHOTS / 'mixed-1440.png'), full_page=True)
        print(f'PASS {width}x{height}: menu, modes, no overflow, no page errors')
        page.close()
    browser.close()

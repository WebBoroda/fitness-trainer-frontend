"""Frontend smoke tests for the visual review build."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
HTML = (BASE / 'index.html').read_text(encoding='utf-8')
SHOTS = BASE / 'tests' / '_screenshots'
SHOTS.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width, height in ((375, 812), (768, 1024), (1024, 768), (1440, 900)):
        for scheme in ('light', 'dark'):
            page = browser.new_page(viewport={'width': width, 'height': height}, color_scheme=scheme)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.evaluate("""Object.defineProperty(window, 'localStorage', {
                configurable:true,
                value: {data:{}, getItem(k){return this.data[k]??null},
                    setItem(k,v){this.data[k]=v}}
            })""")
            page.set_content(HTML, wait_until='domcontentloaded', timeout=30000)
            assert page.locator('html').get_attribute('data-theme') == scheme
            assert page.locator('main section').count() == 11
            assert page.locator('[data-set-theme]').count() == 3
            assert page.locator('[data-set-theme="auto"]').count() == 0
            assert page.locator('img').count() >= 20
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            menu = page.get_by_role('button', name='Відкрити меню')
            menu.click()
            assert page.locator('#mobile-menu').is_visible()
            page.keyboard.press('Escape')
            assert not page.locator('#mobile-menu').is_visible()
            toggle = page.get_by_role('button', name='Вибрати оформлення')
            toggle.click()
            page.locator('[data-set-theme="mixed"]').click()
            assert page.locator('html').get_attribute('data-theme') == 'mixed'
            assert page.evaluate("localStorage.getItem('fitness-theme')") == 'mixed'
            page.set_content(HTML, wait_until='domcontentloaded', timeout=30000)
            assert page.locator('html').get_attribute('data-theme') == 'mixed'
            assert not errors, errors
            if (width, scheme) in ((375, 'light'), (1440, 'dark')):
                page.screenshot(path=str(SHOTS / f'viewport-{width}-{scheme}.png'), full_page=False)
            print(f'PASS {width}x{height} {scheme}: themes, persistence, menu, overflow, errors')
            page.close()
    browser.close()

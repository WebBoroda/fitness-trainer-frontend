"""Real-origin Playwright smoke coverage for the fitness landing page."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]
SHOTS=BASE/'tests'/'_screenshots'
SHOTS.mkdir(parents=True,exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(BASE)))
thread=Thread(target=server.serve_forever,daemon=True);thread.start()
url=f'http://127.0.0.1:{server.server_port}/'
def overlaps(a,b):
    return bool(a and b and a['x'] < b['x']+b['width'] and a['x']+a['width'] > b['x'] and a['y'] < b['y']+b['height'] and a['y']+a['height'] > b['y'])

try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for width,height in ((320,740),(375,812),(768,1024),(900,1100),(1024,900),(1100,900),(1440,900),(1536,1024)):
            for scheme in ('light','dark'):
                page=browser.new_page(viewport={'width':width,'height':height},color_scheme=scheme,device_scale_factor=1)
                errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(url,wait_until='networkidle',timeout=45000)
                assert page.locator('html').get_attribute('data-theme')==scheme,(width,scheme)
                assert page.locator('main section').count()==11
                assert page.locator('[data-set-theme]').count()==3
                assert page.locator('[data-set-theme="auto"]').count()==0
                assert page.locator('.fhero-photo').evaluate('(im)=>im.complete && im.naturalWidth > 0'),width
                assert page.locator('.fhero-photo').evaluate('(el)=>getComputedStyle(el).zIndex')=='0', 'Hero photo must paint above the section background'
                assert page.locator('body').evaluate('el=>getComputedStyle(el).fontFamily')!='',width
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'),width
                assert not errors,(width,errors)
                if 761<=width<=940:
                    assert not overlaps(page.locator('.fhero-actions').bounding_box(),page.locator('.fhero-features').bounding_box()),f'Tablet buttons overlap panel at {width}'
                    assert not overlaps(page.locator('.fhero-features').bounding_box(),page.locator('.fhero-watch').bounding_box()),f'Tablet panel overlaps video at {width}'
                if 941<=width<=1100:
                    assert not overlaps(page.locator('.fhero-watch').bounding_box(),page.locator('.fhero-scroll').bounding_box()),f'Watch and scroll overlap at {width}'
                menu=page.get_by_role('button',name='Відкрити меню')
                menu.click();assert page.locator('#mobile-menu').is_visible()
                page.keyboard.press('Escape');assert not page.locator('#mobile-menu').is_visible()
                toggle=page.get_by_role('button',name='Вибрати оформлення')
                toggle.click();page.locator('[data-set-theme="mixed"]').click()
                assert page.locator('html').get_attribute('data-theme')=='mixed'
                assert page.evaluate("localStorage.getItem('fitness-theme')")=='mixed'
                page.reload(wait_until='domcontentloaded')
                assert page.locator('html').get_attribute('data-theme')=='mixed'
                if (width,scheme) in ((375,'light'),(768,'dark'),(900,'dark'),(1024,'dark'),(1536,'dark')):
                    page.screenshot(path=str(SHOTS/f'hero-{width}-{scheme}.png'),full_page=False)
                print(f'PASS {width}x{height} {scheme}: responsive, panels, menu, theme, JS')
                page.close()
        browser.close()
finally:
    server.shutdown();server.server_close()

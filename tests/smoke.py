"""Real-origin Playwright smoke coverage for the fitness landing page."""
from functools import partial
from io import BytesIO
from PIL import Image
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
        chrome=Path('/usr/bin/google-chrome')
        browser=p.chromium.launch(headless=True,executable_path=str(chrome) if chrome.exists() else None)
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
                assert page.locator('.fhero-avatars img').count()==3
                assert page.locator('.fhero-avatars img').evaluate_all('(imgs)=>imgs.every(im=>im.complete && im.naturalWidth===162)'), 'Client photo sprite must load'
                assert page.locator('.fhero-photo').evaluate('(el)=>getComputedStyle(el).zIndex')=='0', 'Hero photo must paint above the section background'
                if width==1536 and scheme=='dark':
                    png=Image.open(BytesIO(page.screenshot(full_page=False))).convert('RGB')
                    probes=[png.getpixel((950,250)),png.getpixel((900,330)),png.getpixel((1050,350))]
                    assert max(map(sum,probes))>130,f'Hero background not visibly painted: {probes}'
                assert page.locator('body').evaluate('el=>getComputedStyle(el).fontFamily')!='',width
                if page.evaluate('document.documentElement.scrollWidth > innerWidth'):
                    offenders=page.evaluate("""() => [...document.querySelectorAll('*')].map(e=>({cls:typeof e.className==='string'?e.className:'svg',right:Math.round(e.getBoundingClientRect().right),left:Math.round(e.getBoundingClientRect().left)})).filter(o=>o.right>innerWidth+1||o.left < -1).slice(0,18)""")
                    print(f'OVERFLOW at {width}: {offenders}',flush=True)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'),width
                assert not errors,(width,errors)
                if width<=760:
                    assert not overlaps(page.locator('.fhero-audience').bounding_box(),page.locator('.fhero-stats').bounding_box()),f'Mobile audience collides with stats at {width}'
                    assert not overlaps(page.locator('.fhero-stats').bounding_box(),page.locator('.fhero-features').bounding_box()),f'Mobile stats collide with features at {width}'
                    assert not overlaps(page.locator('.fhero-features').bounding_box(),page.locator('.fhero-watch').bounding_box()),f'Mobile features collide with video at {width}'
                if 761<=width<=940:
                    assert not overlaps(page.locator('.fhero-actions').bounding_box(),page.locator('.fhero-features').bounding_box()),f'Tablet buttons overlap panel at {width}'
                    assert not overlaps(page.locator('.fhero-features').bounding_box(),page.locator('.fhero-watch').bounding_box()),f'Tablet panel overlaps video at {width}'
                if 941<=width<=1100:
                    assert not overlaps(page.locator('.fhero-watch').bounding_box(),page.locator('.fhero-scroll').bounding_box()),f'Watch and scroll overlap at {width}'
                # Capture Light/Dark before testing manual Mixed selection.
                if (width,scheme) in ((320,'light'),(375,'light'),(375,'dark'),(768,'dark'),(900,'dark'),(1024,'dark'),(1536,'light'),(1536,'dark')):
                    png=page.screenshot(path=str(SHOTS/f'hero-{width}-{scheme}.png'),full_page=False)
                    if width==1536:
                        px=Image.open(BytesIO(png)).convert('RGB').getpixel((110,800))
                        if scheme=='light':
                            assert sum(px)>420,f'Light hero appears dark: {px}'
                        else:
                            assert sum(px)<230,f'Dark hero appears light: {px}'
                if width==1536:
                    expected={'.fhero-main':(96,152),'.fhero-stats':(96,779),'.fhero-features':(1210,139),'.fhero-watch':(1210,738),'.fhero-actions':(96,520),'.fhero-audience':(96,642)}
                    for selector,(x,y) in expected.items():
                        box=page.locator(selector).bounding_box()
                        assert box and abs(box['x']-x)<9 and abs(box['y']-y)<12,(selector,box)
                    assert abs(page.locator('.fhero-features').bounding_box()['width']-268)<2
                    assert abs(page.locator('.fhero-stats').bounding_box()['width']-550)<2
                menu=page.get_by_role('button',name='Відкрити меню')
                menu.click();assert page.locator('#mobile-menu').is_visible()
                page.keyboard.press('Escape');assert not page.locator('#mobile-menu').is_visible()
                toggle=page.get_by_role('button',name='Вибрати оформлення')
                toggle.click();page.locator('[data-set-theme="mixed"]').click()
                assert page.locator('html').get_attribute('data-theme')=='mixed'
                assert page.evaluate("localStorage.getItem('fitness-theme')")=='mixed'
                page.reload(wait_until='domcontentloaded')
                assert page.locator('html').get_attribute('data-theme')=='mixed'
                print(f'PASS {width}x{height} {scheme}: responsive, panels, menu, theme, JS')
                page.close()
        browser.close()
finally:
    server.shutdown();server.server_close()

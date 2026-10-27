"""Independent fast, full-page screenshot capture for design comparisons."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
import shutil

root = Path(__file__).resolve().parents[1]
out = root / 'tests' / '_screenshots'
out.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_): pass
server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        chrome = shutil.which('google-chrome') or shutil.which('chromium')
        browser = p.chromium.launch(headless=True,executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        for width,height in [(375,812),(768,1024),(1536,1024)]:
            for scheme in ['dark','light','mixed']:
                page = browser.new_page(viewport={'width':width,'height':height},color_scheme=scheme if scheme!='mixed' else 'dark',device_scale_factor=1,reduced_motion='reduce',locale='uk-UA')
                page.add_init_script("localStorage.setItem('fitness-theme','" + scheme + "')")
                page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='networkidle')
                for image in page.locator('main img:visible').all():
                    image.scroll_into_view_if_needed()
                    image.evaluate('(el)=>el.decode().catch(()=>{})')
                page.locator('.reveal').evaluate_all("(els)=>els.forEach(el=>el.classList.add('visible'))")
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(out / f'visual-{width}-{scheme}.png'),full_page=True,animations='disabled')
                print('CAPTURE',width,scheme,'pageheight',page.evaluate('document.documentElement.scrollHeight'))
                page.close()
        browser.close()
finally:
    server.shutdown();server.server_close()

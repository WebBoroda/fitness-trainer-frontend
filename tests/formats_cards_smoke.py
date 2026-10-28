"""Third-screen photo cards: real images, unified CSS shade, aligned content."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
import shutil
BASE=Path(__file__).resolve().parents[1]
SHOTS=BASE/'tests'/'_screenshots'/'formats'
SHOTS.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(BASE)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        chrome=shutil.which('google-chrome') or shutil.which('chromium')
        b=p.chromium.launch(headless=True,executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        for w,h in [(320,740),(375,812),(480,900),(768,1024),(1024,768),(1440,900),(1920,1080)]:
            for theme in ('light','dark'):
                page=b.new_page(viewport={'width':w,'height':h},reduced_motion='reduce')
                page.add_init_script(f"localStorage.setItem('fitness-theme','{theme}');localStorage.setItem('yuliia-language','uk')")
                page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle')
                page.locator('#formats').scroll_into_view_if_needed()
                cards=page.locator('#formats .program-card')
                assert cards.count()==4,(w,theme,'card count')
                for image in cards.locator('img').all():
                    image.scroll_into_view_if_needed()
                    image.evaluate('(el)=>el.decode().catch(()=>{})')
                page.wait_for_function("[...document.querySelectorAll('#formats .program-card img')].every(img=>img.complete && img.naturalWidth>=1000)")
                page.locator('#formats').scroll_into_view_if_needed()
                data=cards.evaluate_all("""els=>els.map(el=>{
                    const img=el.querySelector('img');
                    const box=x=>{const r=x.getBoundingClientRect();return [r.top,r.bottom]};
                    return {src:img.getAttribute('src'),width:img.naturalWidth,
                      filter:getComputedStyle(img).filter,
                      fit:getComputedStyle(img).objectFit,
                      mask:getComputedStyle(img).maskImage,
                      duration:getComputedStyle(img).transitionDuration,
                      backing:getComputedStyle(el).backgroundImage,
                      ink:getComputedStyle(el).color,
                      overlay:getComputedStyle(el,'::after').backgroundImage,
                      card:box(el),ico:box(el.querySelector('.ico')),
                      title:box(el.querySelector('h3')),
                      desc:box(el.querySelector('p')),
                      link:box(el.querySelector('a'))}
                })""")
                for i,x in enumerate(data):
                    assert x['src']==(
                        f"assets/images/formats-{['personal','group','online'][i]}-v2.webp" if i<3
                        else "assets/images/formats-nutrition.webp"
                    ),(w,i,x['src'])
                    assert x['width']>=1000,(w,i,'image resolution',x['width'])
                    # Mobile card widths require more lines than desktop. Check
                    # the actual content flow rather than a fixed height percentage.
                    assert x['ico'][1]<=x['title'][0]+2,(w,theme,i,'icon/title overlap')
                    assert x['title'][1]<=x['desc'][0]+2,(w,theme,i,'title/description overlap')
                    assert x['desc'][1]<=x['link'][0]+2,(w,theme,i,'description/link overlap')
                    assert x['link'][1]>=x['card'][1]-42,(w,theme,i,'link not at bottom')
                    assert x['link'][0]-x['desc'][1]<=32,(w,theme,i,'excess gap above details')
                    assert x['filter']=='none',(w,theme,i,'unwanted photo filter')
                    assert x['fit']==('contain' if i<3 else 'cover'),(w,theme,i,'photo fitting')
                    assert x['backing']=='none',(w,theme,i,'duplicated photo backdrop')
                    if i<3:
                        assert 'linear-gradient' in x['mask'],(w,theme,i,'photo fade is abrupt')
                    else:
                        assert x['mask']=='none',(w,theme,i,'nutrition framing changed')
                    assert max(float(t.strip().removesuffix('s')) for t in x['duration'].split(',')) < .05,(w,theme,i,'reduced-motion animation not minimized',x['duration'])
                    assert 'linear-gradient' in x['overlay'],(w,theme,i,'missing CSS overlay')
                    assert x['ink']=='rgb(255, 255, 255)',(w,theme,i,'wrong ink',x['ink'])
                for i,x in enumerate(data):
                    row=[y for y in data if abs(y['card'][0]-x['card'][0])<=2]
                    if len(row)<2: continue
                    for key,index in [('ico',0),('title',0),('desc',0),('link',1)]:
                        ys=[y[key][index] for y in row]
                        assert max(ys)-min(ys)<=2,(w,theme,key,ys)
                assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=2,(w,theme,'horizontal overflow')
                if w in (375,768,1440):
                    page.locator('#formats').screenshot(path=str(SHOTS/f'{theme}-{w}.png'),animations='disabled')
                page.close()
        b.close()
finally:
    server.shutdown()
    server.server_close()
print('PASS formats cards: semantic photos, lower aligned content, CSS overlay, light/dark, 320–1920px')
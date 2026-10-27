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
        for width,height in ((280,740),(320,740),(360,780),(375,812),(480,900),(640,960),(768,1024),(900,1100),(1024,900),(1100,900),(1337,593),(1348,621),(1440,900),(1536,1024),(1920,1080),(2007,904)):
            for scheme in ('light','dark'):
                page=browser.new_page(viewport={'width':width,'height':height},color_scheme=scheme,device_scale_factor=1)
                errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                page.add_init_script("if (!localStorage.getItem('fitness-theme')) localStorage.setItem('fitness-theme', '"+scheme+"')")
                page.goto(url,wait_until='networkidle',timeout=45000)
                assert page.locator('html').get_attribute('data-theme')==scheme,(width,scheme)
                assert page.locator('main section').count()==11
                # One theme icon container, but with distinct light/dark/mixed artwork.
                icon=page.locator('#theme-button svg.fhero-theme-symbol')
                assert icon.count()==1,('single theme icon',width)
                glyphs=page.locator('#theme-button .fhero-theme-glyph')
                assert glyphs.count()==3,('sun / moon / contrast artwork',width)
                def visible_theme_glyph():
                    return page.locator('#theme-button .fhero-theme-glyph').evaluate_all(
                        '(nodes)=>nodes.filter(n=>getComputedStyle(n).display !== "none").map(n=>n.classList[1])'
                    )
                expected_glyph={'light':'fhero-theme-glyph-sun','dark':'fhero-theme-glyph-moon'}
                assert visible_theme_glyph()==[expected_glyph[scheme]], ('wrong initial icon for theme',width,scheme,visible_theme_glyph())
                assert page.locator('#theme-button .fhero-theme-symbol').count()==1, ('single dual-tone theme icon',width)
                assert page.locator('#theme-button svg').count()==1, ('obsolete theme icon remains',width)
                assert page.locator('[data-set-theme]').count()==0
                assert page.locator('[data-set-theme="auto"]').count()==0
                assert page.locator('.fhero-photo').evaluate('(im)=>im.complete && im.naturalWidth > 0'),width
                if width>=1337:
                    hero=page.locator('.hero.fhero').bounding_box()
                    assert hero and abs(hero['x'])<2 and abs(hero['width']-width)<2,('Hero should span entire viewport',width,hero)

                # All four panel rows are keyboard-accessible, correctly targeted links.
                feature_links=page.locator('.fhero-features a.fhero-feature')
                assert feature_links.count()==4,('feature links missing',width)
                if width <= 671:
                    # Reference-approved mobile composition: 2x2 features with no stray rules.
                    panel_box=page.locator('.fhero-features').bounding_box()
                    rows=[link.bounding_box() for link in feature_links.all()]
                    assert all(box and box['height']>=58 for box in rows),('benefit touch targets too short',width,rows)
                    assert abs(rows[0]['y']-rows[1]['y'])<3 and abs(rows[2]['y']-rows[3]['y'])<3,('benefits should form two aligned rows',width,rows)
                    assert rows[1]['x']>=rows[0]['x']+rows[0]['width']-2,('first two benefits must be side by side',width,rows)
                    assert rows[3]['x']>=rows[2]['x']+rows[2]['width']-2,('second two benefits must be side by side',width,rows)
                    assert rows[2]['y']>=rows[0]['y']+rows[0]['height']-2,('2x2 benefit rows collide',width,rows)
                    for index,box in enumerate(rows):
                        assert box['x']>=panel_box['x']+4,('benefit has no left inset',width,index,box,panel_box)
                        assert box['x']+box['width']<=panel_box['x']+panel_box['width']-4,('benefit has no right inset',width,index,box,panel_box)
                        assert feature_links.nth(index).evaluate('(el)=>getComputedStyle(el,"::after").content')=='none',('unwanted separator inside mobile 2x2 module',width,index)
                        assert feature_links.nth(index).evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')>=10.8,('benefit font too small',width,index)
                    watch=page.locator('.fhero-watch').bounding_box()
                    scroll=page.locator('.fhero-scroll').bounding_box()
                    assert watch and scroll,('mobile actions missing',width)
                    assert watch['x']+watch['width']<=scroll['x']+2,('video and scroll must be separate horizontally',width,watch,scroll)
                    watch_mid=watch['y']+watch['height']/2
                    scroll_mid=scroll['y']+scroll['height']/2
                    assert abs(watch_mid-scroll_mid)<8,('video and scroll controls not aligned on one row',width,watch,scroll)
                    assert watch['y']>=panel_box['y']+panel_box['height']+10,('insufficient gap below benefits',width,watch,panel_box)
                    buttons=page.locator('.fhero-actions .fhero-button')
                    first,second=buttons.nth(0).bounding_box(),buttons.nth(1).bounding_box()
                    assert second['y']-(first['y']+first['height'])>=12,('mobile primary CTAs need breathing room',width,first,second)
                    assert abs(first['width']-second['width'])<2,('mobile primary CTAs should share the same width',width,first,second)

                for i,href in enumerate(('#formats','#formats','#nutrition','#results')):
                    link=feature_links.nth(i)
                    assert link.get_attribute('href')==href,(i,href)
                    assert page.locator(href).count()==1,('missing destination',href)
                # Approved benefit panel: each icon is on the left, its text on the right.
                for feature in page.locator('.fhero-feature').all():
                    icon=feature.locator('.fhero-feature-icon').bounding_box()
                    label=feature.locator('span').last.bounding_box()
                    assert icon and label and icon['x']+icon['width'] <= label['x']+1,('benefit icon/text order',width,icon,label)
                    assert abs((icon['y']+icon['height']/2)-(label['y']+label['height']/2))<=8,('benefit row vertical alignment',width,icon,label)
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
                hero=page.locator('.hero.fhero').bounding_box()
                if width>=1801:
                    assert abs(hero['x'])<1 and abs(hero['width']-width)<1,('Hero must be full bleed',width,hero)
                if width>=1600 and height<=980 and height>720:
                    assert not overlaps(page.locator('.fhero-audience').bounding_box(),page.locator('.fhero-stats').bounding_box()),'Wide low-height audience and stats collide'
                    assert not overlaps(page.locator('.fhero-features').bounding_box(),page.locator('.fhero-watch').bounding_box()),'Wide low-height features/video collide'
                    assert not overlaps(page.locator('.fhero-watch').bounding_box(),page.locator('.fhero-scroll').bounding_box()),'Wide low-height video/scroll collide'
                if width==1337 and height==593:
                    assert hero['height']<=height+1,('Short laptop hero must fit the viewport',hero)
                    assert not overlaps(page.locator('.fhero-audience').bounding_box(),page.locator('.fhero-stats').bounding_box()),'Short laptop audience/stats overlap'
                    audience_box=page.locator('.fhero-audience').bounding_box()
                    stats_box=page.locator('.fhero-stats').bounding_box()
                    gap=stats_box['y']-(audience_box['y']+audience_box['height'])
                    assert 0 <= gap <= 95,('short desktop content spacing',gap)
                    assert not overlaps(page.locator('.fhero-features').bounding_box(),page.locator('.fhero-watch').bounding_box()),'Short laptop feature/video overlap'
                    assert not overlaps(page.locator('.fhero-handwrite').bounding_box(),page.locator('.fhero-scroll').bounding_box()),'Short laptop handwriting/scroll overlap'
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
                if (width,scheme) in ((320,'light'),(375,'light'),(375,'dark'),(768,'dark'),(900,'dark'),(1024,'dark'),(1337,'dark'),(1536,'light'),(1536,'dark'),(1920,'dark'),(1920,'light'),(2007,'dark')):
                    png=page.screenshot(path=str(SHOTS/f'hero-{width}-{scheme}.png'),full_page=False)
                    if width==1536:
                        px=Image.open(BytesIO(png)).convert('RGB').getpixel((12,800))
                        if scheme=='light':
                            assert sum(px)>420,f'Light hero appears dark: {px}'
                        else:
                            assert sum(px)<230,f'Dark hero appears light: {px}'
                if width>=1101:
                    # Equal outer spacing, avoiding the former large unused lower edge.
                    header=page.locator('.fhero-header').bounding_box()
                    eyebrow=page.locator('.fhero-eyebrow').bounding_box()
                    stats=page.locator('.fhero-stats').bounding_box()
                    hero_box=page.locator('.hero.fhero').bounding_box()
                    top_gap=eyebrow['y']-(header['y']+header['height'])
                    bottom_gap=(hero_box['y']+hero_box['height'])-(stats['y']+stats['height'])
                    if width>=1408 and height>=950:
                        assert 42<=top_gap<=100,('approved hero top inset',width,top_gap)
                        assert 55<=bottom_gap<=145,('approved hero bottom inset',width,bottom_gap)
                    else:
                        assert abs(top_gap-bottom_gap)<=3,('balanced hero edge spacing',width,top_gap,bottom_gap)
                    title=page.locator('.fhero-title').bounding_box()
                    summary=page.locator('.fhero-summary').bounding_box()
                    actions=page.locator('.fhero-actions').bounding_box()
                    audience=page.locator('.fhero-audience').bounding_box()
                    assert summary['y']-(title['y']+title['height'])>=10,('heading/body spacing',width)
                    assert actions['y']-(summary['y']+summary['height'])>=10,('body/CTA spacing',width)
                    assert audience['y']-(actions['y']+actions['height'])>=10,('CTA/audience spacing',width)
                    # One soft rounded hover surface includes both icon and label.
                    feature=feature_links.first
                    normal=feature.evaluate('(el)=>getComputedStyle(el).backgroundColor')
                    feature.hover()
                    page.wait_for_timeout(240)  # The approved hover transition lasts 200 ms.
                    hovered=feature.evaluate('(el)=>({background:getComputedStyle(el).backgroundColor,radius:parseFloat(getComputedStyle(el).borderTopLeftRadius)})')
                    assert hovered['background']!=normal and hovered['radius']>=12,('rounded feature hover',width,hovered)
                    page.mouse.move(0,0)
                    panel=page.locator('.fhero-features').bounding_box()
                    feature_box=feature_links.first.bounding_box()
                    assert feature_box and abs(feature_box['x']-panel['x'])<=2, ('hover must reach module left edge',width,feature_box,panel)
                    assert abs((feature_box['x']+feature_box['width'])-(panel['x']+panel['width']))<=2, ('hover must reach module right edge',width,feature_box,panel)
                    feature_icon=feature_links.first.locator('.fhero-feature-icon').bounding_box()
                    assert feature_icon and feature_icon['x']-panel['x']>=18, ('icon needs inner inset, not border-hugging',width,feature_icon,panel)
                    video=page.locator('.fhero-watch').bounding_box()
                    assert panel and video and video['y']-(panel['y']+panel['height']) >= 18,('video must be below feature panel',width,panel,video)
                    scroll=page.locator('.fhero-scroll').bounding_box()
                    hero_bounds=page.locator('.hero.fhero').bounding_box()
                    print('HERO RIGHT LAYOUT',width, 'panel',panel,'video',video,'scroll',scroll, flush=True)
                    delta=(scroll['y']+scroll['height'])-(stats['y']+stats['height'])
                    print('HERO BOTTOM ALIGNMENT',width,'stats',stats['y']+stats['height'],'scroll',scroll['y']+scroll['height'],'delta',delta,flush=True)
                    assert abs(delta)<=5, ('scroll baseline should match stats bottom',width,delta)
                    assert scroll and video['y']+video['height'] <= scroll['y']+1,('video and scroll collision',width)
                    assert hero_bounds['y']+hero_bounds['height']-(scroll['y']+scroll['height']) >= 16,('keep aligned controls clear of the hero lower edge',width)
                    hero=page.locator('.hero.fhero').bounding_box()
                    assert hero and abs(hero['width']-width)<2,(width,'Hero width',hero)
                    assert page.locator('.fhero-photo').evaluate('(im)=>getComputedStyle(im).objectFit')=='contain',(width,'cropped photo')
                    a=page.locator('.fhero-header-cta').evaluate('(el)=>getComputedStyle(el).backgroundColor')
                    b=page.locator('.fhero-button-primary').evaluate('(el)=>getComputedStyle(el).backgroundColor')
                    assert a==b,(width,scheme,a,b)
                    assert page.locator('.fhero-main').evaluate('(el)=>getComputedStyle(el).scale')=='none'
                    assert page.locator('.fhero-navigation a').first.evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')>=16
                    for selector in ('.fhero-header-cta','.fhero-button-primary','.fhero-button-secondary'):
                        size=page.locator(selector).first.evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')
                        assert 16<=size<=17,(selector,width,size)
                    watch_font=page.locator('.fhero-watch-label').first.evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')
                    assert 14<=watch_font<=17,('fluid video label needs legible text',width,watch_font)
                assert page.locator('#hero-video-trigger').count()==1
                trigger=page.locator('#hero-video-trigger')
                trigger.click()
                assert page.locator('#hero-video-dialog').evaluate('(d)=>d.open')
                page.keyboard.press('Escape')
                assert not page.locator('#hero-video-dialog').evaluate('(d)=>d.open')
                assert page.locator('.fhero-scroll').get_attribute('href')=='#mission'
                if (width,scheme) in ((320,'light'),(375,'light'),(375,'dark'),(768,'dark'),(1024,'dark'),(1337,'dark'),(1536,'dark'),(1536,'light'),(1920,'dark'),(2007,'dark')):
                    page.evaluate("() => { window.scrollTo({top:0,behavior:'instant'}); document.activeElement?.blur(); }")
                    page.wait_for_timeout(100)
                    page.screenshot(path=str(SHOTS/f'hero-v2-{width}-{scheme}.png'),full_page=False)
                assert page.locator('#themes').count()==0
                menu=page.get_by_role('button',name='Відкрити меню')
                if width<=1100:
                    assert menu.is_visible(),('menu missing on narrow screen',width)
                    assert not page.locator('.fhero-navigation').is_visible()
                    menu.click();assert page.locator('#mobile-menu').is_visible()
                    page.keyboard.press('Escape');assert not page.locator('#mobile-menu').is_visible()
                else:
                    assert not menu.is_visible(),('hamburger shown on desktop',width)
                    assert page.locator('.fhero-navigation').is_visible()
                themeButton=page.locator('#theme-button')
                wanted='dark' if scheme=='light' else 'mixed'
                themeButton.click()
                assert page.locator('html').get_attribute('data-theme')==wanted
                assert visible_theme_glyph()==[{'light':'fhero-theme-glyph-sun','dark':'fhero-theme-glyph-moon','mixed':'fhero-theme-glyph-mixed'}[wanted]], ('icon must change with selected theme',width,wanted)
                assert page.evaluate("localStorage.getItem('fitness-theme')")==wanted
                if wanted=='mixed':
                    assert 'контрастна' in themeButton.get_attribute('aria-label')
                    if width in (375,1536):
                        page.screenshot(path=str(SHOTS/f'hero-{width}-mixed.png'),full_page=False)
                        mission=page.locator('#mission')
                        mission.scroll_into_view_if_needed()
                        mission.screenshot(path=str(SHOTS/f'mission-{width}-mixed.png'),animations='disabled')
                page.reload(wait_until='domcontentloaded')
                assert page.locator('html').get_attribute('data-theme')==wanted
                if wanted=='dark':
                    themeButton.click()
                    assert page.locator('html').get_attribute('data-theme')=='mixed'
                    themeButton.click()
                    assert page.locator('html').get_attribute('data-theme')=='light'
                mission=page.locator('#mission')
                assert mission.locator('h2').count()==1
                assert mission.locator('.benefit').count()==4
                assert mission.locator('.mission-layout').count()==1
                if width>=1024:
                    first=mission.locator('.intro').bounding_box()
                    second=mission.locator('.cards').bounding_box()
                    assert first and second and second['x']>first['x']+first['width']-2,('mission side-by-side',width,first,second)
                assert mission.locator('.quote blockquote').count()==0
                about=page.locator('#about')
                assert about.locator('.quote blockquote').count()==1
                photo=about.locator('img[src$="mission-quote.jpg"]')
                assert photo.count()==1
                photo.scroll_into_view_if_needed()
                photo.evaluate("(img)=>img.decode()")
                assert photo.evaluate('(im)=>im.complete && im.naturalWidth>0')
                assert mission.evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),('mission overflow',width)
                assert about.evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),('about overflow',width)
                assert page.locator('img[src^="data:"]').count()==0, 'Images should be external resources'
                if (width,scheme) in ((320,'light'),(375,'light'),(375,'dark'),(768,'light'),(1024,'dark'),(1337,'light'),(1536,'light'),(1536,'dark'),(1920,'light')):
                    mission.scroll_into_view_if_needed()
                    mission.locator('.reveal').evaluate_all('(els)=>els.forEach(e=>e.classList.add("visible"))')
                    # Restore the original OS theme before taking the labelled reference image.
                    page.evaluate("(theme)=>{document.documentElement.dataset.theme=theme}",scheme)
                    assert page.locator('html').get_attribute('data-theme')==scheme
                    mission.screenshot(path=str(SHOTS/f'mission-{width}-{scheme}.png'),animations='disabled',timeout=30000)
                if (width,scheme) in ((375,'dark'),(768,'dark')):
                    page.evaluate("(theme)=>{document.documentElement.dataset.theme=theme}",scheme)
                    page.locator('.hero.fhero').screenshot(path=str(SHOTS/f'hero-full-{width}-{scheme}.png'),animations='disabled')
                if width in (375,1536) and scheme=='dark':
                    for n,hash_target in ((0,'#formats'),(2,'#nutrition'),(3,'#results')):
                        feature_links.nth(n).click()
                        assert page.evaluate('location.hash')==hash_target,(n,hash_target)
                print(f'PASS {width}x{height} {scheme}: responsive, panels, menu, theme, JS')
                page.close()
        browser.close()
finally:
    server.shutdown();server.server_close()

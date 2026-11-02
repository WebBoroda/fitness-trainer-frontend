/* EDIT THE JSON OBJECT ONLY — one place for core site settings.
   GitHub Pages build writes SEO values into the actual static HTML. */
window.YF_SITE_CONFIG = {
  "brand": {
    "name": "Fitnes Trener",
    "isPerson": false,
    "taglineUk": "Сильніша версія тебе",
    "taglineEn": "A Stronger You"
  },
  "favicon": {
    "light": "fitness-trener-favicon-light.svg",
    "dark": "fitness-trener-favicon-dark.svg",
    "mixed": "dark"
  },
  "seo": {
    "roleUk": "Фітнес-тренер",
    "roleEn": "Fitness Coach",
    "titleSuffixUk": "Персональні та онлайн-тренування",
    "titleSuffixEn": "Personal and Online Training",
    "descriptionUk": "Персональні, групові та онлайн-тренування. Індивідуальні програми, підтримка та консультації.",
    "descriptionEn": "Personal, group and online fitness training. Individual programs, support and consultations.",
    "baseUrl": "https://webboroda.github.io/fitness-trainer-frontend/",
    "robots": "noindex,follow",
    "ogImage": "fitness-trainer-hero.webp"
  },
  "theme": {
    "default": "mixed",
    "accent": "#efd8c6",
    "light": {
      "background": "#f8f5f1",
      "surface": "#fffdfb",
      "text": "#1b1715",
      "muted": "#60574f",
      "border": "#dfd2c8"
    },
    "dark": {
      "background": "#0e1010",
      "surface": "#171a1a",
      "text": "#f6f1ed",
      "muted": "#c9bdb6",
      "border": "#ffffff29"
    }
  },
  "typography": {
    "body": "Inter, Manrope, sans-serif",
    "heading": "Manrope, Inter, sans-serif"
  },
  "design": {
    "cardRadiusPx": 22,
    "glassBlurPx": 8
  },
  "motion": {
    "enabled": true,
    "speed": 1,
    "parallax": true
  },
  "language": {
    "default": "uk",
    "available": [
      "uk",
      "en"
    ]
  },
  "location": {
    "isDemo": true,
    "venueName": "Тренування онлайн та в залі",
    "address": "м. Київ, вул. Хрещатик, 22",
    "latitude": 50.449855,
    "longitude": 30.523063,
    "mapZoom": 16
  },
  "contact": {
    "phone": "",
    "email": ""
  },
  "socialLinks": {
    "instagram": "",
    "facebook": "",
    "tiktok": "",
    "youtube": "",
    "telegram": "",
    "whatsapp": "",
    "viber": ""
  },
  "media": {
    "fitness-trainer-hero.webp": "fitness-trainer-hero.webp",
    "fitness-training-background.webp": "fitness-training-background.webp",
    "fitness-trainer-portrait.webp": "fitness-trainer-portrait.webp",
    "fitness-trainer-final-cta.webp": "fitness-trainer-final-cta.webp",
    "fitness-training-video-preview.webp": "fitness-training-video-preview.webp",
    "fitness-training-motivation.jpg": "fitness-training-motivation.jpg",
    "fitness-clients-avatars.webp": "fitness-clients-avatars.webp",
    "fitness-client-avatar-01.webp": "fitness-client-avatar-01.webp",
    "fitness-client-avatar-02.webp": "fitness-client-avatar-02.webp",
    "fitness-client-avatar-03.webp": "fitness-client-avatar-03.webp",
    "personal-fitness-training.webp": "personal-fitness-training.webp",
    "group-fitness-training.webp": "group-fitness-training.webp",
    "online-fitness-coaching.webp": "online-fitness-coaching.webp",
    "fitness-nutrition-program.webp": "fitness-nutrition-program.webp",
    "personal-fitness-training-alternative.webp": "personal-fitness-training-alternative.webp",
    "group-fitness-training-alternative.webp": "group-fitness-training-alternative.webp",
    "online-fitness-coaching-alternative.webp": "online-fitness-coaching-alternative.webp",
    "fitness-gym-main.webp": "fitness-gym-main.webp",
    "fitness-gym-dumbbells.webp": "fitness-gym-dumbbells.webp",
    "fitness-gym-cardio.webp": "fitness-gym-cardio.webp",
    "fitness-gym-strength.webp": "fitness-gym-strength.webp",
    "fitness-gym-stretching.webp": "fitness-gym-stretching.webp",
    "fitness-results-before-after-01.webp": "fitness-results-before-after-01.webp",
    "fitness-results-before-after-02.webp": "fitness-results-before-after-02.webp",
    "fitness-results-before-after-03.webp": "fitness-results-before-after-03.webp",
    "fitness-results-before-after-04.webp": "fitness-results-before-after-04.webp",
    "fitness-results-before-after-05.webp": "fitness-results-before-after-05.webp",
    "fitness-results-before-after-06.webp": "fitness-results-before-after-06.webp",
    "fitness-editorial-01.jpg": "fitness-editorial-01.jpg",
    "fitness-editorial-02.jpg": "fitness-editorial-02.jpg",
    "fitness-editorial-03.jpg": "fitness-editorial-03.jpg",
    "fitness-editorial-04.jpg": "fitness-editorial-04.jpg",
    "fitness-editorial-05.jpg": "fitness-editorial-05.jpg",
    "fitness-editorial-06.jpg": "fitness-editorial-06.jpg",
    "fitness-editorial-07.jpg": "fitness-editorial-07.jpg",
    "fitness-editorial-08.jpg": "fitness-editorial-08.jpg",
    "fitness-editorial-09.jpg": "fitness-editorial-09.jpg",
    "fitness-editorial-10.jpg": "fitness-editorial-10.jpg",
    "fitness-editorial-11.jpg": "fitness-editorial-11.jpg",
    "fitness-editorial-12.jpg": "fitness-editorial-12.jpg",
    "fitness-editorial-13.jpg": "fitness-editorial-13.jpg",
    "fitness-editorial-14.jpg": "fitness-editorial-14.jpg",
    "fitness-editorial-15.jpg": "fitness-editorial-15.jpg",
    "fitness-editorial-16.jpg": "fitness-editorial-16.jpg"
  }
};
/* END SITE DATA */
(() => {
  'use strict';
  const c = window.YF_SITE_CONFIG, root = document.documentElement;
  // Update the same browser-tab icon when the visible theme changes.
  const favicon = document.querySelector('link[rel="icon"]');
  const safeIcon = name => typeof name === 'string' && /^[a-z0-9][a-z0-9-]*\.svg$/.test(name) ? name : null;
  const syncFavicon = () => {
    const theme = root.dataset.theme || c.theme.default || 'mixed';
    const mode = theme === 'light' ? 'light' : theme === 'dark' ? 'dark' :
      c.favicon?.mixed === 'light' ? 'light' : 'dark';
    const name = safeIcon(c.favicon?.[mode]) || 'fitness-trener-favicon-' + mode + '.svg';
    const target = 'assets/images/' + name;
    if (favicon && favicon.getAttribute('href') !== target) favicon.setAttribute('href', target);
  };
  syncFavicon();
  new MutationObserver(syncFavicon).observe(root, {attributes: true, attributeFilter: ['data-theme']});
  const baseline = {"accent":"#efd8c6","light":{"background":"#f8f5f1","surface":"#fffdfb","text":"#1b1715","muted":"#60574f","border":"#dfd2c8"},"dark":{"background":"#0e1010","surface":"#171a1a","text":"#f6f1ed","muted":"#c9bdb6","border":"#ffffff29"}};
  const safeColor = v => /^#[0-9a-fA-F]{6}$/.test(v || '') ? v : null;
  const accent = safeColor(c.theme.accent) || baseline.accent;
  const custom = accent.toLowerCase() !== baseline.accent ||
    ['light','dark'].some(t => Object.keys(baseline[t]).some(k => c.theme[t]?.[k] !== baseline[t][k]));
  root.dataset.customPalette = String(custom);
  root.dataset.motionEnabled = String(c.motion.enabled !== false);
  root.dataset.motionParallax = String(c.motion.parallax !== false);
  for (const theme of ['light','dark']) {
    for (const [key,value] of Object.entries(c.theme[theme])) {
      const v = safeColor(value);
      if (v) root.style.setProperty('--cfg-' + theme + '-' + key, v);
    }
  }
  root.style.setProperty('--cfg-accent', accent);
  if (accent.toLowerCase() !== baseline.accent) {
    for (const key of ['--yf-sand','--hero-accent','--accent','--yf-cta-primary-fill','--yf-cta-primary-hover','--yf-cta-primary-edge'])
      root.style.setProperty(key, accent);
    const rgb=accent.slice(1).match(/../g).map(v=>parseInt(v,16)/255);
    const linear=rgb.map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    const L=.2126*linear[0]+.7152*linear[1]+.0722*linear[2];
    root.style.setProperty('--yf-cta-primary-ink',(L+.05)/.05>=4.5?'#111111':'#ffffff');
  }
  if (Number(c.design.cardRadiusPx)!==22 && Number.isFinite(+c.design.cardRadiusPx)) {
    root.style.setProperty('--radius',c.design.cardRadiusPx+'px');
    root.style.setProperty('--yf-radius',c.design.cardRadiusPx+'px');
  }
  const speed=+c.motion.speed;
  if (speed>0 && Number.isFinite(speed)) root.style.setProperty('--yf-motion-duration',660*speed+'ms');
  if(c.typography.body!=='Inter, Manrope, sans-serif' || c.typography.heading!=='Manrope, Inter, sans-serif') {
    root.dataset.customFonts='true';
    root.style.setProperty('--cfg-font-body',c.typography.body);
    root.style.setProperty('--cfg-font-heading',c.typography.heading);
  }
  const renderBrand = () => {
    const name=String(c.brand.name||'Fitnes Trener').trim(), upper=name.toUpperCase();
    const space=upper.indexOf(' '),first=space<0?upper:upper.slice(0,space),last=space<0?'':upper.slice(space+1);
    document.querySelectorAll('[data-site-brand]').forEach(el=>{
      const suffix=el.querySelector('span,small');
      if(suffix) {
        [...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).forEach(n=>n.remove());
        el.insertBefore(document.createTextNode(first),suffix);
        suffix.textContent=last;
      } else el.textContent=name;
      el.setAttribute('aria-label',name+' — на початок');
    });
    const about=document.querySelector('#yf-about-details-title');
    if(about) about.textContent=upper;
    const right=document.querySelector('.yf-copyright');
    const year=right?.querySelector('.yf-year');
    if(year) {
      [...right.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).forEach(n=>n.remove());
      right.insertBefore(document.createTextNode('© '),year);
      year.after(document.createTextNode(' '+name+' · Усі права захищено'));
    }
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',renderBrand,{once:true});
  else renderBrand();
})();

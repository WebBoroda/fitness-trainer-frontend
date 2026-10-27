/* English/Ukrainian UI with device-language detection and persisted manual choice.
   Never relies on a location lookup or third-party translation service. */
(() => {
  'use strict';
  const root = document.documentElement;
  const english = window.YF_ENGLISH || {};
  const key = 'yuliia-language';
  const originals = new WeakMap();
  const attributes = new WeakMap();
  const translatableAttrs = ['aria-label', 'alt', 'title', 'placeholder', 'content'];
  const normalize = value => String(value).replace(/\s+/g, ' ').trim();
  const translate = value => {
    const source = normalize(value);
    if (english[source]) return english[source];
    const theme = /^Тема: (світла|темна|контрастна)(?:\. Перемкнути на | · наступна: )(світла|темна|контрастна)$/.exec(source);
    if (theme) return 'Theme: ' + english[theme[1]] + ' · next: ' + english[theme[2]];
    const gallery = /^Переглянути фото: (.+)$/.exec(source);
    if (gallery) return 'View photo: ' + (english[gallery[1]] || gallery[1]);
    return value;
  };
  const remember = language => {
    try { localStorage.setItem(key, language); } catch (_) { /* Private browsing */ }
  };
  const preferred = () => {
    try {
      const stored = localStorage.getItem(key);
      if (stored === 'uk' || stored === 'en') return stored;
    } catch (_) {}
    const first = (navigator.languages?.[0] || navigator.language || 'uk').toLowerCase();
    return first.startsWith('en') ? 'en' : 'uk';
  };
  let language = preferred();
  const excluded = node => {
    let p = node.parentElement;
    while (p && p !== document.body) {
      if (/^(SCRIPT|STYLE|SVG|NOSCRIPT|CODE|PRE)$/i.test(p.tagName)) return true;
      if (p.hasAttribute('data-i18n-skip')) return true;
      p = p.parentElement;
    }
    return false;
  };
  const translateTextNode = node => {
    if (!node || node.nodeType !== Node.TEXT_NODE || excluded(node)) return;
    const value = node.nodeValue;
    if (!normalize(value)) return;
    let source = originals.get(node);
    // External scripts can change existing nodes (carousel counters/statuses).
    if (source === undefined || (value !== source && value !== translate(source))) {
      source = value;
      originals.set(node, source);
    }
    const target = language === 'en' ? translate(source) : source;
    if (value !== target) {
      const leading = source.match(/^\s*/)?.[0] || '';
      const trailing = source.match(/\s*$/)?.[0] || '';
      const translated = language === 'en' ? leading + translate(source) + trailing : source;
      if (node.nodeValue !== translated) node.nodeValue = translated;
    }
  };
  const translateAttributes = el => {
    if (!(el instanceof Element) || el.closest('[data-i18n-skip]')) return;
    let values = attributes.get(el);
    if (!values) { values = {}; attributes.set(el, values); }
    for (const attr of translatableAttrs) {
      if (!el.hasAttribute(attr)) continue;
      if (attr === 'content' && !el.matches('meta[name="description"]')) continue;
      const value = el.getAttribute(attr);
      if (values[attr] === undefined ||
          (value !== values[attr] && value !== translate(values[attr]))) {
        values[attr] = value;
      }
      const target = language === 'en' ? translate(values[attr]) : values[attr];
      if (value !== target) el.setAttribute(attr, target);
    }
  };
  const translateTree = element => {
    if (!element) return;
    if (element.nodeType === Node.TEXT_NODE) {
      translateTextNode(element);
      return;
    }
    if (element.nodeType !== Node.ELEMENT_NODE) return;
    if (element.matches('script,style,svg,noscript,[data-i18n-skip]')) return;
    translateAttributes(element);
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
      acceptNode: node => excluded(node) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    while (walker.nextNode()) translateTextNode(walker.currentNode);
    element.querySelectorAll('[aria-label],[alt],[title],[placeholder],meta[name="description"]').forEach(translateAttributes);
  };
  // One accessible button with two visual language halves.
  const showSelected = () => {
    const toggle = document.querySelector('[data-language-toggle]');
    if (!toggle) return;
    toggle.dataset.activeLanguage = language;
    toggle.setAttribute('aria-label', language === 'uk'
      ? 'Мова сайту: українська. Перемкнути на англійську'
      : 'Website language: English. Switch to Ukrainian');
    toggle.setAttribute('title', language === 'uk' ? 'Switch to English' : 'Перемкнути українською');
    document.querySelectorAll('[data-language-indicator]').forEach(half => {
      half.classList.toggle('is-active', half.dataset.languageIndicator === language);
    });
  };
  const setLanguage = (next, persist = false) => {
    if (!['uk', 'en'].includes(next)) return;
    language = next;
    root.lang = language;
    root.dataset.language = language;
    translateTree(document.body);
    const description = document.querySelector('meta[name="description"]');
    if (description) translateAttributes(description);
    const titleSource = document.title.includes('A Stronger You')
      ? 'Yuliia Zahorodnia — Сильніша версія тебе'
      : document.title;
    document.title = language === 'en' ? translate(titleSource) : 'Yuliia Zahorodnia — Сильніша версія тебе';
    showSelected();
    if (persist) remember(language);
    document.dispatchEvent(new CustomEvent('yf:languagechange', { detail: { language } }));
  };
  document.querySelector('[data-language-toggle]')?.addEventListener('click', () => {
    setLanguage(language === 'uk' ? 'en' : 'uk', true);
  });
  setLanguage(language);

  // Translate content created after DOM ready by carousels, modals and contact UI.
  const observer = new MutationObserver(records => {
    const elements = new Set();
    for (const record of records) {
      if (record.type === 'characterData') translateTextNode(record.target);
      if (record.type === 'attributes') translateAttributes(record.target);
      if (record.type === 'childList') {
        for (const node of record.addedNodes) {
          if (node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.TEXT_NODE) elements.add(node);
        }
      }
    }
    elements.forEach(translateTree);
  });
  observer.observe(document.body, {
    subtree: true, childList: true, characterData: true,
    attributes: true, attributeFilter: translatableAttrs
  });
  window.YF_I18N = Object.freeze({
    get language() { return language; },
    t: value => language === 'en' ? translate(value) : value,
    setLanguage, translateTree
  });
})();

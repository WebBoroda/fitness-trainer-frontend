/* Interaction layer for the GitHub Pages frontend — no external runtime dependencies. */
(() => {
  'use strict';
  const prefersReduced = matchMedia('(prefers-reduced-motion: reduce)');
  const motion = () => prefersReduced.matches ? 'instant' : 'smooth';
  const byId = id => document.getElementById(id);
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  // A thin reading-progress indicator, throttled to the browser's paint loop.
  const progress = document.createElement('div');
  progress.className = 'yf-scroll-progress';
  progress.setAttribute('aria-hidden', 'true');
  document.body.append(progress);
  let scheduled = false;
  const refreshProgress = () => {
    scheduled = false;
    const max = document.documentElement.scrollHeight - innerHeight;
    progress.style.width = (max > 0 ? Math.max(0, Math.min(100, 100 * scrollY / max)) : 0) + '%';
  };
  addEventListener('scroll', () => {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(refreshProgress);
    }
  }, { passive: true });
  addEventListener('resize', refreshProgress, { passive: true });
  refreshProgress();

  // Native FAQ controls have built-in keyboard support; keep one answer expanded.
  const faqs = $$('#faq details');
  faqs.forEach(item => {
    item.addEventListener('toggle', () => {
      if (item.open) faqs.filter(other => other !== item && other.open).forEach(other => { other.open = false; });
    });
  });

  // Accessible scroll-snap carousels: arrows appear only when contents overflow.
  const carousels = [
    { selector: '#results .result-strip', label: 'Галерея результатів' },
    { selector: '#reviews .reviews-list', label: 'Відгуки клієнток' },
    { selector: '#pricing .price-list', label: 'Пакети тренувань' }
  ];
  carousels.forEach(({ selector, label }) => {
    const track = $(selector);
    if (!track) return;
    track.setAttribute('tabindex', '0');
    track.setAttribute('role', 'region');
    track.setAttribute('aria-label', label);
    const controls = document.createElement('div');
    controls.className = 'yf-carousel-controls';
    const buttons = [-1, 1].map(direction => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = direction < 0 ? '←' : '→';
      button.setAttribute('aria-label', direction < 0 ? label + ': попередні' : label + ': наступні');
      button.addEventListener('click', () => {
        track.scrollBy({ left: direction * Math.max(220, track.clientWidth * .8), behavior: motion() });
      });
      controls.append(button);
      return button;
    });
    track.insertAdjacentElement('afterend', controls);
    const update = () => {
      const max = track.scrollWidth - track.clientWidth;
      controls.hidden = max < 3;
      buttons[0].disabled = track.scrollLeft < 3;
      buttons[1].disabled = track.scrollLeft >= max - 3;
    };
    track.addEventListener('scroll', update, { passive: true });
    addEventListener('resize', update, { passive: true });
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(track);
    addEventListener('load', update, { once: true });
    update();
  });

  // Make the three approved gym photographs fully browsable, without a library.
  const studioImages = $$('#studio .studio-gallery img');
  if (studioImages.length) {
    const dialog = document.createElement('dialog');
    dialog.className = 'yf-gallery-modal';
    dialog.setAttribute('aria-label', 'Перегляд фотографій спортивного простору');
    dialog.innerHTML = '<button class="yf-gallery-close" type="button" aria-label="Закрити галерею">×</button>'
      + '<figure><img alt="" loading="eager"><figcaption></figcaption></figure>'
      + '<div class="yf-gallery-controls"><button type="button" aria-label="Попереднє фото">←</button><button type="button" aria-label="Наступне фото">→</button></div>';
    document.body.append(dialog);
    const photo = $('figure img', dialog), caption = $('figcaption', dialog);
    const [prev, next] = $$('.yf-gallery-controls button', dialog);
    const close = $('.yf-gallery-close', dialog);
    let selected = 0, priorFocus = null;
    const render = () => {
      const source = studioImages[selected];
      photo.src = source.currentSrc || source.src;
      photo.alt = source.alt || '';
      caption.textContent = (source.alt || 'Фотографія зали') + ' · ' + (selected + 1) + ' / ' + studioImages.length;
    };
    const open = index => {
      priorFocus = document.activeElement;
      selected = index;
      render();
      dialog.showModal();
      close.focus();
    };
    const step = direction => { selected = (selected + direction + studioImages.length) % studioImages.length; render(); };
    studioImages.forEach((img, index) => {
      const btn = document.createElement('button');
      btn.className = 'gallery-photo';
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Переглянути фото: ' + (img.alt || (index + 1)));
      img.parentNode.insertBefore(btn, img);
      btn.append(img);
      btn.addEventListener('click', () => open(index));
    });
    const studioCta = document.querySelector('a[href="#studio-gallery"]');
    studioCta?.addEventListener('click', event => { event.preventDefault(); open(0); });
    prev.addEventListener('click', () => step(-1));
    next.addEventListener('click', () => step(1));
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft') { event.preventDefault(); step(-1); }
      if (event.key === 'ArrowRight') { event.preventDefault(); step(1); }
    });
    dialog.addEventListener('close', () => priorFocus?.focus?.());
  }

  // The source layout has no verified booking endpoint. Provide a real, local
  // consultation request composer rather than a fake "message sent" response.
  const planner = document.createElement('dialog');
  planner.className = 'yf-consultation-modal';
  planner.id = 'consultation';
  planner.setAttribute('aria-labelledby', 'yf-planner-title');
  planner.innerHTML = `<form method="dialog" class="yf-consultation-form">
    <button type="button" class="yf-planner-close" aria-label="Закрити форму">×</button>
    <span class="eyebrow">ПОЧНИ СВІЙ ШЛЯХ</span>
    <h2 id="yf-planner-title">Твоя майбутня програма</h2>
    <p class="yf-planner-intro">Склади коротку заявку для консультації. Контакт для надсилання ще не підключено, тому форма <strong>не надсилає персональні дані</strong>.</p>
    <label>Формат занять
      <select name="program" required>
        <option value="Персональні тренування">Персональні тренування</option>
        <option value="Групові тренування">Групові тренування</option>
        <option value="Онлайн-програма">Онлайн-програма</option>
        <option value="Харчування">Харчування</option>
        <option value="Повний супровід">Повний супровід</option>
      </select>
    </label>
    <label>Твоя мета <textarea name="goal" rows="3" maxlength="500" placeholder="Розкажи, чого хочеш досягти" required></textarea></label>
    <button class="btn fill yf-planner-copy" type="submit">Скопіювати заявку<span class="arrow">→</span></button>
    <p class="yf-planner-status" role="status" aria-live="polite"></p>
    <textarea class="yf-planner-fallback" aria-label="Текст заявки для копіювання" readonly hidden></textarea>
  </form>`;
  document.body.append(planner);
  const form = $('.yf-consultation-form', planner), status = $('.yf-planner-status', planner);
  const format = $('select[name=program]', planner);
  const input = $('textarea[name=goal]', planner);
  const fallback = $('.yf-planner-fallback', planner);
  const closePlanner = $('.yf-planner-close', planner);
  let plannerPriorFocus = null;
  const openPlanner = program => {
    plannerPriorFocus = document.activeElement;
    const values = Array.from(format.options).map(option => option.value);
    if (program && values.includes(program)) format.value = program;
    status.textContent = '';
    fallback.hidden = true;
    planner.showModal();
    format.focus();
  };
  $$('a[href="#consultation"], [data-consultation]').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      openPlanner(link.getAttribute('data-program'));
    });
  });
  closePlanner.addEventListener('click', () => planner.close());
  planner.addEventListener('click', event => { if (event.target === planner) planner.close(); });
  planner.addEventListener('close', () => plannerPriorFocus?.focus?.());
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const goal = input.value.trim();
    if (!goal) { input.focus(); return; }
    const tr = value => window.YF_I18N?.t(value) || value;
    const value = tr('Заявка на консультацію YULIIA ZAGORODNIA') + '\n'
      + tr('Формат:') + ' ' + tr(format.value) + '\n'
      + tr('Мета:') + ' ' + goal;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard not available');
      await navigator.clipboard.writeText(value);
      status.textContent = 'Заявку скопійовано. Вона не надсилалася на сервер.';
      fallback.hidden = true;
    } catch (_) {
      fallback.value = value;
      fallback.hidden = false;
      fallback.select();
      status.textContent = 'Виділи та скопіюй текст заявки нижче. Дані не надсилалися.';
    }
  });

  // A landing page can be dynamic without animating on every scroll frame.
  // Observe heading sections to provide active navigation feedback.
  const links = $$('a[href^="#"]').filter(a => a.closest('.fhero-navigation, .mobile-menu, .footer-links'));
  if ('IntersectionObserver' in window) {
    const ids = ['about','formats','nutrition','results','reviews','faq'];
    const activeObserver = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio);
      if (!visible.length) return;
      const current = '#' + visible[0].target.id;
      links.forEach(link => {
        if (link.getAttribute('href') === current) link.setAttribute('aria-current','location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin:'-20% 0px -55% 0px', threshold:[0,.2,.5] });
    ids.map(byId).filter(Boolean).forEach(section=>activeObserver.observe(section));
  }
})();

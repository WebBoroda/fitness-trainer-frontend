/* Small progressive enhancement for the approved frontend: no runtime deps. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection?.saveData === true;
  if (reduced.matches || saveData || !('IntersectionObserver' in window)) return;

  // The effect is applied to existing cards; markup, ordering and dimensions
  // are untouched. Reveal-once avoids replaying motion while reading the page.
  const groups = [
    ['#mission .cards', '.benefit'],
    ['#formats .program-cards', '.program-card'],
    ['#studio .studio-gallery', '.gallery-photo'],
    ['#results .result-strip', '.yf-result-card'],
    ['#reviews .reviews-list', '.review'],
    ['#pricing .price-list', '.price'],
    ['#faq .faq-list', 'details']
  ];
  const targets = groups.flatMap(([parent, child]) => {
    const container = document.querySelector(parent);
    return container ? [...container.querySelectorAll(`:scope > ${child}`)] : [];
  });
  const observer = new IntersectionObserver(entries => {
    entries.forEach(({ target, isIntersecting }) => {
      if (!isIntersecting) return;
      target.classList.add('yf-motion-visible');
      observer.unobserve(target);
    });
  }, { threshold: .08, rootMargin: '0px 0px 35px 0px' });

  groups.forEach(([parent, child]) => {
    const container = document.querySelector(parent);
    if (!container) return;
    [...container.querySelectorAll(`:scope > ${child}`)].forEach((element, index) => {
      const delay = Math.min(index, 5) * 75;
      element.style.setProperty('--yf-motion-delay', `${delay}ms`);
      element.classList.add('yf-motion-item');
      element.addEventListener('focusin', () => {
        element.classList.add('yf-motion-visible');
        observer.unobserve(element);
      }, { once: true });
      observer.observe(element);
    });
  });

  // Modest, desktop-only parallax. All updates are scheduled once per frame,
  // and only while the portrait is in view; no library or scroll layout writes.
  const media = window.matchMedia('(min-width: 768px)');
  const portraitFrame = document.querySelector('#about .yf-about-media');
  const portrait = portraitFrame?.querySelector('img');
  let frameVisible = false;
  let scheduled = false;
  const update = () => {
    scheduled = false;
    if (!frameVisible || !media.matches || reduced.matches || !portraitFrame) return;
    const bounds = portraitFrame.getBoundingClientRect();
    const relative = (bounds.top + bounds.height / 2 - innerHeight / 2) / Math.max(1, innerHeight);
    const distance = Math.max(-12, Math.min(12, -relative * 15));
    portraitFrame.style.setProperty('--yf-motion-parallax', `${distance.toFixed(2)}px`);
  };
  const requestUpdate = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  };
  if (portraitFrame && portrait && media.matches) {
    portrait.classList.add('yf-motion-portrait');
    const visibleObserver = new IntersectionObserver(entries => {
      frameVisible = entries[0]?.isIntersecting === true;
      if (frameVisible) requestUpdate();
    }, { rootMargin: '100px' });
    visibleObserver.observe(portraitFrame);
    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate, { passive: true });
  }

  const disable = () => {
    observer.disconnect();
    targets.forEach(target => {
      target.classList.remove('yf-motion-item');
      target.classList.add('yf-motion-visible');
    });
    portrait?.classList.remove('yf-motion-portrait');
    portraitFrame?.style.removeProperty('--yf-motion-parallax');
  };
  reduced.addEventListener?.('change', event => { if (event.matches) disable(); });
  document.addEventListener('visibilitychange', () => {
    document.documentElement.classList.toggle('yf-motion-paused', document.hidden);
  });
})();

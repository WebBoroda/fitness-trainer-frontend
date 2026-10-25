(() => {
  'use strict';
  const root = document.documentElement;
  const trigger = document.querySelector('.theme-trigger');
  const options = document.getElementById('theme-options');
  const current = document.querySelector('.theme-current');
  const menu = document.querySelector('.menu-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  const allowed = new Set(['light', 'dark', 'mixed', 'auto']);
  const labels = { light: 'Light', dark: 'Dark', mixed: 'Mixed', auto: 'Auto' };
  let selected = 'mixed';
  try { const saved = localStorage.getItem('fitness-design-mode'); if (allowed.has(saved)) selected = saved; } catch (_) { /* Private mode may deny storage. */ }

  const apply = () => {
    const active = selected === 'auto' ? (media.matches ? 'dark' : 'light') : selected;
    root.dataset.theme = active;
    current.textContent = labels[selected];
    options.querySelectorAll('[data-mode]').forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.mode === selected)));
  };
  const closeTheme = () => { trigger.setAttribute('aria-expanded', 'false'); options.hidden = true; };
  const closeMenu = () => { menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Відкрити меню'); mobileNav.hidden = true; };
  apply();
  media.addEventListener?.('change', () => { if (selected === 'auto') apply(); });
  trigger.addEventListener('click', () => {
    const open = trigger.getAttribute('aria-expanded') !== 'true';
    closeMenu();
    trigger.setAttribute('aria-expanded', String(open));
    options.hidden = !open;
    if (open) options.querySelector('[aria-pressed="true"]')?.focus();
  });
  options.addEventListener('click', event => {
    const button = event.target.closest('button[data-mode]');
    if (!button) return;
    selected = button.dataset.mode;
    apply();
    try { localStorage.setItem('fitness-design-mode', selected); } catch (_) { /* Continue without persistence. */ }
    closeTheme();
    trigger.focus();
  });
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    closeTheme();
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Закрити меню' : 'Відкрити меню');
    mobileNav.hidden = !open;
  });
  mobileNav.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('click', event => { if (!event.target.closest('.theme-control')) closeTheme(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { closeTheme(); closeMenu(); }
  });
  const reveals = [...document.querySelectorAll('[data-reveal]')];
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); } });
    }, { threshold: 0.08, rootMargin: '0px 0px 70px 0px' });
    reveals.forEach(element => observer.observe(element));
  } else { reveals.forEach(element => element.classList.add('is-visible')); }
})();
/* Accessible fifth-screen detail dialog; native Escape / focus handling. */
(() => {
  'use strict';
  const open = document.querySelector('[data-about-open]');
  const dialog = document.getElementById('yf-about-details');
  const close = dialog?.querySelector('[data-about-close]');
  if (!open || !dialog || !close) return;
  open.addEventListener('click', () => dialog.showModal());
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.querySelector('[data-about-details-link]')?.addEventListener('click', () => dialog.close());
})();

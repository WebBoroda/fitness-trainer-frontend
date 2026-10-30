/* Preview footer: responsive map and social links driven by editable data. */
(() => {
  'use strict';
  const config = window.YF_SITE_CONFIG || {};
  const location = config.location || {};
  const socials = config.socialLinks || {};
  const $ = selector => document.querySelector(selector);
  const name = $('#yf-venue-name'), address = $('#yf-address');
  if (!name || !address) return;

  if (typeof location.venueName === 'string') name.textContent = location.venueName;
  if (typeof location.address === 'string') address.textContent = location.address;
  const isDemo = location.isDemo !== false;
  const mapDemoBadge = $('.yf-map-badge');
  if (mapDemoBadge) mapDemoBadge.hidden = !isDemo;
  $('.yf-year').textContent = String(new Date().getFullYear());

  const icons = {
    instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>',
    facebook: '<path d="M14 21v-8h3l.5-3.5H14V7c0-1.2.4-2 2-2h1.5V2.1A20 20 0 0 0 15 2c-3 0-5 1.9-5 5.3v2.2H7V13h3v8Z" fill="currentColor" stroke="none"/>',
    tiktok: '<path d="M14 3v11.4a4.4 4.4 0 1 1-3.6-4.3v3.4a1.2 1.2 0 1 0 .6 1V3h3Zm0 0c.3 3 2 4.4 5 4.7v3.3c-2.1 0-3.7-.6-5-1.8"/>',
    youtube: '<rect x="2" y="5" width="20" height="14" rx="4"/><path d="m10 9 6 3-6 3Z" fill="currentColor" stroke="none"/>',
    telegram: '<path d="m21 3-3.5 18-5.7-4.6-3.2 3.1.7-5.2L3 12.2 21 3Z"/><path d="m9.3 14.2 8.8-7.3"/>',
    whatsapp: '<path d="M20.5 11.7a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.5-4.6A8.5 8.5 0 1 1 20.5 11.7Z"/><path d="M8.8 8.3c.3-.6.7-.6 1.1 0l1 1.5c.1.3.1.5-.2.8l-.5.6c.9 1.5 1.9 2.5 3.6 3.2l.6-.7c.3-.3.6-.3.9-.1l1.6.8c.5.3.5.7.1 1.1-1.1 1.3-2.6 1.2-4.1.6a9 9 0 0 1-4.7-4.5c-.6-1.3-.6-2.3.6-3.3Z"/>',
    viber: '<rect x="3" y="3" width="18" height="16" rx="5"/><path d="M8 19 7 22l5-3M9 8c.8 3 2.5 4.5 5.5 5.7l1.5-1.4 1.5 1.1-.3 2c-4 1-9.5-4.4-9-8.3Z"/><path d="M13 7.5a4 4 0 0 1 4 4"/>'
  };
  const container = $('#yf-socials');
  if (container) for (const [network, svg] of Object.entries(icons)) {
    const raw = typeof socials[network] === 'string' ? socials[network].trim() : '';
    let valid = '';
    try {
      const url = new URL(raw);
      if (url.protocol === 'https:') valid = url.href;
    } catch (_) {}
    const element = document.createElement(valid ? 'a' : 'span');
    element.className = 'yf-social-link' + (valid ? '' : ' is-placeholder');
    element.setAttribute('aria-label', network.charAt(0).toUpperCase() + network.slice(1));
    if (valid) {
      element.href = valid;
      element.target = '_blank';
      element.rel = 'noopener noreferrer';
    } else {
      element.setAttribute('aria-disabled', 'true');
    }
    element.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + svg + '</svg>';
    container.appendChild(element);
  }

  const latitude = Number(location.latitude), longitude = Number(location.longitude);
  const validCoordinates = Number.isFinite(latitude) && Number.isFinite(longitude)
    && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
  const map = $('#yf-map'), directions = $('#yf-directions');
  const hasAddress = typeof location.address === 'string' && location.address.trim().length > 0;
  if (map && hasAddress) {
    const mapLabel = 'Карта: ' + location.address.trim();
    map.setAttribute('title', mapLabel);
    map.setAttribute('aria-label', mapLabel);
  }
  if (map && validCoordinates) {
    const zoom = Math.min(18, Math.max(8, Number(location.mapZoom) || 14));
    const delta = 0.006 * Math.pow(2, 14 - zoom);
    const bbox = [
      longitude - delta, latitude - delta,
      longitude + delta, latitude + delta
    ].map(n => n.toFixed(6)).join(',');
    map.src = 'https://www.openstreetmap.org/export/embed.html?bbox='
      + encodeURIComponent(bbox) + '&layer=mapnik&marker='
      + encodeURIComponent(latitude + ',' + longitude);
  }
  if (directions && hasAddress && validCoordinates) {
    directions.href = 'https://www.google.com/maps/dir/?api=1&destination='
      + encodeURIComponent(latitude + ',' + longitude);
    directions.target = '_blank';
    directions.rel = 'noopener noreferrer';
    directions.removeAttribute('aria-disabled');
    directions.removeAttribute('title');
  } else if (directions) {
    directions.removeAttribute('href');
    directions.setAttribute('aria-disabled', 'true');
    directions.setAttribute('title', 'Маршрут стане доступний після додавання адреси залу.');
  }
})();

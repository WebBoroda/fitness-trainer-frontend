(() => {
    'use strict';
    const root = document.documentElement;
    const body = document.body;
    const themeButton = document.getElementById('theme-button');
    const menuButton = document.getElementById('menu-button');
    const menu = document.getElementById('mobile-menu');
    const desktop = window.matchMedia('(min-width:1101px)');
    const dark = window.matchMedia('(prefers-color-scheme: dark)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const modes = ['light', 'dark', 'mixed'];
    const labels = { light: 'світла', dark: 'темна', mixed: 'контрастна' };
    const getSaved = () => {
        try { const value = localStorage.getItem('fitness-theme'); return modes.includes(value) ? value : null; }
        catch (_) { return null; }
    };
    const apply = (value, save = false) => {
        if (!modes.includes(value)) return;
        root.dataset.theme = value;
        root.dataset.selectedTheme = value;
        if (themeButton) {
            const next = modes[(modes.indexOf(value) + 1) % modes.length];
            themeButton.setAttribute('aria-label', 'Тема: ' + labels[value] + '. Перемкнути на ' + labels[next]);
            themeButton.title = 'Тема: ' + labels[value];
        }
        if (save) try { localStorage.setItem('fitness-theme', value); } catch (_) { /* Private mode. */ }
    };
    apply(getSaved() || (dark.matches ? 'dark' : 'light'));
    themeButton?.addEventListener('click', () => {
        const index = modes.indexOf(root.dataset.theme);
        apply(modes[(index + 1) % modes.length], true);
    });
    dark.addEventListener?.('change', () => { if (!getSaved()) apply(dark.matches ? 'dark' : 'light'); });

    const closeMenu = (focus = false) => {
        if (!menu || !menuButton) return;
        menu.hidden = true;
        menuButton.setAttribute('aria-expanded', 'false');
        menuButton.setAttribute('aria-label', 'Відкрити меню');
        body.classList.remove('menu-open');
        if (focus) menuButton.focus();
    };
    menuButton?.addEventListener('click', () => {
        if (!menu || desktop.matches) return;
        const opening = menu.hidden;
        menu.hidden = !opening;
        menuButton.setAttribute('aria-expanded', String(opening));
        menuButton.setAttribute('aria-label', opening ? 'Закрити меню' : 'Відкрити меню');
        body.classList.toggle('menu-open', opening);
        if (opening) menu.querySelector('a')?.focus();
    });
    menu?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => closeMenu()));
    desktop.addEventListener?.('change', () => { if (desktop.matches) closeMenu(); });

    const videoDialog = document.getElementById('hero-video-dialog');
    const videoTrigger = document.getElementById('hero-video-trigger');
    const pause = () => videoDialog?.querySelector('video')?.pause();
    videoTrigger?.addEventListener('click', () => {
        if (videoDialog && typeof videoDialog.showModal === 'function') videoDialog.showModal();
    });
    videoDialog?.querySelector('.fhero-video-close')?.addEventListener('click', () => videoDialog.close());
    videoDialog?.addEventListener('click', event => { if (event.target === videoDialog) videoDialog.close(); });
    videoDialog?.addEventListener('close', pause);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') closeMenu(true);
    });

    const reveals = Array.from(document.querySelectorAll('.reveal'));
    if ('IntersectionObserver' in window && !reduced.matches) {
        root.classList.add('yf-motion');
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px 40px 0px' });
        reveals.forEach((element, index) => {
            element.style.transitionDelay = ((index % 4) * 65) + 'ms';
            observer.observe(element);
        });
    } else reveals.forEach(element => element.classList.add('visible'));
    reduced.addEventListener?.('change', event => {
        if (event.matches) {
            root.classList.remove('yf-motion');
            reveals.forEach(element => element.classList.add('visible'));
        }
    });

    document.querySelectorAll('.faq-list details').forEach(details => {
        details.addEventListener('toggle', () => {
            if (!details.open) return;
            document.querySelectorAll('.faq-list details[open]').forEach(other => {
                if (other !== details) other.open = false;
            });
        });
    });

    // Responsive, keyboard-accessible carousel controls are only added on overflow.
    [document.querySelector('.result-strip'), document.querySelector('.reviews-list')].forEach(strip => {
        if (!strip) return;
        strip.setAttribute('tabindex', '0');
        strip.setAttribute('role', 'region');
        strip.setAttribute('aria-label', strip.classList.contains('result-strip') ? 'Галерея результатів' : 'Відгуки клієнток');
        const controls = document.createElement('div');
        controls.className = 'yf-slider-controls';
        for (const [direction, label, symbol] of [[-1, 'Попередні', '←'], [1, 'Наступні', '→']]) {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = symbol;
            button.setAttribute('aria-label', label);
            button.addEventListener('click', () => {
                strip.scrollBy({ left: direction * Math.max(240, strip.clientWidth * 0.8), behavior: reduced.matches ? 'instant' : 'smooth' });
            });
            controls.appendChild(button);
        }
        strip.insertAdjacentElement('afterend', controls);
        const update = () => { controls.hidden = strip.scrollWidth <= strip.clientWidth + 2; };
        if ('ResizeObserver' in window) new ResizeObserver(update).observe(strip);
        window.addEventListener('load', update, { once: true });
        update();
    });
})();

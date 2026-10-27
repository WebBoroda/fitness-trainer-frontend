# YULIIA ZAGORODNIA — interactive frontend

**Primary deliverable: the responsive, animated frontend published on GitHub Pages.** This is not a WordPress theme and does not need WordPress, PHP, or a build step.

Live URL: https://webboroda.github.io/fitness-trainer-frontend/

## Design and components

Implemented from the approved light/dark reference: a cinematic full-bleed hero, benefits, four program choices, studio photo gallery, trainer story with an overlay quote, nutrition, before/after gallery, reviews, pricing cards, FAQ and closing CTA. Original section architecture preserved and refined for 320–1920px.

- CSS: original design CSS in `index.html`, `assets/css/hero.css` and `assets/css/mission.css`; full-page layout updates in `assets/css/experience.css`; consultation modal in `assets/css/consultation.css`.
- JS: hero theme/menu and optional training-preview modal in `index.html`; accessible studio photo lightbox, scroll-snapping carousels, FAQ, progress indicator, active-section navigation and consultation-request composer in `assets/js/experience.js`.
- Media: local JPEG/WebP assets. 16 former base64-embedded section images are now separate optimized JPEGs for caching and faster HTML parsing.

## Actual interactive behavior

The visitor can switch between Light, Dark and Mixed color modes (stored locally), use the keyboard-accessible mobile menu, inspect studio pictures in a dialog (Escape + arrow keys), scroll the photo and review carousels, expand FAQ answers and open the consultation planner. The planner **copies a message locally**, and does not pretend to send data to an unconfigured server. Once a real contact channel or backend is provided, replace this demo intake flow with actual delivery.

The hero's video preview is currently an explanatory placeholder and **does not claim a playable real video**. A licensed and approved video is still required.

Motion includes progressive reveal and subtle hover motion, and honors `prefers-reduced-motion`.

## Development and tests

Run a local static HTTP server with Python:

```sh
python3 -m http.server 8000
```

Test interactive desktop/mobile rendering with:

```sh
pip install playwright pillow
playwright install chromium
python tests/smoke.py
python tests/experience_smoke.py
```

GitHub Actions validates this branch. It captures actual browser screenshots for visual review. Test success does **not** establish pixel-perfect equivalence with an unmeasured static reference.

## Remaining approval requirements

The approved reference is a visual screenshot rather than structured Figma geometry. Accurate photos, original media rights, verified client statistics, prices, authentic reviews and an actual video/contact endpoint have not been supplied. All such demonstration text must be replaced or validated before a commercial launch. Browser QA covers supported viewport checks, but full manual Safari/iOS review, WCAG audit and measured production Core Web Vitals are still outstanding.

The experimental WordPress conversion in a separate draft branch is not needed for this frontend delivery and is not deployed with GitHub Pages.


## Bilingual UI and editable footer data

- Language controls are in the header: **UA / EN**. On the first visit the page checks the browser's first preferred language (`en-*` → English, `uk-*` → Ukrainian, others → Ukrainian). A manual selection is saved in `localStorage` under `yuliia-language`, then takes precedence on return visits.
- English translations, including texts in all eleven sections, photo descriptions and consultation UI, live in **`assets/js/translations-en.js`**. The original Ukrainian copy stays in `index.html`. Translate dynamic elements using the same dictionary key; nothing requires a translation API.
- Social profile links, studio location and map coordinates are collected in **`assets/js/site-config.js`**. Fill in the verified destination address and social URLs there, then set `location.isDemo` to `false`. The map uses OpenStreetMap. A working Google Maps directions link is generated only once real coordinates are configured.
- Until real links are configured, social icons are intentionally non-clickable. The map is explicitly marked as a **demo location**, not a gym address; directions are disabled.
- Shared visual tokens for type tracking, CTA sizes, icon circles, spacing, fluid typography and footer layout are in **`assets/css/design-system.css`**. The handwritten video note is always visible and its decorative arrow has been removed.

### Automated checks

```sh
python tests/bilingual_system_smoke.py
python tests/hero_visual_audit.py
python tests/experience_smoke.py
```

The bilingual test checks first-visit language detection, persistent UA/EN switching, translated dynamic dialogs, working layout of CTA arrows, map/social rendering and captures mobile/tablet/desktop screenshots in both languages. CI gates publishing on these checks; this does not replace pixel-diff validation against a design source.

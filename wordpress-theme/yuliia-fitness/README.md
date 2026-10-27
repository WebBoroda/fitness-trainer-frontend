# Yuliia Fitness — dynamic WordPress theme

**Status: development / review, not production-ready.** This is a real classic WordPress theme with Gutenberg-managed, server-rendered section blocks. It is **not** a static HTML copy: all main section content lives in a WordPress page as editable block attributes and is rendered by PHP. The classic shell is deliberate because it preserves the custom approved 11-section hero layout more accurately than reflowing it through generic core blocks.

## Files

- `sections/*.php`: 11 reference-derived render templates (approved layout and CSS classes).
- `inc/sections.json`: editable texts, images, button destinations and labels for each section.
- `blocks/landing-section/block.json` and `assets/js/editor.js`: Gutenberg section picker, text controls, image media library and URLs.
- `assets/css/{site,hero,mission,motion}.css`: preserved reference styles and progressive animations.
- `assets/js/site.js`: color theme switcher, menu, scrolling reveals, keyboard-aware galleries, native FAQ accordion and optional video dialog.
- `parts/contact.php` + `functions.php`: WordPress booking/contact form using nonce validation, sanitization, consent, honeypot, rate limiting and `wp_mail`.
- `theme.json`: shared WordPress colors, typography and layout tokens.
- `tests/check_assets.py`: structural checks for all section files and media assets.

## Installation

1. Use a WordPress staging site with PHP 8.0+ and WordPress 6.5+.
2. Copy **the entire `yuliia-fitness` directory** into `wp-content/themes/`.
3. Go to **Appearance → Themes** and activate **Yuliia Fitness**.
4. If there is no configured homepage, the theme creates a **Головна** page with 11 dynamic blocks and assigns it as the homepage. A configured homepage is **never overwritten**.
5. To edit, open **Pages → Головна → Edit**. Select each `Yuliia — секція лендингу` block. Change text, links, and images using the built-in Gutenberg controls. Drag whole sections to reorder them. Click **Update**.
6. Configure navigation in **Appearance → Menus** (or **Appearance → Menus → Manage Locations**): assign the menu to **Головне меню**. Without one, the approved default section-anchor links appear.
7. Configure **Settings → General → Administration Email Address** and check a reliable SMTP/mail transport. Form submissions send to the administrator email. Verify outbound mail end-to-end before accepting inquiries.
8. In **Appearance → Customize → Yuliia: налаштування сайту**, optionally set an MP4 video URL. The play control is hidden when there is no video. The demo-content notice may be disabled **only after** images, client statistics, prices, and testimonials are verified.
9. Configure a privacy policy through WordPress settings before collecting personal information. Check consent text against the site's actual data processing practices.
10. Configure backups, staging, canonical metadata/SEO plugin if used, caching and monitoring based on the target host. No production deployment is included in this branch.

## What is dynamic?

Each Gutenberg block has a section type and editable structured fields. Frontend PHP reads **saved block attributes from the WordPress database**, escapes output, loads selected WordPress media images and renders the approved HTML structure. Blocks can be reordered or removed. Menus are WordPress menus; the contact form is server-side and submits to WordPress. The WordPress editor supports section-specific text, button targets and image replacement. **Individual card counts and new repeater cards are not yet editable**, although existing cards' content can be changed.

## Interactions and motion

- Theme modes: light, dark, mixed; locally remembered preference; auto-detect on first visit.
- Motion only when supported and allowed: CSS entrances, scroll reveals, subtle card transitions.
- Accessible mobile menu (expanded state, focus and Escape).
- Gallery carousel arrows only when the content overflows; touch/keyboard scrolling retained.
- FAQ uses native `details/summary`.
- Video dialog appears only for a configured MP4 URL; close pauses playback.
- `prefers-reduced-motion` disables meaningful animation; content remains visible if JavaScript is off.

## Quality and limitations

Run from repository root:

```bash
find wordpress-theme/yuliia-fitness -type f -name '*.php' -print0 | xargs -0 -n1 php -l
node --check wordpress-theme/yuliia-fitness/assets/js/site.js
node --check wordpress-theme/yuliia-fitness/assets/js/editor.js
python3 wordpress-theme/yuliia-fitness/tests/check_assets.py
```

GitHub Actions runs static validation. **NOT TESTED:** theme installation in WordPress, Gutenberg persistence, contact email delivery, accessibility audit, responsive visual comparison with the approved 320–1920px mockups, Safari/iOS and Firefox, real Lighthouse/CWV measurements. Tests must be run on staging before production use.

**Media provenance:** extracted pictures are temporary fragments of the supplied reference design, **not licensed original photos**. Replace them with approved originals. **Demo figures, prices, success stories and reviews are not verified facts**; do not publish them as claims without sign-off.

## Deployment

Create a backup; deploy/theme-install on staging; configure menus and mail; replace all media and verify claims; test mobile/desktop and editing; run QA; then promote to production with rollback to the previous theme possible. Theme switching does not delete block content.

See `QA.md` for the per-section checklist and verification gates.

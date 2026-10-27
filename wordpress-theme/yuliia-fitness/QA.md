# WordPress QA status — Yuliia Fitness

Legend: PASS = executed and passing; FAIL = executed and failed; NOT TESTED = not executed; BLOCKED = missing environment / approval. Static checks become PASS only when CI has run successfully.

## Page-by-page (homepage — 11 sections)

| Section | Implemented PHP | Block editing on live WordPress | Responsive/visual | Animation/interaction | Content validation |
|---|---|---|---|---|---|
| First screen | PASS | NOT TESTED | NOT TESTED | PASS — theme switch | BLOCKED — media and statistics |
| Mission | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — original image |
| Programs | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — media |
| Studio | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — venue photos |
| About | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — biography and photo |
| Nutrition | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — nutrition photo |
| Results | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — consent and claims |
| Reviews | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — authentic testimonials |
| Pricing | PASS | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — real prices |
| FAQ | PASS | NOT TESTED | NOT TESTED | PASS — accordion | NOT TESTED |
| Final CTA | PASS | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Contact form | PASS | N/A | NOT TESTED | NOT TESTED | BLOCKED — SMTP, privacy policy |

## Cross-cutting gates

| Item | Status | Required verification |
|---|---|---|
| PHP syntax | PASS | GitHub Actions PHP 8.2 |
| JS syntax | PASS | GitHub Actions Node 22 |
| Structure/media integrity | PASS | 11 sections, schema and media check |
| Gutenberg block data saving | PASS | WordPress + MySQL, changed field and re-rendered via WP-CLI |
| Gutenberg visual editor | NOT TESTED | Manual editor/media library verification |
| Theme switcher | PASS | Chromium interactive switch and persistence |
| Mobile navigation | PASS | Chromium open/close/Escape; mobile touch NOT TESTED |
| Contact email delivery | BLOCKED | SMTP test and admin email |
| Video playback | BLOCKED | Approved MP4 URL |
| WCAG 2.2 AA | NOT TESTED | Axe + keyboard + screen readers |
| Core Web Vitals | NOT TESTED | Real measured LCP/INP/CLS |
| Responsive overflow 320–1920px | PASS | Chromium viewport checks and screenshots |
| Visual regression vs approved screenshots | NOT TESTED | Screenshots collected but not compared to source mockup |
| SEO | NOT TESTED | Sitemap, canonical, metadata, structured data only if factual |
| Security | NOT TESTED | WordPress runtime validation + dependency review |
| Browser matrix | NOT TESTED | Chromium smoke PASS; Firefox, Safari, Edge, iOS and Android NOT TESTED |

**Production readiness: BLOCKED.** Do not mark as approved until all required criteria are passed.

# WordPress QA status — Yuliia Fitness

Legend: PASS = executed and passing; FAIL = executed and failed; NOT TESTED = not executed; BLOCKED = missing environment / approval. Static checks become PASS only when CI has run successfully.

## Page-by-page (homepage — 11 sections)

| Section | Implemented PHP | Block editing on live WordPress | Responsive/visual | Animation/interaction | Content validation |
|---|---|---|---|---|---|
| First screen | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — media and statistics |
| Mission | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — original image |
| Programs | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — media |
| Studio | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — venue photos |
| About | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — biography and photo |
| Nutrition | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — nutrition photo |
| Results | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — consent and claims |
| Reviews | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — authentic testimonials |
| Pricing | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | BLOCKED — real prices |
| FAQ | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Final CTA | Code added / NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Contact form | Code added / NOT TESTED | N/A | NOT TESTED | NOT TESTED | BLOCKED — SMTP, privacy policy |

## Cross-cutting gates

| Item | Status | Required verification |
|---|---|---|
| PHP syntax | NOT TESTED | GitHub Actions workflow PHP 8.2 |
| JS syntax | NOT TESTED | Node check |
| Structure/media integrity | NOT TESTED | Python structural test |
| Gutenberg edit/save | NOT TESTED | Insert blocks, update fields, reload |
| Theme switcher | NOT TESTED | Light/dark/mixed, system preference and persistence |
| Mobile navigation | NOT TESTED | Touch, keyboard, Escape and links |
| Contact email delivery | BLOCKED | SMTP test and admin email |
| Video playback | BLOCKED | Approved MP4 URL |
| WCAG 2.2 AA | NOT TESTED | Axe + keyboard + screen readers |
| Core Web Vitals | NOT TESTED | Real measured LCP/INP/CLS |
| Visual regression 320–1920px | NOT TESTED | Browser screenshots vs supplied references |
| SEO | NOT TESTED | Sitemap, canonical, metadata, structured data only if factual |
| Security | NOT TESTED | WordPress runtime validation + dependency review |
| Browser matrix | NOT TESTED | Chrome, Firefox, Safari, Edge, iOS and Android |

**Production readiness: BLOCKED.** Do not mark as approved until all required criteria are passed.

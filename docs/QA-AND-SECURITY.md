# QA and publishing review — 2026-10-19

## Automated QA (`python tests/qa.py`): 41 passed, 0 failed
Desktop 1440, tablet 820, mobile 390 (headless Chromium): no console errors/warnings, only same-origin requests, no horizontal scroll, one `h1`, all images loaded with `alt`, anchors resolve, external links https + `rel=noopener`, mobile menu, 4 dialogs open/close (Esc), PT toggle and full PT key coverage, skip link first in tab order, reduced-motion shows all content, no-JS shows hero and projects, contact renders only configured channels.
Not done: Lighthouse/axe, real-device test, formal contrast measurement (palette chosen for high contrast; muted text #98a4b6 on #0a0d12 ≈ 7.5:1 by calculation).

## Claims audit (source: fivem-lab docs + live runs, 2026-10-19)
| Claim on site | Evidence |
|---|---|
| 1,152 tests, 0 failed | Re-run today: core 29 + phone Lua 617 + character Lua 389 + UI unit 5 + Chromium e2e 112 |
| Core booted on real FXServer | `docs/testing.md` 2026-10-18 (loopback, resource started, JSON log) |
| PR #780 open, +16/−3, 1 file | `gh pr view 780`: OPEN, REVIEW_REQUIRED, not merged |
| Character/phone not verified in-game | Stated in their docs; shown on the site |
Screenshots are the NUI in headless Chromium with a simulated bridge (labelled). No clients, testimonials, downloads, certifications or invented contacts.

## Publishing safety review
- Files are only the static site (HTML/CSS/JS, 3 phone images, OG image, icons). No source from the private `fivem-lab`, no `server.cfg`/`secrets.cfg`, tokens, IPs, local paths (static scan in `qa.py` passes).
- Phone screenshots show demo data only (fictional names, fake balance, "simulation" banners); contain a third-party car name ("Bugatti Chiron") in a home widget: trademark use is incidental, but consider swapping the demo vehicle to a generic name and recapturing.
- The private repo stays private; nothing here references its URL.
- Pending before going live: Discord/e-mail in `config.js` (optional), user approval (Gate E).

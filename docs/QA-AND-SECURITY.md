# QA and security review: V2 final gate (2026-10-19)

## 1. Demo iframe: threat model and decision
The demo is the phone's own NUI code running in an `<iframe>`. Its only user-controlled input is text the visitor types into it (messages, PIX fields), which the app renders as plain text.
| Option | Isolation | Verdict |
|---|---|---|
| Same origin, no sandbox (state in commit `90af5ce`) | None: frame script can read/modify the parent DOM, storage, cookies | Rejected: unnecessary trust for a visitor-facing page |
| `sandbox="allow-scripts allow-same-origin"` (commit `90af5ce` first attempt) | **Equivalent to no sandbox** for a same-origin page (Chromium warns the frame "can escape its sandboxing") | Rejected; the warning was right |
| **`sandbox="allow-scripts"` (chosen)** | Opaque origin: the frame cannot touch the parent DOM, `localStorage`, cookies or `window.parent` data; no popups, no forms, no top navigation, no downloads | Chosen |
| Separate origin (second domain) | Strongest | Not available (no custom domain); the opaque origin gives the same property |
Cost of the choice: an opaque-origin page loads its ES modules with CORS. **GitHub Pages sends `Access-Control-Allow-Origin: *`** (verified with `curl -I https://pages.github.com/`), and the local test servers send the same header. Residual risk: if Pages ever stopped sending it, the demo would not load (it fails closed; the poster/launch button area would stay empty). The post-publish smoke test in `PUBLISH-PLAN.md` covers it.

Additional layers (nothing was weakened to silence a warning):
- Iframe attributes: `sandbox="allow-scripts"`, `allow=""` (no camera/mic/geolocation/clipboard policy grants), `referrerpolicy="no-referrer"`, created only on click.
- Page CSP (meta): `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'`. No inline scripts (the former inline script moved to `assets/js/boot.js`), no `unsafe-inline`, no `unsafe-eval`.
- Demo document CSP (vendored file, patched by script): `connect-src 'none'`-equivalent for the network is `'self'` only (was `'self' https:`), plus `base-uri/form-action/object-src 'none'`. The only `fetch` in the code targets `https://devlab_phone/<name>` and is answered in-page by `sim.js` before any network call.
- Verified by `tests/qa.py`: sandbox value exact, parent cannot read the frame, no external requests, no console warnings after a full interaction, storage holds nothing but the language preference.
- Not possible on a static Pages site: `frame-ancestors`/`X-Frame-Options` headers (meta CSP ignores them). Impact: the site itself can be framed by others; it holds no session or data, so clickjacking has nothing to steal.

## 2. Data and provenance
- Demo data is fictitious (made-up names, fake balance, "COMPROVANTE DE SIMULAÇÃO"). No credentials, IPs, tokens, license keys, webhooks or local paths in tracked files (static scan, including Discord token/webhook patterns).
- `demo/phone/` = devlab_phone NUI @ `aa99dd7` (committed state, not working tree) + `sim.js` + `demo.css`; every deviation is a scripted, asserted patch listed in `demo/phone/SOURCE.txt`; `python tools/sync-demo.py --src … --rev aa99dd7 --check` fails on any drift.
- Assets: screenshots are of this project's own NUI (recaptured from `demo/phone` after the vehicle rename); no stock images, no web fonts (system stack), icons follow Lucide (ISC), attribution in `NOTICE.md`. The private repo has **no license file**: code is all-rights-reserved until the owner decides (see PUBLISH-PLAN Gate 0).
- Trademark: the demo now shows "Supercarro (demo)". The vehicle id (`chiron`) remains in internal test ids and the simulated RPC payload only (never displayed). The real game behavior is untouched (patch is display-only, in the generated copy).

## 3. Evidence (reproducible)
`python tools/verify-evidence.py --src … --python …` exports commit `aa99dd7` with `git archive` (source repo and branches untouched) and re-runs the suites: core 29, phone Lua 617, character Lua 417, UI unit 5, UI e2e 112 = **1,180 passed, 0 failed**; `gh pr view 780` = OPEN, REVIEW_REQUIRED, not merged. The page matches. Numbers are dated snapshots (2026-10-19), not live; the page says so. Qbox PR #780 is presented as open/awaiting review everywhere (hero, cards, dialog, evidence table, Discord text).

## 4. Results
| Check | Result |
|---|---|
| `python tests/qa.py` (desktop/tablet/mobile, security posture, i18n, quote flow, Discord states, demo, static scan) | 78 passed, 0 failed |
| `python tests/test_tools.py` (discord_apply against a fake API, set-contact) | 22 passed, 0 failed |
| Browser walk-through, desktop 1440 + mobile 390 (keyboard, nav, demo full interaction, console, network, storage) | 34 passed, 0 failed |
| Lighthouse 13.5 mobile / desktop (local server) | performance 99 / 100, accessibility 100 / 100, best-practices 100 / 100, SEO 92 / 92; LCP 2.0 s / 0.6 s, CLS 0, TBT 0 ms, 198 KB transferred |
| axe-core 4.14 (WCAG 2.0/2.1/2.2 A+AA + best-practice) on page EN/PT/mobile, dialog open, quote with brief | 0 violations |
| axe on the vendored demo | 3 violations in the **product's own NUI** (see below) |
Lighthouse SEO 92: the `robots-txt` audit fails only because Lighthouse fetches `robots.txt` through the page, and `connect-src 'none'` blocks that fetch. Crawlers are not subject to the page CSP; file content is valid. Kept on purpose (relaxing the CSP to score 100 would trade away a protection).
axe "needs review" items (not violations): colour contrast on gradient/translucent areas (Lighthouse's own contrast audit passes) and one `aria-prohibited-attr` candidate.

### Findings in `devlab_phone` (not changed, belongs to the private project)
1. `.widget-today` and `#btn-back`: accessible name does not contain the visible text (WCAG 2.5.3).
2. `.pill` (vehicle call button in its pending state): low contrast.
Recommendation: fix in `devlab_phone`, then re-run `sync-demo.py`. They are real accessibility issues of the NUI, independent of the portfolio.

## 5. Not done
Real-device testing, in-game verification, post-publish checks (impossible before publishing). Discord layout, permissions, and channel text were applied on 2026-10-19 (see `docs/discord/SETUP.md`). No public invite was created.

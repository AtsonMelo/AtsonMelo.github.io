# QA and publishing review — V2 (2026-10-19)

## Automated QA (`python tests/qa.py`): see result in the final report
Covers desktop 1440 / tablet 820 / mobile 390: console clean, same-origin requests only (including the demo iframe), no horizontal scroll, one h1, images loaded with alt, anchors, external links, mobile menu, 4 dialogs, PT/EN (text, alt, placeholders, full key coverage), skip link, reduced motion, no-JS, 4 service cards + CTA preselect, quote form (validation, brief, channel-dependent actions, configured-channel variant), demo (render, vehicle call, PIX receipt, close/reopen, mobile fit), evidence numbers (new total present, stale one absent), static scan (private IPs, secret-like words, local paths).
Not done: Lighthouse/axe, real devices, formal contrast measurement, in-game verification.

## Claims audit
| Claim | Evidence |
|---|---|
| 1,180 tests, 0 failed (snapshot 2026-10-19) | core 29 + phone Lua 617 + character Lua 417 + UI unit 5 + Chromium e2e 112, fivem-lab @ aa99dd7 (working branch) |
| Core booted on real FXServer | fivem-lab docs/testing.md, 2026-10-18 |
| PR #780 open, review required | `gh pr view 780`, 2026-10-19 |
| Core is a reference resource; other resources reuse its patterns, no runtime dependency | manifests: no dependency entries; devlab_phone manifest comment ("same pattern as devlab_core") |
| Character: per-player persistence, ACE-restricted commands | server/main.lua (resource KVP, IsPlayerAceAllowed); offline tests only |
V1 text said core was "shared by the other resources": corrected.

## Visual inspection (2026-10-19)
Browser walk-through of desktop 1440 and mobile 390 (Chromium): 34 checks, 0 failures; QA suite 58, 0 failures. Fixed during inspection: Chromium warning from the iframe sandbox (removed, it added no isolation), demo vehicle text claiming in-game confirmation (patched by script), mobile hero stat cards covering the phone, lazy-image test flake.

## Publishing risks to decide (Gate E)
1. **`demo/phone/` is NUI source code** of a private resource. Publishing it publishes that frontend. It is client-delivered code in any server using it, contains no secrets (scan passes), but it is a decision for the owner.
2. Demo/screenshots show the model name "Bugatti Chiron" (third-party trademark, incidental). Consider a generic demo vehicle.
3. Quote destination: no e-mail/Discord configured; public-issue option is off by default.
4. The tests commit is on a private working branch; the page says so.

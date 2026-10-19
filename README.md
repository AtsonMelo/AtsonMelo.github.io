# DEVLAB — Atson Melo (portfolio)

Static portfolio site for Atson Melo, FiveM developer. Plain HTML/CSS/JS: no framework, no build step, no external requests (system fonts), so it runs as-is on GitHub Pages.

## Layout
```
index.html            page (English source text) + project detail dialogs
assets/css/styles.css design tokens (:root) and all styles
assets/js/config.js   CONTACT CONFIG — fill in confirmed channels
assets/js/i18n.js     Portuguese strings (EN lives in the HTML)
assets/js/main.js     language toggle, menu, dialogs, contact render, reveal
assets/img/           phone-*.webp (screenshots), og.png, favicon.svg
tools/                og.html + make-og.py (regenerates the social image)
tests/qa.py           local QA (console, overflow, links, i18n, dialogs, scan)
docs/                 QA report, publishing review
```

## Run locally
```
python -m http.server 8000      # then open http://localhost:8000
python tests/qa.py              # needs: pip install playwright && playwright install chromium
python tests/qa.py --shots out  # also saves full-page screenshots
```

## Update content
- **Projects:** edit the `<article class="card">` blocks and matching `<dialog>` in `index.html`. For every text, add/update the PT string in `assets/js/i18n.js` (same `data-i18n` key); `tests/qa.py` fails if a key is missing.
- **Status honesty rule:** only claim what is verified. Keep badges accurate (tested offline / in development / submitted / merged). Do not write "merged" for a PR until GitHub says so.
- **Numbers** (tests, PR state) are dated; re-verify before each publish: hero, proof strip and dialogs.

## Screenshots and video
- Put images in `assets/img/` (prefer `.webp`, ≤ 100 KB each) and reference them in the card's `.card-media`. Replace the "MEDIA PLACEHOLDER" block of DevLab Character with a real in-game capture when one exists.
- Video: use a short, compressed `.mp4`/`.webm` (≤ 5 MB) in `assets/video/` with a `poster`, or link to YouTube. Never use captures showing IPs, usernames, license keys, or third-party assets you cannot redistribute.
- The current phone images are the NUI rendered in headless Chromium with a simulated FiveM bridge (labelled on the page), not in-game captures.

## Contacts
Edit `assets/js/config.js`. Empty values are not rendered; nothing is invented. While Discord and e-mail are empty, the page shows a note and GitHub only.

## Publish (GitHub Pages, user site)
1. Create the **public** repo `AtsonMelo/AtsonMelo.github.io` (exact name).
2. Push `main`. 3. Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)`.
4. Wait ~1 min; site appears at https://atsonmelo.github.io/. `.nojekyll` is already present.

## Roll back
`git revert <commit>` and push (no force push needed), or Settings → Pages → *Unpublish site*. Deleting/making the repo private also takes the site down.

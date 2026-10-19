# Publishing plan: AtsonMelo/AtsonMelo.github.io (NOT executed)

Nothing below has been run. Every step that touches GitHub needs the owner's explicit approval.

## Facts checked (2026-10-19)
- Repo `AtsonMelo/AtsonMelo.github.io` does **not** exist (name is free). Account `AtsonMelo` is a User account, so the repo name `<user>.github.io` publishes at **https://atsonmelo.github.io/** (root URL, no sub-path).
- `AtsonMelo/fivem-lab` is **private** and stays private; nothing here references or links to it.
- GitHub Pages sends `Access-Control-Allow-Origin: *` (verified with `curl -I https://pages.github.com/`). The sandboxed demo iframe depends on it for its ES modules.
- A free-plan Pages site requires a **public** repo. Everything tracked in git becomes public, including `docs/`, `tests/`, `tools/`, `demo/`.

## Gate 0: decisions needed before publishing
1. Publish `demo/phone/` (the phone's NUI frontend source, no secrets)? If not: delete `demo/`, the `#demo` section and `data-open`/launch JS, and drop `tools/sync-demo.py`.
2. Code license. None chosen (all rights reserved by default, stated in `NOTICE.md`). Options: keep all rights reserved (safest for a commercial portfolio) or add MIT for the site shell only. Not decided for you.
3. Contact: Discord invite (see `docs/discord/SETUP.md`), e-mail, or neither (copy-only flow with the "being set up" note).
4. Discord pre-check: make sure `#github-updates` does not leak private repo activity before sharing any invite.

## Step 1: final local gate (no network writes)
```
python tools/preflight.py --src C:\Atson\02-projetos\fivem-lab --python C:\Atson\02-projetos\fivem-lab\.venv\Scripts\python.exe
```
Must print `VERDICT: GO`. It runs QA, tool tests, demo drift check, evidence re-measure, file scan and the contact status.

## Step 2: bring the branch to `main` (local)
```
git switch main
git merge --ff-only feat/v2-commercial     # main only has the V1 commit; this is a fast-forward
git log --oneline -6
```

## Step 3: create the public repo and push (needs approval)
```
gh repo create AtsonMelo/AtsonMelo.github.io --public --description "DEVLAB - Atson Melo, FiveM developer portfolio"
git remote add origin https://github.com/AtsonMelo/AtsonMelo.github.io.git
git push -u origin main
```
Never `--force`. Review the exact file list first: `git ls-files`.

## Step 4: enable Pages
```
gh api -X POST repos/AtsonMelo/AtsonMelo.github.io/pages -f "source[branch]=main" -f "source[path]=/"
gh api repos/AtsonMelo/AtsonMelo.github.io/pages --jq .html_url
```
Settings → Pages: tick **Enforce HTTPS** (default). `.nojekyll` is present, so files are served as-is.

## Step 5: post-publish smoke test (after ~1-2 minutes)
- `curl -sI https://atsonmelo.github.io/` → 200; also `/robots.txt`, `/sitemap.xml`, `/assets/img/og.png`, `/demo/phone/index.html`, `/demo/phone/js/main.js` (must carry `access-control-allow-origin: *`).
- Open the site: console clean, demo launches and a vehicle call completes, PT/EN toggle, quote flow, links (GitHub, PR #780, issue #678, Discord if set).
- Link previews: paste the URL in Discord/Slack to check the `og:image` (absolute URL, valid only after publishing).
- Optional: `gh repo edit AtsonMelo/AtsonMelo.github.io --homepage https://atsonmelo.github.io`.

## Updating later
- Content/evidence: edit, then `python tools/verify-evidence.py ...` and `tools/preflight.py`; commit; push.
- Demo: `python tools/sync-demo.py --src <fivem-lab> --rev <commit>` (reads a commit, not the working tree), then `--check`, QA, commit. The commit hash in `demo/phone/SOURCE.txt` and the evidence table must match what you measured.
- Do not edit `demo/phone/` by hand (drift check fails).

## Rollback
- Bad content: `git revert <sha>` + push (history preserved, no force push). Pages redeploys in ~1 min.
- Take the site down immediately: `gh api -X DELETE repos/AtsonMelo/AtsonMelo.github.io/pages` (unpublish) or set the repo private.
- Remove only the demo: `git rm -r demo` + remove the `#demo` section, commit, push.
- Leaked something: unpublish first, then rotate whatever leaked; deleting a commit later does not erase forks/caches.

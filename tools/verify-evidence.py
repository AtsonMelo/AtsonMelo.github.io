"""Pre-publish gate: re-measures the numbers shown on the site and fails if the page is stale.

Runs the private project's suites against an exported copy of ONE COMMIT (git archive: the source repo,
its branches and its working tree are never modified) and compares with index.html and the Qbox PR state.

  python tools/verify-evidence.py --src <fivem-lab> --python <py with lupa> [--commit aa99dd7]

--python: interpreter that can import `lupa` (the fivem-lab .venv). Playwright must be importable by the
interpreter running this script (used for the browser suite). Needs: git, node, gh (logged in)."""
import argparse, io, json, pathlib, re, subprocess, sys, tarfile, tempfile

root = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True); ap.add_argument("--python", required=True); ap.add_argument("--commit")
a = ap.parse_args()
html = (root / "index.html").read_text(encoding="utf-8")
commit = a.commit or re.search(r"commit ([0-9a-f]{7})", html).group(1)

def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def passed(out, pat):
    m = re.findall(pat, out)
    return int(m[-1]) if m else None

with tempfile.TemporaryDirectory() as t:
    data = subprocess.run(["git", "-C", a.src, "archive", commit, "resources"], capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(data)).extractall(t, filter="data")
    rows = []
    for name, cmd, pat in (
        ("devlab_core Lua", [a.python, "-I", "resources/devlab_core/tests/run.py"], r"(\d+) passed, \d+ failed"),
        ("devlab_phone Lua", [a.python, "-I", "resources/devlab_phone/tests/run.py"], r"TOTAL: (\d+) passed"),
        ("devlab_character Lua", [a.python, "-I", "resources/devlab_character/tests/run.py"], r"TOTAL: (\d+) passed"),
        ("phone UI unit (node)", ["node", "--test", "resources/devlab_phone/tests/ui/unit.test.mjs"], r"ℹ pass (\d+)"),
        ("phone UI e2e (chromium)", [sys.executable, "resources/devlab_phone/tests/ui/e2e.py"], r"UI e2e: (\d+) passed"),
    ):
        code, out = run(cmd, t)
        fails = passed(out, r"(\d+) failed") if "node" not in cmd[0] else passed(out, r"ℹ fail (\d+)")
        rows.append((name, passed(out, pat), fails, code))

total = sum(r[1] or 0 for r in rows)
print(f"commit {commit}")
for n, p, f, c in rows: print(f"  {n:26} passed={p} failed={f} exit={c}")
print(f"  TOTAL passed={total}")
problems = []
if any(r[1] is None or r[3] != 0 or (r[2] or 0) != 0 for r in rows): problems.append("a suite failed or could not be parsed")
shown = f"{total:,}"
if f"{shown} passed" not in html: problems.append(f"index.html does not show the measured total {shown}")
for n, p, _, _ in rows:
    if p is not None and not re.search(rf"\b{p} passed, 0 failed", html): problems.append(f"index.html lacks '{p} passed, 0 failed' for {n}")

pr = json.loads(subprocess.run(["gh", "pr", "view", "780", "--repo", "Qbox-project/qbx_core", "--json", "state,mergedAt,reviewDecision"], capture_output=True, text=True, encoding="utf-8").stdout or "{}")
print("  Qbox PR #780:", pr)
if pr.get("state") != "OPEN" or pr.get("mergedAt"):
    problems.append(f"PR #780 is no longer open ({pr}); update the PR wording on the page")
if problems:
    print("STALE / FAIL:"); [print("  -", x) for x in problems]; sys.exit(1)
print("OK: page numbers match a fresh run of the exported commit; PR state matches the page.")

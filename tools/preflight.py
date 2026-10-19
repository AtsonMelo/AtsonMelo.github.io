"""Go/no-go report before publishing. Read-only: runs checks, prints a verdict, changes nothing.

  python tools/preflight.py [--src <fivem-lab> --python <py with lupa>]

Always: git state, QA suites, tools tests, file list/size/forbidden-name scan, contact config status.
With --src (+ --python): demo drift check against the recorded commit and a fresh re-measure of the evidence."""
import argparse, json, pathlib, re, subprocess, sys

root = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument("--src"); ap.add_argument("--python"); a = ap.parse_args()
blockers, pending = [], []

def sh(cmd, **kw):
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    return r.returncode, (r.stdout + r.stderr).strip()

code, out = sh(["git", "status", "--porcelain"])
print("git:", sh(["git", "branch", "--show-current"])[1], "| HEAD", sh(["git", "rev-parse", "--short", "HEAD"])[1], "| dirty files:", len(out.splitlines()))
if out: blockers.append("working tree not clean (commit or stash first)")

for name, cmd in (("QA suite", [sys.executable, "tests/qa.py"]), ("tools tests", [sys.executable, "tests/test_tools.py"])):
    code, out = sh(cmd); last = out.splitlines()[-1] if out else ""
    print(f"{name}: {last}")
    if code: blockers.append(f"{name} failed")

files = sh(["git", "ls-files"])[1].splitlines()
big = [(f, (root / f).stat().st_size) for f in files if (root / f).stat().st_size > 1_000_000]
bad = [f for f in files if re.search(r"(?i)(\.env|\.cfg|\.pem|\.key|\.pfx|secrets?|credential|id_rsa)", pathlib.Path(f).name)]
print(f"files to publish: {len(files)}, total {sum((root / f).stat().st_size for f in files) // 1024} KB; > 1 MB: {big or 'none'}; forbidden names: {bad or 'none'}")
if big or bad: blockers.append("oversized or forbidden-looking file in the tracked set")

cfg = (root / "assets/js/config.js").read_text(encoding="utf-8").split("window.SITE_CONFIG", 1)[1]  # skip the explanatory comment
val = lambda k: (re.search(rf'{k}:\s*"([^"]*)"', cfg) or [None, ""])[1]
for k in ("discordUrl", "email"):
    print(f"contact {k}: {'SET' if val(k) else 'EMPTY'}")
if not (val("discordUrl") or val("email") or val("issuesRepo")): pending.append("no real contact channel configured (quote flow is copy-only)")
if val("discordUrl"):
    code, out = sh([sys.executable, "tools/set-contact.py", "--discord", val("discordUrl"), "--check-online"]); print(out.splitlines()[0] if out else "")
    if code: blockers.append("configured Discord invite failed validation: " + out.splitlines()[-1])

if a.src:
    code, out = sh([sys.executable, "tools/sync-demo.py", "--src", a.src, "--rev", re.search(r"commit ([0-9a-f]{7})", (root / "demo/phone/SOURCE.txt").read_text(encoding="utf-8")).group(1), "--check"]); print("demo drift:", out.splitlines()[-1])
    if code: blockers.append("demo/phone drifted from its recorded source commit")
    if a.python:
        code, out = sh([sys.executable, "tools/verify-evidence.py", "--src", a.src, "--python", a.python]); print("evidence:", out.splitlines()[-1])
        if code: blockers.append("evidence numbers stale or suites failing")
else:
    pending.append("demo drift and evidence not re-verified (pass --src and --python)")

print("\nBLOCKERS:", blockers or "none"); print("PENDING (owner decisions / data):", pending or "none")
print("VERDICT:", "NO-GO" if blockers else "GO (technically); resolve pending items you care about")
sys.exit(1 if blockers else 0)

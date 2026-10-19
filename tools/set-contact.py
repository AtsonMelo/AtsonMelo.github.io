"""Validates and writes the real contact channels into assets/js/config.js (nothing is invented).

  python tools/set-contact.py --discord https://discord.gg/CODE [--check-online]
  python tools/set-contact.py --email name@domain [--issues owner/repo] [--clear-discord]

--check-online asks Discord's public invite endpoint (no login, read-only) whether the invite works, which
server and channel it opens, and whether it expires. A temporary or limited invite is rejected: the site
would break for visitors."""
import argparse, json, pathlib, re, sys, urllib.error, urllib.request

CFG = pathlib.Path(__file__).resolve().parents[1] / "assets" / "js" / "config.js"
INVITE = re.compile(r"^https://(?:discord\.gg|discord\.com/invite)/([A-Za-z0-9-]{2,32})$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def check_online(code):
    req = urllib.request.Request(f"https://discord.com/api/v10/invites/{code}?with_counts=true", headers={"User-Agent": "devlab-set-contact/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: j = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"invite rejected by Discord (HTTP {e.code}): expired, revoked or wrong code")
    g, ch = j.get("guild", {}), j.get("channel", {})
    print(f"invite OK: server '{g.get('name')}', opens #{ch.get('name')}, members ~{j.get('approximate_member_count')}")
    if j.get("expires_at"): sys.exit(f"invite expires at {j['expires_at']}: create a permanent one (Edit invite link -> Expire after: Never, Max uses: No limit)")
    return g.get("name")


def set_key(text, key, value):
    pat = re.compile(rf'({key}:\s*)"[^"]*"')
    if not pat.search(text): sys.exit(f"key {key} not found in config.js")
    return pat.sub(lambda m: m.group(1) + json.dumps(value), text, 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--discord"); ap.add_argument("--email"); ap.add_argument("--issues"); ap.add_argument("--clear-discord", action="store_true")
    ap.add_argument("--check-online", action="store_true"); a = ap.parse_args(argv)
    text = CFG.read_text(encoding="utf-8")
    if a.discord:
        m = INVITE.match(a.discord.strip())
        if not m: sys.exit("not a Discord invite URL (expected https://discord.gg/CODE or https://discord.com/invite/CODE)")
        if a.check_online: check_online(m.group(1))
        text = set_key(text, "discordUrl", a.discord.strip())
    if a.clear_discord: text = set_key(text, "discordUrl", "")
    if a.email:
        if not EMAIL.match(a.email): sys.exit("invalid e-mail")
        text = set_key(text, "email", a.email)
    if a.issues:
        if not REPO.match(a.issues): sys.exit("--issues must be owner/repo")
        text = set_key(text, "issuesRepo", a.issues)
    CFG.write_text(text, encoding="utf-8"); print("config.js updated")


if __name__ == "__main__":
    main()

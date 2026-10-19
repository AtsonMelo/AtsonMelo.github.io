"""Creates the DevLab Discord layout from docs/discord/blueprint.json. Additive only.

  - Creates categories/channels that do not exist yet (matched by name, case-insensitive).
  - NEVER edits, renames, moves or deletes existing channels, never deletes messages, never touches roles.
  - Posts the welcome/portfolio/quote/support messages ONLY in channels it created in this run.
  - Creates one permanent, unlimited invite pointing at the welcome channel (reuses an identical one).
  - Dry-run by default. Nothing is sent to Discord without --yes.

Bot setup (the only manual part, ~3 min): https://discord.com/developers/applications -> New Application ->
Bot -> copy token -> OAuth2 URL with scope `bot` and ONLY these permissions: View Channels, Manage Channels,
Send Messages, Create Instant Invite (+ Manage Roles only if you use --apply-permissions). NOT Administrator.
The token is read from the DISCORD_BOT_TOKEN environment variable, never from arguments, never printed or stored.

  $env:DISCORD_BOT_TOKEN = '...'          # PowerShell, current session only
  python tools/discord_apply.py --guild <server id>                 # dry-run: shows the plan
  python tools/discord_apply.py --guild <server id> --yes           # apply
  python tools/discord_apply.py --guild <server id> --yes --apply-permissions   # also set read-only / private-thread access
Server id: Discord -> User Settings -> Advanced -> Developer Mode, then right-click the server -> Copy Server ID."""
import argparse, json, os, pathlib, re, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BP_DIR = ROOT / "docs" / "discord"
API = os.environ.get("DISCORD_API_BASE", "https://discord.com/api/v10")  # override only for tests
PERMS = {  # Discord permission bit flags
    "VIEW_CHANNEL": 1 << 10, "SEND_MESSAGES": 1 << 11, "ADD_REACTIONS": 1 << 6, "READ_MESSAGE_HISTORY": 1 << 16,
    "MENTION_EVERYONE": 1 << 17, "CREATE_PUBLIC_THREADS": 1 << 35, "CREATE_PRIVATE_THREADS": 1 << 36, "SEND_MESSAGES_IN_THREADS": 1 << 38,
}


class Discord:
    def __init__(self, token): self.token = token

    def call(self, method, path, body=None):
        for attempt in range(5):
            req = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                         headers={"Authorization": f"Bot {self.token}", "Content-Type": "application/json", "User-Agent": "DiscordBot (devlab-apply, 1.0)"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read() or b"null")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(min(float(json.loads(e.read() or b"{}").get("retry_after", 1)), 30)); continue
                detail = e.read().decode(errors="replace")[:300]
                sys.exit(f"Discord API {method} {path} -> HTTP {e.code}: {detail}")  # never includes the token
        sys.exit(f"Discord API {method} {path}: rate-limited too often")


def overwrite(profile, everyone_id):
    allow = sum(PERMS[p] for p in profile["everyone_allow"]); deny = sum(PERMS[p] for p in profile["everyone_deny"])
    return [{"id": everyone_id, "type": 0, "allow": str(allow), "deny": str(deny)}]


def chunks(text, limit=1900):
    out, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > limit and cur: out.append(cur.rstrip()); cur = ""
        cur += para + "\n\n"
    if cur.strip(): out.append(cur.rstrip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guild", required=True); ap.add_argument("--yes", action="store_true"); ap.add_argument("--apply-permissions", action="store_true")
    a = ap.parse_args()
    if not re.fullmatch(r"\d{15,25}", a.guild): sys.exit("--guild must be the numeric server id")
    bp = json.loads((BP_DIR / "blueprint.json").read_text(encoding="utf-8"))
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not a.yes:
        print("DRY-RUN (nothing is sent). Plan:")
        for c in bp["categories"]:
            print(f"  category {c['name']}")
            for ch in c["channels"]: print(f"    #{ch['name']}  [{ch['access']}]  message: {ch['message']}")
        print(f"  invite: permanent, unlimited, to #{bp['welcome_channel']}\n  permissions: {'will be applied' if a.apply_permissions else 'NOT applied (set by hand, see docs/discord/SETUP.md)'}\nRe-run with --yes (and DISCORD_BOT_TOKEN set) to apply.")
        return
    if not token: sys.exit("Set DISCORD_BOT_TOKEN in the environment first.")
    d = Discord(token); gid = a.guild
    existing = d.call("GET", f"/guilds/{gid}/channels")
    find = lambda name, typ: next((c for c in existing if c["name"].lower() == name.lower() and c["type"] == typ), None)
    created, ids = [], {}
    for cat in bp["categories"]:
        cobj = find(cat["name"], 4) or d.call("POST", f"/guilds/{gid}/channels", {"name": cat["name"], "type": 4}); existing.append(cobj)
        print(("exists   " if cobj in existing[:-1] else "created  ") + f"category {cat['name']}")
        for ch in cat["channels"]:
            cur = find(ch["name"], 0)
            if cur: ids[ch["name"]] = cur["id"]; print(f"exists   #{ch['name']}  (left untouched)"); continue
            body = {"name": ch["name"], "type": 0, "topic": ch["topic"], "parent_id": cobj["id"]}
            if a.apply_permissions: body["permission_overwrites"] = overwrite(bp["access_profiles"][ch["access"]], gid)
            new = d.call("POST", f"/guilds/{gid}/channels", body); existing.append(new)
            ids[ch["name"]] = new["id"]; created.append(ch); print(f"created  #{ch['name']}")
    for ch in created:  # messages only where we just created an empty channel; <#name> -> real channel mention
        text = (BP_DIR / ch["message"]).read_text(encoding="utf-8")
        text = re.sub(r"<#([a-z0-9-]+)>", lambda m: f"<#{ids[m.group(1)]}>" if m.group(1) in ids else m.group(0), text)
        for part in chunks(text): d.call("POST", f"/channels/{ids[ch['name']]}/messages", {"content": part}); time.sleep(1)
        print(f"posted   message in #{ch['name']}")
    wid = ids.get(bp["welcome_channel"])
    if wid:
        inv = d.call("POST", f"/channels/{wid}/invites", {"max_age": 0, "max_uses": 0, "temporary": False, "unique": False})
        print(f"\nINVITE https://discord.gg/{inv['code']}\nNext: python tools/set-contact.py --discord https://discord.gg/{inv['code']} --check-online")


if __name__ == "__main__":
    main()

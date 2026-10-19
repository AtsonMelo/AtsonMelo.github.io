"""Offline tests for tools/discord_apply.py (fake Discord API) and tools/set-contact.py.
Run: python tests/test_tools.py"""
import importlib.util, json, os, pathlib, re, subprocess, sys, tempfile, threading, http.server

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = bad = 0
def check(name, cond, extra=""):
    global ok, bad
    if cond: ok += 1
    else: bad += 1; print("FAIL:", name, extra)

GUILD = "123456789012345678"
BOTROLE = "888888888888888888"
SECRET = "TEST-TOKEN-NOT-REAL-123"
EVERYONE = (1 << 0) | (1 << 6) | (1 << 10) | (1 << 11) | (1 << 16) | (1 << 17) | (1 << 35) | (1 << 36) | (1 << 38)
BOT = (1 << 4) | (1 << 28)
VIEW, SEND, ADMIN = 1 << 10, 1 << 11, 1 << 3

def seed():
    roles = [
        {"id": GUILD, "name": "@everyone", "permissions": str(EVERYONE), "managed": False},
        {"id": BOTROLE, "name": "DevLab Automation", "permissions": str(BOT), "managed": True},
    ]
    return {
        "channels": [
            {"id": "1", "name": "Canais de Texto", "type": 4, "position": 0, "permission_overwrites": []},
            {"id": "2", "name": "Canais de Voz", "type": 4, "position": 0, "permission_overwrites": []},
            {"id": "3", "name": "geral", "type": 0, "parent_id": "1", "position": 0, "permission_overwrites": []},
            {"id": "4", "name": "estrada-smart", "type": 0, "parent_id": "1", "position": 1, "permission_overwrites": []},
            {"id": "5", "name": "github-updates", "type": 0, "parent_id": "1", "position": 2, "permission_overwrites": []},
            {"id": "6", "name": "Geral", "type": 2, "parent_id": "2", "position": 0, "permission_overwrites": []},
        ],
        "roles": roles,
        "guild": {"id": GUILD, "name": "DevLab", "verification_level": 0, "approximate_member_count": 2, "features": [], "roles": roles},
        "log": [], "next": 1000, "throttled": False, "messages": {}, "invites": [], "allow_guild": False,
    }

state = seed()
backup = tempfile.mkdtemp(prefix="devlab-discord-")
class Fake(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        raw = b"" if code == 204 else json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(raw))); self.end_headers()
        if raw: self.wfile.write(raw)
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        path = self.path.split("?")[0]
        state["log"].append(("GET", path, None, self.headers.get("Authorization")))
        if path.endswith("/channels"): return self._send(200, state["channels"])
        if path.endswith("/roles"): return self._send(200, state["roles"])
        if path.endswith("/threads/active"): return self._send(200, {"threads": []})
        if path.endswith("/users/@me/guilds"): return self._send(200, [{"id": GUILD, "name": "DevLab", "permissions": str(EVERYONE | BOT)}])
        if path.endswith("/users/@me"): return self._send(200, {"id": "42", "username": "DevLab Automation", "bot": True})
        if "/messages" in path and "/channels/" in path:
            cid = path.split("/channels/")[1].split("/")[0]
            return self._send(200, state["messages"].get(cid, [])[:1])
        if path.endswith("/invites"):
            if not state.get("allow_guild"): return self._send(403, {"message": "Missing Permissions"})
            return self._send(200, state.get("invites") or [])
        if path.endswith("/guilds/" + GUILD): return self._send(200, state["guild"])
        self._send(404, {"message": "not found"})
    def do_POST(self):
        body = self._body(); path = self.path.split("?")[0]
        state["log"].append(("POST", path, body, self.headers.get("Authorization")))
        if "/messages" in path and not state["throttled"]:
            state["throttled"] = True; return self._send(429, {"retry_after": 0.01})
        if path.endswith("/channels"):
            state["next"] += 1
            ch = {"id": str(state["next"]), "name": body["name"], "type": body["type"], "parent_id": body.get("parent_id"),
                  "topic": body.get("topic") or "", "permission_overwrites": body.get("permission_overwrites") or [], "position": 0}
            state["channels"].append(ch); return self._send(201, ch)
        if path.endswith("/invites"): return self._send(200, {"code": "AbCd123"})
        if "/messages" in path and "/channels/" in path:
            cid = path.split("/channels/")[1].split("/")[0]
            state["messages"].setdefault(cid, []).append({"id": "m" + str(len(state["messages"].get(cid, []))), "content": body.get("content", "")})
            return self._send(200, {"id": "m"})
        self._send(200, {"id": "m"})
    def do_PATCH(self):
        body = self._body(); path = self.path.split("?")[0]
        state["log"].append(("PATCH", path, body, self.headers.get("Authorization")))
        if "/roles/" in path:
            rid = path.rstrip("/").split("/")[-1]
            for role in state["roles"]:
                if role["id"] == rid:
                    if "permissions" in body: role["permissions"] = str(body["permissions"])
                    return self._send(200, role)
            return self._send(404, {})
        if path.rstrip("/") == "/guilds/" + GUILD:
            if not state.get("allow_guild"): return self._send(403, {"message": "Missing Permissions"})
            state["guild"].update(body); return self._send(200, state["guild"])
        cid = path.rstrip("/").split("/")[-1]
        for ch in state["channels"]:
            if ch["id"] == cid:
                ch.update(body); return self._send(200, ch)
        self._send(404, {})
    def do_DELETE(self):
        path = self.path.split("?")[0]; cid = path.rstrip("/").split("/")[-1]
        state["log"].append(("DELETE", path, None, self.headers.get("Authorization")))
        if "/channels/" in path:
            state["channels"] = [c for c in state["channels"] if c["id"] != cid]
        self._send(204, {})
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=srv.serve_forever, daemon=True).start()
env = {**os.environ, "DISCORD_API_BASE": f"http://127.0.0.1:{srv.server_address[1]}", "DISCORD_BOT_TOKEN": SECRET,
       "DISCORD_BACKUP_DIR": backup, "DISCORD_LOG_DIR": backup, "PYTHONIOENCODING": "utf-8", "LOCALAPPDATA": backup}
run = lambda *args, e=env: subprocess.run([sys.executable, str(ROOT / "tools" / "discord_apply.py"), *args], capture_output=True, text=True, env=e, encoding="utf-8")
methods = lambda: [item[0] for item in state["log"]]

r = run("--guild", GUILD, e={k: v for k, v in env.items() if k != "DISCORD_BOT_TOKEN"})
check("dry-run without token is refused and calls nothing", r.returncode != 0 and not state["log"], r.stdout + r.stderr)
check("bad guild id rejected", run("--guild", "abc").returncode != 0)
check("--yes alone is refused", run("--guild", GUILD, "--yes").returncode != 0 and "POST" not in methods())
state["log"].clear()
r = run("--guild", GUILD)
out = r.stdout + r.stderr
check("live dry-run is GET-only", r.returncode == 0 and out.count("DRY-RUN") == 1 and set(methods()) == {"GET"}, out)
check("dry-run sees the real names and blocks the invite", "INVITE BLOCKED" in out and "PRIVACY FAIL #github-updates" in out and "CREATE #boas-vindas" in out and "REUSE #geral" in out and "BLOCK-MOVE #estrada-smart" in out and "KEEP #Geral" in out, out)
check("dry-run is idempotent", run("--guild", GUILD).stdout == r.stdout)
check("verify fails while internal channels are public", run("--guild", GUILD, "--verify").returncode == 1)
state["log"].clear()
r = run("--discover")
check("discover lists the guild and does not mutate", r.returncode == 0 and "GUILD DevLab" in r.stdout and set(methods()) == {"GET"}, r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--create-missing")
check("create without permissions is refused before any POST", r.returncode != 0 and "refusing to create" in (r.stdout + r.stderr) and "POST" not in methods(), r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--create-invite")
check("invite refused while internal channels are visible", r.returncode != 0 and "INVITE BLOCKED" in (r.stdout + r.stderr) and not [item for item in state["log"] if item[1].endswith("/invites")], r.stdout + r.stderr)

state["log"].clear()
before = len(state["channels"])
r = run("--guild", GUILD, "--yes", "--create-missing", "--apply-permissions", "--post-messages")
out = r.stdout + r.stderr
names = [c["name"] for c in state["channels"]]
check("apply exits 0", r.returncode == 0, out)
check("creates the commercial channels once", all(names.count(n) == 1 for n in ("boas-vindas", "portfolio", "novidades", "solicitar-orcamento", "suporte", "dev-interno", "DEVLAB | INÍCIO", "DEVLAB | COMERCIAL", "DEVLAB | EQUIPE — PRIVADO")), str(names))
check("existing channels were not duplicated", names.count("geral") == 1 and names.count("github-updates") == 1 and names.count("estrada-smart") == 1 and len(state["channels"]) == before + 9, str(len(state["channels"])))
check("create does not PATCH or DELETE", not [item for item in state["log"] if item[0] in ("PATCH", "DELETE")])
check("token never printed", SECRET not in out and SECRET not in pathlib.Path(backup).read_text(encoding="utf-8", errors="replace") if False else SECRET not in out)
check("backup and log contain no token", SECRET not in "\n".join(p.read_text(encoding="utf-8") for p in pathlib.Path(backup).glob("*")))
check("all calls authenticated as Bot", all(item[3] == f"Bot {SECRET}" for item in state["log"] if item[3] is not None))
posts = [item for item in state["log"] if item[0] == "POST" and "/messages" in item[1]]
by_id = {c["id"]: c["name"] for c in state["channels"]}
posted_in = {by_id[item[1].split("/")[2]] for item in posts}
check("messages only in channels created on this run", posted_in == {"boas-vindas", "portfolio", "novidades", "solicitar-orcamento", "suporte", "dev-interno"}, str(posted_in))
check("every message under 2000 chars and mentions resolved", all(len(item[2]["content"]) <= 2000 and not re.search(r"<#[a-z-]+>", item[2]["content"]) for item in posts))
created_posts = [item[2] for item in state["log"] if item[0] == "POST" and item[1].endswith("/channels")]
text_posts = [body for body in created_posts if body["type"] == 0]
check("new text channels are born with everyone and bot overwrites, never Administrator",
      text_posts and all(len(body["permission_overwrites"]) == 2 and int(body["permission_overwrites"][0]["allow"]) & ADMIN == 0 and int(body["permission_overwrites"][0]["deny"]) & ADMIN == 0 for body in text_posts))
staff = next(body for body in text_posts if body["name"] == "dev-interno")
check("staff channel denies @everyone view at creation", int(staff["permission_overwrites"][0]["deny"]) & VIEW and staff["permission_overwrites"][0]["id"] == GUILD)
check("bot keeps view on the staff channel", int(staff["permission_overwrites"][1]["allow"]) & VIEW and staff["permission_overwrites"][1]["id"] == BOTROLE)
welcome = next(body for body in text_posts if body["name"] == "boas-vindas")
check("welcome channel is readable but not writable by @everyone", int(welcome["permission_overwrites"][0]["allow"]) & VIEW and int(welcome["permission_overwrites"][0]["deny"]) & SEND and int(welcome["permission_overwrites"][0]["deny"]) & (1 << 38))
check("same-run post does not read history first", not [item for item in state["log"] if item[0] == "GET" and "/messages" in item[1]])
MENTION, INVITE = 1 << 17, 1 << 0
public_text = [body for body in text_posts if body["name"] != "dev-interno"]
check("public channels deny @everyone mentions and invites", public_text and all(int(body["permission_overwrites"][0]["deny"]) & MENTION and int(body["permission_overwrites"][0]["deny"]) & INVITE for body in public_text))
quote = next(body for body in text_posts if body["name"] == "solicitar-orcamento")
check("quote channel allows private threads only", int(quote["permission_overwrites"][0]["allow"]) & (1 << 36) and int(quote["permission_overwrites"][0]["deny"]) & (1 << 35) and int(quote["permission_overwrites"][0]["deny"]) & SEND)
state["log"].clear()
again = len(state["channels"])
r2 = run("--guild", GUILD, "--yes", "--create-missing", "--apply-permissions")
check("second create is idempotent", r2.returncode == 0 and len(state["channels"]) == again and "POST" not in methods(), r2.stdout + r2.stderr)

state["log"].clear()
r = run("--guild", GUILD, "--yes", "--lock-internal")
locked = [item for item in state["log"] if item[0] == "PATCH"]
check("lock only changes the existing internal channels", r.returncode == 0 and {by_id[item[1].rstrip("/").split("/")[-1]] for item in locked} == {"github-updates", "estrada-smart"}, r.stdout + r.stderr)
check("lock denies view and keeps the bot", locked and all(int(item[2]["permission_overwrites"][0]["deny"]) & VIEW and int(item[2]["permission_overwrites"][1]["allow"]) & VIEW for item in locked))
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--lock-internal")
check("second lock writes nothing", r.returncode == 0 and "PATCH" not in methods() and "LOCK-UNCHANGED #github-updates" in r.stdout, r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--verify")
check("verify passes after the internal lock", r.returncode == 0 and "INVITE ALLOWED" in r.stdout, r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--create-invite")
inv = [item for item in state["log"] if item[0] == "POST" and item[1].endswith("/invites")]
check("one permanent unlimited invite after the lock", r.returncode == 0 and len(inv) == 1 and inv[0][2]["max_age"] == 0 and inv[0][2]["max_uses"] == 0 and "https://discord.gg/AbCd123" in r.stdout, r.stdout + r.stderr)

runs = sorted(pathlib.Path(backup).glob("*-run.json"), key=lambda p: p.stat().st_mtime)
lock_manifest = next(p for p in runs if json.loads(p.read_text(encoding="utf-8"))["locked_channel_ids"])
create_manifest = next(p for p in runs if json.loads(p.read_text(encoding="utf-8"))["created_channels"])
state["log"].clear()
r = run("--rollback", str(lock_manifest))
check("rollback dry-run restores locks without writing", r.returncode == 0 and "ROLLBACK-RESTORE #github-updates" in r.stdout and "PATCH" not in methods(), r.stdout + r.stderr)
state["log"].clear()
r = run("--rollback", str(lock_manifest), "--yes")
check("rollback restores the previous overwrites", r.returncode == 0 and "DELETE" not in methods() and any(item[0] == "PATCH" and item[2]["permission_overwrites"] == [] for item in state["log"]), r.stdout + r.stderr)
check("internal channel still exists after lock rollback", any(c["name"] == "github-updates" for c in state["channels"]))
state["log"].clear()
r = run("--rollback", str(create_manifest), "--yes")
left = {c["name"] for c in state["channels"]}
check("rollback deletes only channels created by the tool", r.returncode == 0 and left == {"Canais de Texto", "Canais de Voz", "geral", "estrada-smart", "github-updates", "Geral"}, r.stdout + " " + str(sorted(left)))
bad_manifest = pathlib.Path(backup) / "bad-run.json"
pre = json.loads(create_manifest.read_text(encoding="utf-8"))["preimage"]
bad_manifest.write_text(json.dumps({"guild_id": GUILD, "preimage": pre, "created_channels": [{"id": "3", "name": "geral", "type": 0}], "invite_codes": [], "locked_channel_ids": []}), encoding="utf-8")
state["log"].clear()
r = run("--rollback", str(bad_manifest), "--yes")
check("rollback refuses a manifest that targets a pre-existing channel", r.returncode != 0 and "DELETE" not in methods() and any(c["id"] == "3" for c in state["channels"]), r.stdout + r.stderr)

state["log"].clear()
r = run("--guild", GUILD, "--yes", "--tighten-public")
channel_patches = [item for item in state["log"] if item[0] == "PATCH" and "/channels/" in item[1]]
role_patches = [item for item in state["log"] if item[0] == "PATCH" and "/roles/" in item[1]]
patched = {next(c["name"] for c in state["channels"] if c["id"] == item[1].rstrip("/").split("/")[-1]) for item in channel_patches}
check("tighten only the legacy public containers", r.returncode == 0 and patched == {"geral", "Geral", "Canais de Texto", "Canais de Voz"}, r.stdout + r.stderr + str(patched))
check("tighten denies mention and invite without hiding the channel", channel_patches and all(
    int(item[2]["permission_overwrites"][0]["deny"]) & MENTION and int(item[2]["permission_overwrites"][0]["deny"]) & INVITE and not (int(item[2]["permission_overwrites"][0]["deny"]) & VIEW)
    and int(item[2]["permission_overwrites"][1]["allow"]) & VIEW for item in channel_patches))
everyone_role = next(role for role in state["roles"] if role["id"] == GUILD)
check("everyone role lost mention and invite but can still talk", role_patches and not (int(everyone_role["permissions"]) & MENTION) and not (int(everyone_role["permissions"]) & INVITE) and int(everyone_role["permissions"]) & SEND)
tighten_manifest = re.search(r"BACKUP (\S+?-run\.json)", r.stdout).group(1)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--tighten-public")
check("second tighten writes nothing", r.returncode == 0 and "PATCH" not in methods() and "ROLE-UNCHANGED @everyone" in r.stdout, r.stdout + r.stderr)
state["log"].clear()
r = run("--rollback", tighten_manifest, "--yes")
everyone_role = next(role for role in state["roles"] if role["id"] == GUILD)
geral = next(c for c in state["channels"] if c["name"] == "geral")
check("tighten rollback restores the role and the legacy overwrites", r.returncode == 0 and int(everyone_role["permissions"]) == EVERYONE and geral["permission_overwrites"] == [], r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--create-missing", "--apply-permissions")
check("channels can be recreated after rollback", r.returncode == 0 and any(c["name"] == "boas-vindas" for c in state["channels"]), r.stdout + r.stderr)
welcome_live = next(c for c in state["channels"] if c["name"] == "boas-vindas")
welcome_live["permission_overwrites"][0]["deny"] = str(int(welcome_live["permission_overwrites"][0]["deny"]) & ~(1 << 38))
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--tighten-public")
retightened = [item for item in state["log"] if item[0] == "PATCH" and "/channels/" in item[1]]
retightened_names = {next(c["name"] for c in state["channels"] if c["id"] == item[1].rstrip("/").split("/")[-1]) for item in retightened}
check("tighten refreshes a read-only channel that lost the thread deny", "boas-vindas" in retightened_names and "dev-interno" not in retightened_names and "github-updates" not in retightened_names, str(retightened_names))
welcome_live = next(c for c in state["channels"] if c["name"] == "boas-vindas")
check("read-only thread deny is restored", int(welcome_live["permission_overwrites"][0]["deny"]) & (1 << 38))
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--post-messages")
posts = [item for item in state["log"] if item[0] == "POST" and "/messages" in item[1]]
by_id = {c["id"]: c["name"] for c in state["channels"]}
posted_in = {by_id[item[1].split("/")[2]] for item in posts}
check("post-only fills every empty blueprint channel", r.returncode == 0 and posted_in == {"boas-vindas", "portfolio", "novidades", "solicitar-orcamento", "suporte", "dev-interno"}, r.stdout + str(posted_in))
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--post-messages")
check("second post skips channels that already have a message", r.returncode == 0 and "POST-SKIP #boas-vindas" in r.stdout and "POST-SKIP #dev-interno" in r.stdout and not [item for item in state["log"] if item[0] == "POST" and "/messages" in item[1]], r.stdout + r.stderr)
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--review-guild")
check("review guild reports the missing Manage Guild permission", r.returncode == 0 and "GUILD-SKIP verification" in r.stdout and "GUILD-SKIP invites" in r.stdout and state["guild"]["verification_level"] == 0, r.stdout + r.stderr)
state["allow_guild"] = True
state["guild"]["verification_level"] = 0
state["invites"] = [{"code": "OldInvite1", "channel": {"id": "3"}, "max_age": 0, "max_uses": 0, "uses": 1}]
state["log"].clear()
r = run("--guild", GUILD, "--yes", "--review-guild")
check("review guild raises verification and revokes a listed invite without printing the code", r.returncode == 0 and state["guild"]["verification_level"] == 1 and "INVITES listed=1 revoked=1" in r.stdout and "OldInvite1" not in r.stdout and any(item[0] == "DELETE" and item[1].endswith("/invites/OldInvite1") for item in state["log"]), r.stdout + r.stderr)
state["allow_guild"] = False

# ---------- set-contact ----------
spec = importlib.util.spec_from_file_location("sc", ROOT / "tools" / "set-contact.py"); sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
with tempfile.TemporaryDirectory() as t:
    sc.CFG = pathlib.Path(t) / "config.js"; sc.CFG.write_text((ROOT / "assets" / "js" / "config.js").read_text(encoding="utf-8"), encoding="utf-8")
    def tryrun(*args):
        try: sc.main(list(args)); return True
        except SystemExit as e: return e.code in (0, None)
    check("rejects non-invite URL", not tryrun("--discord", "https://evil.example/invite/abc"))
    check("rejects javascript: URL", not tryrun("--discord", "javascript:alert(1)"))
    check("rejects invalid e-mail", not tryrun("--email", "not-an-email"))
    check("accepts valid invite", tryrun("--discord", "https://discord.gg/AbCd123") and '"https://discord.gg/AbCd123"' in sc.CFG.read_text(encoding="utf-8"))
    check("accepts valid e-mail + issues repo", tryrun("--email", "contact@example.test", "--issues", "o/r") and "contact@example.test" in sc.CFG.read_text(encoding="utf-8"))
    check("clear-discord resets", tryrun("--clear-discord") and 'discordUrl: ""' in sc.CFG.read_text(encoding="utf-8"))
    check("config.js stays valid JS (node parses it)", subprocess.run(["node", "-e", f"global.window={{}};require({json.dumps(str(sc.CFG))});if(!window.SITE_CONFIG)process.exit(1)"]).returncode == 0)
print(f"TOOLS: {ok} passed, {bad} failed"); sys.exit(1 if bad else 0)

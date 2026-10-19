"""Offline tests for tools/discord_apply.py (against a fake Discord API) and tools/set-contact.py.
Run: python tests/test_tools.py"""
import importlib.util, json, os, pathlib, re, subprocess, sys, tempfile, threading, http.server

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = bad = 0
def check(name, cond, extra=""):
    global ok, bad
    if cond: ok += 1
    else: bad += 1; print("FAIL:", name, extra)

# ---------- fake Discord ----------
SECRET = "TEST-TOKEN-NOT-REAL-123"
state = {"channels": [{"id": "900", "name": "geral", "type": 0}, {"id": "901", "name": "ATENDIMENTO", "type": 4}, {"id": "902", "name": "suporte", "type": 0}], "log": [], "next": 1000, "throttled": False}
class Fake(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    def _body(self): return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
    def do_GET(self):
        state["log"].append(("GET", self.path, None, self.headers.get("Authorization")))
        self._send(200, state["channels"] if self.path.endswith("/channels") else {})
    def do_POST(self):
        body = self._body(); state["log"].append(("POST", self.path, body, self.headers.get("Authorization")))
        if "/messages" in self.path and not state["throttled"]:
            state["throttled"] = True; return self._send(429, {"retry_after": 0.01})
        if self.path.endswith("/channels"):
            state["next"] += 1; ch = {"id": str(state["next"]), **{k: body[k] for k in ("name", "type") if k in body}, "parent_id": body.get("parent_id")}
            state["channels"].append(ch); return self._send(201, ch)
        if self.path.endswith("/invites"): return self._send(200, {"code": "AbCd123"})
        self._send(200, {"id": "m"})
    def do_PATCH(self): state["log"].append(("PATCH", self.path, None, None)); self._send(200, {})
    def do_DELETE(self): state["log"].append(("DELETE", self.path, None, None)); self._send(204, {})
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake); threading.Thread(target=srv.serve_forever, daemon=True).start()
env = {**os.environ, "DISCORD_API_BASE": f"http://127.0.0.1:{srv.server_address[1]}", "DISCORD_BOT_TOKEN": SECRET}
run = lambda *args, e=env: subprocess.run([sys.executable, str(ROOT / "tools" / "discord_apply.py"), *args], capture_output=True, text=True, env=e, encoding="utf-8")

# dry-run: no request, no token needed
r = run("--guild", "123456789012345678", e={k: v for k, v in env.items() if k != "DISCORD_BOT_TOKEN"})
check("dry-run succeeds without a token and calls nothing", r.returncode == 0 and "DRY-RUN" in r.stdout and not state["log"], r.stdout + r.stderr)
check("bad guild id rejected", run("--guild", "abc").returncode != 0)
check("--yes without token refused", run("--guild", "123456789012345678", "--yes", e={k: v for k, v in env.items() if k != "DISCORD_BOT_TOKEN"}).returncode != 0)

# apply
r = run("--guild", "123456789012345678", "--yes", "--apply-permissions")
out = r.stdout + r.stderr
check("apply exits 0", r.returncode == 0, out)
names = [c["name"] for c in state["channels"]]
check("creates missing channels", all(n in names for n in ("boas-vindas", "portfolio", "solicitar-orcamento", "DEVLAB")), str(names))
check("existing channel not recreated (#suporte, ATENDIMENTO)", names.count("suporte") == 1 and names.count("ATENDIMENTO") == 1)
check("never PATCH/DELETE", not [l for l in state["log"] if l[0] in ("PATCH", "DELETE")])
check("token never printed", SECRET not in out)
check("all calls authenticated as Bot", all(l[3] == f"Bot {SECRET}" for l in state["log"] if l[3] is not None))
posts = [l for l in state["log"] if l[0] == "POST" and "/messages" in l[1]]
by_id = {c["id"]: c["name"] for c in state["channels"]}
posted_in = {by_id[l[1].split("/")[2]] for l in posts}
check("messages only in newly created channels (not #suporte)", posted_in == {"boas-vindas", "portfolio", "solicitar-orcamento"}, str(posted_in))
check("every message under 2000 chars", all(len(l[2]["content"]) <= 2000 for l in posts))
check("<#name> mentions resolved to ids", all(not re.search(r"<#[a-z-]+>", l[2]["content"]) for l in posts))
inv = [l for l in state["log"] if l[1].endswith("/invites")]
check("one permanent unlimited invite", len(inv) == 1 and inv[0][2]["max_age"] == 0 and inv[0][2]["max_uses"] == 0 and "https://discord.gg/AbCd123" in out)
ov = [l[2] for l in state["log"] if l[0] == "POST" and l[1].endswith("/channels") and l[2].get("type") == 0 and "permission_overwrites" in l[2]]
check("permission overwrites only for @everyone and never ADMINISTRATOR", ov and all(len(o["permission_overwrites"]) == 1 and int(o["permission_overwrites"][0]["allow"]) & (1 << 3) == 0 for o in ov))
# second run: idempotent
before = len(state["channels"]); r2 = run("--guild", "123456789012345678", "--yes")
check("second run creates nothing new", r2.returncode == 0 and len(state["channels"]) == before, r2.stdout + r2.stderr)

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

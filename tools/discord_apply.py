"""DevLab Discord layout. Reads docs/discord/blueprint.json. Dry-run by default.

The bot token is read from DISCORD_BOT_TOKEN. It is never printed, logged, or written.
Load it with tools/discord.ps1, which uses the Windows-protected file and clears the
environment afterwards. Do not pass the token as an argument.

  python tools/discord_apply.py --discover
  python tools/discord_apply.py --guild <id>                         # dry-run against the live server
  python tools/discord_apply.py --guild <id> --verify                 # exit 1 when a public invite would be unsafe
  python tools/discord_apply.py --guild <id> --yes --create-missing --apply-permissions
  python tools/discord_apply.py --guild <id> --yes --lock-internal
  python tools/discord_apply.py --guild <id> --yes --post-messages
  python tools/discord_apply.py --guild <id> --yes --create-invite
  python tools/discord_apply.py --rollback <manifest.json>            # plan
  python tools/discord_apply.py --rollback <manifest.json> --yes      # delete only channels this tool created

Nothing is renamed, moved, or deleted on a normal apply. Existing channels are reused.
Staff channels are not created unless --apply-permissions is set, so they are never born public.
A public invite is refused while an internal channel is still visible to @everyone.
"""
import argparse, datetime, json, os, pathlib, re, sys, time, urllib.error, urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
BP_DIR = ROOT / "docs" / "discord"
API = os.environ.get("DISCORD_API_BASE", "https://discord.com/api/v10")
PERMS = {
    "CREATE_INSTANT_INVITE": 1 << 0, "KICK_MEMBERS": 1 << 1, "BAN_MEMBERS": 1 << 2,
    "ADMINISTRATOR": 1 << 3, "MANAGE_CHANNELS": 1 << 4, "MANAGE_GUILD": 1 << 5,
    "ADD_REACTIONS": 1 << 6, "VIEW_AUDIT_LOG": 1 << 7, "VIEW_CHANNEL": 1 << 10,
    "SEND_MESSAGES": 1 << 11, "MANAGE_MESSAGES": 1 << 13, "EMBED_LINKS": 1 << 14,
    "ATTACH_FILES": 1 << 15, "READ_MESSAGE_HISTORY": 1 << 16, "MENTION_EVERYONE": 1 << 17,
    "CONNECT": 1 << 20, "SPEAK": 1 << 21, "MUTE_MEMBERS": 1 << 22, "MOVE_MEMBERS": 1 << 24,
    "MANAGE_ROLES": 1 << 28, "MANAGE_WEBHOOKS": 1 << 29, "MANAGE_THREADS": 1 << 34,
    "CREATE_PUBLIC_THREADS": 1 << 35, "CREATE_PRIVATE_THREADS": 1 << 36,
    "SEND_MESSAGES_IN_THREADS": 1 << 38, "MODERATE_MEMBERS": 1 << 40,
}
TYPE_NAME = {0: "text", 2: "voice", 4: "category", 5: "announcement", 15: "forum"}


class ApiError(SystemExit):
    pass


def scrub(text, token):
    if not text:
        return ""
    if token:
        text = text.replace(token, "[redacted]")
    return re.sub(r"(?i)(authorization:\s*bot\s+)\S+", r"\1[redacted]", text)


def log_line(token, message):
    line = scrub(message, token)
    print(line)
    directory = os.environ.get("DISCORD_LOG_DIR", "")
    if not directory:
        base = os.environ.get("LOCALAPPDATA")
        if base:
            directory = str(pathlib.Path(base) / "DevLab" / "logs")
    if not directory:
        return
    path = pathlib.Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    with (path / "discord-apply.log").open("a", encoding="utf-8") as fh:
        fh.write(datetime.datetime.now(datetime.timezone.utc).isoformat() + " " + line + "\n")


class Discord:
    def __init__(self, token):
        self.token = token

    def call(self, method, path, body=None, ok=(200, 201, 204)):
        data = None if body is None else json.dumps(body).encode()
        for _ in range(5):
            req = urllib.request.Request(
                API + path, method=method, data=data,
                headers={"Authorization": f"Bot {self.token}", "Content-Type": "application/json",
                         "User-Agent": "DiscordBot (devlab-apply, 1.0)"})
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    raw = response.read()
                    if response.status not in ok:
                        raise ApiError(f"Discord API {method} {path} -> HTTP {response.status}")
                    return json.loads(raw or b"null")
            except urllib.error.HTTPError as error:
                detail = scrub(error.read().decode(errors="replace")[:300], self.token)
                if error.code == 429:
                    time.sleep(min(float(json.loads(detail or "{}").get("retry_after", 1) if detail.startswith("{") else 1), 30))
                    continue
                raise ApiError(f"Discord API {method} {path} -> HTTP {error.code}: {detail}") from None
        raise ApiError(f"Discord API {method} {path}: rate-limited too often")


def bit_sum(names):
    return sum(PERMS[name] for name in names)


def perm_names(value):
    value = int(value or 0)
    return [name for name, bit in PERMS.items() if value & bit]


def find(channels, name, typ):
    hits = [channel for channel in channels if channel["name"].lower() == name.lower() and channel["type"] == typ]
    if len(hits) > 1:
        raise ApiError(f"ambiguous channel #{name} type {typ}: {len(hits)} matches; refusing to guess")
    return hits[0] if hits else None


def everyone_bits(roles, guild_id):
    role = next((item for item in roles if item["id"] == guild_id), None)
    if not role:
        raise ApiError("@everyone role missing from the guild payload")
    return int(role["permissions"])


def bot_role(roles):
    managed = [role for role in roles if role.get("managed") and role["name"] != "@everyone"]
    if len(managed) != 1:
        raise ApiError(f"expected one managed bot role, found {len(managed)}")
    return managed[0]


def bot_bits(roles, guild_id):
    base = everyone_bits(roles, guild_id)
    base |= int(bot_role(roles)["permissions"])
    return base


def channel_everyone_bits(channel, roles, guild_id):
    value = everyone_bits(roles, guild_id)
    overwrite = next((item for item in channel.get("permission_overwrites") or []
                      if item.get("type") == 0 and item.get("id") == guild_id), None)
    if overwrite:
        value = (value & ~int(overwrite.get("deny") or 0)) | int(overwrite.get("allow") or 0)
    if value & PERMS["ADMINISTRATOR"]:
        return (1 << 50) - 1
    return value


def can(channel, roles, guild_id, name):
    return bool(channel_everyone_bits(channel, roles, guild_id) & PERMS[name])


def build_overwrites(guild_id, role_id, profile, held_bits):
    allow = bit_sum(profile["everyone_allow"])
    deny = bit_sum(profile["everyone_deny"])
    bot_allow = bit_sum(profile["bot_allow"])
    missing = [name for name, bit in PERMS.items() if (allow | deny | bot_allow) & bit and not (held_bits & bit or held_bits & PERMS["ADMINISTRATOR"])]
    if missing:
        raise ApiError("bot cannot set permission bits it does not hold: " + ", ".join(missing))
    if profile["everyone_deny"] and "VIEW_CHANNEL" in profile["everyone_deny"] and not (bot_allow & PERMS["VIEW_CHANNEL"]):
        raise ApiError("refusing overwrite that would hide the channel from the bot")
    return [
        {"id": guild_id, "type": 0, "allow": str(allow), "deny": str(deny)},
        {"id": role_id, "type": 0, "allow": str(bot_allow), "deny": "0"},
    ]


def same_overwrites(current, wanted):
    def norm(rows):
        return sorted((row["id"], row["type"], int(row.get("allow") or 0), int(row.get("deny") or 0)) for row in rows)
    return norm(current or []) == norm(wanted)


def chunks(text, limit=1900):
    out, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > limit and cur:
            out.append(cur.rstrip()); cur = ""
        cur += para + "\n\n"
    if cur.strip():
        out.append(cur.rstrip())
    return out


def load_blueprint():
    return json.loads((BP_DIR / "blueprint.json").read_text(encoding="utf-8"))


def iter_channels(blueprint):
    for category in blueprint["categories"]:
        for channel in category["channels"]:
            yield category, channel


def internal_names(blueprint):
    return {channel["name"] for _, channel in iter_channels(blueprint) if channel["access"] == "staff_only"}


def fetch(discord, guild_id):
    guild = discord.call("GET", f"/guilds/{guild_id}?with_counts=true")
    channels = discord.call("GET", f"/guilds/{guild_id}/channels")
    roles = guild.get("roles") or discord.call("GET", f"/guilds/{guild_id}/roles")
    threads = discord.call("GET", f"/guilds/{guild_id}/threads/active")
    return {"guild": guild, "channels": channels, "roles": roles, "threads": threads.get("threads", []) if isinstance(threads, dict) else []}


def backup_dir():
    override = os.environ.get("DISCORD_BACKUP_DIR", "")
    if override:
        path = pathlib.Path(override)
    else:
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise ApiError("LOCALAPPDATA is not set; cannot write a backup outside the repo")
        path = pathlib.Path(base) / "DevLab" / "discord-backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot(state):
    guild = state["guild"]
    return {
        "taken_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "guild_id": guild["id"],
        "guild_name": guild.get("name"),
        "verification_level": guild.get("verification_level"),
        "features": guild.get("features") or [],
        "roles": [{"id": role["id"], "name": role["name"], "permissions": str(role["permissions"]), "managed": bool(role.get("managed"))} for role in state["roles"]],
        "channels": [{
            "id": channel["id"], "name": channel["name"], "type": channel["type"],
            "parent_id": channel.get("parent_id"), "topic": channel.get("topic") or "",
            "permission_overwrites": channel.get("permission_overwrites") or [],
        } for channel in state["channels"]],
    }


def privacy(state, blueprint):
    guild_id = state["guild"]["id"]
    failures, warnings = [], []
    by_id = {channel["id"]: channel for channel in state["channels"]}
    for channel in state["channels"]:
        if channel["type"] not in (0, 5):
            continue
        if channel["name"] not in internal_names(blueprint):
            continue
        parent = by_id.get(channel.get("parent_id") or "")
        if can(channel, state["roles"], guild_id, "VIEW_CHANNEL"):
            failures.append(f"#{channel['name']} is visible to @everyone (parent: {parent['name'] if parent else 'none'})")
    level = state["guild"].get("verification_level")
    if level == 0:
        warnings.append("verification level is None; a new member can talk immediately")
    everyone = everyone_bits(state["roles"], guild_id)
    if everyone & PERMS["CREATE_INSTANT_INVITE"]:
        warnings.append("@everyone can create invites")
    if everyone & PERMS["MENTION_EVERYONE"]:
        warnings.append("@everyone can mention @everyone")
    if everyone & PERMS["ADMINISTRATOR"]:
        failures.append("@everyone has Administrator")
    held = bot_bits(state["roles"], guild_id)
    if held & PERMS["ADMINISTRATOR"]:
        failures.append("the bot has Administrator")
    if not (held & PERMS["MANAGE_THREADS"]):
        warnings.append("the bot lacks MANAGE_THREADS; only the owner can see private threads the bot did not create")
    if not (held & PERMS["MANAGE_GUILD"]):
        warnings.append("the bot lacks MANAGE_GUILD; it cannot change verification level or list every invite")
    return failures, warnings


def render(state, blueprint, token):
    guild = state["guild"]
    guild_id = guild["id"]
    by_id = {channel["id"]: channel for channel in state["channels"]}
    log_line(token, f"DRY-RUN guild {guild.get('name')} ({guild_id}) verification={guild.get('verification_level')} members~{guild.get('approximate_member_count')}")
    role = bot_role(state["roles"])
    held = bot_bits(state["roles"], guild_id)
    log_line(token, f"BOT role {role['name']} administrator={'yes' if held & PERMS['ADMINISTRATOR'] else 'no'}")
    log_line(token, "INVENTORY")
    for channel in sorted(state["channels"], key=lambda item: (item.get("parent_id") or "", item.get("position") or 0, item["name"])):
        parent = by_id.get(channel.get("parent_id") or "")
        kind = TYPE_NAME.get(channel["type"], str(channel["type"]))
        extra = ""
        if channel["type"] == 0:
            extra = f" everyone_view={'yes' if can(channel, state['roles'], guild_id, 'VIEW_CHANNEL') else 'no'} everyone_send={'yes' if can(channel, state['roles'], guild_id, 'SEND_MESSAGES') else 'no'}"
        log_line(token, f"  {kind} #{channel['name']} parent={parent['name'] if parent else '-'}{extra}")
    if state["threads"]:
        log_line(token, f"THREADS active={len(state['threads'])}")
    else:
        log_line(token, "THREADS active=0")
    log_line(token, "PLAN")
    known = {(channel["name"].lower(), channel["type"]) for channel in state["channels"]}
    for category in blueprint["categories"]:
        exists = ("category", True) if (category["name"].lower(), 4) in known else ("category", False)
        log_line(token, ("REUSE category " if exists[1] else "CREATE category ") + category["name"])
        for channel in category["channels"]:
            present = (channel["name"].lower(), 0) in known
            if channel["action"] == "reuse":
                marker = "REUSE" if present else "MISSING"
                log_line(token, f"  {marker} #{channel['name']} stay-put access={channel['access']}")
                if present and channel.get("move_to"):
                    current = find(state["channels"], channel["name"], 0)
                    parent = by_id.get(current.get("parent_id") or "") if current else None
                    log_line(token, f"  BLOCK-MOVE #{channel['name']} from {parent['name'] if parent else '-'} to {channel['move_to']} (approval required; not applied)")
            elif present:
                log_line(token, f"  REUSE #{channel['name']} already exists; left untouched")
            else:
                log_line(token, f"  CREATE #{channel['name']} in {category['name']} [{channel['access']}]")
    for item in blueprint.get("preserve", []):
        present = find(state["channels"], item["name"], item["type"])
        log_line(token, ("KEEP #" if present else "KEEP-MISSING #") + item["name"])
    failures, warnings = privacy(state, blueprint)
    for item in failures:
        log_line(token, "PRIVACY FAIL " + item)
    for item in warnings:
        log_line(token, "PRIVACY WARN " + item)
    if not failures and not warnings:
        log_line(token, "PRIVACY ok")
    log_line(token, "INVITE BLOCKED" if failures else "INVITE ALLOWED")
    log_line(token, "NO MUTATIONS")
    return failures


def require_token():
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        raise ApiError("DISCORD_BOT_TOKEN is not set. Use tools/discord.ps1 so the protected file is loaded only for this run.")
    return token


def create_missing(discord, state, blueprint, token, apply_permissions, manifest, manifest_path):
    guild_id = state["guild"]["id"]
    held = bot_bits(state["roles"], guild_id)
    role_id = bot_role(state["roles"])["id"]
    channels = state["channels"]
    pending = []
    for category in blueprint["categories"]:
        if find(channels, category["name"], 4) is None and category.get("private") and not apply_permissions:
            raise ApiError(f"refusing to create private category {category['name']} without --apply-permissions")
        for channel in category["channels"]:
            if channel["action"] != "create" or find(channels, channel["name"], 0):
                continue
            profile = blueprint["access_profiles"][channel["access"]]
            if profile is None:
                raise ApiError(f"#{channel['name']} has no access profile")
            if not apply_permissions:
                raise ApiError(f"refusing to create #{channel['name']} without --apply-permissions; it would be born with @everyone defaults")
            pending.append(build_overwrites(guild_id, role_id, profile, held))
    if not pending and all(find(channels, category["name"], 4) for category in blueprint["categories"]):
        log_line(token, "CREATE nothing missing")
    for category in blueprint["categories"]:
        current = find(channels, category["name"], 4)
        if current is None:
            body = {"name": category["name"], "type": 4}
            if category.get("private"):
                body["permission_overwrites"] = build_overwrites(guild_id, role_id, blueprint["access_profiles"]["staff_only"], held)
            current = discord.call("POST", f"/guilds/{guild_id}/channels", body)
            channels.append(current)
            manifest["created_channels"].append({"id": current["id"], "name": current["name"], "type": 4})
            remember(manifest_path, manifest)
            log_line(token, f"CREATED category {category['name']} {current['id']}")
        for channel in category["channels"]:
            if channel["action"] != "create":
                continue
            existing = find(channels, channel["name"], 0)
            if existing:
                log_line(token, f"REUSE #{channel['name']} {existing['id']}")
                continue
            profile = blueprint["access_profiles"][channel["access"]]
            body = {"name": channel["name"], "type": 0, "topic": channel.get("topic", ""), "parent_id": current["id"],
                    "permission_overwrites": build_overwrites(guild_id, role_id, profile, held)}
            made = discord.call("POST", f"/guilds/{guild_id}/channels", body)
            channels.append(made)
            manifest["created_channels"].append({"id": made["id"], "name": made["name"], "type": 0})
            remember(manifest_path, manifest)
            log_line(token, f"CREATED #{channel['name']} {made['id']}")
    return manifest["created_channels"]


def post_messages(discord, state, blueprint, token, created_ids):
    ids = {channel["name"]: channel["id"] for channel in state["channels"] if channel["type"] == 0}
    posted = []
    for _, channel in iter_channels(blueprint):
        if channel["name"] not in created_ids or not channel.get("message"):
            continue
        text = (BP_DIR / channel["message"]).read_text(encoding="utf-8")
        text = re.sub(r"<#([a-z0-9-]+)>", lambda match: f"<#{ids[match.group(1)]}>" if match.group(1) in ids else match.group(0), text)
        for part in chunks(text):
            discord.call("POST", f"/channels/{ids[channel['name']]}/messages", {"content": part})
            time.sleep(0.3)
        posted.append(channel["name"])
        log_line(token, f"POST #{channel['name']}")
    return posted


def lock_targets(state, blueprint):
    targets = []
    for name in [category["name"] for category in blueprint["categories"] if category.get("private")]:
        found = find(state["channels"], name, 4)
        if found:
            targets.append(found)
    for name in sorted(internal_names(blueprint)):
        found = find(state["channels"], name, 0)
        if found:
            targets.append(found)
    return targets


def lock_internal(discord, state, blueprint, token, manifest, manifest_path):
    guild_id = state["guild"]["id"]
    held = bot_bits(state["roles"], guild_id)
    role_id = bot_role(state["roles"])["id"]
    wanted = build_overwrites(guild_id, role_id, blueprint["access_profiles"]["staff_only"], held)
    targets = lock_targets(state, blueprint)
    for name in sorted(internal_names(blueprint)):
        if not find(state["channels"], name, 0):
            log_line(token, f"LOCK-SKIP #{name} does not exist yet")
    for channel in targets:
        foreign = [row for row in channel.get("permission_overwrites") or [] if row["id"] not in {guild_id, role_id}]
        if foreign:
            raise ApiError(f"refusing to replace foreign overwrites on #{channel['name']}")
    for channel in targets:
        if same_overwrites(channel.get("permission_overwrites"), wanted):
            log_line(token, f"LOCK-UNCHANGED #{channel['name']}")
            continue
        updated = discord.call("PATCH", f"/channels/{channel['id']}", {"permission_overwrites": wanted})
        channel["permission_overwrites"] = updated.get("permission_overwrites", wanted)
        if channel["id"] not in manifest["locked_channel_ids"]:
            manifest["locked_channel_ids"].append(channel["id"])
            remember(manifest_path, manifest)
        log_line(token, f"LOCK #{channel['name']} {channel['id']}")
    return manifest["locked_channel_ids"]


def create_invite(discord, state, blueprint, token):
    failures, _ = privacy(state, blueprint)
    if failures:
        raise ApiError("INVITE BLOCKED\n" + "\n".join(failures))
    welcome = find(state["channels"], blueprint["welcome_channel"], 0)
    if not welcome:
        raise ApiError(f"#{blueprint['welcome_channel']} does not exist; invite not created")
    invite = discord.call("POST", f"/channels/{welcome['id']}/invites", {"max_age": 0, "max_uses": 0, "temporary": False, "unique": False})
    log_line(token, f"INVITE https://discord.gg/{invite['code']}")
    return invite["code"]


def start_manifest(preimage):
    directory = backup_dir()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    pre_path = directory / f"{stamp}-{preimage['guild_id']}-pre.json"
    man_path = directory / f"{stamp}-{preimage['guild_id']}-run.json"
    write_json(pre_path, preimage)
    manifest = {"guild_id": preimage["guild_id"], "preimage": str(pre_path), "created_channels": [], "invite_codes": [], "locked_channel_ids": []}
    write_json(man_path, manifest)
    return man_path, manifest


def remember(path, manifest):
    write_json(path, manifest)


def rollback(discord, manifest_path, token, apply):
    manifest = json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    preimage = json.loads(pathlib.Path(manifest["preimage"]).read_text(encoding="utf-8"))
    pre_ids = {channel["id"] for channel in preimage["channels"]}
    state = fetch(discord, manifest["guild_id"])
    live = {channel["id"]: channel for channel in state["channels"]}
    victims = []
    for channel in manifest.get("created_channels") or []:
        if channel["id"] in pre_ids:
            raise ApiError(f"manifest lists a pre-existing channel {channel['id']}; refusing")
        current = live.get(channel["id"])
        if not current:
            log_line(token, f"ROLLBACK-GONE #{channel['name']} {channel['id']}")
            continue
        if current["name"].lower() != channel["name"].lower() or current["type"] != channel["type"]:
            raise ApiError(f"channel {channel['id']} no longer matches the manifest; refusing")
        victims.append(current)
    for channel in sorted(victims, key=lambda item: item["type"] == 4):
        log_line(token, f"ROLLBACK-DELETE #{channel['name']} {channel['id']}")
        if apply:
            discord.call("DELETE", f"/channels/{channel['id']}")
    pre_by_id = {channel["id"]: channel for channel in preimage["channels"]}
    for channel_id in manifest.get("locked_channel_ids") or []:
        old = pre_by_id.get(channel_id)
        if not old or channel_id not in live:
            log_line(token, f"ROLLBACK-LOCK-SKIP {channel_id}")
            continue
        log_line(token, f"ROLLBACK-RESTORE #{live[channel_id]['name']} {channel_id}")
        if apply:
            discord.call("PATCH", f"/channels/{channel_id}", {"permission_overwrites": old.get("permission_overwrites") or []})
    for code in manifest.get("invite_codes") or []:
        log_line(token, f"ROLLBACK-INVITE {code}")
        if apply:
            discord.call("DELETE", f"/invites/{code}")
    if not apply:
        log_line(token, "ROLLBACK dry-run; re-run with --yes to delete only the ids above")


def discover(discord, token):
    guilds = discord.call("GET", "/users/@me/guilds")
    me = discord.call("GET", "/users/@me")
    log_line(token, f"BOT {me.get('username')} id={me.get('id')} bot={me.get('bot')}")
    for guild in guilds:
        bits = int(guild.get("permissions") or 0)
        log_line(token, f"GUILD {guild.get('name')} id={guild['id']} administrator={'yes' if bits & PERMS['ADMINISTRATOR'] else 'no'}")
    return guilds


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--guild")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--create-missing", action="store_true")
    parser.add_argument("--apply-permissions", action="store_true")
    parser.add_argument("--post-messages", action="store_true")
    parser.add_argument("--create-invite", action="store_true")
    parser.add_argument("--lock-internal", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rollback", default="")
    args = parser.parse_args(argv)
    mutations = [args.create_missing, args.post_messages, args.create_invite, args.lock_internal]
    if args.yes and not any(mutations) and not args.rollback:
        raise ApiError("--yes does nothing by itself. Pass --create-missing, --lock-internal, --post-messages, or --create-invite.")
    if any(mutations) and not args.yes:
        raise ApiError("mutation flags require --yes")
    if args.rollback and any(mutations):
        raise ApiError("--rollback cannot be combined with other mutations")
    token = require_token()
    discord = Discord(token)
    try:
        if args.discover:
            discover(discord, token)
            return 0
        if args.rollback:
            if not re.fullmatch(r".+", args.rollback):
                raise ApiError("--rollback needs a manifest path")
            rollback(discord, args.rollback, token, args.yes)
            return 0
        if not args.guild or not re.fullmatch(r"\d{15,25}", args.guild):
            raise ApiError("--guild must be the numeric server id (or use --discover)")
        blueprint = load_blueprint()
        state = fetch(discord, args.guild)
        if state["guild"]["id"] != args.guild:
            raise ApiError("guild id mismatch; refusing")
        if not args.yes:
            failures = render(state, blueprint, token)
            return 1 if args.verify and failures else 0
        man_path, manifest = start_manifest(snapshot(state))
        log_line(token, f"BACKUP {man_path}")
        if args.create_missing:
            create_missing(discord, state, blueprint, token, args.apply_permissions, manifest, man_path)
        if args.lock_internal:
            lock_internal(discord, state, blueprint, token, manifest, man_path)
        if args.post_messages:
            post_messages(discord, state, blueprint, token, {item["name"] for item in manifest["created_channels"] if item["type"] == 0})
        if args.create_invite:
            state = fetch(discord, args.guild)
            manifest["invite_codes"].append(create_invite(discord, state, blueprint, token))
            remember(man_path, manifest)
        return 0
    except ApiError as error:
        log_line(token, str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())

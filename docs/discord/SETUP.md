# DevLab Discord: commercial channel setup

State on 2026-10-19: no Discord integration, token, CLI or logged-in browser session was available to Claude Code, so **nothing was created on the server and no invite exists**. Everything below is ready to apply. Existing channels (`#geral`, `#estrada-smart`, `#github-updates`, voice Geral) are never touched.

## 0. Read this before sharing any invite (security)
A public invite lets anyone join and see every channel that `@everyone` can view.
1. **`#github-updates`**: if it receives events from the private `fivem-lab` repo (commits, PRs, branch names), it leaks private work to every invitee. Make it private (Channel settings → Permissions → `@everyone` → View Channel ✗) or confirm it only shows public repos.
2. **`#estrada-smart`** (another project) and **`#geral`**: decide if they should be visible to visitors. If not, same permission change.
3. Server Settings → **Safety Setup**: verification level at least *Low* (verified e-mail), and enable **Rules Screening** if the server is a Community server.
4. Do not give any role Administrator except the owner. Do not install bots you do not need.

## 1. Layout (blueprint: `blueprint.json`, texts: `messages/`)
| Category | Channel | @everyone can | Purpose |
|---|---|---|---|
| DEVLAB | `#boas-vindas` | read, react | welcome, rules, invite target |
| DEVLAB | `#portfolio` | read, react | projects with honest status |
| ATENDIMENTO | `#solicitar-orcamento` | read, **create private threads**, write in threads (not in the channel) | quote requests, one private thread per client |
| ATENDIMENTO | `#suporte` | read, write | public questions; secrets forbidden by the pinned text |

Private data rule: quotes and anything with server details go in a **private thread** (visible only to the requester, the owner and members with *Manage Threads*). No bot or ticket plugin is required.

## 2. Path A: by hand (about 10 minutes, no bot)
1. Create the categories **DEVLAB** and **ATENDIMENTO** and the four channels above (type: text), with the topics from `blueprint.json`.
2. Permissions per channel (Channel settings → Permissions → `@everyone`):
   - `#boas-vindas`, `#portfolio`: Send Messages ✗, Create Public/Private Threads ✗, Add Reactions ✓.
   - `#solicitar-orcamento`: Send Messages ✗, Create Public Threads ✗, **Create Private Threads ✓**, **Send Messages in Threads ✓**.
   - `#suporte`: Send Messages ✓, Mention @everyone ✗, Create Private Threads ✗.
3. Paste each file from `messages/` into its channel (they are written for Discord markdown, PT-BR then EN). In the posted text, replace the channel names with real mentions by typing `#`. Pin the message.
4. Invite: open `#boas-vindas` → **Invite people** → **Edit invite link** → *Expire after* **Never**, *Max number of uses* **No limit** → copy the link.

## 3. Path B: script (needs a bot, token never leaves your machine)
Only if you want the channels, texts and invite created for you.
1. https://discord.com/developers/applications → **New Application** → **Bot** → *Reset Token* → copy it.
2. OAuth2 → URL Generator: scope `bot`, permissions **View Channels, Manage Channels, Send Messages, Create Instant Invite** (add *Manage Roles* only if you want the script to set the permissions of step 2 as well). **Never Administrator.** Open the URL and add the bot to the DevLab server.
3. Discord → User Settings → Advanced → Developer Mode on; right-click the server → **Copy Server ID**.
4. In PowerShell, in this repo:
```
$env:DISCORD_BOT_TOKEN = '<token>'            # current session only; never commit it
python tools/discord_apply.py --guild <server id>                     # dry-run: shows the plan
python tools/discord_apply.py --guild <server id> --yes               # create channels, post texts, create invite
python tools/discord_apply.py --guild <server id> --yes --apply-permissions   # also set the access table above
```
The script only creates what is missing, never edits or deletes anything, posts messages only into channels it just created, and prints the permanent invite. Afterwards remove the bot from the server and reset its token (Developer Portal).

## 4. Put the invite on the site
```
python tools/set-contact.py --discord https://discord.gg/<code> --check-online
python tools/preflight.py
```
`--check-online` asks Discord's public endpoint whether the invite works, which server/channel it opens and rejects expiring invites. Once `discordUrl` is set, the site shows **Join Discord** in the hero and in the contact flow, and the quote flow says the brief was **not** sent automatically: the visitor copies it, joins, and pastes it in a private thread in `#solicitar-orcamento`.

## 5. Moderation basics
Keep Developer Mode off for visitors, enable *Block messages with links from new members* only if spam appears, review the audit log weekly, and delete any visitor message that contains secrets.

# DevLab Discord

Applied on 2026-10-19, bot `DevLab Automation` (not Administrator). `LockInternal`, `CreateChannels`, `TightenPublic`, and `PostMessages` ran. No channel was renamed, moved, or deleted. Verification level is **Low** (API `verification=1`). The public invite is `https://discord.gg/JPfR8ekkrj`. It does not expire, and the public invite endpoint opens `#boas-vindas` (`1561844477050626090`) on DevLab. Backups are under `%LOCALAPPDATA%\DevLab\discord-backups\`, not in this repo.

## What is there now

| Where | Channel | @everyone can view | Notes |
|---|---|---|---|
| Canais de Texto | `#geral` | yes, can send | Mentions and invites denied. The old bot message is still there. |
| Canais de Texto | `#estrada-smart` | no | Locked in place. Empty. |
| Canais de Texto | `#github-updates` | no | Locked in place. Empty. Do not attach a webhook until this stays denied. |
| DEVLAB \| INÍCIO | `#boas-vindas` `#portfolio` `#novidades` | yes, cannot send or write in threads | Prepared text posted once. |
| DEVLAB \| COMERCIAL | `#solicitar-orcamento` | yes, private threads only | Instructions posted. Owner confirmed account B could not see account A's thread. |
| DEVLAB \| COMERCIAL | `#suporte` | yes, can send | Mentions and invites denied. Guidance posted. |
| DEVLAB \| EQUIPE — PRIVADO | `#dev-interno` | no | Staff rules posted. Not visible to @everyone. |
| Canais de Voz | `Geral` | yes (connect/speak) | Mentions and invites denied. |

There is no staff role. The owner sees every channel because Discord does not apply overwrites to the owner. The bot role can view the locked channels and can still send the prepared text. `@everyone` no longer has Create Invite or Mention Everyone on the role. The same two bits are denied again on `#geral`, the voice channel, the public categories, and the presentation channels. A later channel created by hand can still be synced from its category, which now denies both bits.

## Target

New categories and channels are created only where something is missing. Existing channels stay put until a move is approved.

| Category | Channel | Action | @everyone after an approved apply |
|---|---|---|---|
| DEVLAB \| INÍCIO | `#boas-vindas` `#portfolio` `#novidades` | create | read, react, no send, no thread send |
| DEVLAB \| COMERCIAL | `#solicitar-orcamento` | create | read, create **private** threads, write in threads, no channel messages, no public threads |
| DEVLAB \| COMERCIAL | `#suporte` | create | read and write, no @everyone mention, no private threads |
| (stays) | `#geral` | reuse, then tighten | read and write, no mention, no invite |
| DEVLAB \| EQUIPE — PRIVADO | `#github-updates` `#estrada-smart` | reuse, then lock in place | view denied |
| DEVLAB \| EQUIPE — PRIVADO | `#dev-interno` | create already locked | view denied |
| Canais de Voz | `Geral` | keep, then tighten | connect and speak, no mention, no invite |

Denying view for `@everyone` also denies it for the bot unless the same request allows the bot role. The tool sends both overwrites together and refuses to hide a channel from itself. It will not replace overwrites that mention some other user or role.

## Quotes

Private threads are the flow. Discord's API creates a private thread **without** a public starter message (`Start Thread without Message`, type `GUILD_PRIVATE_THREAD`, text channels only). Visibility is the author, people who were added, and anyone with Manage Threads. The owner sees them. This server's `@everyone` already has Create Private Threads and Send Messages in Threads. No boost is required.

`#solicitar-orcamento` must deny Send Messages and Create Public Threads so a brief cannot be typed into the channel or into a public thread. The site only copies the brief; it does not send it.

Proven on 2026-10-19 by the owner: account A opened a private thread and account B could not see it. If a future client hides the private-thread control, the visitor posts only `quero um orçamento` in `#suporte` and the owner adds them to a private thread. A resident ticket bot is not justified while that fallback works.

A future teammate who is not the owner needs Manage Threads on that channel. The bot does not hold Manage Threads, so it cannot grant that bit. The owner sets it in the client, or grants the bit to the bot first.

## Commands

Token file: `%LOCALAPPDATA%\DevLab\Secrets\discord-bot-token.xml`. Do not print, copy, or commit it.

```
pwsh -File tools/discord.ps1                  # diagnose + diff, no writes
pwsh -File tools/discord.ps1 -Action verify   # exit 1 while an internal channel is public
```

These write to Discord only when `-Approve` names the scope:

```
pwsh -File tools/discord.ps1 -Action apply -Approve LockInternal
pwsh -File tools/discord.ps1 -Action apply -Approve CreateChannels
pwsh -File tools/discord.ps1 -Action apply -Approve TightenPublic
pwsh -File tools/discord.ps1 -Action apply -Approve ReviewGuild
pwsh -File tools/discord.ps1 -Action apply -Approve PostMessages
pwsh -File tools/discord.ps1 -Action apply -Approve CreateInvite
```

`LockInternal` denies `@everyone` view on the internal channels where they already are. `CreateChannels` creates only missing categories and channels and puts their overwrites on the create. `TightenPublic` denies mentions and invites on `#geral`, the voice channel, the public categories, and refreshes the read-only channels. It also removes those two bits from the `@everyone` role when the bot is allowed to. `ReviewGuild` tries to set verification to Low and to list invites; without Manage Guild it logs `GUILD-SKIP` and changes nothing. `PostMessages` posts each `messages/` file once: into channels created in that same run, or, when the run creates nothing, into an existing empty channel. A second run skips channels that already have a message. `CreateInvite` makes one permanent invite to `#boas-vindas` and refuses while any internal channel is visible. Do not run it until two ordinary accounts have proved a private thread.

Rollback: `docs/discord/ROLLBACK.md`.

## Site

The checked invite is in `assets/js/config.js` as `discordUrl`: `https://discord.gg/JPfR8ekkrj`.

```
python tools/set-contact.py --discord https://discord.gg/JPfR8ekkrj --check-online
python tools/preflight.py
```

`discordUrl` shows **Entrar no Discord** / **Join Discord** and the quote steps. The quote status must keep saying the brief was not sent. The invite change did not publish the site.

Published later on 2026-10-19: https://atsonmelo.github.io/ at `8c1e94d39af23ebdd589fa08d3612f99f54e67ea`. Public checks on that URL: 35/35. Quotes stay manual, in a private thread.

The bot's own institutional messages were edited in place on the post-launch pass. Same IDs, no second message. `#dev-interno` (`1561857831035080726`) was left as posted: it is private and did not say the site was unpublished. `#suporte` (`1561857825884340345`) was left as posted: its guidance was already the manual flow.

| Channel | Message |
|---|---|
| `#boas-vindas` | `1561857802903756932` |
| `#portfolio` | `1561857809245798490` |
| `#novidades` | `1561857814085894214` |
| `#solicitar-orcamento` | `1561857819827773480` |

## GitHub

Do not install a GitHub integration yet.

- Public facts (published demo, confirmed fix, public release) can later be posted by hand, or by a webhook, in `#novidades`.
- Private repositories, branches, commits, and internal issues belong in `#github-updates` only after `LockInternal`. The channel is empty today and must not receive a webhook before that.
- No extra GitHub app is required for that split. A webhook per channel is enough, and only after the permission check passes.

## Moderation

Before the invite is public, the owner sets Server Settings → Safety to at least **Low** (verified email). The bot cannot change this (no Manage Guild). Keep Administrator on the owner only. Review the audit log when a member joins. Delete any message that contains a secret. Do not accept or distribute pirated assets.

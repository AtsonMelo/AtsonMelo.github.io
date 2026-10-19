# DevLab Discord

Applied on 2026-10-19, bot `DevLab Automation` (not Administrator). `LockInternal` and `CreateChannels` ran. No channel was renamed or moved. No welcome text was posted. No invite was created. Verification level is still **None**. Backups are under `%LOCALAPPDATA%\DevLab\discord-backups\`, not in this repo.

## What is there now

| Where | Channel | @everyone can view | Notes |
|---|---|---|---|
| Canais de Texto | `#geral` | yes | Untouched. Still allows mentions and invites. |
| Canais de Texto | `#estrada-smart` | no | Locked in place. Empty. |
| Canais de Texto | `#github-updates` | no | Locked in place. Empty. Do not attach a webhook until this stays denied. |
| DEVLAB \| INÍCIO | `#boas-vindas` `#portfolio` `#novidades` | yes, cannot send | No messages yet. |
| DEVLAB \| COMERCIAL | `#solicitar-orcamento` | yes, private threads only | No messages yet. Test with a non-owner account before any public invite. |
| DEVLAB \| COMERCIAL | `#suporte` | yes, can send | Mentions and invites denied. No messages yet. |
| DEVLAB \| EQUIPE — PRIVADO | `#dev-interno` | no | Born private. No messages yet. |
| Canais de Voz | `Geral` | yes (connect/speak) | Untouched. |

There is no staff role. The owner sees every channel because Discord does not apply overwrites to the owner. The bot role is allowed to view the locked channels. `@everyone` still has Create Invite and Mention Everyone on the role itself; the new public channels deny both. `#geral` and the voice channel do not.

## Target

New categories and channels are created only where something is missing. Existing channels stay put until a move is approved.

| Category | Channel | Action | @everyone after an approved apply |
|---|---|---|---|
| DEVLAB \| INÍCIO | `#boas-vindas` `#portfolio` `#novidades` | create | read, react, no send |
| DEVLAB \| COMERCIAL | `#solicitar-orcamento` | create | read, create **private** threads, write in threads, no channel messages, no public threads |
| DEVLAB \| COMERCIAL | `#suporte` | create | read and write, no @everyone mention, no private threads |
| (stays) | `#geral` | reuse | unchanged until a separate approval |
| DEVLAB \| EQUIPE — PRIVADO | `#github-updates` `#estrada-smart` | reuse, then lock in place | view denied |
| DEVLAB \| EQUIPE — PRIVADO | `#dev-interno` | create already locked | view denied |
| Canais de Voz | `Geral` | keep | unchanged |

Denying view for `@everyone` also denies it for the bot unless the same request allows the bot role. The tool sends both overwrites together and refuses to hide a channel from itself. It will not replace overwrites that mention some other user or role.

## Quotes

Private threads are the flow. Discord's API creates a private thread **without** a public starter message (`Start Thread without Message`, type `GUILD_PRIVATE_THREAD`, text channels only). Visibility is the author, people who were added, and anyone with Manage Threads. The owner sees them. This server's `@everyone` already has Create Private Threads and Send Messages in Threads. No boost is required.

`#solicitar-orcamento` must deny Send Messages and Create Public Threads so a brief cannot be typed into the channel or into a public thread. The site only copies the brief; it does not send it.

Not proven yet: a non-owner Discord client may hide the private-thread control. The owner's client is not a valid test. After the channel exists, one second account has to open a private thread and another member must confirm they cannot see it. If the client refuses, the visitor posts only `quero um orçamento` in `#suporte` and the owner adds them to a private thread. A resident ticket bot is not justified while that fallback works.

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
pwsh -File tools/discord.ps1 -Action apply -Approve PostMessages
pwsh -File tools/discord.ps1 -Action apply -Approve CreateInvite
```

`LockInternal` is the privacy gate: it denies `@everyone` view on `#github-updates` and `#estrada-smart` where they already are. `CreateChannels` creates only missing categories and channels and puts their overwrites on the create, so a staff channel is never born public. `PostMessages` posts the files in `messages/` only into channels that same run created. `CreateInvite` makes one permanent, unlimited invite to `#boas-vindas` and refuses while any internal channel is still visible.

Do this in that order: lock, create, post, prove a private thread with a second account, then invite. Rollback: `docs/discord/ROLLBACK.md`.

## Site

After the invite exists and has been checked:

```
python tools/set-contact.py --discord https://discord.gg/<code> --check-online
python tools/preflight.py
```

`discordUrl` is what shows **Entrar no Discord** / **Join Discord** and the quote steps. Empty means those controls stay hidden. The quote status must keep saying the brief was not sent.

## GitHub

Do not install a GitHub integration yet.

- Public facts (published demo, confirmed fix, public release) can later be posted by hand, or by a webhook, in `#novidades`.
- Private repositories, branches, commits, and internal issues belong in `#github-updates` only after `LockInternal`. The channel is empty today and must not receive a webhook before that.
- No extra GitHub app is required for that split. A webhook per channel is enough, and only after the permission check passes.

## Moderation

Before the invite is public, the owner sets Server Settings → Safety to at least **Low** (verified email). The bot cannot change this (no Manage Guild). Keep Administrator on the owner only. Review the audit log when a member joins. Delete any message that contains a secret. Do not accept or distribute pirated assets.

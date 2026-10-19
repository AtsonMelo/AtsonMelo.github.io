# Rollback

`tools/discord_apply.py` writes two local files before it changes anything, under `%LOCALAPPDATA%\DevLab\discord-backups\` (never in this repository):

- `*-pre.json`: channels, roles, and overwrites as they were.
- `*-run.json`: ids created by that run, invite codes, and ids whose overwrites were locked.

The run file is updated as each channel is created, so a partial run can still be rolled back.

```
pwsh -File tools/discord.ps1 -Action rollback -RollbackManifest <path-to-run.json>
pwsh -File tools/discord.ps1 -Action rollback -RollbackManifest <path-to-run.json> -Approve Rollback
```

The first command only prints the plan. With `-Approve Rollback` the tool:

- deletes a channel only when its id is in `created_channels`, its name and type still match, and that id was not already in the preimage;
- restores overwrites of channels in `locked_channel_ids` from the preimage (locks and public tightening share this list);
- restores `@everyone` permissions when that run recorded `everyone_permissions_before`;
- deletes invite codes recorded in that run.

It does not delete `#geral`, `#estrada-smart`, `#github-updates`, the voice channel, or any channel it did not create. If a created channel was renamed, rollback stops instead of guessing.

## Text, docs, protection, and the site

These are separate from the channel rollback above. Do not unpublish Pages as the first step, and do not delete a channel to undo a sentence.

- Discord text: edit the same bot message back to `docs/discord/messages/` at `8c1e94d`. Do not post another message. `#dev-interno` was not changed in the launch text pass.
- Documentation: revert that commit through a pull request.
- `main` protection: `gh api -X DELETE repos/AtsonMelo/AtsonMelo.github.io/branches/main/protection`.
- Site: revert the content commit through a pull request so Pages rebuilds. Unpublish only to take the site offline.

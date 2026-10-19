# DevLab Discord operator. Dry-run unless -Approve names an explicit scope.
# The bot token stays in the Windows-protected file and is cleared when this process ends.
#   pwsh -File tools/discord.ps1
#   pwsh -File tools/discord.ps1 -Action verify
#   pwsh -File tools/discord.ps1 -Action apply -Approve CreateChannels
#   pwsh -File tools/discord.ps1 -Action apply -Approve LockInternal
#   pwsh -File tools/discord.ps1 -Action apply -Approve TightenPublic
#   pwsh -File tools/discord.ps1 -Action apply -Approve ReviewGuild
#   pwsh -File tools/discord.ps1 -Action apply -Approve PostMessages
#   pwsh -File tools/discord.ps1 -Action apply -Approve CreateInvite
#   pwsh -File tools/discord.ps1 -Action rollback -RollbackManifest <path> -Approve Rollback
[CmdletBinding()]
param(
    [ValidateSet('diagnose', 'diff', 'verify', 'apply', 'rollback')]
    [string]$Action = 'diagnose',
    [string]$Guild = '',
    [ValidateSet('CreateChannels', 'LockInternal', 'TightenPublic', 'ReviewGuild', 'PostMessages', 'CreateInvite', 'Rollback')]
    [string[]]$Approve = @(),
    [string]$RollbackManifest = ''
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$tool = Join-Path $repo 'tools\discord_apply.py'
if (-not (Test-Path -LiteralPath $tool)) { throw "discord_apply.py not found at $tool" }
$tokenPath = Join-Path $env:LOCALAPPDATA 'DevLab\Secrets\discord-bot-token.xml'
if (-not (Test-Path -LiteralPath $tokenPath)) { throw 'protected bot token not found' }
$guildFile = Join-Path $env:LOCALAPPDATA 'DevLab\discord-guild.id'
$allowed = @{
    diagnose = @()
    diff     = @()
    verify   = @()
    apply    = @('CreateChannels', 'LockInternal', 'TightenPublic', 'ReviewGuild', 'PostMessages', 'CreateInvite')
    rollback = @('Rollback')
}
foreach ($item in $Approve) {
    if ($allowed[$Action] -notcontains $item) { throw "-Approve $item is not valid for $Action" }
}
if ($Action -eq 'apply' -and -not $Approve) { throw 'apply requires -Approve with one or more of: CreateChannels, LockInternal, TightenPublic, ReviewGuild, PostMessages, CreateInvite' }
if ($Action -eq 'rollback' -and -not $RollbackManifest) { throw 'rollback requires -RollbackManifest' }

$script:BotExit = 1
function Invoke-Bot {
    param([Parameter(Mandatory = $true)][string[]]$PyArgs, [switch]$Capture)
    $sec = Import-Clixml -LiteralPath $tokenPath
    if ($sec -isnot [System.Security.SecureString]) { throw 'protected token has an unexpected type' }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    $previous = $env:PYTHONIOENCODING
    try {
        $env:DISCORD_BOT_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $env:PYTHONIOENCODING = 'utf-8'
        if ($Capture) {
            $script:BotOutput = (& python $tool @PyArgs 2>&1 | Out-String)
            Write-Host $script:BotOutput
        } else {
            & python $tool @PyArgs
        }
        $script:BotExit = $LASTEXITCODE
    } finally {
        Remove-Item Env:\DISCORD_BOT_TOKEN -ErrorAction SilentlyContinue
        if ($null -eq $previous) { Remove-Item Env:\PYTHONIOENCODING -ErrorAction SilentlyContinue } else { $env:PYTHONIOENCODING = $previous }
        if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
        Remove-Variable sec, bstr -ErrorAction SilentlyContinue
        [GC]::Collect()
    }
}

if (-not $Guild -and (Test-Path -LiteralPath $guildFile)) { $Guild = (Get-Content -LiteralPath $guildFile -Raw).Trim() }
if (-not $Guild -and $Action -ne 'rollback') {
    Invoke-Bot -PyArgs @('--discover') -Capture
    if ($script:BotExit -ne 0) { exit $script:BotExit }
    $ids = [regex]::Matches([string]$script:BotOutput, 'GUILD .+ id=(\d{15,25}) ')
    if ($ids.Count -ne 1) { throw "expected exactly one Discord server, found $($ids.Count); pass -Guild" }
    $Guild = $ids[0].Groups[1].Value
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $guildFile) | Out-Null
    Set-Content -LiteralPath $guildFile -Value $Guild -Encoding ascii -NoNewline
    Write-Host 'saved server id for later runs (local file only)'
}

$py = @()
switch ($Action) {
    'rollback' {
        $py = @('--rollback', $RollbackManifest)
        if ($Approve -contains 'Rollback') { $py += '--yes' }
    }
    'apply' {
        $py = @('--guild', $Guild, '--yes')
        if ($Approve -contains 'CreateChannels') { $py += @('--create-missing', '--apply-permissions') }
        if ($Approve -contains 'LockInternal') { $py += '--lock-internal' }
        if ($Approve -contains 'TightenPublic') { $py += '--tighten-public' }
        if ($Approve -contains 'ReviewGuild') { $py += '--review-guild' }
        if ($Approve -contains 'PostMessages') { $py += '--post-messages' }
        if ($Approve -contains 'CreateInvite') { $py += '--create-invite' }
    }
    'verify' { $py = @('--guild', $Guild, '--verify') }
    default { $py = @('--guild', $Guild) }
}
Invoke-Bot -PyArgs $py
exit $script:BotExit

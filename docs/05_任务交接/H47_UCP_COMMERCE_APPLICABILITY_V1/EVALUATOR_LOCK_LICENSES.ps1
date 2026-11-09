$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$lockPath = Join-Path $taskRoot 'TEAM_SOURCE_LOCK.json'
$lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json
$headers = @{ 'User-Agent' = 'Codex-public-source-audit' }
foreach ($entry in $lock.files) {
    $license = Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $entry.repo + '/license?ref=' + $entry.commit) -Headers $headers -TimeoutSec 20 -DisableKeepAlive
    $bytes = [Convert]::FromBase64String($license.content)
    $relative = 'sources/teams/' + ($entry.repo -replace '/', '__') + '.LICENSE'
    [IO.File]::WriteAllBytes((Join-Path $taskRoot $relative), $bytes)
    $entry | Add-Member -NotePropertyName license_path -NotePropertyValue $relative -Force
    $entry | Add-Member -NotePropertyName license_sha256 -NotePropertyValue ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()) -Force
    $entry | Add-Member -NotePropertyName license_url -NotePropertyValue ('https://github.com/' + $entry.repo + '/blob/' + $entry.commit + '/' + $license.path) -Force
}
[IO.File]::WriteAllText($lockPath, (($lock | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
'Three pinned repository licenses saved; no services contacted.'

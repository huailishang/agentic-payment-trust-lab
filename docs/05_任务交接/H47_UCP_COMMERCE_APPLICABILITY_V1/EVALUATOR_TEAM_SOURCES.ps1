$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$repoNames = @('filtalgo/Filtmall-Shopping-Skill', 'tiny-agent-company/agent-card-skill', 'Henry-Social/skills')
$headers = @{ 'User-Agent' = 'Codex-public-source-audit' }
$entries = @()
foreach ($repoName in $repoNames) {
    $metadata = Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $repoName) -Headers $headers -TimeoutSec 20 -DisableKeepAlive
    $commit = Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $repoName + '/commits/' + $metadata.default_branch) -Headers $headers -TimeoutSec 20 -DisableKeepAlive
    $readme = Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $repoName + '/readme?ref=' + $commit.sha) -Headers $headers -TimeoutSec 20 -DisableKeepAlive
    $bytes = [Convert]::FromBase64String($readme.content)
    $name = ($repoName -replace '/', '__') + '.md'
    $folder = Join-Path $taskRoot 'sources/teams'
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $folder $name), $bytes)
    $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    $entries += @{ repo=$repoName; commit=$commit.sha; path=('sources/teams/' + $name); upstream_path=$readme.path; url=('https://github.com/' + $repoName + '/blob/' + $commit.sha + '/' + $readme.path); sha256=$sha; bytes=$bytes.Length; license_spdx=$metadata.license.spdx_id; evidence_level='PUBLIC_WORKFLOW_ONLY_NOT_CUSTOMER_DEMAND' }
}
$lock = @{ schema='h47-team-sources/v1'; retrieved_on='2026-10-15'; files=$entries }
[IO.File]::WriteAllText((Join-Path $taskRoot 'TEAM_SOURCE_LOCK.json'), (($lock | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
$entries | Select-Object repo,commit,bytes,license_spdx | ConvertTo-Json -Compress

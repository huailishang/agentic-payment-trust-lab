$task = 'docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1'
$submission = Get-Content -Raw -LiteralPath "$task/SUBMISSION.json" | ConvertFrom-Json -AsHashtable
if ((git rev-parse HEAD) -ne $submission.head) { throw 'HEAD mismatch' }
foreach ($name in $submission.files.Keys) {
    if ((Get-FileHash -LiteralPath $name).Hash.ToLowerInvariant() -ne $submission.files[$name]) { throw "Submission drift: $name" }
}
$gate = Get-Content -Raw -LiteralPath "$task/evidence/attempt-1/L2-GATE.json" | ConvertFrom-Json -AsHashtable
if ($gate.result -ne 'PASS' -or $gate.checks.Count -ne 6) { throw 'L2 not eligible' }
$outdir = "$task/evidence/evaluator"
if (Test-Path -LiteralPath $outdir) { throw 'Evaluator evidence already exists' }
New-Item -ItemType Directory -Path $outdir -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath CURRENT.md -Destination "$outdir/CURRENT.pre_acceptance.md" -ErrorAction Stop
$files = [ordered]@{}
foreach ($name in ($submission.files.Keys | Sort-Object)) {
    if ($name -ne 'CURRENT.md') { $files[$name] = $submission.files[$name] }
}
$files["$task/SUBMISSION.json"] = (Get-FileHash -LiteralPath "$task/SUBMISSION.json").Hash.ToLowerInvariant()
$record = [ordered]@{classification = 'EVALUATOR_ACCEPTED_SUBMITTED_SNAPSHOT'; head = $submission.head; accepted_at_utc = [DateTimeOffset]::UtcNow.ToString('o'); pre_acceptance_router_sha256 = $submission.files['CURRENT.md']; map_sha256 = (Get-FileHash -LiteralPath docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md).Hash.ToLowerInvariant(); protected_files = 325; accepted_files = $files.Count; submission = $files; original_l2_checks = 6}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$outdir/ACCEPTANCE.json" -Encoding utf8NoBOM
$record.accepted_files

[CmdletBinding()]
param(
    [string]$CondaExe = "D:\SoftWare\Anaconda\install\Scripts\conda.exe",
    [string]$EnvironmentName = "webshop38",
    [string]$RepositoryRoot = "",
    [string]$SmokeOutput = "",
    [string]$MirrorEvidenceOutput = "",
    [string]$IndexEvidenceOutput = "",
    [switch]$AllowChecksumMirrorFallback
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
$WebShopRoot = Join-Path $RepositoryRoot "local_sources\third_party\webshop"
$VerifyScript = Join-Path $RepositoryRoot "scripts\validation\webshop\verify_webshop_small_assets.py"
$SmokeScript = Join-Path $RepositoryRoot "scripts\validation\webshop\smoke_webshop_small.py"
if ([string]::IsNullOrWhiteSpace($SmokeOutput)) {
    $SmokeOutput = Join-Path $RepositoryRoot "docs\05_任务交接\P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1\evidence\webshop_small_smoke.json"
}
if ([string]::IsNullOrWhiteSpace($MirrorEvidenceOutput)) {
    $MirrorEvidenceOutput = Join-Path $RepositoryRoot "docs\05_任务交接\P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1\evidence\webshop_small_mirror_assets.json"
}
if ([string]::IsNullOrWhiteSpace($IndexEvidenceOutput)) {
    $IndexEvidenceOutput = Join-Path $RepositoryRoot "docs\05_任务交接\P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1\evidence\webshop_small_index_query.json"
}

$ExpectedCommit = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
$CondaForge = "https://conda.anaconda.org/conda-forge"
$PyTorchChannel = "https://conda.anaconda.org/pytorch"

$CondaPackages = @(
    "beautifulsoup4=4.11.1",
    "cleantext=1.1.4",
    "cloudpickle=2.2.1",
    "faiss-cpu=1.7.4",
    "intel-openmp=2021.4.0",
    "mkl=2021.4.0",
    "flask=2.1.2",
    "werkzeug=2.1.2",
    "gdown=5.2.0",
    "numpy=1.23.5",
    "pandas=1.4.2",
    "pyyaml=6.0",
    "requests=2.27.1",
    "rich=12.4.4",
    "scikit-learn=1.1.1",
    "selenium=4.2.0",
    "spacy=3.3.0",
    "thefuzz=0.19.0",
    "pytorch=1.11.0",
    "cpuonly",
    "transformers=4.19.2",
    "tqdm=4.64.0",
    "pyjnius>=1.4,<1.5",
    "typing_extensions=4.1.1"
)

$LocalArtifacts = @(
    @{
        Name = "gym_notices-0.0.8-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/25/26/d786c6bec30fe6110fd3d22c9a273a2a0e56c0b73b93e25ea1af5a53243b/gym_notices-0.0.8-py3-none-any.whl"
        Sha256 = "e5f82e00823a166747b4c2a07de63b6560b1acb880638547e0cabf825a01e463"
    },
    @{
        Name = "gym-0.24.0.tar.gz"
        Uri = "https://files.pythonhosted.org/packages/34/e8/c8953e7fb2e3b3a232a21f87248b87fe9354b8db74e79ece99f53ce31a3d/gym-0.24.0.tar.gz"
        Sha256 = "69f96424be40d23088be978b61f45c23911e2ccddafad08cf2fac608e8bd86e4"
    },
    @{
        Name = "rank_bm25-0.2.2-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/2a/21/f691fb2613100a62b3fa91e9988c991e9ca5b89ea31c0d3152a3210344f9/rank_bm25-0.2.2-py3-none-any.whl"
        Sha256 = "7bd4a95571adadfc271746fa146a4bcfd89c0cf731e49c3d1ad863290adbe8ae"
    },
    @{
        Name = "pyserini-0.17.0-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/47/f2/95224a22c23485b7f75772c6b6f39573cdea94a8ec6e02bdf8dab6eb0e7f/pyserini-0.17.0-py3-none-any.whl"
        Sha256 = "95d8edc9720b9c2d237156b11d8596f1ff72044b1db465a7b9ee0d63f865b486"
    },
    @{
        Name = "en_core_web_sm-3.3.0-py3-none-any.whl"
        Uri = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.3.0/en_core_web_sm-3.3.0-py3-none-any.whl"
        Sha256 = "84d7d8059bfbf53c09b39139782f76cd6ac7064851e7799dcc685c06ebf5fd4f"
    },
    @{
        Name = "onnxruntime-1.12.1-cp38-cp38-win_amd64.whl"
        Uri = "https://files.pythonhosted.org/packages/36/84/276c11a89f3625415f4c16b87dcc46dbb6fea8fd6a28276a05d1f6f3fb6f/onnxruntime-1.12.1-cp38-cp38-win_amd64.whl"
        Sha256 = "f0104e0e8327c8468d646941540af9397b737155dffe078da4bf36da95d1c21e"
    },
    @{
        Name = "coloredlogs-15.0.1-py2.py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/a7/06/3d6badcf13db419e25b07041d9c7b4a2c331d3f4e7134445ec5df57714cd/coloredlogs-15.0.1-py2.py3-none-any.whl"
        Sha256 = "612ee75c546f53e92e70049c9dbfcc18c935a2b9a53b66085ce9ef6a6e5c0934"
    },
    @{
        Name = "humanfriendly-10.0-py2.py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/f0/0f/310fb31e39e2d734ccaa2c0fb981ee41f7bd5056ce9bc29b2248bd569169/humanfriendly-10.0-py2.py3-none-any.whl"
        Sha256 = "1697e1a8a8f550fd43c2865cd84542fc175a61dcb779b6fee18cf6b6ccba1477"
    },
    @{
        Name = "pyreadline3-3.4.1-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/56/fc/a3c13ded7b3057680c8ae95a9b6cc83e63657c38e0005c400a5d018a33a7/pyreadline3-3.4.1-py3-none-any.whl"
        Sha256 = "b0efb6516fd4fb07b45949053826a62fa4cb353db5be2bbb4a7aa1fdd1e345fb"
    },
    @{
        Name = "flatbuffers-2.0.7-py2.py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/d7/0d/b5bfb553a6ac66d6ec2b6d7f1e814a908fba7188356ac94bb36ae3d905c3/flatbuffers-2.0.7-py2.py3-none-any.whl"
        Sha256 = "71e135d533be527192819aaab757c5e3d109cb10fbb01e687f6bdb7a61ad39d1"
    },
    @{
        Name = "protobuf-3.20.3-cp38-cp38-win_amd64.whl"
        Uri = "https://files.pythonhosted.org/packages/32/f8/52f598bceb16fe365f4ef8e957ac8890aeb56abf97d365ff5abd8c1250cf/protobuf-3.20.3-cp38-cp38-win_amd64.whl"
        Sha256 = "447d43819997825d4e71bf5769d869b968ce96848b6479397e29fc24c4a5dfe9"
    },
    @{
        Name = "sympy-1.10.1-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/d0/04/66be21ceb305c66a4b326b0ae44cc4f027a43bc08cac204b48fb45bb3653/sympy-1.10.1-py3-none-any.whl"
        Sha256 = "df75d738930f6fe9ebe7034e59d56698f29e85f443f743e51e47df0caccc2130"
    },
    @{
        Name = "mpmath-1.2.1-py3-none-any.whl"
        Uri = "https://files.pythonhosted.org/packages/d4/cf/3965bddbb4f1a61c49aacae0e78fd1fe36b5dc36c797b31f30cf07dcbbb7/mpmath-1.2.1-py3-none-any.whl"
        Sha256 = "604bc21bd22d2322a177c73bdb573994ef76e62edd595d17e00aff24b0667e5c"
    }
)

$ApprovedMirror = @{
    Repository = "YWZBrandon/webshop-data"
    Revision = "ce990fff5aee388db2706f07820c578ab68e0453"
    BaseUrl = "https://huggingface.co/datasets/YWZBrandon/webshop-data/resolve/ce990fff5aee388db2706f07820c578ab68e0453/"
}
$ApprovedData = @(
    @{ Name = "items_shuffle_1000.json"; Id = "1EgHdxQ_YxqIQlvvq5iKlCrkEKR6-j0Ib"; Bytes = 4467013; Sha256 = "30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269" },
    @{ Name = "items_ins_v2_1000.json"; Id = "1IduG0xl544V_A_jv3tHXC0kyFi7PnyBu"; Bytes = 147099; Sha256 = "f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f" },
    @{ Name = "items_human_ins.json"; Id = "14Kb5SPBk_jfdLZ_CDBNitW98QLDlKR5O"; Bytes = 5137548; Sha256 = "cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3" }
)

function Invoke-CondaChecked {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & $CondaExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "conda command failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

function Assert-Sha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Expected
    )
    $Actual = (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected.ToLowerInvariant()) {
        throw "SHA-256 mismatch for $Path. Expected $Expected, actual $Actual"
    }
}

if (-not (Test-Path -LiteralPath $CondaExe -PathType Leaf)) {
    throw "Conda executable not found: $CondaExe"
}
if (-not (Test-Path -LiteralPath $WebShopRoot -PathType Container)) {
    throw "Pinned WebShop checkout not found: $WebShopRoot"
}

$EnvironmentInventory = (& $CondaExe env list --json | ConvertFrom-Json)
$EnvironmentPath = $EnvironmentInventory.envs | Where-Object {
    (Split-Path -Leaf $_) -eq $EnvironmentName
} | Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($EnvironmentPath)) {
    Invoke-CondaChecked @(
        "create", "-n", $EnvironmentName,
        "--override-channels", "-c", $CondaForge,
        "--strict-channel-priority",
        "python=3.8.13", "openjdk=11", "pip", "-y"
    )
    $EnvironmentInventory = (& $CondaExe env list --json | ConvertFrom-Json)
    $EnvironmentPath = $EnvironmentInventory.envs | Where-Object {
        (Split-Path -Leaf $_) -eq $EnvironmentName
    } | Select-Object -First 1
}

$PythonVersion = ((& $CondaExe run -n $EnvironmentName python --version 2>&1) -join "`n").Trim()
if ($LASTEXITCODE -ne 0 -or $PythonVersion -ne "Python 3.8.13") {
    throw "Existing $EnvironmentName is not the approved Python 3.8.13 environment: $PythonVersion"
}

Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", $VerifyScript,
    "--checkout", $WebShopRoot,
    "--expected-commit", $ExpectedCommit,
    "--checkout-only"
)

Invoke-CondaChecked (@(
    "install", "-n", $EnvironmentName,
    "--override-channels", "-c", $PyTorchChannel, "-c", $CondaForge,
    "--strict-channel-priority", "-y"
) + $CondaPackages)

$CacheDirectory = Join-Path $EnvironmentPath "webshop_bootstrap_cache"
New-Item -ItemType Directory -Force -Path $CacheDirectory | Out-Null
foreach ($Artifact in $LocalArtifacts) {
    $Destination = Join-Path $CacheDirectory $Artifact.Name
    if (-not (Test-Path -LiteralPath $Destination -PathType Leaf)) {
        Invoke-WebRequest -UseBasicParsing -Uri $Artifact.Uri -OutFile $Destination
    }
    Assert-Sha256 -Path $Destination -Expected $Artifact.Sha256
}

$ArtifactPaths = $LocalArtifacts | ForEach-Object { Join-Path $CacheDirectory $_.Name }
Invoke-CondaChecked (@(
    "run", "-n", $EnvironmentName,
    "python", "-m", "pip", "install",
    "--isolated", "--no-index", "--no-deps", "--no-build-isolation"
) + $ArtifactPaths)

Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", "-c",
    "import faiss, gym, numpy, onnxruntime, pyserini, spacy, torch, transformers, yaml; from pyserini.search.lucene import LuceneSearcher; nlp=spacy.load('en_core_web_sm'); assert gym.__version__=='0.24.0'; assert numpy.__version__=='1.23.5'; assert onnxruntime.__version__=='1.12.1'; assert spacy.__version__=='3.3.0'; assert torch.__version__.startswith('1.11.0'); assert transformers.__version__=='4.19.2'; assert yaml.__version__=='6.0'; assert nlp.meta['version']=='3.3.0'; assert LuceneSearcher.__name__=='LuceneSearcher'"
)

$DataDirectory = Join-Path $WebShopRoot "data"
New-Item -ItemType Directory -Force -Path $DataDirectory | Out-Null
$PresentData = @($ApprovedData | Where-Object {
    Test-Path -LiteralPath (Join-Path $DataDirectory $_.Name) -PathType Leaf
})
if ($PresentData.Count -ne 0 -and $PresentData.Count -ne $ApprovedData.Count) {
    throw "Partial WebShop small-data state detected; refusing to overwrite or repair in place"
}
if ($PresentData.Count -eq 0) {
    if (-not $AllowChecksumMirrorFallback.IsPresent) {
        throw "Google Drive permission failure is retained in EV-17. Mirror fallback requires -AllowChecksumMirrorFallback."
    }
    $StagingDirectory = Join-Path $EnvironmentPath ("webshop_small_staging_" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $StagingDirectory | Out-Null
    try {
        foreach ($DataFile in $ApprovedData) {
            $Destination = Join-Path $StagingDirectory $DataFile.Name
            $Uri = "$($ApprovedMirror.BaseUrl)$($DataFile.Name)"
            Write-Output "WEBSHOP_MIRROR_REPOSITORY=$($ApprovedMirror.Repository)"
            Write-Output "WEBSHOP_MIRROR_REVISION=$($ApprovedMirror.Revision)"
            Write-Output "WEBSHOP_MIRROR_URL=$Uri"
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 300 -Uri $Uri -OutFile $Destination
        }
        Invoke-CondaChecked @(
            "run", "-n", $EnvironmentName,
            "python", $VerifyScript,
            "--staging-dir", $StagingDirectory,
            "--destination-dir", $DataDirectory,
            "--mirror-repository", $ApprovedMirror.Repository,
            "--mirror-revision", $ApprovedMirror.Revision,
            "--allow-checksum-mirror-fallback",
            "--promote-staged-data",
            "--output", $MirrorEvidenceOutput
        )
    }
    finally {
        if (Test-Path -LiteralPath $StagingDirectory -PathType Container) {
            Remove-Item -LiteralPath $StagingDirectory -Recurse -Force
        }
    }
}
else {
    Write-Output "Existing WebShop small assets detected; validating exact approved fingerprints before reuse."
}

Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", $VerifyScript,
    "--checkout", $WebShopRoot,
    "--expected-commit", $ExpectedCommit,
    "--no-index"
)
Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", $VerifyScript,
    "--checkout", $WebShopRoot,
    "--expected-commit", $ExpectedCommit,
    "--build-resources"
)

$IndexDirectory = Join-Path $WebShopRoot "search_engine\indexes_1k"
if (-not (Test-Path -LiteralPath $IndexDirectory -PathType Container)) {
    Push-Location (Join-Path $WebShopRoot "search_engine")
    try {
        Invoke-CondaChecked @(
            "run", "-n", $EnvironmentName,
            "python", "-m", "pyserini.index.lucene",
            "--collection", "JsonCollection",
            "--input", "resources_1k",
            "--index", "indexes_1k",
            "--generator", "DefaultLuceneDocumentGenerator",
            "--threads", "1",
            "--storePositions", "--storeDocvectors", "--storeRaw"
        )
    }
    finally {
        Pop-Location
    }
}

Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", $VerifyScript,
    "--checkout", $WebShopRoot,
    "--expected-commit", $ExpectedCommit,
    "--query-index",
    "--output", $IndexEvidenceOutput
)
Invoke-CondaChecked @(
    "run", "-n", $EnvironmentName,
    "python", $SmokeScript,
    "--checkout", $WebShopRoot,
    "--expected-commit", $ExpectedCommit,
    "--output", $SmokeOutput
)

Write-Output "WebShop small runtime bootstrap completed without executing click[buy now]."

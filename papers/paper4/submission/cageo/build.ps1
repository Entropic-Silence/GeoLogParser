param(
    [switch]$Final
)

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $here '..\..\..\..')).Path
$paperRoot = Join-Path $repoRoot 'papers\paper4'
$templateRoot = Join-Path $repoRoot '..\CAGEO_LaTeXTemplate'
$toolRoot = Join-Path $repoRoot '..\tools'

function Resolve-BuildTool {
    param(
        [string]$EnvironmentVariable,
        [string]$CommandName,
        [string]$BundledPath
    )

    $configured = [Environment]::GetEnvironmentVariable($EnvironmentVariable)
    if ($configured) {
        $resolved = Get-Command $configured -ErrorAction SilentlyContinue
        if ($resolved) { return $resolved.Source }
        if (Test-Path -LiteralPath $configured) { return (Resolve-Path -LiteralPath $configured).Path }
        throw "$EnvironmentVariable points to a missing command: $configured"
    }
    if (Test-Path -LiteralPath $BundledPath) {
        return (Resolve-Path -LiteralPath $BundledPath).Path
    }
    $resolved = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($resolved) { return $resolved.Source }
    throw "Required build tool not found: $CommandName. Set $EnvironmentVariable to its executable."
}

$pandoc = Resolve-BuildTool 'PANDOC' 'pandoc' (Join-Path $toolRoot 'pandoc-3.10.2\bin\pandoc-3.10.2\pandoc.exe')
$tectonic = Resolve-BuildTool 'TECTONIC' 'tectonic' (Join-Path $toolRoot 'tectonic-0.17.0\bin\tectonic.exe')
$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

function Assert-BuildToolVersion {
    param(
        [string]$Program,
        [string]$ExpectedVersion
    )
    $versionLine = (& $Program --version | Select-Object -First 1) -join ''
    if (-not $versionLine -or $versionLine -notmatch "\b$([regex]::Escape($ExpectedVersion))\b") {
        throw "Expected $Program version $ExpectedVersion; found: $versionLine"
    }
}

Assert-BuildToolVersion $pandoc '3.10.2'
Assert-BuildToolVersion $tectonic '0.17.0'

# Tectonic otherwise embeds the wall-clock time in the PDF metadata.  Use the
# release date as the default reproducibility epoch while allowing a caller to
# provide an explicit SOURCE_DATE_EPOCH for an archival rebuild.
if (-not $env:SOURCE_DATE_EPOCH) {
    $releaseMetadata = Get-Content -Raw (Join-Path $paperRoot 'release_metadata.json') | ConvertFrom-Json
    $releaseEpoch = [DateTimeOffset]::Parse("$($releaseMetadata.release_date)T00:00:00Z").ToUnixTimeSeconds()
    $env:SOURCE_DATE_EPOCH = [string]$releaseEpoch
}

foreach ($name in @('cas-sc.cls', 'cas-dc.cls', 'cas-common.sty', 'cas-model2-names.bst')) {
    $destination = Join-Path $here $name
    if (-not (Test-Path -LiteralPath $destination)) {
        Copy-Item -LiteralPath (Join-Path $templateRoot $name) -Destination $destination
    }
}

$bodyPath = Join-Path $here 'body_pandoc.tex'
& $pandoc (Join-Path $paperRoot 'manuscript.md') --from 'markdown+tex_math_dollars+raw_tex' --to latex --natbib --wrap=none --resource-path $paperRoot -o $bodyPath
if ($LASTEXITCODE -ne 0) { throw "Pandoc conversion failed with exit code $LASTEXITCODE" }

$buildArgs = @($bodyPath)
if ($Final) { $buildArgs += '--final' }
& $python (Join-Path $here 'build_review.py') @buildArgs
if ($LASTEXITCODE -ne 0) { throw "Review source generation failed with exit code $LASTEXITCODE" }

Push-Location $here
try {
    & $tectonic 'manuscript.tex' '--keep-logs' '--keep-intermediates' '--reruns' '2'
    if ($LASTEXITCODE -ne 0) { throw "Tectonic compilation failed with exit code $LASTEXITCODE" }
    if ($Final) {
        Copy-Item -LiteralPath 'manuscript.pdf' -Destination 'manuscript_final.pdf' -Force
    } else {
        Copy-Item -LiteralPath 'manuscript.pdf' -Destination 'manuscript_review.pdf' -Force
        Copy-Item -LiteralPath 'manuscript.pdf' -Destination 'manuscript_review_v2.pdf' -Force
    }
}
finally {
    Pop-Location
}

Remove-Item -LiteralPath $bodyPath -Force -ErrorAction SilentlyContinue
if ($Final) {
    Write-Output "Created $here\manuscript_final.pdf and $here\manuscript_final.md"
} else {
    Write-Output "Created $here\manuscript_review.pdf and $here\manuscript_review_v2.pdf"
}

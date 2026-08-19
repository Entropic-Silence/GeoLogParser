param(
    [switch]$Final
)

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $here '..\..\..\..')).Path
$paperRoot = Join-Path $repoRoot 'papers\paper4'
$templateRoot = Join-Path $repoRoot '..\CAGEO_LaTeXTemplate'
$toolRoot = Join-Path $repoRoot '..\tools'

$pandoc = if ($env:PANDOC) { $env:PANDOC } else { Join-Path $toolRoot 'pandoc-3.10.2\bin\pandoc-3.10.2\pandoc.exe' }
$tectonic = if ($env:TECTONIC) { $env:TECTONIC } else { Join-Path $toolRoot 'tectonic-0.17.0\bin\tectonic.exe' }
$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

foreach ($program in @($pandoc, $tectonic)) {
    if (-not (Test-Path -LiteralPath $program)) {
        throw "Required build tool not found: $program. Set PANDOC or TECTONIC to override."
    }
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

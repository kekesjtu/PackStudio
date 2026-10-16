[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$ListOnly,
    [switch]$IncludePackages
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$rootPrefix = $projectRoot + [IO.Path]::DirectorySeparatorChar

# Retain installed dependencies, daily Vite caches, dist, packages, and service logs.
$candidates = @(
    '.pytest_cache', '.ruff_cache', 'build',
    'node_modules/.vite-temp',
    'node_modules/.vite-browser-probe', 'node_modules/.vite-browser-trace',
    'node_modules/.vite-profile-baseline', 'node_modules/.vite-profile-fixed',
    'node_modules/.vite-profile-runtime'
) | ForEach-Object { Join-Path $projectRoot $_ }
if ($IncludePackages) { $candidates += Join-Path $projectRoot 'release' }
# Electron was removed; only remove its empty leftover directory.
$electronRoot = Join-Path $projectRoot 'electron'
if ((Test-Path -LiteralPath $electronRoot -PathType Container) -and
    @(Get-ChildItem -LiteralPath $electronRoot -Force).Count -eq 0) {
    $candidates += $electronRoot
}
$temporaryRoot = Join-Path $projectRoot 'tmp'
if (Test-Path -LiteralPath $temporaryRoot) {
    $candidates += @(Get-ChildItem -LiteralPath $temporaryRoot -Force |
        Where-Object Name -ne 'startup' | Select-Object -ExpandProperty FullName)
}
$viteCache = Join-Path $projectRoot 'node_modules/.vite'
if (Test-Path -LiteralPath $viteCache) {
    $candidates += @(Get-ChildItem -LiteralPath $viteCache -Directory -Filter 'deps_temp_*' |
        Select-Object -ExpandProperty FullName)
}
foreach ($source in @('src', 'tests', 'tools', 'flotherm_pack_data/validation')) {
    $sourcePath = Join-Path $projectRoot $source
    if (Test-Path -LiteralPath $sourcePath) {
        $candidates += @(Get-ChildItem -LiteralPath $sourcePath -Directory -Recurse -Filter '__pycache__' |
            Select-Object -ExpandProperty FullName)
    }
}

$validated = foreach ($candidate in ($candidates | Sort-Object -Unique)) {
    $fullPath = [IO.Path]::GetFullPath($candidate)
    if (-not $fullPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside workspace: $fullPath"
    }
    if (-not (Test-Path -LiteralPath $fullPath)) { continue }
    # Reject redirected paths before any recursive operation.
    $ancestor = $fullPath
    while ($ancestor -ne $projectRoot) {
        if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing redirected path: $ancestor"
        }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    $relativePath = $fullPath.Substring($rootPrefix.Length).Replace('\', '/')
    $tracked = @(git -c core.fsmonitor=false --literal-pathspecs -C $projectRoot ls-files -- $relativePath)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to verify Git tracked files' }
    if ($tracked.Count -gt 0) { throw "Refusing to remove tracked files: $relativePath" }
    $fullPath
}
if ($ListOnly) {
    $validated
    return
}

$removed = 0
$failed = 0
foreach ($path in $validated) {
    if ($PSCmdlet.ShouldProcess($path, 'Remove generated files')) {
        try {
            Remove-Item -LiteralPath $path -Recurse -Force
            $removed++
        }
        catch {
            $failed++
            Write-Warning "Unable to remove ${path}: $($_.Exception.Message)"
        }
    }
}
Write-Host "Cleanup targets: $($validated.Count); removed: $removed; failed: $failed"
if ($failed -gt 0) { exit 1 }

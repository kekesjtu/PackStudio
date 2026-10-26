param(
    [Parameter(Mandatory = $true)][string]$Installation,
    [Parameter(Mandatory = $true)][string]$Directory,
    [ValidateRange(1, 86400)][int]$TimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'
$packRoot = (Resolve-Path -LiteralPath $Installation).Path
$packRun = (Resolve-Path -LiteralPath $Directory).Path
$packResultPath = Join-Path $packRun 'process.json'
if (Test-Path -LiteralPath $packResultPath) { throw 'Process result already exists; use a new run.' }
$packTimer = [Diagnostics.Stopwatch]::StartNew()
$packResult = @{ exit_code = $null; seconds = 0; errors = @() }
try {
    $packPaths = @{
        FLO_ROOT = $packRoot
        FLOPRODUCTDIR = Join-Path $packRoot 'WinXP'
        FLO_PATH = Join-Path $packRoot 'WinXP\bin'
        FLO_LIBPATH = Join-Path $packRoot 'WinXP\lib'
        FLOSCRIPTSCHEMA = Join-Path $packRoot 'WinXP\lib'
        FLOPRODUCTCONFIG = Join-Path $packRun 'config'
        FLOTRANSLATIONS = Join-Path $packRun 'config'
        FLOCENTRALDIR = Join-Path $packRun 'central'
        FLOUSERDIR = Join-Path $packRun 'user'
        TEMP = Join-Path $packRun 'temp'
        TMP = Join-Path $packRun 'temp'
        QT_PLUGIN_PATH = Join-Path $packRoot 'WinXP\64lib\plugins'
        QT_QPA_PLATFORM_PLUGIN_PATH = Join-Path $packRoot 'WinXP\64lib\plugins\platforms'
    }
    foreach ($packKey in $packPaths.Keys) {
        [Environment]::SetEnvironmentVariable($packKey, $packPaths[$packKey], 'Process')
    }
    $env:PATH = (Join-Path $packRoot 'WinXP\bin') + ';' +
        (Join-Path $packRoot 'WinXP\64lib') + ';' + $env:PATH
    $packExecutable = Join-Path $packRoot 'WinXP\bin\flopack.exe'
    $packResult.file_version = (Get-Item -LiteralPath $packExecutable).VersionInfo.FileVersion
    $packStart = @{
        FilePath = $packExecutable
        ArgumentList = @('-f', ('"{0}"' -f (Join-Path $packRun 'replay.xml')))
        WorkingDirectory = $packRun
        WindowStyle = 'Hidden'
        PassThru = $true
        RedirectStandardOutput = Join-Path $packRun 'stdout.txt'
        RedirectStandardError = Join-Path $packRun 'stderr.txt'
    }
    $packProcess = Start-Process @packStart
    $null = $packProcess.Handle
    $packResult.pid = $packProcess.Id
    $packResult | ConvertTo-Json | Set-Content -LiteralPath $packResultPath -Encoding UTF8
    if ($packProcess.WaitForExit($TimeoutSeconds * 1000)) {
        $packResult.exit_code = $packProcess.ExitCode
    } else {
        $packProcess.Kill($true)
        $packProcess.WaitForExit()
        $packResult.exit_code = 'timeout'
    }
} catch {
    $packResult.errors += $_.Exception.Message
} finally {
    $packTimer.Stop()
    $packResult.seconds = $packTimer.Elapsed.TotalSeconds
    $packResult | ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath $packResultPath -Encoding UTF8
}
if ($packResult.exit_code -ne 0 -or $packResult.errors.Count -ne 0) { exit 1 }

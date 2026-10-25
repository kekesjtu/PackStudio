param(
    [Parameter(Mandatory = $true)][string]$Installation,
    [Parameter(Mandatory = $true)][string]$Directory
)

$ErrorActionPreference = 'Stop'
$packRoot = (Resolve-Path -LiteralPath $Installation).Path
$packRun = (Resolve-Path -LiteralPath $Directory).Path
$packScript = Join-Path $packRun 'replay.xml'
[xml]$packCommands = Get-Content -LiteralPath $packScript -Raw
$packExports = @($packCommands.flopack_xml_log_file.export_floxml | ForEach-Object { $_.filename })
foreach ($packExport in $packExports) {
    if (Test-Path -LiteralPath $packExport) { throw "Export already exists: $packExport" }
}
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
    QT_PLUGIN_PATH = Join-Path $packRoot 'WinXP\64lib\plugins'
    QT_QPA_PLATFORM_PLUGIN_PATH = Join-Path $packRoot 'WinXP\64lib\plugins\platforms'
}
foreach ($packKey in $packPaths.Keys) {
    [Environment]::SetEnvironmentVariable($packKey, $packPaths[$packKey], 'Process')
}
$env:PATH = (Join-Path $packRoot 'WinXP\bin') + ';' +
    (Join-Path $packRoot 'WinXP\64lib') + ';' + $env:PATH
$packExecutable = Join-Path $packRoot 'WinXP\bin\flopack.exe'
$packStart = @{
    FilePath = $packExecutable
    ArgumentList = @('-f', ('"{0}"' -f $packScript))
    WorkingDirectory = $packRun
    WindowStyle = 'Hidden'
    PassThru = $true
    RedirectStandardOutput = Join-Path $packRun 'stdout.txt'
    RedirectStandardError = Join-Path $packRun 'stderr.txt'
}
$packTimer = [Diagnostics.Stopwatch]::StartNew()
$packProcess = Start-Process @packStart
$null = $packProcess.Handle
$packFinished = $packProcess.WaitForExit(50000)
if ($packFinished) {
    $packCode = $packProcess.ExitCode
} else {
    $packProcess.Kill()
    $packProcess.WaitForExit()
    $packCode = 'timeout'
}
$packTimer.Stop()
$packDigests = @{}
foreach ($packExport in $packExports) {
    if (Test-Path -LiteralPath $packExport) {
        $packDigests[[IO.Path]::GetFileNameWithoutExtension($packExport)] =
            (Get-FileHash -LiteralPath $packExport -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$packBinaries = @{}
foreach ($packBinary in @('flopackrealise.dll', 'flopackfloxmlhandling.dll', 'flopackmaterials.dll')) {
    $packBinaryPath = Join-Path $packRoot "WinXP\bin\$packBinary"
    $packBinaries[$packBinary] =
        (Get-FileHash -LiteralPath $packBinaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
$packErrors = @()
foreach ($packLog in Get-ChildItem -LiteralPath (Join-Path $packRun 'LogFiles') -Filter '*.xml') {
    try {
        [xml]$packLogXml = Get-Content -LiteralPath $packLog.FullName -Raw
        $packErrors += @($packLogXml.SelectNodes('//message') |
            Where-Object { $_.text -match 'ERROR' } | ForEach-Object { $_.text })
    } catch {
        $packErrors += "Invalid native log: $($packLog.Name)"
    }
}
$packResult = @{
    exit_code = $packCode
    seconds = $packTimer.Elapsed.TotalSeconds
    executable = $packExecutable
    executable_sha256 = (Get-FileHash -LiteralPath $packExecutable).Hash.ToLowerInvariant()
    file_version = (Get-Item -LiteralPath $packExecutable).VersionInfo.FileVersion
    binary_sha256 = $packBinaries
    script_sha256 = (Get-FileHash -LiteralPath $packScript).Hash.ToLowerInvariant()
    launcher_sha256 = (Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
    exports = $packDigests
    errors = @($packErrors)
    launcher = 'PowerShell Start-Process -WindowStyle Hidden'
}
$packResult | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $packRun 'run.json') -Encoding UTF8
if ($packCode -ne 0 -or $packErrors.Count -ne 0 -or $packDigests.Count -ne $packExports.Count) {
    throw 'Native PACK replay failed; see run.json and native logs.'
}

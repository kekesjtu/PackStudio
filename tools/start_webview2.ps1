[CmdletBinding()]
param(
    [ValidateRange(0, 65535)][int]$Port = 18080,
    [switch]$BuildOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    & uv sync --locked --python-preference only-managed
    if ($LASTEXITCODE -ne 0) { throw 'Python 环境准备失败。' }
    & node tools/ensure_frontend_build.mjs
    if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' }
    & dotnet restore src/webview2/PackStudio.WebView2.csproj --locked-mode
    if ($LASTEXITCODE -ne 0) { throw 'WebView2 依赖恢复失败。' }
    & dotnet build src/webview2/PackStudio.WebView2.csproj -c Release --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'WebView2 宿主构建失败。' }
    if (!$BuildOnly) {
        $executable = Join-Path $projectRoot 'build/dotnet/PackStudio.WebView2/bin/Release/net10.0-windows/PackStudio.WebView2.exe'
        Start-Process -FilePath $executable -ArgumentList @('--root', ('"' + $projectRoot + '"'), '--port', $Port)
    }
}
finally { Pop-Location }

[CmdletBinding()]
param([string]$OutputDirectory)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (!$OutputDirectory) { $OutputDirectory = Join-Path $projectRoot 'release/webview2' }
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if ((Test-Path -LiteralPath $OutputDirectory) -and
    (Get-ChildItem -LiteralPath $OutputDirectory -Force | Select-Object -First 1)) {
    throw '输出目录已有文件，请指定新的 -OutputDirectory，避免混入旧打包产物。'
}
Push-Location $projectRoot
try {
    & uv sync --locked --python-preference only-managed
    if ($LASTEXITCODE -ne 0) { throw 'Python 环境准备失败。' }
    & node tools/ensure_frontend_build.mjs
    if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' }
    & uv run --locked --group packaging python tools/build_backend.py
    if ($LASTEXITCODE -ne 0) { throw '后端打包失败。' }
    & dotnet restore src/webview2/PackStudio.WebView2.csproj --locked-mode
    if ($LASTEXITCODE -ne 0) { throw 'WebView2 依赖恢复失败。' }
    & dotnet publish src/webview2/PackStudio.WebView2.csproj -c Release --no-restore -o $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'WebView2 宿主发布失败。' }
    Copy-Item -LiteralPath (Join-Path $projectRoot 'release/backend/packstudio-backend') -Destination (Join-Path $OutputDirectory 'backend') -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot 'dist') -Destination (Join-Path $OutputDirectory 'frontend') -Recurse
    Write-Host "运行目录已生成：$OutputDirectory"
    Write-Host '打开 PackStudio.WebView2.exe；目标机器需要 .NET Desktop Runtime 10 和 WebView2 Runtime。'
}
finally { Pop-Location }

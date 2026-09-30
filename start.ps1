[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$BackendPort = 8000,
    [ValidateRange(1, 65535)]
    [int]$FrontendPort = 5173,
    [switch]$Setup,
    [switch]$NoBrowser,
    [switch]$Check
)
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$lockFile = Join-Path $projectRoot "uv.lock"
$packageFile = Join-Path $projectRoot "package.json"
$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"
$isWindowsPlatform = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT

function Resolve-NativeCommand {
    param(
        [Parameter(Mandatory)]
        [string[]]$Names,
        [Parameter(Mandatory)]
        [string]$InstallHint
    )

    foreach ($name in $Names) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $command) {
            return $command.Source
        }
    }

    throw "未找到 $($Names[-1])。$InstallHint"
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$FailureMessage
    )
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Assert-PortAvailable {
    param([Parameter(Mandatory)][int]$Port)

    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        $Port
    )

    try {
        $listener.Start()
    }
    catch {
        throw "端口 $Port 已被占用，请先关闭占用该端口的程序。"
    }
    finally {
        $listener.Stop()
    }
}

function Assert-ProcessRunning {
    param(
        [Parameter(Mandatory)][System.Diagnostics.Process]$Process,
        [Parameter(Mandatory)][string]$Name
    )

    $Process.Refresh()
    if ($Process.HasExited) {
        throw "$Name 已退出（退出码 $($Process.ExitCode)）。可运行 .\start.ps1 -Setup 刷新依赖后重试。"
    }
}

function Wait-ForEndpoint {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][System.Diagnostics.Process]$BackendProcess,
        [Parameter(Mandatory)][System.Diagnostics.Process]$FrontendProcess,
        [int]$TimeoutSeconds = 60
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        Assert-ProcessRunning -Process $BackendProcess -Name "后端服务"
        Assert-ProcessRunning -Process $FrontendProcess -Name "前端服务"

        try {
            $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "等待 $Uri 就绪超时。"
}

function Stop-ManagedProcess {
    param([System.Diagnostics.Process]$Process)
    if ($null -eq $Process) {
        return
    }
    try {
        $Process.Refresh()
        if ($Process.HasExited) {
            return
        }
        if ($isWindowsPlatform) {
            $processIds = @($Process.Id)
            for ($index = 0; $index -lt $processIds.Count; $index++) {
                $children = Get-CimInstance Win32_Process `
                    -Filter "ParentProcessId = $($processIds[$index])" `
                    -ErrorAction SilentlyContinue
                foreach ($child in $children) {
                    $processIds += $child.ProcessId
                }
            }
            Stop-Process -Id $processIds -Force -ErrorAction SilentlyContinue
        }
        else {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Warning "未能自动停止进程 $($Process.Id)：$($_.Exception.Message)"
    }
}

$backendProcess = $null
$frontendProcess = $null

try {
    if (-not (Test-Path -LiteralPath $lockFile)) {
        throw "缺少 uv.lock：$lockFile"
    }
    if (-not (Test-Path -LiteralPath $packageFile)) {
        throw "缺少 package.json：$packageFile"
    }

    $uvNames = if ($isWindowsPlatform) { @("uv.exe", "uv") } else { @("uv") }
    $npmNames = if ($isWindowsPlatform) { @("npm.cmd", "npm") } else { @("npm") }
    $uvPath = Resolve-NativeCommand -Names $uvNames -InstallHint "请安装 uv 并将其加入 PATH。"
    $npmPath = Resolve-NativeCommand -Names $npmNames -InstallHint "请安装 Node.js 22.12+ 与 npm，并将其加入 PATH。"

    Push-Location $projectRoot
    try {
        Write-Host "正在根据 uv.lock 同步 Python 环境 ..." -ForegroundColor Cyan
        Invoke-CheckedCommand -FilePath $uvPath `
            -ArgumentList @("sync", "--locked", "--python-preference", "only-managed") `
            -FailureMessage "同步 uv 环境失败。依赖声明改变后请先执行 uv lock。"

        $viteExecutable = if ($isWindowsPlatform) {
            Join-Path $projectRoot "node_modules\.bin\vite.cmd"
        }
        else {
            Join-Path $projectRoot "node_modules/.bin/vite"
        }

        if ($Setup -or -not (Test-Path -LiteralPath $viteExecutable)) {
            Write-Host "正在安装前端依赖 ..." -ForegroundColor Cyan
            Invoke-CheckedCommand -FilePath $npmPath `
                -ArgumentList @("install") `
                -FailureMessage "安装前端依赖失败。"
        }

        Assert-PortAvailable -Port $BackendPort
        Assert-PortAvailable -Port $FrontendPort

        Write-Host "正在启动 PackStudio ..." -ForegroundColor Cyan
        $backendProcess = Start-Process -FilePath $uvPath `
            -ArgumentList @(
                "run", "--locked", "--no-sync",
                "python", "-m", "uvicorn", "packstudio.api.app:app",
                "--app-dir", "src", "--host", "127.0.0.1", "--port", "$BackendPort", "--reload"
            ) `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden `
            -PassThru

        $apiTargetWasSet = Test-Path Env:PACKSTUDIO_API_TARGET
        $previousApiTarget = $env:PACKSTUDIO_API_TARGET
        $env:PACKSTUDIO_API_TARGET = $backendUrl
        try {
            $frontendProcess = Start-Process -FilePath $npmPath `
                -ArgumentList @(
                    "run", "dev", "--", "--host", "127.0.0.1",
                    "--port", "$FrontendPort", "--strictPort"
                ) `
                -WorkingDirectory $projectRoot `
                -WindowStyle Hidden `
                -PassThru
        }
        finally {
            if ($apiTargetWasSet) {
                $env:PACKSTUDIO_API_TARGET = $previousApiTarget
            }
            else {
                Remove-Item Env:PACKSTUDIO_API_TARGET -ErrorAction SilentlyContinue
            }
        }

        Wait-ForEndpoint -Uri "$backendUrl/api/health" `
            -BackendProcess $backendProcess `
            -FrontendProcess $frontendProcess
        Wait-ForEndpoint -Uri "$frontendUrl/api/health" `
            -BackendProcess $backendProcess `
            -FrontendProcess $frontendProcess

        Write-Host ""
        Write-Host "PackStudio 已就绪" -ForegroundColor Green
        Write-Host "前端：$frontendUrl"
        Write-Host "API： $backendUrl/docs"

        if ($Check) {
            Write-Host "启动检查通过，正在关闭测试进程。" -ForegroundColor Green
            return
        }

        if (-not $NoBrowser) {
            Start-Process $frontendUrl | Out-Null
        }

        Write-Host "按 Ctrl+C 同时停止前后端。"
        while ($true) {
            Assert-ProcessRunning -Process $backendProcess -Name "后端服务"
            Assert-ProcessRunning -Process $frontendProcess -Name "前端服务"
            Start-Sleep -Seconds 1
        }
    }
    finally {
        Pop-Location
        if ($null -ne $backendProcess -or $null -ne $frontendProcess) {
            Write-Host "正在停止 PackStudio ..." -ForegroundColor DarkGray
        }
        Stop-ManagedProcess -Process $frontendProcess
        Stop-ManagedProcess -Process $backendProcess
    }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

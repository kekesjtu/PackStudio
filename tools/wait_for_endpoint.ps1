function Wait-ForEndpoint {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][System.Diagnostics.Process]$BackendProcess,
        [Parameter(Mandatory)][System.Diagnostics.Process]$FrontendProcess,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 60
    )

    Add-Type -AssemblyName System.Net.Http
    $handler = [System.Net.Http.HttpClientHandler]::new()
    # Readiness requests are local and must not depend on a system/network proxy.
    $handler.UseProxy = $false
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(2)
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $nextProgressSeconds = 5
    $lastFailure = "尚未收到响应"
    Write-Host "$Stage ..." -ForegroundColor Cyan
    try {
        while ($timer.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
            Assert-ProcessRunning -Process $BackendProcess -Name "后端服务"
            Assert-ProcessRunning -Process $FrontendProcess -Name "前端服务"
            $response = $null
            try {
                # Read the body too: the schema call also warms the template library.
                $response = $client.GetAsync($Uri).GetAwaiter().GetResult()
                if ([int]$response.StatusCode -eq 200) {
                    Write-Host ("{0}完成（{1:N1} 秒）" -f $Stage, $timer.Elapsed.TotalSeconds)
                    return
                }
                $lastFailure = "HTTP $([int]$response.StatusCode)"
            }
            catch {
                $failure = $_.Exception
                while ($null -ne $failure.InnerException -and $failure -isnot [System.OperationCanceledException]) {
                    $failure = $failure.InnerException
                }
                $lastFailure = if ($failure -is [System.OperationCanceledException]) {
                    "本次检查超过 2 秒，服务暂未响应；继续等待"
                } else { $failure.Message }
            }
            finally { if ($null -ne $response) { $response.Dispose() } }
            if ($timer.Elapsed.TotalSeconds -ge $nextProgressSeconds) {
                Write-Host ("仍在{0}，已等待 {1:N0} 秒：{2}" -f $Stage, $timer.Elapsed.TotalSeconds, $lastFailure)
                $nextProgressSeconds += 5
            }
            Start-Sleep -Milliseconds 500
        }
        throw "$Stage 超时（$Uri）。最后一次检查：$lastFailure"
    }
    finally { $client.Dispose() }
}

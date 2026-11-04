[CmdletBinding()]
param([switch]$Check, [switch]$BuildOnly, [switch]$Offline)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot 'build.ps1') -Target Desktop -Offline:$Offline
    if (-not $Check -and -not $BuildOnly) {
        Start-Process -FilePath (Join-Path $PSScriptRoot 'src/PackStudio.Desktop/bin/Release/net10.0-windows/PackStudio.exe') -WorkingDirectory $PSScriptRoot -WindowStyle Normal
    }
}
finally { Pop-Location }

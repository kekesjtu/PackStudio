[CmdletBinding()]
param([switch]$Check, [switch]$BuildOnly)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    dotnet restore PackStudio.slnx --locked-mode
    if ($LASTEXITCODE -ne 0) { throw 'NuGet restore failed' }
    dotnet build src/PackStudio.Desktop/PackStudio.Desktop.csproj -c Release --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed' }
    if (-not $Check -and -not $BuildOnly) {
        Start-Process -FilePath (Join-Path $PSScriptRoot 'src/PackStudio.Desktop/bin/Release/net10.0-windows/PackStudio.exe') -WorkingDirectory $PSScriptRoot -WindowStyle Normal
    }
}
finally { Pop-Location }
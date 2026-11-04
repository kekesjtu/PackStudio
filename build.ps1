[CmdletBinding()]
param(
    [ValidateSet('All', 'Desktop', 'Cli')][string]$Target = 'All',
    [string]$ArtifactsPath,
    [switch]$Offline
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $project = switch ($Target) {
        'Desktop' { 'src/PackStudio.Desktop/PackStudio.Desktop.csproj' }
        'Cli' { 'src/PackStudio.Cli/PackStudio.Cli.csproj' }
        'All' { 'PackStudio.slnx' }
    }
    $artifactArguments = @()
    if ($ArtifactsPath) { $artifactArguments = @('--artifacts-path', [IO.Path]::GetFullPath($ArtifactsPath)) }
    $restoreArguments = @()
    if ($Offline) { $restoreArguments = @('--ignore-failed-sources', '-p:NuGetAudit=false') }
    dotnet restore $project --locked-mode --disable-parallel -m:1 @artifactArguments @restoreArguments
    if ($LASTEXITCODE -ne 0) { throw 'NuGet restore failed' }
    dotnet build $project -c Release --no-restore -m:1 -p:UseSharedCompilation=false @artifactArguments
    if ($LASTEXITCODE -ne 0) { throw "$Target build failed" }
}
finally { Pop-Location }

[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+\.\d+$')][string]$Version = '0.1.1',
    [string]$CompilerPath
)

$ErrorActionPreference = 'Stop'
$packageVersion = [version]$Version

$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$release = Join-Path $repo 'release'
$package = Join-Path $release 'PackStudio-Setup-x64.exe'
$workRoot = Join-Path $repo ('tmp\{0:yyyy-MM-dd}-packstudio-installer' -f (Get-Date))
$work = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))

if ($CompilerPath) {
    $CompilerPath = (Resolve-Path -LiteralPath $CompilerPath).Path
} else {
    $programFiles = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)
    $localPrograms = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
    $compilerCandidates = @(
        (Join-Path $release '.tools\inno-6.6.1\ISCC.exe')
        (Join-Path $programFiles 'Inno Setup 6\ISCC.exe')
        (Join-Path $localPrograms 'Programs\Inno Setup 6\ISCC.exe')
        (Get-Command ISCC.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
    )
    $CompilerPath = $compilerCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
}
if (!$CompilerPath) { throw 'Install Inno Setup 6.6.1 or specify the path to ISCC.exe with -CompilerPath.' }

Push-Location $repo
try {
    New-Item -ItemType Directory -Path $work, $release -Force | Out-Null
    $desktop = Join-Path $work 'desktop'
    $cli = Join-Path $work 'cli'
    $artifacts = Join-Path $work 'artifacts'
    $publishArguments = @('-c', 'Release', '-r', 'win-x64', '--self-contained', '--artifacts-path', $artifacts,
        '-m:1', '-p:UseSharedCompilation=false', "-p:Version=$packageVersion",
        '-p:RestorePackagesWithLockFile=false', "-p:NuGetLockFilePath=$(Join-Path $work 'publish.lock.json')")

    dotnet publish src/PackStudio.Desktop/PackStudio.Desktop.csproj @publishArguments -o $desktop
    if ($LASTEXITCODE -ne 0) { throw 'PackStudio Desktop publish failed.' }
    dotnet publish src/PackStudio.Cli/PackStudio.Cli.csproj @publishArguments -o $cli
    if ($LASTEXITCODE -ne 0) { throw 'PackStudio CLI publish failed.' }

    $stagedPackage = Join-Path $work ([IO.Path]::GetFileName($package))
    & $CompilerPath /Qp "/O$work" "/DReleaseVersion=$packageVersion" "/DDesktopPublish=$desktop" "/DCliPublish=$cli" `
        (Join-Path $PSScriptRoot 'PackStudio.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed.' }

    if ([IO.File]::Exists($package)) {
        [IO.File]::Replace($stagedPackage, $package, [NullString]::Value)
    } else {
        [IO.File]::Move($stagedPackage, $package)
    }
    Write-Output $package
}
finally {
    if (Test-Path -LiteralPath $work -PathType Container) {
        $resolvedWork = (Resolve-Path -LiteralPath $work).Path
        $resolvedRoot = (Resolve-Path -LiteralPath $workRoot).Path
        if ([IO.Path]::GetDirectoryName($resolvedWork) -eq $resolvedRoot -and $resolvedRoot -eq $workRoot) {
            Remove-Item -LiteralPath $resolvedWork -Recurse -Force
        }
    }
    Pop-Location
}

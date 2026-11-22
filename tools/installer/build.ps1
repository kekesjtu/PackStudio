[CmdletBinding()]
param(
    [ValidatePattern('^\d{1,3}\.\d{1,3}\.\d{1,5}$')][string]$Version = '0.1.0',
    [string]$WixPath
)

$ErrorActionPreference = 'Stop'
$packageVersion = [version]$Version
if ($packageVersion.Major -gt 255 -or $packageVersion.Minor -gt 255 -or $packageVersion.Build -gt 65535) {
    throw 'MSI versions must be in the range 0.0.0 to 255.255.65535.'
}

$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$release = Join-Path $repo 'release'
$package = Join-Path $release 'PackStudio-Setup-x64.msi'
$workRoot = Join-Path $repo ('tmp\{0:yyyy-MM-dd}-packstudio-installer' -f (Get-Date))
$work = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))

Push-Location $repo
try {
    if ($WixPath) {
        $WixPath = (Resolve-Path -LiteralPath $WixPath).Path
    } else {
        $wixVersion = '6.0.2'
        $wixDirectory = Join-Path $release ".tools\wix-$wixVersion"
        $WixPath = Join-Path $wixDirectory 'wix.exe'
        if (!(Test-Path -LiteralPath $WixPath -PathType Leaf)) {
            dotnet tool install wix --version $wixVersion --tool-path $wixDirectory
            if ($LASTEXITCODE -ne 0) { throw 'WiX restore failed.' }
        }
    }

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

    $stagedPackage = Join-Path $work 'PackStudio-Setup-x64.msi'
    & $WixPath build -arch x64 -pdbtype none -intermediateFolder (Join-Path $work 'wix') `
        -d "Version=$packageVersion" -d "DesktopPublish=$desktop" -d "CliPublish=$cli" `
        -o $stagedPackage (Join-Path $PSScriptRoot 'PackStudio.wxs')
    if ($LASTEXITCODE -ne 0) { throw 'PackStudio MSI build failed.' }

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

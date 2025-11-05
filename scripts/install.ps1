$ErrorActionPreference = "Stop"

# Scriptum installer for Windows users.
# Downloads the latest release binary and ensures it is on the user's PATH.

$repo = "Scriptum-Lang/Scriptum"
$downloadUri = "https://github.com/$repo/releases/latest/download/scriptum.exe"

$installDir = Join-Path $env:LOCALAPPDATA "Programs\scriptum"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

$binaryPath = Join-Path $installDir "scriptum.exe"
Write-Host "Downloading Scriptum from $downloadUri..."
Invoke-WebRequest -Uri $downloadUri -OutFile $binaryPath -UseBasicParsing

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ([string]::IsNullOrWhiteSpace($userPath)) {
    $userPath = ""
}

$pathSeparator = ";"
$pathEntries = $userPath.Split($pathSeparator, [StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() }

$pathContainsInstallDir = $false
$normalizedInstallDir = $installDir.TrimEnd('\')
foreach ($entry in $pathEntries) {
    if ($entry.TrimEnd('\') -ieq $normalizedInstallDir) {
        $pathContainsInstallDir = $true
        break
    }
}

if (-not $pathContainsInstallDir) {
    if ([string]::IsNullOrEmpty($userPath)) {
        $newPath = $installDir
    }
    else {
        $newPath = "$userPath$pathSeparator$installDir"
    }

    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path$pathSeparator$installDir"
    Write-Host "Added $installDir to your user PATH."
}
else {
    Write-Host "Install directory already present on PATH."
}

Write-Host ""
Write-Host "Scriptum installed to $binaryPath"
Write-Host "You may need to restart your terminal for PATH changes to take effect."
Write-Host "Run 'scriptum --help' to get started."

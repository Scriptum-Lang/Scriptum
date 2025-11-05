$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $scriptDir "..\dist"
$binary = Join-Path $distDir "scriptum.exe"

if (-not (Test-Path $binary)) {
    Write-Error "Scriptum binary not found at $binary"
}

& $binary --version
& $binary --help
& $binary lex (Join-Path $scriptDir "..\examples\hello.stm")
& $binary parse (Join-Path $scriptDir "..\examples\hello.stm")

$helpOutput = & $binary --help
if ($helpOutput -match "sema") {
    & $binary sema (Join-Path $scriptDir "..\examples\hello.stm")
}

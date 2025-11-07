$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $scriptDir "..\dist"
$binary = Join-Path $distDir "scriptum.exe"

if (-not (Test-Path $binary)) {
    Write-Error "Scriptum binary not found at $binary"
}

& $binary --version
& $binary --help
& $binary (Join-Path $scriptDir "..\examples\hello.stm")
& $binary dev lex (Join-Path $scriptDir "..\examples\hello.stm")
& $binary dev ast (Join-Path $scriptDir "..\examples\hello.stm")
& $binary check (Join-Path $scriptDir "..\examples\err\type_mismatch.stm") --json

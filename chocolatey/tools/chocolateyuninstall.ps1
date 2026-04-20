$ErrorActionPreference = 'Continue'

$pypiPackage = 'pinelabs-mcp-server'
$shimName    = 'pinelabs-mcp'

# Remove the Chocolatey shim first (idempotent).
try {
    Uninstall-BinFile -Name $shimName
    Write-Host "Removed shim '$shimName'."
} catch {
    Write-Host "Shim '$shimName' was not present; skipping."
}

# Refresh PATH and try to locate Python; if absent the package is already gone.
Update-SessionEnvironment
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "python.exe not on PATH; skipping pip uninstall of $pypiPackage."
    return
}

Write-Host "Uninstalling $pypiPackage via pip..."
try {
    & $python.Source -m pip uninstall -y $pypiPackage
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip uninstall returned exit $LASTEXITCODE; continuing."
    }
} catch {
    Write-Host "pip uninstall threw: $($_.Exception.Message); continuing."
}

Write-Host "$pypiPackage uninstall complete."

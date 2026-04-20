$ErrorActionPreference = 'Stop'

$packageName    = 'pinelabs-mcp'
$pypiPackage    = 'pinelabs-mcp-server'
$packageVersion = $env:ChocolateyPackageVersion
$shimName       = 'pinelabs-mcp'

# Refresh PATH so python3 (just installed via dependency) is visible.
Update-SessionEnvironment

# --- Locate Python 3.10+ -------------------------------------------------
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "python.exe not found on PATH after installing the 'python3' Chocolatey dependency. Please reinstall or open a new shell and retry."
}

$versionOutput = & $python.Source --version 2>&1
if ($versionOutput -notmatch 'Python\s+(\d+)\.(\d+)\.(\d+)') {
    throw "Unable to parse Python version from: $versionOutput"
}
$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    throw "Python 3.10+ required, found $versionOutput. Run: choco upgrade python3"
}
Write-Host "Using $versionOutput at $($python.Source)"

# --- Install the PyPI package -------------------------------------------
Write-Host "Installing $pypiPackage==$packageVersion from PyPI..."
& $python.Source -m pip install --upgrade --no-warn-script-location "$pypiPackage==$packageVersion"
if ($LASTEXITCODE -ne 0) {
    throw "pip install $pypiPackage==$packageVersion failed (exit $LASTEXITCODE)."
}

# --- Resolve the entrypoint and register a shim --------------------------
$scriptsDir = & $python.Source -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$scriptsDir = $scriptsDir.Trim()
$entrypoint = Join-Path $scriptsDir 'pinelabs-mcp-server.exe'

if (-not (Test-Path $entrypoint)) {
    throw "Expected entrypoint not found at $entrypoint after installing $pypiPackage."
}

Write-Host "Registering Chocolatey shim '$shimName' -> $entrypoint"
Install-BinFile -Name $shimName -Path $entrypoint

# --- Smoke test ----------------------------------------------------------
Write-Host "Smoke testing '$shimName --help'..."
$null = & $shimName --help 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Smoke test failed: '$shimName --help' returned exit code $LASTEXITCODE."
}

Write-Host "$packageName $packageVersion installed successfully."
Write-Host "Run: pinelabs-mcp stdio --client-id <ID> --client-secret <SECRET> --env uat"

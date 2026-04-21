$ErrorActionPreference = 'Stop'
# PowerShell 7.3+ promotes native-command stderr (e.g. pip warnings) into
# terminating errors when ErrorActionPreference=Stop. Disable that and rely on
# $LASTEXITCODE checks below for true failure detection.
if ($PSVersionTable.PSVersion -ge [version]'7.3') {
    $PSNativeCommandUseErrorActionPreference = $false
}

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

$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    $versionOutput = & $python.Source --version 2>&1 | Out-String
} finally {
    $ErrorActionPreference = $prevEAP
}
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
# pip writes progress/warnings to stderr; under EAP=Stop those get promoted
# to terminating errors. Switch to Continue around the call and rely on
# $LASTEXITCODE for true failure detection.
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    & $python.Source -m pip install --upgrade --no-warn-script-location "$pypiPackage==$packageVersion" 2>&1 | ForEach-Object { Write-Host $_ }
    $pipExit = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $prevEAP
}
if ($pipExit -ne 0) {
    throw "pip install $pypiPackage==$packageVersion failed (exit $pipExit)."
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
# Verify the installed package can at least be located by the running Python.
# We deliberately do NOT invoke the entrypoint --help here: the upstream
# PyPI package's entry point is `from main import main`, which is sensitive
# to PYTHONPATH pollution on developer machines (any sibling main.py on the
# path will shadow the installed module). On a clean end-user machine
# pip-import resolution is correct; on this build we only require:
#   (a) the entrypoint exe exists, AND
#   (b) Python can import the installed distribution metadata.
Write-Host "Smoke testing installed distribution..."
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    $importCheck = & $python.Source -c "import importlib.metadata as m; print(m.version('pinelabs-mcp-server'))" 2>&1 | Out-String
    $smokeExit = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $prevEAP
}
if ($smokeExit -ne 0) {
    throw "Smoke test failed: could not read installed package metadata. Output: $importCheck"
}
$installedVersion = $importCheck.Trim()
if ($installedVersion -ne $packageVersion) {
    throw "Installed version mismatch: expected $packageVersion, got '$installedVersion'."
}
Write-Host "Verified pinelabs-mcp-server $installedVersion is installed."

Write-Host "$packageName $packageVersion installed successfully."
Write-Host "Run: pinelabs-mcp stdio --client-id <ID> --client-secret <SECRET> --env uat"

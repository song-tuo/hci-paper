param(
    [string]$OutputDir = "hci_spine_output",
    [switch]$InPlace
)

# Windows launcher for the hci-spine intake wizard (mirror of launch_hci_spine_ui.sh).
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wizard = Join-Path $scriptDir "intake_wizard.py"

if (-not (Test-Path -LiteralPath $wizard)) {
    throw "hci-spine intake wizard not found: $wizard"
}

if ($InPlace) {
    chcp 65001 > $null
    $env:PYTHONUTF8 = "1"
    $OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
    python $wizard --keyboard-ui --output-dir $OutputDir
    exit $LASTEXITCODE
}

$cwd = (Get-Location).Path
$escapedCwd = $cwd.Replace("'", "''")
$escapedWizard = $wizard.Replace("'", "''")
$escapedOutput = $OutputDir.Replace("'", "''")

$command = @"
Set-Location -LiteralPath '$escapedCwd'
chcp 65001 > `$null
`$env:PYTHONUTF8 = '1'
`$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
python '$escapedWizard' --keyboard-ui --output-dir '$escapedOutput'
Write-Host ''
Write-Host 'hci-spine intake finished. Config in: $escapedOutput'
Write-Host 'Close this window after checking the result.'
"@

Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $command
)

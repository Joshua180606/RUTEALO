<#
Simple PowerShell installer for this project.
Creates a virtual environment (default: .venv) and installs packages from requirements.txt
#>
param(
    [string]$VenvName = ".venv"
)

Write-Host "Using virtual environment: $VenvName"

if (-not (Test-Path $VenvName)) {
    Write-Host "Creating virtual environment..."
    python -m venv $VenvName
}

$python = Join-Path -Path $PSScriptRoot -ChildPath "$VenvName\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python not found in $VenvName. Make sure Python is installed and available in PATH."
    exit 1
}

Write-Host "Upgrading pip and installing requirements..."
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path -Path $PSScriptRoot -ChildPath 'requirements.txt')

Write-Host "Done. To activate the virtual environment for the current session run:`n    .\$VenvName\Scripts\Activate.ps1"

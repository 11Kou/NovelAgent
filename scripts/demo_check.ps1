param(
    [switch]$SkipFrontend,
    [switch]$RunApiSmoke
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (!(Test-Path "backend\.venv\Scripts\python.exe")) {
    throw "backend\.venv was not found. Create it and install backend\requirements.txt first."
}

Invoke-Checked "Check Ollama embedding model" {
    & "backend\.venv\Scripts\python.exe" "backend\scripts\check_ollama.py"
}

$env:PYTHONPATH = "backend"

Invoke-Checked "Run backend tests" {
    & "backend\.venv\Scripts\python.exe" -m pytest "backend\tests" -q
}

Invoke-Checked "Compile backend files" {
    & "backend\.venv\Scripts\python.exe" -m compileall "backend\app" "backend\tests" "backend\scripts"
}

if (!$SkipFrontend) {
    Invoke-Checked "Build frontend" {
        Push-Location "frontend"
        try {
            & pnpm build
        }
        finally {
            Pop-Location
        }
    }
}

if ($RunApiSmoke) {
    Invoke-Checked "Run real API smoke" {
        Push-Location "backend"
        try {
            & ".\.venv\Scripts\python.exe" "scripts\api_smoke.py"
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "[ok] Demo checks completed."

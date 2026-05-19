$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Starting PDF Extraction Assistant on http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""
python -m uvicorn app.main:app --reload --app-dir $projectRoot --host 127.0.0.1 --port 8000

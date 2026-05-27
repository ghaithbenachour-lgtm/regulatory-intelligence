$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m pip install -r requirements.txt -q

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

$env:API_HOST = "0.0.0.0"
$env:PORT = "8080"
$env:CORS_ORIGINS = "*"

Write-Host ""
Write-Host "Starting Regulatory Intelligence on all network interfaces..."
Write-Host "  Local:   http://127.0.0.1:8080"
Write-Host "  Network: http://<your-ip>:8080"
Write-Host ""
Write-Host "For public internet access, deploy with Docker or Render (see README)."
Write-Host ""

& $Python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080

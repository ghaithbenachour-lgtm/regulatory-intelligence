$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Root
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  $Python = "python"
}

$IngestAction = New-ScheduledTaskAction -Execute $Python -Argument "-m backend.app.jobs.runner ingest" -WorkingDirectory $ProjectRoot
$DigestAction = New-ScheduledTaskAction -Execute $Python -Argument "-m backend.app.jobs.runner digest" -WorkingDirectory $ProjectRoot

Register-ScheduledTask -TaskName "RegulatoryIntel-Ingest" -Action $IngestAction -Trigger (New-ScheduledTaskTrigger -Daily -At 6:00AM) -Force
Register-ScheduledTask -TaskName "RegulatoryIntel-Digest" -Action $DigestAction -Trigger (New-ScheduledTaskTrigger -Daily -At 7:00AM) -Force

Write-Host "Scheduled tasks registered: RegulatoryIntel-Ingest (06:00), RegulatoryIntel-Digest (07:00)"

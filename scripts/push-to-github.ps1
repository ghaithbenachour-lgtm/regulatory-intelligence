# One-shot deploy helper (run after GitHub repo exists)
param(
    [Parameter(Mandatory = $true)]
    [string]$GitHubUsername,
    [Parameter(Mandatory = $true)]
    [string]$GitHubToken,
    [string]$RepoName = "regulatory-intelligence"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$git = Join-Path $Root ".tools\MinGit\cmd\git.exe"
if (-not (Test-Path $git)) {
    throw "Portable git not found at $git. Re-run setup or install Git for Windows."
}

$remote = "https://${GitHubUsername}:${GitHubToken}@github.com/${GitHubUsername}/${RepoName}.git"

& $git branch -M main 2>$null
& $git remote remove origin 2>$null
& $git remote add origin $remote
& $git push -u origin main

Write-Host "Pushed to https://github.com/$GitHubUsername/$RepoName"

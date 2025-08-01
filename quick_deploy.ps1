# Quick Deploy - Minimal Script for Immediate Success
param([switch]$DryRun = $false)

Write-Host "🚀 Quick Deploy - Isolated HF Strategy" -ForegroundColor Green

# Basic validation
if (!(Test-Path "universal-api-bridge")) {
    Write-Host "❌ universal-api-bridge directory not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Project structure validated" -ForegroundColor Green

# Check git status
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Found changes to commit" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️ No changes to commit" -ForegroundColor Blue
}

if ($DryRun) {
    Write-Host "🔍 DRY RUN - Would deploy with isolated HF config" -ForegroundColor Blue
    exit 0
}

# Commit if changes exist
if ($gitStatus) {
    git add .
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Deploy: Isolated HF configuration strategy - $timestamp"
}

# Deploy using explicit branch reference
Write-Host "🚀 Deploying with isolated strategy..." -ForegroundColor Yellow
$pushResult = git push origin "refs/heads/Beta:refs/heads/Beta" 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "✅ SUCCESS! Core platform deployed" -ForegroundColor Green
    Write-Host "🎯 HF can be configured post-deployment via admin interface" -ForegroundColor Blue
} else {
    Write-Host "❌ Deploy failed: $pushResult" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Deployment completed with isolation strategy!" -ForegroundColor Green 
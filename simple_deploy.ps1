# Simple PowerShell Deployment Script for News Platform
param(
    [string]$Branch = "Beta",
    [switch]$DryRun = $false
)

Write-Host "🚀 Simple News Platform Deployment" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check current directory
$currentDir = Get-Location
Write-Host "📁 Current directory: $currentDir" -ForegroundColor Yellow

# Verify project structure
if (!(Test-Path "universal-api-bridge")) {
    Write-Host "❌ universal-api-bridge directory not found!" -ForegroundColor Red
    exit 1
}

# Check for hardcoded tokens
Write-Host "🔍 Checking for security issues..." -ForegroundColor Blue
$tokenFound = $false
Get-ChildItem -Path "universal-api-bridge\*.html" -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "hf_[a-zA-Z0-9]{20,}") {
        Write-Host "❌ Found hardcoded token in: $($_.Name)" -ForegroundColor Red
        $tokenFound = $true
    }
}

if ($tokenFound) {
    Write-Host "🔒 GitHub will block push due to hardcoded tokens" -ForegroundColor Red
    Write-Host "💡 Use admin interface to configure tokens instead" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ No hardcoded tokens found" -ForegroundColor Green
}

# Check git status
Write-Host "📋 Checking git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Found changes to commit" -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "ℹ️ No changes to commit" -ForegroundColor Blue
}

# Handle dry run
if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No actual changes will be made" -ForegroundColor Blue
    Write-Host "Would execute: git push origin refs/heads/$Branch`:refs/heads/$Branch" -ForegroundColor Gray
    exit 0
}

# Add and commit if there are changes
if ($gitStatus) {
    Write-Host "➕ Adding files..." -ForegroundColor Yellow
    git add .
    
    Write-Host "💾 Creating commit..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Deploy: News Platform with security fixes - $timestamp"
}

# Push using explicit reference
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
$pushRef = "refs/heads/$Branch`:refs/heads/$Branch"
Write-Host "📤 Using reference: $pushRef" -ForegroundColor Blue

$pushOutput = git push origin $pushRef 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "❌ Push failed with exit code: $exitCode" -ForegroundColor Red
    Write-Host "Error output:" -ForegroundColor Yellow
    Write-Host $pushOutput -ForegroundColor Gray
    
    if ($pushOutput -match "secret") {
        Write-Host "🔒 GitHub secret scanning detected" -ForegroundColor Red
    }
    exit 1
}

# Verification
Write-Host "🔍 Verification..." -ForegroundColor Blue
$lastCommit = git log -1 --oneline
Write-Host "📝 Latest commit: $lastCommit" -ForegroundColor Blue

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green 
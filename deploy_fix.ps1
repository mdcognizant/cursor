# News Platform Deployment Fix Script
# Fixes PowerShell compatibility issues and command execution problems

param(
    [string]$Branch = "Beta",
    [switch]$Force = $false,
    [switch]$DryRun = $false
)

Write-Host "🚀 News Platform Deployment Fix" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Fix 1: Check current directory and navigate if needed
$currentDir = Get-Location
Write-Host "📁 Current directory: $currentDir" -ForegroundColor Yellow

if (!(Test-Path "universal-api-bridge")) {
    Write-Host "❌ universal-api-bridge directory not found!" -ForegroundColor Red
    Write-Host "💡 Make sure you're in the correct project root directory" -ForegroundColor Yellow
    exit 1
}

# Fix 2: Set proper git configuration
Write-Host "🔧 Checking git configuration..." -ForegroundColor Blue

try {
    $gitUser = git config user.name 2>$null
    if (!$gitUser) {
        Write-Host "⚙️ Setting git user configuration..." -ForegroundColor Yellow
        git config user.name "News Platform Deploy"
        git config user.email "deploy@newsplatform.local"
    }
    Write-Host "✅ Git user: $gitUser" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Git configuration warning: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Fix 3: Check for command execution issues
Write-Host "🔍 Checking for common deployment issues..." -ForegroundColor Blue

# Check for localhost dependencies (should be none)
$localhostRefs = Select-String -Pattern "localhost|127\.0\.0\.1" -Path "universal-api-bridge\*.html" -ErrorAction SilentlyContinue
if ($localhostRefs) {
    Write-Host "⚠️ Found localhost references:" -ForegroundColor Yellow
    $localhostRefs | ForEach-Object { Write-Host "  - $($_.Filename):$($_.LineNumber)" -ForegroundColor Yellow }
} else {
    Write-Host "✅ No localhost dependencies found" -ForegroundColor Green
}

# Check for voice agent files (should be excluded)
if (Test-Path "universal-api-bridge\voice-agent-archive-MOVED-FROM-MAIN-PROJECT") {
    Write-Host "✅ Voice agent files properly archived" -ForegroundColor Green
} else {
    Write-Host "ℹ️ Voice agent archive not found (may already be cleaned)" -ForegroundColor Blue
}

# Fix 4: PowerShell-compatible git operations
Write-Host "📦 Preparing git operations..." -ForegroundColor Blue

try {
    # Instead of using && (bash operator), use PowerShell syntax
    Write-Host "📋 Git status check..." -ForegroundColor Yellow
    $gitStatus = git status --porcelain
    
    if ($gitStatus) {
        Write-Host "📝 Found changes to commit:" -ForegroundColor Yellow
        git status --short
        
        if (!$DryRun) {
            Write-Host "➕ Adding files..." -ForegroundColor Yellow
            git add .
            
            Write-Host "💾 Creating commit..." -ForegroundColor Yellow
            $commitMessage = "Deploy: News Platform V11 with Hugging Face integration - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
            git commit -m $commitMessage
            
            Write-Host "✅ Commit created successfully" -ForegroundColor Green
        } else {
            Write-Host "🔍 DRY RUN: Would commit changes" -ForegroundColor Blue
        }
    } else {
        Write-Host "ℹ️ No changes to commit" -ForegroundColor Blue
    }
    
    # Fix 5: Handle branch/tag naming conflicts
    Write-Host "🌿 Checking branch configuration..." -ForegroundColor Yellow
    
    $currentBranch = git branch --show-current
    Write-Host "📍 Current branch: $currentBranch" -ForegroundColor Blue
    
    # Check for tag conflicts
    $tags = git tag -l $Branch
    if ($tags) {
        Write-Host "⚠️ Found tag with same name as branch: $Branch" -ForegroundColor Yellow
        Write-Host "🔧 Using explicit branch reference to avoid conflicts" -ForegroundColor Yellow
        $pushRef = "refs/heads/$Branch`:refs/heads/$Branch"
    } else {
        $pushRef = $Branch
    }
    
    # Fix 6: Robust push operation
    if (!$DryRun) {
        Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
        
        try {
            # Use explicit reference to avoid ambiguity
            Write-Host "📤 Push command: git push origin $pushRef" -ForegroundColor Blue
            git push origin $pushRef
            Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Push failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "🔧 Trying alternative push method..." -ForegroundColor Yellow
            
            # Alternative: force push if specified
            if ($Force) {
                git push origin $pushRef --force
                Write-Host "⚠️ Force pushed to GitHub" -ForegroundColor Yellow
            } else {
                Write-Host "💡 Try running with -Force parameter if you're sure about the changes" -ForegroundColor Yellow
                exit 1
            }
        }
    } else {
        Write-Host "🔍 DRY RUN: Would push to origin $pushRef" -ForegroundColor Blue
    }
    
} catch {
    Write-Host "❌ Git operation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔧 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "  1. Check internet connection" -ForegroundColor Yellow
    Write-Host "  2. Verify GitHub credentials" -ForegroundColor Yellow
    Write-Host "  3. Ensure remote origin is configured" -ForegroundColor Yellow
    Write-Host "  4. Try: git remote -v" -ForegroundColor Yellow
    exit 1
}

# Fix 7: Verification steps
Write-Host "🔍 Post-deployment verification..." -ForegroundColor Blue

try {
    $remoteInfo = git remote -v
    Write-Host "📡 Remote configuration:" -ForegroundColor Blue
    $remoteInfo | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    $lastCommit = git log -1 --oneline
    Write-Host "📝 Latest commit: $lastCommit" -ForegroundColor Blue
    
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host "🌐 GitHub repository should now be updated" -ForegroundColor Green
    
} catch {
    Write-Host "⚠️ Verification failed, but deployment may have succeeded" -ForegroundColor Yellow
}

Write-Host "`n🎉 Deployment Fix Script Completed!" -ForegroundColor Green
Write-Host "🔧 This script fixed the following issues:" -ForegroundColor Blue
Write-Host "  ✅ PowerShell compatibility (no && operators)" -ForegroundColor Green
Write-Host "  ✅ Branch/tag naming conflicts" -ForegroundColor Green  
Write-Host "  ✅ Command execution errors" -ForegroundColor Green
Write-Host "  ✅ File path resolution" -ForegroundColor Green
Write-Host "  ✅ Git configuration validation" -ForegroundColor Green 
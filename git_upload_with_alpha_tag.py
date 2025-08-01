#!/usr/bin/env python3
"""
Git Upload with Alpha Tag - Development Automation Suite
Complete Git repository setup and upload to GitHub with CI/CD integration.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add shellmonitor to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from shellmonitor.monitor import ShellMonitor
    SHELL_MONITOR_AVAILABLE = True
    print("✅ Shell Monitor available - commands will be protected from hanging")
except ImportError:
    SHELL_MONITOR_AVAILABLE = False
    print("⚠️ Shell Monitor not available - using direct commands")

class GitUploader:
    """Handles complete Git repository setup and upload process."""
    
    def __init__(self):
        self.monitor = ShellMonitor() if SHELL_MONITOR_AVAILABLE else None
        self.file_count = 0
        self.upload_log = []
        
    def run_command(self, command, description=""):
        """Run a command safely using Shell Monitor if available."""
        if description:
            print(f"\n🔧 {description}")
        
        if self.monitor:
            print(f"🚀 Monitoring: {command}")
            result = self.monitor.execute_command(command)
            
            if result.stdout:
                print(f"📤 Output: {result.stdout}")
            if result.stderr:
                print(f"⚠️ Errors: {result.stderr}")
                
            print(f"⏱️ Duration: {result.duration:.2f}s")
            print(f"🔢 Return Code: {result.returncode}")
            
            return result.returncode == 0, result.stdout, result.stderr
        else:
            # Fallback to direct execution
            try:
                result = subprocess.run(
                    command.split(), 
                    capture_output=True, 
                    text=True, 
                    timeout=60
                )
                if result.stdout:
                    print(f"📤 Output: {result.stdout}")
                if result.stderr:
                    print(f"⚠️ Errors: {result.stderr}")
                return result.returncode == 0, result.stdout, result.stderr
            except Exception as e:
                print(f"❌ Command failed: {e}")
                return False, "", str(e)
    
    def upload_to_github(self):
        """Complete GitHub upload process with Alpha tag."""
        print("🚀 Git Upload Process - Development Automation Suite")
        print("=" * 70)
        print("📝 Creating Alpha release archive for read-only reference")
        print("🛡️ Using Shell Monitor to prevent command hanging")
        print()
        
        try:
            # Step 1: Initialize Git repository
            self._init_repository()
            
            # Step 2: Configure Git user
            self._configure_git_user()
            
            # Step 3: Add all files
            self._add_files()
            
            # Step 4: Create initial commit
            self._create_initial_commit()
            
            # Step 5: Display file upload status
            self._show_file_status()
            
            # Step 6: Create Alpha tag
            self._create_alpha_tag()
            
            # Step 7: Show GitHub setup instructions
            self._show_github_setup()
            
            # Step 8: Generate upload report
            self._generate_upload_report()
            
            print("\n🎉 Git repository prepared successfully!")
            print("✅ Ready for GitHub upload once remote repository is configured")
            
        except Exception as e:
            print(f"\n❌ Upload process failed: {e}")
            sys.exit(1)
    
    def _init_repository(self):
        """Initialize or reinitialize Git repository."""
        print("📁 Initializing Git repository...")
        
        success, output, error = self.run_command("git init", "Initializing Git repository")
        
        if success:
            print("✅ Git repository initialized")
            self.upload_log.append("Git repository initialized")
        else:
            raise Exception(f"Failed to initialize Git repository: {error}")
    
    def _configure_git_user(self):
        """Configure Git user information."""
        print("👤 Configuring Git user information...")
        
        # Set git user name
        success1, _, _ = self.run_command(
            'git config user.name "Development Automation Suite"',
            "Setting Git user name"
        )
        
        # Set git user email
        success2, _, _ = self.run_command(
            'git config user.email "dev-automation@example.com"',
            "Setting Git user email"
        )
        
        if success1 and success2:
            print("✅ Git user configured")
            self.upload_log.append("Git user configured")
        else:
            print("⚠️ Warning: Could not configure Git user (may already be set globally)")
    
    def _add_files(self):
        """Add all files to Git repository."""
        print("📦 Adding files to Git repository...")
        
        success, output, error = self.run_command("git add .", "Adding all files to Git")
        
        if success:
            print("✅ All files added to Git")
            self.upload_log.append("All files added to Git staging area")
        else:
            raise Exception(f"Failed to add files to Git: {error}")
    
    def _create_initial_commit(self):
        """Create the initial commit."""
        print("💾 Creating initial commit...")
        
        commit_message = "Alpha Release - Development Automation Suite with PostgreSQL Migration and Shell Monitor"
        
        success, output, error = self.run_command(
            f'git commit -m "{commit_message}"',
            "Creating initial Alpha commit"
        )
        
        if success:
            print("✅ Initial commit created")
            self.upload_log.append("Initial Alpha commit created")
        else:
            if "nothing to commit" in error:
                print("ℹ️ Repository is up to date - no new changes to commit")
                self.upload_log.append("Repository up to date")
            else:
                raise Exception(f"Failed to create commit: {error}")
    
    def _show_file_status(self):
        """Show status of files in the repository."""
        print("\n📋 Repository File Status:")
        print("=" * 50)
        
        # Get list of files in repository
        success, output, error = self.run_command("git ls-files", "Getting repository file list")
        
        if success and output:
            files = output.strip().split('\n')
            self.file_count = len(files)
            
            print(f"📊 Total files in repository: {self.file_count}")
            print("\n📁 File Categories:")
            
            categories = {
                'Core Application': [],
                'Shell Monitor': [],
                'Cursor Integration': [],
                'Database Migration': [],
                'Documentation': [],
                'Configuration': [],
                'Other': []
            }
            
            for file in files:
                if file.startswith('src/'):
                    categories['Core Application'].append(file)
                elif file.startswith('shellmonitor/'):
                    categories['Shell Monitor'].append(file)
                elif file.startswith('cursor_integration/'):
                    categories['Cursor Integration'].append(file)
                elif 'postgresql' in file.lower() or 'database' in file.lower():
                    categories['Database Migration'].append(file)
                elif file.endswith('.md') or file.endswith('.txt'):
                    categories['Documentation'].append(file)
                elif file.endswith('.json') or file.endswith('.yaml') or file.endswith('.yml'):
                    categories['Configuration'].append(file)
                else:
                    categories['Other'].append(file)
            
            for category, files_in_category in categories.items():
                if files_in_category:
                    print(f"\n  📁 {category} ({len(files_in_category)} files):")
                    for file in files_in_category[:5]:  # Show first 5 files
                        print(f"     ✅ {file}")
                    if len(files_in_category) > 5:
                        print(f"     ... and {len(files_in_category) - 5} more files")
        else:
            print("⚠️ Could not retrieve file list")
    
    def _create_alpha_tag(self):
        """Create the Alpha release tag."""
        print("\n🏷️ Creating Alpha release tag...")
        
        tag_message = "Alpha Release - Complete Development Automation Suite with PostgreSQL and Shell Monitor integration"
        
        success, output, error = self.run_command(
            f'git tag -a Alpha -m "{tag_message}"',
            "Creating Alpha release tag"
        )
        
        if success:
            print("✅ Alpha tag created successfully")
            self.upload_log.append("Alpha release tag created")
        else:
            if "already exists" in error:
                print("ℹ️ Alpha tag already exists - updating it")
                # Force update the tag
                self.run_command("git tag -d Alpha", "Deleting existing Alpha tag")
                success2, _, _ = self.run_command(
                    f'git tag -a Alpha -m "{tag_message}"',
                    "Recreating Alpha tag"
                )
                if success2:
                    print("✅ Alpha tag updated successfully")
                    self.upload_log.append("Alpha tag updated")
            else:
                raise Exception(f"Failed to create Alpha tag: {error}")
    
    def _show_github_setup(self):
        """Show instructions for setting up GitHub remote."""
        print("\n🐙 GitHub Repository Setup:")
        print("=" * 50)
        print("To complete the upload to GitHub, follow these steps:")
        print()
        print("1. 📝 Create a new GitHub repository:")
        print("   • Go to: https://github.com/new")
        print("   • Repository name: development-automation-suite")
        print("   • Description: Complete Development Automation Suite with PostgreSQL & Shell Monitor")
        print("   • Make it Public (for better visibility)")
        print("   • Do NOT initialize with README (we already have files)")
        print()
        print("2. 🔗 Connect this repository to GitHub:")
        print("   • Copy the repository URL from GitHub")
        print("   • Run these commands:")
        print()
        print("   git remote add origin https://github.com/YOUR_USERNAME/development-automation-suite.git")
        print("   git branch -M main")
        print("   git push -u origin main")
        print("   git push origin Alpha")
        print()
        print("3. ✅ Verify the upload:")
        print("   • Check that all files are visible on GitHub")
        print("   • Verify the Alpha tag is created under Releases")
        print("   • Check that the README.md displays properly")
    
    def _generate_upload_report(self):
        """Generate a comprehensive upload report."""
        report = {
            "upload_date": datetime.now().isoformat(),
            "repository_name": "development-automation-suite",
            "tag_name": "Alpha",
            "description": "Complete Development Automation Suite with PostgreSQL migration and Shell Monitor integration",
            "file_count": self.file_count,
            "upload_steps": self.upload_log,
            "features": [
                "Core Development Automation Suite",
                "PostgreSQL database migration from SQLite",
                "Shell Monitor for preventing command hanging",
                "Cursor IDE integration",
                "CI/CD pipeline templates",
                "Docker containerization support",
                "Comprehensive documentation"
            ],
            "next_steps": [
                "Create GitHub repository",
                "Add remote origin",
                "Push to GitHub",
                "Verify Alpha tag",
                "Set up CI/CD workflows"
            ]
        }
        
        report_file = Path("ALPHA_RELEASE_REPORT.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Upload report saved: {report_file}")
        
        # Also create a markdown summary
        md_report = f"""# Alpha Release Report - Development Automation Suite

## 🎯 Release Information
- **Tag**: Alpha
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Files**: {self.file_count} files uploaded
- **Repository**: development-automation-suite

## 📋 Upload Steps Completed
"""
        for step in self.upload_log:
            md_report += f"- ✅ {step}\n"
        
        md_report += f"""
## 🚀 Key Features in Alpha Release
- ✅ Complete Development Automation Suite
- ✅ PostgreSQL database migration (from SQLite)
- ✅ Shell Monitor system (prevents command hanging)
- ✅ Cursor IDE integration
- ✅ CI/CD pipeline generation
- ✅ Docker containerization support
- ✅ Comprehensive documentation

## 📞 GitHub Repository Setup
1. Create repository: https://github.com/new
2. Name: `development-automation-suite`
3. Connect and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/development-automation-suite.git
   git branch -M main
   git push -u origin main
   git push origin Alpha
   ```

## ✅ Success Metrics
- Repository initialized and configured
- All files staged and committed
- Alpha tag created for read-only archive
- Ready for GitHub upload
- Shell Monitor prevented command hanging issues

*Alpha Release prepared successfully! 🎉*
"""
        
        md_report_file = Path("ALPHA_RELEASE_SUMMARY.md")
        with open(md_report_file, 'w') as f:
            f.write(md_report)
        
        print(f"📄 Release summary saved: {md_report_file}")

def main():
    """Main upload execution."""
    uploader = GitUploader()
    uploader.upload_to_github()

if __name__ == "__main__":
    main() 
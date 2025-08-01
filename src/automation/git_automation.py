"""
Git Automation for Development Automation Suite
Provides automated Git operations and workflow management.
"""

import os
import subprocess
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.config_manager import ConfigManager

class GitAutomation:
    """Handles automated Git operations and workflows."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.auto_commit_thread = None
        self.stop_auto_commit = threading.Event()
        self.file_watcher = None
    
    def initialize_repository(self, project_path: Path) -> bool:
        """Initialize a new Git repository."""
        try:
            # Check if already a git repo
            if (project_path / ".git").exists():
                self.logger.info("Git repository already exists")
                return True
            
            # Initialize repository
            subprocess.run(["git", "init"], cwd=project_path, check=True)
            self.logger.info("Git repository initialized")
            
            # Set up initial configuration
            self._setup_git_config(project_path)
            
            # Install hooks if configured
            if self.config_manager.development.pre_commit_hooks:
                self.install_pre_commit_hooks(project_path)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to initialize Git repository: {e}")
            return False
    
    def _setup_git_config(self, project_path: Path):
        """Setup Git configuration for the repository."""
        config = self.config_manager.git
        
        try:
            if config.username:
                subprocess.run(
                    ["git", "config", "user.name", config.username],
                    cwd=project_path, check=True
                )
            
            if config.email:
                subprocess.run(
                    ["git", "config", "user.email", config.email],
                    cwd=project_path, check=True
                )
            
            # Set default branch name
            subprocess.run(
                ["git", "config", "init.defaultBranch", config.default_branch],
                cwd=project_path, check=True
            )
            
            self.logger.info("Git configuration setup completed")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to setup Git configuration: {e}")
    
    def install_pre_commit_hooks(self, project_path: Path) -> bool:
        """Install pre-commit hooks."""
        try:
            # Check if pre-commit is available
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
            
            # Install pre-commit hooks
            subprocess.run(
                ["pre-commit", "install"],
                cwd=project_path, check=True
            )
            
            # Install commit-msg hook for conventional commits
            subprocess.run(
                ["pre-commit", "install", "--hook-type", "commit-msg"],
                cwd=project_path, check=True
            )
            
            self.logger.info("Pre-commit hooks installed successfully")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Failed to install pre-commit hooks: {e}")
            return False
    
    def start_auto_commit(self, project_path: Path, interval_minutes: int = 30):
        """Start automatic commit monitoring."""
        if self.auto_commit_thread and self.auto_commit_thread.is_alive():
            self.logger.warning("Auto-commit is already running")
            return
        
        self.stop_auto_commit.clear()
        self.auto_commit_thread = threading.Thread(
            target=self._auto_commit_worker,
            args=(project_path, interval_minutes)
        )
        self.auto_commit_thread.daemon = True
        self.auto_commit_thread.start()
        
        self.logger.info(f"Auto-commit started with {interval_minutes} minute interval")
    
    def stop_auto_commit_monitoring(self):
        """Stop automatic commit monitoring."""
        if self.auto_commit_thread:
            self.stop_auto_commit.set()
            self.auto_commit_thread.join(timeout=5)
            self.logger.info("Auto-commit monitoring stopped")
    
    def _auto_commit_worker(self, project_path: Path, interval_minutes: int):
        """Worker thread for automatic commits."""
        while not self.stop_auto_commit.wait(interval_minutes * 60):
            try:
                if self._has_changes(project_path):
                    self._perform_auto_commit(project_path)
            except Exception as e:
                self.logger.error(f"Auto-commit error: {e}")
    
    def _has_changes(self, project_path: Path) -> bool:
        """Check if there are changes to commit."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def _perform_auto_commit(self, project_path: Path):
        """Perform an automatic commit."""
        try:
            # Add all changes
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)
            
            # Create commit message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = self.config_manager.git.commit_message_template.format(
                description=f"Auto-commit on {timestamp}"
            )
            
            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_path, check=True
            )
            
            self.logger.info(f"Auto-commit completed: {message}")
            
            # Push if remote is configured
            if self.config_manager.git.remote_origin:
                self._safe_push(project_path)
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Auto-commit failed: {e}")
    
    def _safe_push(self, project_path: Path):
        """Safely push changes to remote."""
        try:
            # Check if remote exists
            subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path, check=True, capture_output=True
            )
            
            # Push changes
            subprocess.run(
                ["git", "push", "origin", self.config_manager.git.default_branch],
                cwd=project_path, check=True, capture_output=True
            )
            
            self.logger.info("Changes pushed to remote successfully")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to push to remote: {e}")
    
    def create_feature_branch(self, project_path: Path, feature_name: str) -> bool:
        """Create a new feature branch."""
        try:
            branch_name = f"feature/{feature_name.lower().replace(' ', '-')}"
            
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_path, check=True
            )
            
            self.logger.info(f"Created feature branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create feature branch: {e}")
            return False
    
    def merge_feature_branch(self, project_path: Path, branch_name: str, 
                           delete_after_merge: bool = True) -> bool:
        """Merge a feature branch back to main."""
        try:
            main_branch = self.config_manager.git.default_branch
            
            # Switch to main branch
            subprocess.run(
                ["git", "checkout", main_branch],
                cwd=project_path, check=True
            )
            
            # Pull latest changes
            subprocess.run(
                ["git", "pull", "origin", main_branch],
                cwd=project_path, check=True
            )
            
            # Merge feature branch
            subprocess.run(
                ["git", "merge", "--no-ff", branch_name],
                cwd=project_path, check=True
            )
            
            # Delete branch if requested
            if delete_after_merge:
                subprocess.run(
                    ["git", "branch", "-d", branch_name],
                    cwd=project_path, check=True
                )
            
            self.logger.info(f"Merged feature branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to merge feature branch: {e}")
            return False
    
    def create_release_tag(self, project_path: Path, version: str, 
                          message: Optional[str] = None) -> bool:
        """Create a release tag."""
        try:
            tag_name = f"v{version}"
            tag_message = message or f"Release {version}"
            
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                cwd=project_path, check=True
            )
            
            # Push tag to remote
            if self.config_manager.git.remote_origin:
                subprocess.run(
                    ["git", "push", "origin", tag_name],
                    cwd=project_path, check=True
                )
            
            self.logger.info(f"Created release tag: {tag_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create release tag: {e}")
            return False
    
    def get_repository_status(self, project_path: Path) -> Dict[str, Any]:
        """Get comprehensive repository status."""
        status = {
            'is_repo': False,
            'current_branch': None,
            'changes': [],
            'commits_ahead': 0,
            'commits_behind': 0,
            'tags': [],
            'remotes': [],
            'last_commit': None
        }
        
        try:
            # Check if it's a git repository
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=project_path, check=True, capture_output=True
            )
            status['is_repo'] = True
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            status['current_branch'] = result.stdout.strip()
            
            # Get changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            status['changes'] = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Get tags
            result = subprocess.run(
                ["git", "tag", "--list"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            status['tags'] = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            
            # Get remotes
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            status['remotes'] = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Get last commit
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
                cwd=project_path, capture_output=True, text=True, check=True
            )
            if result.stdout:
                parts = result.stdout.split('|')
                if len(parts) == 4:
                    status['last_commit'] = {
                        'hash': parts[0][:8],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    }
            
        except subprocess.CalledProcessError:
            pass
        
        return status
    
    def setup_github_integration(self, project_path: Path, repo_url: str) -> bool:
        """Setup GitHub integration for the repository."""
        try:
            # Add remote origin
            subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=project_path, check=True
            )
            
            # Push to remote
            subprocess.run(
                ["git", "push", "-u", "origin", self.config_manager.git.default_branch],
                cwd=project_path, check=True
            )
            
            self.logger.info(f"GitHub integration setup completed: {repo_url}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to setup GitHub integration: {e}")
            return False
    
    def generate_gitignore(self, project_path: Path, language: str) -> bool:
        """Generate appropriate .gitignore file."""
        gitignore_templates = {
            'python': '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
.dev_automation/
logs/
''',
            'javascript': '''# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory
coverage/

# Build outputs
build/
dist/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
.dev_automation/
logs/
''',
            'generic': '''# Build outputs
build/
dist/
*.o
*.obj
*.exe

# Dependencies
node_modules/
vendor/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Project specific
.dev_automation/
'''
        }
        
        try:
            gitignore_content = gitignore_templates.get(language, gitignore_templates['generic'])
            gitignore_path = project_path / ".gitignore"
            
            gitignore_path.write_text(gitignore_content)
            self.logger.info(f"Generated .gitignore for {language}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate .gitignore: {e}")
            return False
    
    def run_git_command(self, project_path: Path, command: List[str]) -> Dict[str, Any]:
        """Run a Git command and return the result."""
        try:
            full_command = ["git"] + command
            result = subprocess.run(
                full_command,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'stdout': e.stdout,
                'stderr': e.stderr,
                'returncode': e.returncode,
                'error': str(e)
            } 
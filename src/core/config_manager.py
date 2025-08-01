"""
Configuration Manager for Development Automation Suite
Handles all configuration with intelligent defaults and validation.
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import yaml

@dataclass
class ProjectConfig:
    """Configuration for project settings."""
    name: str = ""
    description: str = ""
    language: str = "python"
    framework: str = ""
    version: str = "1.0.0"
    author: str = ""
    license: str = "MIT"
    python_version: str = "3.9+"

@dataclass
class GitConfig:
    """Configuration for Git settings."""
    username: str = ""
    email: str = ""
    default_branch: str = "main"
    auto_commit: bool = True
    commit_message_template: str = "feat: {description}"
    remote_origin: str = ""

@dataclass
class CICDConfig:
    """Configuration for CI/CD pipeline."""
    platform: str = "github_actions"  # github_actions, gitlab_ci, jenkins
    auto_test: bool = True
    auto_deploy: bool = False
    test_command: str = "pytest"
    build_command: str = ""
    deploy_command: str = ""
    environments: list = field(default_factory=lambda: ["development", "staging", "production"])

@dataclass
class DatabaseConfig:
    """Configuration for database settings."""
    type: str = "postgresql"  # postgresql, sqlite, mysql, mongodb
    host: str = "localhost"
    port: int = 5432
    name: str = "dev_automation_db"
    username: str = "postgres"
    password: str = "postgres"
    auto_migration: bool = True
    backup_schedule: str = "daily"  # daily, weekly, monthly

@dataclass
class MonitoringConfig:
    """Configuration for monitoring and logging."""
    log_level: str = "INFO"
    performance_monitoring: bool = True
    error_tracking: bool = True
    metrics_collection: bool = True
    notification_webhook: str = ""

@dataclass
class DevelopmentConfig:
    """Configuration for development tools."""
    code_formatter: str = "black"  # black, autopep8, yapf
    linter: str = "flake8"  # flake8, pylint, ruff
    type_checker: str = "mypy"  # mypy, pyright
    pre_commit_hooks: bool = True
    auto_documentation: bool = True
    code_review_automation: bool = True
    python_path: str = ""
    node_version: str = ""
    npm_version: str = ""
    tkinter_available: bool = False
    platform: str = ""
    platform_version: str = ""

class ConfigManager:
    """Manages all configuration for the development automation suite."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".dev_automation"
        self.config_file = self.config_dir / "config.yaml"
        self.logger = logging.getLogger(__name__)
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize configurations with defaults
        self.project = ProjectConfig()
        self.git = GitConfig()
        self.cicd = CICDConfig()
        self.database = DatabaseConfig()
        self.monitoring = MonitoringConfig()
        self.development = DevelopmentConfig()
        
        # Load existing configuration if available
        self.load_config()
        
        # Auto-detect and populate some settings
        self._auto_detect_settings()
    
    def _auto_detect_settings(self):
        """Auto-detect system settings and populate default configurations."""
        try:
            # Detect Git user info
            try:
                result = subprocess.run(['git', 'config', 'user.name'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.git.username = result.stdout.strip()
            except:
                pass
            
            try:
                result = subprocess.run(['git', 'config', 'user.email'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.git.email = result.stdout.strip()
            except:
                pass
            
            # Detect Python version and path
            try:
                result = subprocess.run([sys.executable, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    # Extract version number (e.g., "Python 3.13.2" -> "3.13.2")
                    version_parts = version_info.split()
                    if len(version_parts) >= 2:
                        self.project.python_version = version_parts[1] + "+"
                        self.development.python_path = sys.executable
                        
                # Verify tkinter support
                try:
                    import tkinter
                    self.development.tkinter_available = True
                except ImportError:
                    self.development.tkinter_available = False
                    
            except Exception as e:
                self.logger.warning(f"Could not detect Python version: {e}")
            
            # Detect Node.js version if available
            try:
                result = subprocess.run(['node', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    node_version = result.stdout.strip().lstrip('v')  # Remove 'v' prefix
                    self.development.node_version = node_version
                    
                # Check npm version
                result = subprocess.run(['npm', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    npm_version = result.stdout.strip()
                    self.development.npm_version = npm_version
                    
            except Exception as e:
                self.logger.warning(f"Could not detect Node.js: {e}")
            
            # Detect system info
            import platform
            self.development.platform = platform.system()
            self.development.platform_version = platform.version()
            
        except Exception as e:
            self.logger.error(f"Error in auto-detection: {e}")
    
    def load_config(self):
        """Load configuration from file."""
        if not self.config_file.exists():
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Load each configuration section
            if 'project' in data:
                self.project = ProjectConfig(**data['project'])
            if 'git' in data:
                self.git = GitConfig(**data['git'])
            if 'cicd' in data:
                self.cicd = CICDConfig(**data['cicd'])
            if 'database' in data:
                self.database = DatabaseConfig(**data['database'])
            if 'monitoring' in data:
                self.monitoring = MonitoringConfig(**data['monitoring'])
            if 'development' in data:
                self.development = DevelopmentConfig(**data['development'])
                
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            config_data = {
                'project': asdict(self.project),
                'git': asdict(self.git),
                'cicd': asdict(self.cicd),
                'database': asdict(self.database),
                'monitoring': asdict(self.monitoring),
                'development': asdict(self.development)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            'project': asdict(self.project),
            'git': asdict(self.git),
            'cicd': asdict(self.cicd),
            'database': asdict(self.database),
            'monitoring': asdict(self.monitoring),
            'development': asdict(self.development)
        }
    
    def update_config(self, section: str, updates: Dict[str, Any]):
        """Update a specific configuration section."""
        config_map = {
            'project': self.project,
            'git': self.git,
            'cicd': self.cicd,
            'database': self.database,
            'monitoring': self.monitoring,
            'development': self.development
        }
        
        if section not in config_map:
            raise ValueError(f"Unknown configuration section: {section}")
        
        config_obj = config_map[section]
        for key, value in updates.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
            else:
                self.logger.warning(f"Unknown configuration key: {key} in section {section}")
        
        self.save_config()
    
    def validate_config(self) -> list:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate project config
        if not self.project.name:
            issues.append("Project name is required")
        
        # Validate git config
        if self.git.auto_commit and not self.git.email:
            issues.append("Git email is required for auto-commit")
        
        # Validate database config
        if self.database.type in ['postgresql', 'mysql'] and not self.database.username:
            issues.append(f"Username is required for {self.database.type} database")
        
        return issues
    
    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return Path.cwd()
    
    def get_templates_dir(self) -> Path:
        """Get the templates directory."""
        templates_dir = self.config_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        return templates_dir 
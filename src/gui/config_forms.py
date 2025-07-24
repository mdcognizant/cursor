"""
Configuration Forms for Development Automation Suite
Provides user-friendly forms for all configuration settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List

from src.core.config_manager import ConfigManager

class ConfigurationTabs:
    """Manages all configuration tabs in a notebook widget."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Create notebook for configuration sections
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create configuration forms
        self.project_form = ProjectConfigForm(self.notebook, config_manager)
        self.git_form = GitConfigForm(self.notebook, config_manager)
        self.cicd_form = CICDConfigForm(self.notebook, config_manager)
        self.database_form = DatabaseConfigForm(self.notebook, config_manager)
        self.monitoring_form = MonitoringConfigForm(self.notebook, config_manager)
        self.development_form = DevelopmentConfigForm(self.notebook, config_manager)
        
        # Add forms to notebook
        self.notebook.add(self.project_form.frame, text="Project")
        self.notebook.add(self.git_form.frame, text="Git & Version Control")
        self.notebook.add(self.cicd_form.frame, text="CI/CD Pipeline")
        self.notebook.add(self.database_form.frame, text="Database")
        self.notebook.add(self.monitoring_form.frame, text="Monitoring & Logs")
        self.notebook.add(self.development_form.frame, text="Development Tools")
    
    def load_configuration(self):
        """Load configuration into all forms."""
        forms = [
            self.project_form, self.git_form, self.cicd_form,
            self.database_form, self.monitoring_form, self.development_form
        ]
        for form in forms:
            form.load_configuration()
    
    def save_configuration(self):
        """Save configuration from all forms."""
        forms = [
            self.project_form, self.git_form, self.cicd_form,
            self.database_form, self.monitoring_form, self.development_form
        ]
        for form in forms:
            form.save_configuration()

class BaseConfigForm:
    """Base class for configuration forms."""
    
    def __init__(self, parent, config_manager: ConfigManager, title: str):
        self.config_manager = config_manager
        self.title = title
        self.widgets = {}
        
        # Create scrollable frame
        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_section(self, title: str, description: str = "") -> ttk.Frame:
        """Create a section with title and optional description."""
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=title, padding=15)
        section_frame.pack(fill='x', padx=10, pady=10)
        
        if description:
            desc_label = ttk.Label(section_frame, text=description, 
                                 style='Help.TLabel', wraplength=400)
            desc_label.pack(anchor='w', pady=(0, 10))
        
        return section_frame
    
    def add_text_field(self, parent: ttk.Frame, label: str, key: str, 
                      help_text: str = "", width: int = 40) -> ttk.Entry:
        """Add a text input field."""
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill='x', pady=5)
        
        ttk.Label(field_frame, text=label, style='Subtitle.TLabel').pack(anchor='w')
        if help_text:
            ttk.Label(field_frame, text=help_text, style='Help.TLabel', 
                     wraplength=400).pack(anchor='w')
        
        entry = ttk.Entry(field_frame, width=width)
        entry.pack(anchor='w', pady=(5, 0))
        
        self.widgets[key] = entry
        return entry
    
    def add_checkbox(self, parent: ttk.Frame, label: str, key: str, 
                    help_text: str = "") -> ttk.Checkbutton:
        """Add a checkbox field."""
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill='x', pady=5)
        
        var = tk.BooleanVar()
        checkbox = ttk.Checkbutton(field_frame, text=label, variable=var)
        checkbox.pack(anchor='w')
        
        if help_text:
            ttk.Label(field_frame, text=help_text, style='Help.TLabel', 
                     wraplength=400).pack(anchor='w', padx=(20, 0))
        
        self.widgets[key] = (checkbox, var)
        return checkbox
    
    def add_combobox(self, parent: ttk.Frame, label: str, key: str, 
                    values: List[str], help_text: str = "", width: int = 30) -> ttk.Combobox:
        """Add a dropdown selection field."""
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill='x', pady=5)
        
        ttk.Label(field_frame, text=label, style='Subtitle.TLabel').pack(anchor='w')
        if help_text:
            ttk.Label(field_frame, text=help_text, style='Help.TLabel', 
                     wraplength=400).pack(anchor='w')
        
        combobox = ttk.Combobox(field_frame, values=values, width=width, state='readonly')
        combobox.pack(anchor='w', pady=(5, 0))
        
        self.widgets[key] = combobox
        return combobox

class ProjectConfigForm(BaseConfigForm):
    """Form for project configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "Project Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the project configuration form."""
        # Basic Information
        basic_section = self.create_section(
            "Basic Information",
            "Tell us about your project. This information will be used throughout the automation."
        )
        
        self.add_text_field(basic_section, "Project Name", "name",
                           "A short, descriptive name for your project (e.g., 'My Web App')")
        
        self.add_text_field(basic_section, "Description", "description",
                           "Brief description of what your project does", width=60)
        
        self.add_text_field(basic_section, "Version", "version",
                           "Starting version number (usually 1.0.0)")
        
        self.add_text_field(basic_section, "Author", "author",
                           "Your name or organization name")
        
        # Technical Details
        tech_section = self.create_section(
            "Technical Details",
            "Choose the technologies your project will use."
        )
        
        self.add_combobox(tech_section, "Primary Language", "language",
                         ["python", "javascript", "typescript", "java", "go", "rust", "php"],
                         "The main programming language for your project")
        
        self.add_combobox(tech_section, "Framework", "framework",
                         ["", "flask", "django", "fastapi", "react", "vue", "angular", "express"],
                         "Web framework or library (leave empty if not using one)")
        
        self.add_text_field(tech_section, "Python Version", "python_version",
                           "Minimum Python version required (e.g., 3.9+)")
        
        # Legal
        legal_section = self.create_section(
            "Legal & Licensing",
            "Choose how others can use your code."
        )
        
        self.add_combobox(legal_section, "License", "license",
                         ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "ISC"],
                         "License for your project (MIT is most permissive)")
    
    def load_configuration(self):
        """Load project configuration into form."""
        config = self.config_manager.project
        
        text_fields = ["name", "description", "version", "author", "python_version"]
        for field in text_fields:
            if field in self.widgets:
                self.widgets[field].delete(0, tk.END)
                self.widgets[field].insert(0, getattr(config, field, ""))
        
        combo_fields = ["language", "framework", "license"]
        for field in combo_fields:
            if field in self.widgets:
                self.widgets[field].set(getattr(config, field, ""))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        text_fields = ["name", "description", "version", "author", "python_version"]
        for field in text_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get().strip()
        
        combo_fields = ["language", "framework", "license"]
        for field in combo_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get()
        
        self.config_manager.update_config("project", updates)

class GitConfigForm(BaseConfigForm):
    """Form for Git configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "Git Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the Git configuration form."""
        # User Information
        user_section = self.create_section(
            "Git User Information",
            "Your Git identity for commits and version control."
        )
        
        self.add_text_field(user_section, "Your Name", "username",
                           "Full name for Git commits (auto-detected if already configured)")
        
        self.add_text_field(user_section, "Email Address", "email",
                           "Email for Git commits (auto-detected if already configured)")
        
        # Repository Settings
        repo_section = self.create_section(
            "Repository Settings",
            "Configure how Git repositories are managed."
        )
        
        self.add_text_field(repo_section, "Default Branch Name", "default_branch",
                           "Name for the main branch (usually 'main' or 'master')")
        
        self.add_text_field(repo_section, "Remote Origin URL", "remote_origin",
                           "GitHub/GitLab repository URL (optional)", width=60)
        
        # Automation
        auto_section = self.create_section(
            "Automation Settings",
            "Let the system help with Git operations."
        )
        
        self.add_checkbox(auto_section, "Automatic Commits", "auto_commit",
                         "Automatically commit changes during project generation")
        
        self.add_text_field(auto_section, "Commit Message Template", "commit_message_template",
                           "Template for commit messages (use {description} for auto-replacement)", width=60)
    
    def load_configuration(self):
        """Load Git configuration into form."""
        config = self.config_manager.git
        
        text_fields = ["username", "email", "default_branch", "remote_origin", "commit_message_template"]
        for field in text_fields:
            if field in self.widgets:
                self.widgets[field].delete(0, tk.END)
                self.widgets[field].insert(0, getattr(config, field, ""))
        
        if "auto_commit" in self.widgets:
            _, var = self.widgets["auto_commit"]
            var.set(getattr(config, "auto_commit", False))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        text_fields = ["username", "email", "default_branch", "remote_origin", "commit_message_template"]
        for field in text_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get().strip()
        
        if "auto_commit" in self.widgets:
            _, var = self.widgets["auto_commit"]
            updates["auto_commit"] = var.get()
        
        self.config_manager.update_config("git", updates)

class CICDConfigForm(BaseConfigForm):
    """Form for CI/CD configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "CI/CD Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the CI/CD configuration form."""
        # Platform Selection
        platform_section = self.create_section(
            "CI/CD Platform",
            "Choose your continuous integration and deployment platform."
        )
        
        self.add_combobox(platform_section, "Platform", "platform",
                         ["github_actions", "gitlab_ci", "jenkins", "circle_ci"],
                         "Where your code will be automatically built and tested")
        
        # Testing Configuration
        test_section = self.create_section(
            "Testing Settings",
            "Configure automatic testing for your code."
        )
        
        self.add_checkbox(test_section, "Automatic Testing", "auto_test",
                         "Run tests automatically when code is pushed")
        
        self.add_text_field(test_section, "Test Command", "test_command",
                           "Command to run your tests (e.g., 'pytest', 'npm test')")
        
        # Build Configuration
        build_section = self.create_section(
            "Build Settings",
            "Configure how your application is built."
        )
        
        self.add_text_field(build_section, "Build Command", "build_command",
                           "Command to build your application (leave empty if not needed)")
        
        # Deployment
        deploy_section = self.create_section(
            "Deployment Settings",
            "Configure automatic deployment (advanced users only)."
        )
        
        self.add_checkbox(deploy_section, "Automatic Deployment", "auto_deploy",
                         "Deploy automatically after successful tests (use with caution)")
        
        self.add_text_field(deploy_section, "Deploy Command", "deploy_command",
                           "Command to deploy your application")
    
    def load_configuration(self):
        """Load CI/CD configuration into form."""
        config = self.config_manager.cicd
        
        if "platform" in self.widgets:
            self.widgets["platform"].set(getattr(config, "platform", ""))
        
        text_fields = ["test_command", "build_command", "deploy_command"]
        for field in text_fields:
            if field in self.widgets:
                self.widgets[field].delete(0, tk.END)
                self.widgets[field].insert(0, getattr(config, field, ""))
        
        bool_fields = ["auto_test", "auto_deploy"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                var.set(getattr(config, field, False))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        if "platform" in self.widgets:
            updates["platform"] = self.widgets["platform"].get()
        
        text_fields = ["test_command", "build_command", "deploy_command"]
        for field in text_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get().strip()
        
        bool_fields = ["auto_test", "auto_deploy"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                updates[field] = var.get()
        
        self.config_manager.update_config("cicd", updates)

class DatabaseConfigForm(BaseConfigForm):
    """Form for database configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "Database Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the database configuration form."""
        # Database Type
        type_section = self.create_section(
            "Database Type",
            "Choose what type of database your project will use."
        )
        
        self.add_combobox(type_section, "Database Type", "type",
                         ["postgresql", "sqlite", "mysql", "mongodb"],
                         "PostgreSQL is recommended for robust applications, SQLite for simple projects")
        
        # Connection Settings
        conn_section = self.create_section(
            "Connection Settings",
            "Configure how to connect to your database (not needed for SQLite)."
        )
        
        self.add_text_field(conn_section, "Database Name", "name",
                           "Name of your database")
        
        self.add_text_field(conn_section, "Host", "host",
                           "Database server address (usually 'localhost' for local)")
        
        self.add_text_field(conn_section, "Port", "port",
                           "Database port (5432 for PostgreSQL, 3306 for MySQL)")
        
        self.add_text_field(conn_section, "Username", "username",
                           "Database username")
        
        # Automation
        auto_section = self.create_section(
            "Database Automation",
            "Let the system manage database tasks automatically."
        )
        
        self.add_checkbox(auto_section, "Automatic Migrations", "auto_migration",
                         "Apply database schema changes automatically")
        
        self.add_combobox(auto_section, "Backup Schedule", "backup_schedule",
                         ["daily", "weekly", "monthly"],
                         "How often to backup your database")
    
    def load_configuration(self):
        """Load database configuration into form."""
        config = self.config_manager.database
        
        combo_fields = ["type", "backup_schedule"]
        for field in combo_fields:
            if field in self.widgets:
                self.widgets[field].set(getattr(config, field, ""))
        
        text_fields = ["name", "host", "username"]
        for field in text_fields:
            if field in self.widgets:
                self.widgets[field].delete(0, tk.END)
                self.widgets[field].insert(0, getattr(config, field, ""))
        
        if "port" in self.widgets:
            self.widgets["port"].delete(0, tk.END)
            self.widgets["port"].insert(0, str(getattr(config, "port", "")))
        
        if "auto_migration" in self.widgets:
            _, var = self.widgets["auto_migration"]
            var.set(getattr(config, "auto_migration", False))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        combo_fields = ["type", "backup_schedule"]
        for field in combo_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get()
        
        text_fields = ["name", "host", "username"]
        for field in text_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get().strip()
        
        if "port" in self.widgets:
            try:
                updates["port"] = int(self.widgets["port"].get().strip() or "0")
            except ValueError:
                updates["port"] = 5432
        
        if "auto_migration" in self.widgets:
            _, var = self.widgets["auto_migration"]
            updates["auto_migration"] = var.get()
        
        self.config_manager.update_config("database", updates)

class MonitoringConfigForm(BaseConfigForm):
    """Form for monitoring configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "Monitoring Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the monitoring configuration form."""
        # Logging
        logging_section = self.create_section(
            "Logging Settings",
            "Configure how your application logs information."
        )
        
        self.add_combobox(logging_section, "Log Level", "log_level",
                         ["DEBUG", "INFO", "WARNING", "ERROR"],
                         "How detailed the logs should be (INFO is recommended)")
        
        # Monitoring Features
        monitor_section = self.create_section(
            "Monitoring Features",
            "Enable various monitoring and tracking features."
        )
        
        self.add_checkbox(monitor_section, "Performance Monitoring", "performance_monitoring",
                         "Track how fast your application runs")
        
        self.add_checkbox(monitor_section, "Error Tracking", "error_tracking",
                         "Automatically capture and report errors")
        
        self.add_checkbox(monitor_section, "Metrics Collection", "metrics_collection",
                         "Collect usage statistics and metrics")
        
        # Notifications
        notif_section = self.create_section(
            "Notifications",
            "Get notified when important things happen."
        )
        
        self.add_text_field(notif_section, "Notification Webhook", "notification_webhook",
                           "URL to send notifications (Slack, Discord, etc.)", width=60)
    
    def load_configuration(self):
        """Load monitoring configuration into form."""
        config = self.config_manager.monitoring
        
        if "log_level" in self.widgets:
            self.widgets["log_level"].set(getattr(config, "log_level", ""))
        
        if "notification_webhook" in self.widgets:
            self.widgets["notification_webhook"].delete(0, tk.END)
            self.widgets["notification_webhook"].insert(0, getattr(config, "notification_webhook", ""))
        
        bool_fields = ["performance_monitoring", "error_tracking", "metrics_collection"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                var.set(getattr(config, field, False))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        if "log_level" in self.widgets:
            updates["log_level"] = self.widgets["log_level"].get()
        
        if "notification_webhook" in self.widgets:
            updates["notification_webhook"] = self.widgets["notification_webhook"].get().strip()
        
        bool_fields = ["performance_monitoring", "error_tracking", "metrics_collection"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                updates[field] = var.get()
        
        self.config_manager.update_config("monitoring", updates)

class DevelopmentConfigForm(BaseConfigForm):
    """Form for development tools configuration."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, config_manager, "Development Tools Configuration")
        self.create_form()
    
    def create_form(self):
        """Create the development tools configuration form."""
        # Code Quality Tools
        quality_section = self.create_section(
            "Code Quality Tools",
            "Tools to keep your code clean and consistent."
        )
        
        self.add_combobox(quality_section, "Code Formatter", "code_formatter",
                         ["black", "autopep8", "yapf"],
                         "Tool to automatically format your code (Black is most popular)")
        
        self.add_combobox(quality_section, "Linter", "linter",
                         ["flake8", "pylint", "ruff"],
                         "Tool to check your code for issues")
        
        self.add_combobox(quality_section, "Type Checker", "type_checker",
                         ["mypy", "pyright"],
                         "Tool to check type annotations (helps find bugs)")
        
        # Automation Features
        auto_section = self.create_section(
            "Development Automation",
            "Features to automate common development tasks."
        )
        
        self.add_checkbox(auto_section, "Pre-commit Hooks", "pre_commit_hooks",
                         "Run quality checks before each commit")
        
        self.add_checkbox(auto_section, "Auto Documentation", "auto_documentation",
                         "Generate documentation from your code comments")
        
        self.add_checkbox(auto_section, "Code Review Automation", "code_review_automation",
                         "Automatically review code changes")
    
    def load_configuration(self):
        """Load development configuration into form."""
        config = self.config_manager.development
        
        combo_fields = ["code_formatter", "linter", "type_checker"]
        for field in combo_fields:
            if field in self.widgets:
                self.widgets[field].set(getattr(config, field, ""))
        
        bool_fields = ["pre_commit_hooks", "auto_documentation", "code_review_automation"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                var.set(getattr(config, field, False))
    
    def save_configuration(self):
        """Save form data to configuration."""
        updates = {}
        
        combo_fields = ["code_formatter", "linter", "type_checker"]
        for field in combo_fields:
            if field in self.widgets:
                updates[field] = self.widgets[field].get()
        
        bool_fields = ["pre_commit_hooks", "auto_documentation", "code_review_automation"]
        for field in bool_fields:
            if field in self.widgets:
                _, var = self.widgets[field]
                updates[field] = var.get()
        
        self.config_manager.update_config("development", updates) 
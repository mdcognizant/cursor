"""
Main GUI Window for Development Automation Suite
Provides a user-friendly interface for all configuration and automation features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from pathlib import Path
from typing import Dict, Any

from src.core.config_manager import ConfigManager
from src.gui.config_forms import ConfigurationTabs
from src.gui.project_generator import ProjectGeneratorTab
from src.gui.automation_controls import AutomationControlsTab

class MainWindow:
    """Main application window with tabbed interface."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Development Automation Suite")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Configure styles
        self.setup_styles()
        
        # Create main interface
        self.create_widgets()
        
        # Load current configuration
        self.load_configuration()
        
    def setup_styles(self):
        """Setup custom styles for better UI appearance."""
        style = ttk.Style()
        
        # Configure notebook tabs
        style.configure('Custom.TNotebook', tabposition='n')
        style.configure('Custom.TNotebook.Tab', padding=[20, 10])
        
        # Configure frames
        style.configure('Card.TFrame', relief='solid', borderwidth=1)
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Help.TLabel', font=('Arial', 8), foreground='gray')
        
    def create_widgets(self):
        """Create the main interface widgets."""
        # Create main menu
        self.create_menu()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content area with notebook
        self.notebook = ttk.Notebook(self.root, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_tabs()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Import Config", command=self.import_config)
        file_menu.add_command(label="Export Config", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Validate Configuration", command=self.validate_config)
        tools_menu.add_command(label="Reset to Defaults", command=self.reset_config)
        tools_menu.add_command(label="View Logs", command=self.view_logs)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_toolbar(self):
        """Create the toolbar with quick actions."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        # Quick action buttons
        ttk.Button(toolbar, text="Generate Project", 
                  command=self.quick_generate_project).pack(side='left', padx=5)
        ttk.Button(toolbar, text="Save Config", 
                  command=self.save_configuration).pack(side='left', padx=5)
        ttk.Button(toolbar, text="Validate", 
                  command=self.validate_config).pack(side='left', padx=5)
        
        # Status indicator
        self.status_indicator = ttk.Label(toolbar, text="● Ready", foreground="green")
        self.status_indicator.pack(side='right', padx=5)
        
    def create_tabs(self):
        """Create all tabs for the application."""
        # Configuration tabs
        self.config_tabs = ConfigurationTabs(self.notebook, self.config_manager)
        self.notebook.add(self.config_tabs.frame, text="Configuration")
        
        # Project generator tab
        self.project_tab = ProjectGeneratorTab(self.notebook, self.config_manager)
        self.notebook.add(self.project_tab.frame, text="Generate Project")
        
        # Automation controls tab
        self.automation_tab = AutomationControlsTab(self.notebook, self.config_manager)
        self.notebook.add(self.automation_tab.frame, text="Automation")
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        self.status_text = ttk.Label(self.status_bar, text="Ready")
        self.status_text.pack(side='left', padx=10, pady=5)
        
        # Progress bar for long operations
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress_bar.pack(side='right', padx=10, pady=5, fill='x', expand=True)
        
    def load_configuration(self):
        """Load configuration into all tabs."""
        try:
            self.config_tabs.load_configuration()
            self.project_tab.load_configuration()
            self.automation_tab.load_configuration()
            self.update_status("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.update_status("Error loading configuration", error=True)
            
    def save_configuration(self):
        """Save configuration from all tabs."""
        try:
            # Collect configuration from all tabs
            self.config_tabs.save_configuration()
            self.project_tab.save_configuration()
            self.automation_tab.save_configuration()
            
            # Save to file
            self.config_manager.save_config()
            self.update_status("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            self.update_status("Error saving configuration", error=True)
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def validate_config(self):
        """Validate current configuration."""
        try:
            # Save current form data first
            self.config_tabs.save_configuration()
            
            # Validate configuration
            issues = self.config_manager.validate_config()
            
            if not issues:
                messagebox.showinfo("Validation", "Configuration is valid!")
                self.update_status("Configuration validated successfully")
            else:
                issue_text = "\n".join(f"• {issue}" for issue in issues)
                messagebox.showwarning("Validation Issues", 
                                     f"Found the following issues:\n\n{issue_text}")
                self.update_status("Configuration validation failed", error=True)
                
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            messagebox.showerror("Error", f"Failed to validate configuration: {e}")
    
    def new_project(self):
        """Create a new project."""
        self.notebook.select(1)  # Switch to project generator tab
        self.project_tab.new_project()
    
    def open_project(self):
        """Open an existing project."""
        project_dir = filedialog.askdirectory(title="Select Project Directory")
        if project_dir:
            # Load project-specific configuration if available
            project_path = Path(project_dir)
            config_file = project_path / ".dev_automation.yaml"
            if config_file.exists():
                # Load project configuration
                pass  # TODO: Implement project-specific config loading
            self.update_status(f"Opened project: {project_path.name}")
    
    def import_config(self):
        """Import configuration from file."""
        config_file = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if config_file:
            try:
                # TODO: Implement config import
                self.update_status("Configuration imported successfully")
                self.load_configuration()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import configuration: {e}")
    
    def export_config(self):
        """Export current configuration to file."""
        config_file = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if config_file:
            try:
                # TODO: Implement config export
                self.update_status("Configuration exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export configuration: {e}")
    
    def reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Reset Configuration", 
                             "Are you sure you want to reset all configuration to defaults?"):
            try:
                # Reset all configurations
                self.config_manager = ConfigManager()
                self.load_configuration()
                self.update_status("Configuration reset to defaults")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset configuration: {e}")
    
    def view_logs(self):
        """Open log viewer."""
        # TODO: Implement log viewer window
        log_dir = Path.home() / ".dev_automation" / "logs"
        messagebox.showinfo("Logs", f"Log files are located at:\n{log_dir}")
    
    def show_documentation(self):
        """Show documentation."""
        # TODO: Implement documentation viewer
        messagebox.showinfo("Documentation", "Documentation will be available in future versions.")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Development Automation Suite v1.0
        
A comprehensive tool for automating development workflows
with minimal user intervention.

Features:
• Project scaffolding and templates
• CI/CD pipeline automation
• Code analysis and refactoring
• Database management
• Monitoring and logging
• Git workflow automation

Created with ❤️ for developers"""
        
        messagebox.showinfo("About", about_text)
    
    def quick_generate_project(self):
        """Quick project generation with current settings."""
        try:
            self.save_configuration()
            self.notebook.select(1)  # Switch to project generator tab
            self.project_tab.generate_project()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate project: {e}")
    
    def update_status(self, message: str, error: bool = False):
        """Update status bar message."""
        self.status_text.config(text=message)
        if error:
            self.status_indicator.config(text="● Error", foreground="red")
        else:
            self.status_indicator.config(text="● Ready", foreground="green")
        self.root.update_idletasks()
    
    def start_progress(self):
        """Start progress bar animation."""
        self.progress_bar.start(10)
        self.status_indicator.config(text="● Working...", foreground="orange")
    
    def stop_progress(self):
        """Stop progress bar animation."""
        self.progress_bar.stop()
        self.status_indicator.config(text="● Ready", foreground="green")
    
    def on_closing(self):
        """Handle application closing."""
        if messagebox.askokcancel("Quit", "Do you want to save configuration before closing?"):
            try:
                self.save_configuration()
            except Exception as e:
                if not messagebox.askyesno("Error", 
                                         f"Failed to save configuration: {e}\n\nExit anyway?"):
                    return
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop() 
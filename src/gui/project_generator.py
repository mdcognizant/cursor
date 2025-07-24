"""
Project Generator Tab for Development Automation Suite
Provides project scaffolding and template generation capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from pathlib import Path
import threading
from typing import Dict, Any

from src.core.config_manager import ConfigManager
from src.automation.project_scaffolder import ProjectScaffolder

class ProjectGeneratorTab:
    """Tab for generating new projects with templates and scaffolding."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Initialize project scaffolder
        self.scaffolder = ProjectScaffolder(config_manager)
        
        # Create interface
        self.create_widgets()
    
    def create_widgets(self):
        """Create the project generator interface."""
        # Main container with scrolling
        main_canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Project Location Section
        location_frame = ttk.LabelFrame(scrollable_frame, text="Project Location", padding=15)
        location_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(location_frame, text="Where would you like to create your project?", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        location_input_frame = ttk.Frame(location_frame)
        location_input_frame.pack(fill='x', pady=10)
        
        self.location_var = tk.StringVar(value=str(Path.cwd()))
        self.location_entry = ttk.Entry(location_input_frame, textvariable=self.location_var, width=60)
        self.location_entry.pack(side='left', padx=(0, 10))
        
        ttk.Button(location_input_frame, text="Browse", 
                  command=self.browse_location).pack(side='left')
        
        # Project Template Section
        template_frame = ttk.LabelFrame(scrollable_frame, text="Project Template", padding=15)
        template_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(template_frame, text="Choose a template that matches your project type:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.template_var = tk.StringVar()
        templates = [
            ("Basic Python Project", "python_basic"),
            ("Flask Web Application", "flask_webapp"),
            ("Django Web Application", "django_webapp"),
            ("FastAPI REST API", "fastapi_api"),
            ("Data Science Project", "data_science"),
            ("CLI Application", "cli_app"),
            ("React Web App", "react_webapp"),
            ("Node.js API", "nodejs_api"),
            ("Custom Template", "custom")
        ]
        
        for i, (display_name, template_id) in enumerate(templates):
            ttk.Radiobutton(template_frame, text=display_name, 
                           variable=self.template_var, value=template_id).pack(anchor='w', pady=2)
        
        # Set default
        self.template_var.set("python_basic")
        
        # Project Features Section
        features_frame = ttk.LabelFrame(scrollable_frame, text="Project Features", padding=15)
        features_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(features_frame, text="Select additional features to include:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.features = {}
        feature_options = [
            ("docker", "Docker containerization", "Add Docker support for easy deployment"),
            ("testing", "Unit testing setup", "Include testing framework and sample tests"),
            ("docs", "Documentation", "Generate README and documentation structure"),
            ("ci_cd", "CI/CD pipeline", "Add GitHub Actions or GitLab CI configuration"),
            ("pre_commit", "Pre-commit hooks", "Code quality checks before commits"),
            ("env_management", "Environment management", "Environment variables and config files"),
            ("logging", "Logging setup", "Structured logging configuration"),
            ("database", "Database integration", "Database models and migration setup")
        ]
        
        for feature_id, display_name, description in feature_options:
            var = tk.BooleanVar(value=True)  # Default to enabled
            self.features[feature_id] = var
            
            feature_frame = ttk.Frame(features_frame)
            feature_frame.pack(fill='x', pady=2)
            
            ttk.Checkbutton(feature_frame, text=display_name, variable=var).pack(anchor='w')
            ttk.Label(feature_frame, text=description, font=('Arial', 8), 
                     foreground='gray').pack(anchor='w', padx=(20, 0))
        
        # Advanced Options Section
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Options", padding=15)
        advanced_frame.pack(fill='x', padx=20, pady=10)
        
        self.init_git_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Initialize Git repository", 
                       variable=self.init_git_var).pack(anchor='w')
        
        self.create_venv_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Create virtual environment", 
                       variable=self.create_venv_var).pack(anchor='w')
        
        self.install_deps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Install dependencies automatically", 
                       variable=self.install_deps_var).pack(anchor='w')
        
        # Generation Controls
        controls_frame = ttk.Frame(scrollable_frame)
        controls_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(controls_frame, text="Generate Project", 
                  command=self.generate_project, 
                  style='Accent.TButton').pack(side='left', padx=10)
        
        ttk.Button(controls_frame, text="Preview Structure", 
                  command=self.preview_structure).pack(side='left', padx=10)
        
        # Progress and Status
        self.progress_frame = ttk.Frame(scrollable_frame)
        self.progress_frame.pack(fill='x', padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.status_label = ttk.Label(self.progress_frame, text="Ready to generate project")
        self.status_label.pack(anchor='w')
        
        # Log output
        log_frame = ttk.LabelFrame(scrollable_frame, text="Generation Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
    
    def browse_location(self):
        """Browse for project location."""
        directory = filedialog.askdirectory(title="Select Project Location")
        if directory:
            self.location_var.set(directory)
    
    def preview_structure(self):
        """Preview the project structure that will be generated."""
        try:
            template = self.template_var.get()
            features = {k: v.get() for k, v in self.features.items()}
            
            structure = self.scaffolder.preview_structure(template, features)
            
            # Show preview in a new window
            preview_window = tk.Toplevel(self.frame)
            preview_window.title("Project Structure Preview")
            preview_window.geometry("600x500")
            
            text_widget = tk.Text(preview_window, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            text_widget.insert('1.0', structure)
            text_widget.config(state='disabled')
            
        except Exception as e:
            self.logger.error(f"Error previewing structure: {e}")
            messagebox.showerror("Error", f"Failed to preview structure: {e}")
    
    def generate_project(self):
        """Generate the project in a separate thread."""
        # Validate inputs
        if not self.config_manager.project.name:
            messagebox.showerror("Error", "Please set a project name in the Configuration tab first.")
            return
        
        project_path = Path(self.location_var.get()) / self.config_manager.project.name
        if project_path.exists():
            if not messagebox.askyesno("Directory Exists", 
                                     f"Directory {project_path} already exists. Continue anyway?"):
                return
        
        # Start generation in separate thread
        self.start_generation_progress()
        
        generation_thread = threading.Thread(target=self._generate_project_thread)
        generation_thread.daemon = True
        generation_thread.start()
    
    def _generate_project_thread(self):
        """Generate project in background thread."""
        try:
            self.log_message("Starting project generation...")
            
            # Collect generation parameters
            params = {
                'location': Path(self.location_var.get()),
                'template': self.template_var.get(),
                'features': {k: v.get() for k, v in self.features.items()},
                'init_git': self.init_git_var.get(),
                'create_venv': self.create_venv_var.get(),
                'install_deps': self.install_deps_var.get()
            }
            
            # Generate project
            result = self.scaffolder.generate_project(params, self.log_message)
            
            if result['success']:
                self.frame.after(0, lambda: self.generation_complete(result))
            else:
                self.frame.after(0, lambda: self.generation_failed(result['error']))
                
        except Exception as e:
            self.logger.error(f"Project generation error: {e}")
            self.frame.after(0, lambda: self.generation_failed(str(e)))
    
    def start_generation_progress(self):
        """Start progress indication."""
        self.progress_bar.pack(fill='x', pady=(0, 10))
        self.progress_bar.start(10)
        self.status_label.config(text="Generating project...")
        self.log_text.delete('1.0', tk.END)
    
    def stop_generation_progress(self):
        """Stop progress indication."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
    
    def generation_complete(self, result):
        """Handle successful project generation."""
        self.stop_generation_progress()
        self.status_label.config(text=f"Project generated successfully at {result['path']}")
        self.log_message("✓ Project generation complete!")
        
        messagebox.showinfo("Success", 
                           f"Project '{self.config_manager.project.name}' generated successfully!\n\n"
                           f"Location: {result['path']}\n\n"
                           f"Next steps:\n"
                           f"1. Open the project in your editor\n"
                           f"2. Review the generated files\n"
                           f"3. Start coding!")
    
    def generation_failed(self, error):
        """Handle failed project generation."""
        self.stop_generation_progress()
        self.status_label.config(text="Project generation failed")
        self.log_message(f"✗ Generation failed: {error}")
        messagebox.showerror("Error", f"Project generation failed:\n{error}")
    
    def log_message(self, message):
        """Add message to log output."""
        def update_log():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.frame.after(0, update_log)
    
    def new_project(self):
        """Start new project creation."""
        self.log_text.delete('1.0', tk.END)
        self.status_label.config(text="Ready to generate project")
        
        # Focus on project name if not set
        if not self.config_manager.project.name:
            messagebox.showinfo("Setup Required", 
                               "Please configure your project settings in the Configuration tab first.")
    
    def load_configuration(self):
        """Load configuration into the tab."""
        # Update location if project name is set
        if self.config_manager.project.name:
            current_location = Path(self.location_var.get())
            new_location = current_location / self.config_manager.project.name
            # Only update if it's a reasonable path
            if len(str(new_location)) < 200:
                self.location_var.set(str(current_location))
    
    def save_configuration(self):
        """Save any configuration changes."""
        # No configuration to save from this tab
        pass 
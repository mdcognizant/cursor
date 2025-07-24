"""
Template Manager for Development Automation Suite
Manages project templates and generates base project structures.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from src.core.config_manager import ConfigManager

class TemplateManager:
    """Manages project templates and generation."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def get_template_structure(self, template: str) -> List[str]:
        """Get the file structure for a given template."""
        structures = {
            'python_basic': [
                'src/',
                'src/__init__.py',
                'src/main.py',
                'tests/',
                'tests/__init__.py',
                'requirements.txt',
                'requirements-dev.txt',
                'README.md',
                '.gitignore',
                'LICENSE'
            ],
            'flask_webapp': [
                'app/',
                'app/__init__.py',
                'app/models.py',
                'app/views.py',
                'app/templates/',
                'app/templates/base.html',
                'app/templates/index.html',
                'app/static/',
                'app/static/css/',
                'app/static/js/',
                'tests/',
                'requirements.txt',
                'config.py',
                'run.py',
                'README.md',
                '.gitignore'
            ],
            'django_webapp': [
                'project/',
                'project/__init__.py',
                'project/settings.py',
                'project/urls.py',
                'project/wsgi.py',
                'app/',
                'app/__init__.py',
                'app/models.py',
                'app/views.py',
                'app/urls.py',
                'app/admin.py',
                'templates/',
                'static/',
                'tests/',
                'requirements.txt',
                'manage.py',
                'README.md',
                '.gitignore'
            ],
            'fastapi_api': [
                'app/',
                'app/__init__.py',
                'app/main.py',
                'app/api/',
                'app/api/__init__.py',
                'app/api/endpoints/',
                'app/core/',
                'app/core/config.py',
                'app/models/',
                'app/schemas/',
                'tests/',
                'requirements.txt',
                'README.md',
                '.gitignore'
            ],
            'data_science': [
                'data/',
                'data/raw/',
                'data/processed/',
                'notebooks/',
                'src/',
                'src/__init__.py',
                'src/data/',
                'src/features/',
                'src/models/',
                'src/visualization/',
                'tests/',
                'requirements.txt',
                'README.md',
                '.gitignore'
            ],
            'cli_app': [
                'src/',
                'src/__init__.py',
                'src/cli.py',
                'src/commands/',
                'src/utils/',
                'tests/',
                'requirements.txt',
                'README.md',
                '.gitignore'
            ],
            'react_webapp': [
                'src/',
                'src/components/',
                'src/pages/',
                'src/hooks/',
                'src/utils/',
                'src/styles/',
                'public/',
                'public/index.html',
                'tests/',
                'package.json',
                'README.md',
                '.gitignore'
            ],
            'nodejs_api': [
                'src/',
                'src/index.js',
                'src/routes/',
                'src/middleware/',
                'src/models/',
                'src/controllers/',
                'src/utils/',
                'tests/',
                'package.json',
                'README.md',
                '.gitignore'
            ]
        }
        
        return structures.get(template, structures['python_basic'])
    
    def generate_template(self, project_path: Path, template: str):
        """Generate the base template files."""
        config = self.config_manager.project
        
        if template == 'python_basic':
            self._generate_python_basic(project_path)
        elif template == 'flask_webapp':
            self._generate_flask_webapp(project_path)
        elif template == 'django_webapp':
            self._generate_django_webapp(project_path)
        elif template == 'fastapi_api':
            self._generate_fastapi_api(project_path)
        elif template == 'data_science':
            self._generate_data_science(project_path)
        elif template == 'cli_app':
            self._generate_cli_app(project_path)
        elif template == 'react_webapp':
            self._generate_react_webapp(project_path)
        elif template == 'nodejs_api':
            self._generate_nodejs_api(project_path)
        else:
            self._generate_python_basic(project_path)  # Default fallback
    
    def _generate_python_basic(self, project_path: Path):
        """Generate basic Python project structure."""
        # Create directories
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Create source files
        (project_path / "src" / "__init__.py").write_text("")
        
        main_content = f'''"""
{self.config_manager.project.name} - Main Module
{self.config_manager.project.description}
"""

def main():
    """Main entry point."""
    print("Hello from {self.config_manager.project.name}!")

if __name__ == "__main__":
    main()
'''
        (project_path / "src" / "main.py").write_text(main_content)
        
        # Create test files
        (project_path / "tests" / "__init__.py").write_text("")
        
        # Requirements files
        requirements = '''# Core dependencies
# Add your project dependencies here
'''
        (project_path / "requirements.txt").write_text(requirements)
        
        requirements_dev = '''# Development dependencies
pytest>=6.0
black>=22.0
flake8>=4.0
mypy>=0.900
pre-commit>=2.15
'''
        (project_path / "requirements-dev.txt").write_text(requirements_dev)
    
    def _generate_flask_webapp(self, project_path: Path):
        """Generate Flask web application structure."""
        # Create directories
        (project_path / "app").mkdir(exist_ok=True)
        (project_path / "app" / "templates").mkdir(exist_ok=True)
        (project_path / "app" / "static" / "css").mkdir(parents=True, exist_ok=True)
        (project_path / "app" / "static" / "js").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # App __init__.py
        init_content = '''"""Flask application factory."""

from flask import Flask

def create_app():
    """Create Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'  # Change in production
    
    from app.views import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app
'''
        (project_path / "app" / "__init__.py").write_text(init_content)
        
        # Models
        models_content = '''"""Database models."""

# Add your database models here
# Example with SQLAlchemy:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
'''
        (project_path / "app" / "models.py").write_text(models_content)
        
        # Views
        views_content = '''"""Application views."""

from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')
'''
        (project_path / "app" / "views.py").write_text(views_content)
        
        # Templates
        base_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title or '{self.config_manager.project.name}' }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{{{ url_for('main.index') }}}}">{self.config_manager.project.name}</a>
        </div>
    </nav>
    
    <main class="container mt-4">
        {{% block content %}}{{% endblock %}}
    </main>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''
        (project_path / "app" / "templates" / "base.html").write_text(base_template)
        
        index_template = '''{{% extends "base.html" %}}

{{% block content %}}
<div class="row">
    <div class="col-md-8">
        <h1>Welcome to ''' + self.config_manager.project.name + '''</h1>
        <p class="lead">''' + self.config_manager.project.description + '''</p>
        <p>This is your Flask application starting point.</p>
    </div>
</div>
{{% endblock %}}
'''
        (project_path / "app" / "templates" / "index.html").write_text(index_template)
        
        # Run script
        run_content = '''"""Application runner."""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
'''
        (project_path / "run.py").write_text(run_content)
        
        # Config
        config_content = '''"""Application configuration."""

import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
'''
        (project_path / "config.py").write_text(config_content)
        
        # Requirements
        requirements = '''Flask>=2.0.0
python-dotenv>=0.19.0
'''
        (project_path / "requirements.txt").write_text(requirements)
    
    def _generate_fastapi_api(self, project_path: Path):
        """Generate FastAPI REST API structure."""
        # Create directories
        (project_path / "app").mkdir(exist_ok=True)
        (project_path / "app" / "api").mkdir(exist_ok=True)
        (project_path / "app" / "api" / "endpoints").mkdir(exist_ok=True)
        (project_path / "app" / "core").mkdir(exist_ok=True)
        (project_path / "app" / "models").mkdir(exist_ok=True)
        (project_path / "app" / "schemas").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Main FastAPI app
        main_content = f'''"""
FastAPI application for {self.config_manager.project.name}
{self.config_manager.project.description}
"""

from fastapi import FastAPI
from app.api.endpoints import items
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="{self.config_manager.project.description}"
)

# Include routers
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {self.config_manager.project.name} API"}}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "version": settings.VERSION}}
'''
        (project_path / "app" / "main.py").write_text(main_content)
        
        # Configuration
        config_content = f'''"""Application configuration."""

from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "{self.config_manager.project.name}"
    VERSION: str = "{self.config_manager.project.version}"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
        (project_path / "app" / "core" / "config.py").write_text(config_content)
        
        # Example endpoints
        endpoints_content = '''"""Example API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.item import Item, ItemCreate

router = APIRouter()

# In-memory storage for demo
items_db = []

@router.get("/", response_model=List[Item])
async def read_items():
    """Get all items."""
    return items_db

@router.post("/", response_model=Item)
async def create_item(item: ItemCreate):
    """Create a new item."""
    new_item = Item(id=len(items_db) + 1, **item.dict())
    items_db.append(new_item)
    return new_item

@router.get("/{item_id}", response_model=Item)
async def read_item(item_id: int):
    """Get item by ID."""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/{item_id}")
async def delete_item(item_id: int):
    """Delete item by ID."""
    for i, item in enumerate(items_db):
        if item.id == item_id:
            del items_db[i]
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
'''
        (project_path / "app" / "api" / "endpoints" / "items.py").write_text(endpoints_content)
        
        # Schemas
        schema_content = '''"""Pydantic schemas for data validation."""

from pydantic import BaseModel

class ItemBase(BaseModel):
    """Base item schema."""
    name: str
    description: str = None

class ItemCreate(ItemBase):
    """Schema for creating items."""
    pass

class Item(ItemBase):
    """Full item schema."""
    id: int
    
    class Config:
        orm_mode = True
'''
        (project_path / "app" / "schemas" / "item.py").write_text(schema_content)
        
        # Package inits
        (project_path / "app" / "__init__.py").write_text("")
        (project_path / "app" / "api" / "__init__.py").write_text("")
        (project_path / "app" / "api" / "endpoints" / "__init__.py").write_text("")
        (project_path / "app" / "core" / "__init__.py").write_text("")
        (project_path / "app" / "models" / "__init__.py").write_text("")
        (project_path / "app" / "schemas" / "__init__.py").write_text("")
        
        # Requirements
        requirements = '''fastapi>=0.68.0
uvicorn[standard]>=0.15.0
pydantic[email]>=1.8.0
python-multipart>=0.0.5
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=0.19.0
'''
        (project_path / "requirements.txt").write_text(requirements)
    
    def _generate_data_science(self, project_path: Path):
        """Generate data science project structure."""
        # Create directories
        (project_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (project_path / "data" / "processed").mkdir(exist_ok=True)
        (project_path / "notebooks").mkdir(exist_ok=True)
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "src" / "data").mkdir(exist_ok=True)
        (project_path / "src" / "features").mkdir(exist_ok=True)
        (project_path / "src" / "models").mkdir(exist_ok=True)
        (project_path / "src" / "visualization").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Create __init__.py files
        for path in ["src", "src/data", "src/features", "src/models", "src/visualization", "tests"]:
            (project_path / path / "__init__.py").write_text("")
        
        # Data loading module
        data_loader_content = '''"""Data loading utilities."""

import pandas as pd
from pathlib import Path

def load_raw_data(filename: str) -> pd.DataFrame:
    """Load raw data from file."""
    data_path = Path(__file__).parent.parent.parent / "data" / "raw" / filename
    return pd.read_csv(data_path)

def save_processed_data(df: pd.DataFrame, filename: str) -> None:
    """Save processed data to file."""
    data_path = Path(__file__).parent.parent.parent / "data" / "processed" / filename
    df.to_csv(data_path, index=False)
'''
        (project_path / "src" / "data" / "loader.py").write_text(data_loader_content)
        
        # Feature engineering
        features_content = '''"""Feature engineering utilities."""

import pandas as pd
import numpy as np

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features from raw data."""
    # Add your feature engineering logic here
    return df

def scale_features(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """Scale numerical features."""
    from sklearn.preprocessing import StandardScaler
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns
    
    scaler = StandardScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df
'''
        (project_path / "src" / "features" / "engineering.py").write_text(features_content)
        
        # Example notebook
        notebook_content = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# ''' + self.config_manager.project.name + ''' - Exploratory Data Analysis\\n",
    "\\n",
    "''' + self.config_manager.project.description + '''"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "%matplotlib inline\\n",
    "sns.set_style('whitegrid')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Data Loading"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Load your data here\\n",
    "# df = pd.read_csv('../data/raw/your_data.csv')\\n",
    "# df.head()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}'''
        (project_path / "notebooks" / "01_exploratory_analysis.ipynb").write_text(notebook_content)
        
        # Requirements for data science
        requirements = '''pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=1.0.0
jupyter>=1.0.0
plotly>=5.0.0
'''
        (project_path / "requirements.txt").write_text(requirements)
    
    def _generate_cli_app(self, project_path: Path):
        """Generate CLI application structure."""
        # Create directories
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "src" / "commands").mkdir(exist_ok=True)
        (project_path / "src" / "utils").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Create __init__.py files
        for path in ["src", "src/commands", "src/utils", "tests"]:
            (project_path / path / "__init__.py").write_text("")
        
        # Main CLI module
        cli_content = f'''"""
Command Line Interface for {self.config_manager.project.name}
{self.config_manager.project.description}
"""

import click
from src.commands import hello, info

@click.group()
@click.version_option(version="{self.config_manager.project.version}")
@click.pass_context
def cli(ctx):
    """
    {self.config_manager.project.name} - {self.config_manager.project.description}
    """
    ctx.ensure_object(dict)

# Add commands
cli.add_command(hello.hello)
cli.add_command(info.info)

if __name__ == "__main__":
    cli()
'''
        (project_path / "src" / "cli.py").write_text(cli_content)
        
        # Hello command
        hello_content = '''"""Hello command implementation."""

import click

@click.command()
@click.option('--name', default='World', help='Name to greet')
@click.option('--count', default=1, help='Number of greetings')
def hello(name, count):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo(f'Hello {name}!')
'''
        (project_path / "src" / "commands" / "hello.py").write_text(hello_content)
        
        # Info command
        info_content = '''"""Info command implementation."""

import click
import sys
import platform

@click.command()
def info():
    """Display system information."""
    click.echo("System Information:")
    click.echo(f"Python version: {sys.version}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Architecture: {platform.architecture()}")
'''
        (project_path / "src" / "commands" / "info.py").write_text(info_content)
        
        # Requirements
        requirements = '''click>=8.0.0
'''
        (project_path / "requirements.txt").write_text(requirements)
    
    def _generate_react_webapp(self, project_path: Path):
        """Generate React web application structure."""
        # Create directories
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "src" / "components").mkdir(exist_ok=True)
        (project_path / "src" / "pages").mkdir(exist_ok=True)
        (project_path / "src" / "hooks").mkdir(exist_ok=True)
        (project_path / "src" / "utils").mkdir(exist_ok=True)
        (project_path / "src" / "styles").mkdir(exist_ok=True)
        (project_path / "public").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Public HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{self.config_manager.project.description}" />
    <title>{self.config_manager.project.name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''
        (project_path / "public" / "index.html").write_text(html_content)
        
        # Main React component
        app_content = f'''import React from 'react';
import './styles/App.css';

function App() {{
  return (
    <div className="App">
      <header className="App-header">
        <h1>{self.config_manager.project.name}</h1>
        <p>{self.config_manager.project.description}</p>
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
      </header>
    </div>
  );
}}

export default App;
'''
        (project_path / "src" / "App.js").write_text(app_content)
        
        # Index.js
        index_content = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
        (project_path / "src" / "index.js").write_text(index_content)
        
        # CSS
        app_css = '''.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
}

.App-header code {
  background-color: #21252b;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}
'''
        (project_path / "src" / "styles" / "App.css").write_text(app_css)
        
        index_css = '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
'''
        (project_path / "src" / "styles" / "index.css").write_text(index_css)
    
    def _generate_nodejs_api(self, project_path: Path):
        """Generate Node.js API structure."""
        # Create directories
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "src" / "routes").mkdir(exist_ok=True)
        (project_path / "src" / "middleware").mkdir(exist_ok=True)
        (project_path / "src" / "models").mkdir(exist_ok=True)
        (project_path / "src" / "controllers").mkdir(exist_ok=True)
        (project_path / "src" / "utils").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        
        # Main server file
        index_content = f'''/**
 * {self.config_manager.project.name} - Express.js API
 * {self.config_manager.project.description}
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({{ extended: true }}));

// Routes
app.get('/', (req, res) => {{
  res.json({{
    message: 'Welcome to {self.config_manager.project.name} API',
    version: '{self.config_manager.project.version}',
    timestamp: new Date().toISOString()
  }});
}});

app.get('/health', (req, res) => {{
  res.json({{ status: 'healthy' }});
}});

// Error handling middleware
app.use((err, req, res, next) => {{
  console.error(err.stack);
  res.status(500).json({{ error: 'Something went wrong!' }});
}});

// 404 handler
app.use((req, res) => {{
  res.status(404).json({{ error: 'Route not found' }});
}});

app.listen(PORT, () => {{
  console.log(`Server running on port ${{PORT}}`);
}});

module.exports = app;
'''
        (project_path / "src" / "index.js").write_text(index_content) 
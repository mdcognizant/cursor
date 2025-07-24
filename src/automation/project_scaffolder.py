"""
Project Scaffolder for Development Automation Suite
Generates complete project structures with automation features.
"""

import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import json
import yaml

from src.core.config_manager import ConfigManager
from src.automation.templates import TemplateManager
# from src.automation.ci_cd_generator import CICDGenerator  # Temporarily disabled due to syntax issues
from src.automation.docker_generator import DockerGenerator

class ProjectScaffolder:
    """Generates complete project structures with automation."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.template_manager = TemplateManager(config_manager)
        # self.cicd_generator = CICDGenerator(config_manager)  # Temporarily disabled
        self.docker_generator = DockerGenerator(config_manager)
    
    def preview_structure(self, template: str, features: Dict[str, bool]) -> str:
        """Preview the project structure that will be generated."""
        structure_lines = []
        
        # Get base template structure
        base_structure = self.template_manager.get_template_structure(template)
        
        # Add feature-specific files
        if features.get('docker', False):
            base_structure.extend([
                'Dockerfile',
                'docker-compose.yml',
                '.dockerignore'
            ])
        
        if features.get('testing', False):
            base_structure.extend([
                'tests/',
                'tests/__init__.py',
                'tests/test_example.py',
                'pytest.ini'
            ])
        
        if features.get('docs', False):
            base_structure.extend([
                'docs/',
                'docs/README.md',
                'docs/CONTRIBUTING.md',
                'docs/CHANGELOG.md'
            ])
        
        if features.get('ci_cd', False):
            if self.config_manager.cicd.platform == 'github_actions':
                base_structure.extend([
                    '.github/',
                    '.github/workflows/',
                    '.github/workflows/ci.yml'
                ])
            elif self.config_manager.cicd.platform == 'gitlab_ci':
                base_structure.append('.gitlab-ci.yml')
        
        if features.get('pre_commit', False):
            base_structure.extend([
                '.pre-commit-config.yaml'
            ])
        
        if features.get('env_management', False):
            base_structure.extend([
                '.env.example',
                '.env.local',
                'config/',
                'config/settings.py'
            ])
        
        # Sort and format structure
        base_structure.sort()
        
        structure_lines.append(f"📁 {self.config_manager.project.name}/")
        for item in base_structure:
            if item.endswith('/'):
                structure_lines.append(f"  📁 {item}")
            else:
                structure_lines.append(f"  📄 {item}")
        
        return "\n".join(structure_lines)
    
    def generate_project(self, params: Dict[str, Any], 
                        progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Generate a complete project with all specified features."""
        try:
            if progress_callback:
                progress_callback("Initializing project generation...")
            
            # Setup project directory
            project_path = params['location'] / self.config_manager.project.name
            project_path.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(f"Created project directory: {project_path}")
            
            # Generate base template
            self._generate_base_template(project_path, params['template'], progress_callback)
            
            # Generate feature-specific files
            self._generate_features(project_path, params['features'], progress_callback)
            
            # Initialize Git repository
            if params.get('init_git', True):
                self._initialize_git(project_path, progress_callback)
            
            # Create virtual environment
            if params.get('create_venv', True):
                self._create_virtual_environment(project_path, progress_callback)
            
            # Install dependencies
            if params.get('install_deps', True):
                self._install_dependencies(project_path, progress_callback)
            
            # Generate automation configurations
            self._generate_automation_configs(project_path, progress_callback)
            
            if progress_callback:
                progress_callback("Project generation completed successfully!")
            
            return {
                'success': True,
                'path': project_path,
                'message': 'Project generated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Project generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_base_template(self, project_path: Path, template: str, 
                               progress_callback: Optional[Callable[[str], None]] = None):
        """Generate the base project template."""
        if progress_callback:
            progress_callback(f"Generating {template} template...")
        
        # Create basic project structure
        self.template_manager.generate_template(project_path, template)
        
        # Generate main configuration files
        self._generate_project_config(project_path)
        self._generate_readme(project_path)
        self._generate_gitignore(project_path)
        
        if progress_callback:
            progress_callback("Base template generated")
    
    def _generate_features(self, project_path: Path, features: Dict[str, bool],
                          progress_callback: Optional[Callable[[str], None]] = None):
        """Generate feature-specific files and configurations."""
        if features.get('docker', False):
            if progress_callback:
                progress_callback("Adding Docker support...")
            self.docker_generator.generate_docker_files(project_path)
        
        if features.get('testing', False):
            if progress_callback:
                progress_callback("Setting up testing framework...")
            self._generate_testing_setup(project_path)
        
        if features.get('docs', False):
            if progress_callback:
                progress_callback("Creating documentation structure...")
            self._generate_documentation(project_path)
        
        if features.get('ci_cd', False):
            if progress_callback:
                progress_callback("Setting up CI/CD pipeline...")
            # self.cicd_generator.generate_pipeline(project_path)  # Temporarily disabled
        
        if features.get('pre_commit', False):
            if progress_callback:
                progress_callback("Configuring pre-commit hooks...")
            self._generate_precommit_config(project_path)
        
        if features.get('env_management', False):
            if progress_callback:
                progress_callback("Setting up environment management...")
            self._generate_env_management(project_path)
        
        if features.get('logging', False):
            if progress_callback:
                progress_callback("Configuring logging...")
            self._generate_logging_config(project_path)
        
        if features.get('database', False):
            if progress_callback:
                progress_callback("Setting up database integration...")
            self._generate_database_setup(project_path)
    
    def _generate_project_config(self, project_path: Path):
        """Generate project configuration files."""
        config = self.config_manager.project
        
        # Generate setup.py or pyproject.toml
        if config.language == 'python':
            if config.framework in ['fastapi', 'flask', 'django']:
                self._generate_pyproject_toml(project_path)
            else:
                self._generate_setup_py(project_path)
        
        # Generate package.json for Node.js projects
        elif config.language in ['javascript', 'typescript']:
            self._generate_package_json(project_path)
    
    def _generate_setup_py(self, project_path: Path):
        """Generate setup.py for Python projects."""
        config = self.config_manager.project
        
        setup_content = f'''#!/usr/bin/env python3
"""Setup script for {config.name}."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{config.name.lower().replace(' ', '-')}",
    version="{config.version}",
    author="{config.author}",
    description="{config.description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: {config.license} License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">={config.python_version.replace('+', '')}",
    install_requires=[
        # Add your dependencies here
    ],
    extras_require={{
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    }},
)
'''
        (project_path / "setup.py").write_text(setup_content)
    
    def _generate_pyproject_toml(self, project_path: Path):
        """Generate pyproject.toml for modern Python projects."""
        config = self.config_manager.project
        
        toml_content = f'''[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm"]
build-backend = "setuptools.build_meta"

[project]
name = "{config.name.lower().replace(' ', '-')}"
version = "{config.version}"
description = "{config.description}"
authors = [
    {{name = "{config.author}"}}
]
license = {{text = "{config.license}"}}
readme = "README.md"
requires-python = ">={config.python_version.replace('+', '')}"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: {config.license} License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
]

dependencies = [
    # Add your dependencies here
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "black>=22.0",
    "flake8>=4.0",
    "mypy>=0.900",
    "pre-commit>=2.15",
]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
'''
        (project_path / "pyproject.toml").write_text(toml_content)
    
    def _generate_package_json(self, project_path: Path):
        """Generate package.json for Node.js projects."""
        config = self.config_manager.project
        
        package_data = {
            "name": config.name.lower().replace(' ', '-'),
            "version": config.version,
            "description": config.description,
            "main": "index.js",
            "scripts": {
                "test": "jest",
                "start": "node index.js",
                "dev": "nodemon index.js",
                "lint": "eslint .",
                "format": "prettier --write ."
            },
            "author": config.author,
            "license": config.license,
            "devDependencies": {
                "jest": "^29.0.0",
                "nodemon": "^2.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.0.0"
            }
        }
        
        (project_path / "package.json").write_text(json.dumps(package_data, indent=2))
    
    def _generate_readme(self, project_path: Path):
        """Generate README.md file."""
        config = self.config_manager.project
        
        readme_content = f'''# {config.name}

{config.description}

## Features

- Modern {config.language.title()} development setup
- Automated testing and CI/CD
- Code quality tools (linting, formatting, type checking)
- Docker support for easy deployment
- Comprehensive documentation

## Quick Start

### Prerequisites

- {config.language.title()} {config.python_version if config.language == 'python' else ''}
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {config.name.lower().replace(' ', '-')}
```

2. Set up the development environment:
```bash
# For Python projects
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -e ".[dev]"

# For Node.js projects
npm install
```

3. Run tests:
```bash
# For Python projects
pytest

# For Node.js projects
npm test
```

## Development

### Project Structure

```
{config.name.lower().replace(' ', '-')}/
├── src/                 # Source code
├── tests/              # Test files
├── docs/               # Documentation
├── .github/workflows/  # CI/CD pipelines
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker compose setup
└── README.md          # This file
```

### Code Quality

This project uses several tools to maintain code quality:

- **Formatter**: {self.config_manager.development.code_formatter}
- **Linter**: {self.config_manager.development.linter}
- **Type Checker**: {self.config_manager.development.type_checker}
- **Pre-commit Hooks**: Automatically run quality checks

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_example.py
```

## Deployment

### Using Docker

```bash
# Build the image
docker build -t {config.name.lower().replace(' ', '-')} .

# Run the container
docker run -p 8000:8000 {config.name.lower().replace(' ', '-')}
```

### Using Docker Compose

```bash
docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the {config.license} License - see the [LICENSE](LICENSE) file for details.

## Author

{config.author}

---

Generated with ❤️ by Development Automation Suite
'''
        (project_path / "README.md").write_text(readme_content)
    
    def _generate_gitignore(self, project_path: Path):
        """Generate .gitignore file."""
        config = self.config_manager.project
        
        if config.language == 'python':
            gitignore_content = '''# Byte-compiled / optimized / DLL files
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

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Dev automation
.dev_automation/
'''
        else:  # JavaScript/TypeScript
            gitignore_content = '''# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# Grunt intermediate storage
.grunt

# node-waf configuration
.lock-wscript

# Compiled binary addons
build/Release

# Dependency directories
jspm_packages/

# TypeScript v1 declaration files
typings/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test

# parcel-bundler cache
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless/

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Dev automation
.dev_automation/
'''
        
        (project_path / ".gitignore").write_text(gitignore_content)
    
    def _generate_testing_setup(self, project_path: Path):
        """Generate testing framework setup."""
        config = self.config_manager.project
        
        # Create tests directory
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("")
        
        if config.language == 'python':
            # Generate pytest configuration
            pytest_config = '''[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
'''
            (project_path / "pytest.ini").write_text(pytest_config)
            
            # Generate example test
            test_content = f'''"""Example tests for {config.name}."""

import pytest


def test_example():
    """Example test case."""
    assert True


def test_addition():
    """Test basic addition."""
    assert 1 + 1 == 2


class TestExample:
    """Example test class."""
    
    def test_method_example(self):
        """Example test method."""
        assert "hello" == "hello"
    
    def test_with_fixture(self):
        """Test using a fixture."""
        # Add your test logic here
        pass


@pytest.fixture
def sample_data():
    """Sample test fixture."""
    return {{"key": "value"}}
'''
            (tests_dir / "test_example.py").write_text(test_content)
    
    def _generate_documentation(self, project_path: Path):
        """Generate documentation structure."""
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Contributing guidelines
        contributing_content = '''# Contributing to this Project

Thank you for your interest in contributing! Here are some guidelines to help you get started.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature
4. Make your changes
5. Run tests to ensure everything works
6. Submit a pull request

## Code Style

This project follows these code style guidelines:

- Use consistent formatting (automated by our formatters)
- Write clear, descriptive variable and function names
- Add comments for complex logic
- Include docstrings for all public functions and classes

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting
- Aim for good test coverage

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all CI checks pass
4. Request review from maintainers
'''
        (docs_dir / "CONTRIBUTING.md").write_text(contributing_content)
        
        # Changelog
        changelog_content = f'''# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Basic project structure

## [{self.config_manager.project.version}] - {self._get_current_date()}

### Added
- Project initialization
- Development automation setup
'''
        (docs_dir / "CHANGELOG.md").write_text(changelog_content)
    
    def _generate_precommit_config(self, project_path: Path):
        """Generate pre-commit configuration."""
        config = self.config_manager.development
        
        precommit_config = f'''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.11.4
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
'''
        (project_path / ".pre-commit-config.yaml").write_text(precommit_config)
    
    def _generate_env_management(self, project_path: Path):
        """Generate environment management files."""
        # .env.example
        env_example = '''# Environment Variables Example
# Copy this file to .env and update with your values

# Application settings
APP_NAME=my_application
APP_VERSION=1.0.0
DEBUG=false

# Database settings
DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# External services
REDIS_URL=redis://localhost:6379
EMAIL_SERVICE_API_KEY=your-email-api-key

# Logging
LOG_LEVEL=INFO
'''
        (project_path / ".env.example").write_text(env_example)
        
        # Config directory and settings
        config_dir = project_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        settings_content = '''"""Application settings and configuration."""

import os
from pathlib import Path
from typing import Optional

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default."""
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is required")
    return value

# Application settings
APP_NAME = get_env_var("APP_NAME", "My Application")
APP_VERSION = get_env_var("APP_VERSION", "1.0.0")
DEBUG = get_env_var("DEBUG", "false").lower() == "true"

# Database settings
DATABASE_URL = get_env_var("DATABASE_URL", "sqlite:///./app.db")

# Security
SECRET_KEY = get_env_var("SECRET_KEY")

# Logging configuration
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO")
'''
        (config_dir / "settings.py").write_text(settings_content)
    
    def _generate_logging_config(self, project_path: Path):
        """Generate logging configuration."""
        config = self.config_manager.monitoring
        
        logging_config = f'''"""Logging configuration for the application."""

import logging
import logging.config
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {{
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {{
        'standard': {{
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }},
        'detailed': {{
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }},
    }},
    'handlers': {{
        'console': {{
            'class': 'logging.StreamHandler',
            'level': '{config.log_level}',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }},
        'file': {{
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }},
        'error_file': {{
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'errors.log'),
            'maxBytes': 5242880,  # 5MB
            'backupCount': 3,
            'encoding': 'utf-8'
        }},
    }},
    'loggers': {{
        '': {{  # root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        }}
    }}
}}

def setup_logging():
    """Set up logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
'''
        
        (project_path / "logging_config.py").write_text(logging_config)
    
    def _generate_database_setup(self, project_path: Path):
        """Generate database setup files."""
        db_config = self.config_manager.database
        
        if db_config.type == 'sqlite':
            # Simple SQLite setup
            db_content = '''"""Database setup and models."""

import sqlite3
from pathlib import Path
from typing import Optional

DATABASE_PATH = Path(__file__).parent.parent / "data" / "app.db"
DATABASE_PATH.parent.mkdir(exist_ok=True)

def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with tables."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
'''
        else:
            # PostgreSQL/MySQL setup with SQLAlchemy
            db_content = f'''"""Database setup with SQLAlchemy."""

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "{db_config.type}://{db_config.username}:password@{db_config.host}:{db_config.port}/{db_config.name}")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
'''
        
        (project_path / "database.py").write_text(db_content)
    
    def _initialize_git(self, project_path: Path, 
                       progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize Git repository."""
        try:
            if progress_callback:
                progress_callback("Initializing Git repository...")
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=project_path, check=True)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)
            
            # Initial commit
            commit_message = f"Initial commit: {self.config_manager.project.name}"
            subprocess.run(["git", "commit", "-m", commit_message], 
                          cwd=project_path, check=True)
            
            if progress_callback:
                progress_callback("Git repository initialized with initial commit")
                
        except subprocess.CalledProcessError as e:
            if progress_callback:
                progress_callback(f"Git initialization failed: {e}")
            self.logger.warning(f"Git initialization failed: {e}")
    
    def _create_virtual_environment(self, project_path: Path,
                                   progress_callback: Optional[Callable[[str], None]] = None):
        """Create Python virtual environment."""
        if self.config_manager.project.language != 'python':
            return
        
        try:
            if progress_callback:
                progress_callback("Creating virtual environment...")
            
            venv_path = project_path / "venv"
            subprocess.run(["python", "-m", "venv", str(venv_path)], 
                          cwd=project_path, check=True)
            
            if progress_callback:
                progress_callback("Virtual environment created")
                
        except subprocess.CalledProcessError as e:
            if progress_callback:
                progress_callback(f"Virtual environment creation failed: {e}")
            self.logger.warning(f"Virtual environment creation failed: {e}")
    
    def _install_dependencies(self, project_path: Path,
                             progress_callback: Optional[Callable[[str], None]] = None):
        """Install project dependencies."""
        config = self.config_manager.project
        
        try:
            if config.language == 'python':
                if progress_callback:
                    progress_callback("Installing Python dependencies...")
                
                # Activate venv and install dependencies
                if (project_path / "venv").exists():
                    if os.name == 'nt':  # Windows
                        pip_cmd = str(project_path / "venv" / "Scripts" / "pip")
                    else:  # Unix-like
                        pip_cmd = str(project_path / "venv" / "bin" / "pip")
                else:
                    pip_cmd = "pip"
                
                subprocess.run([pip_cmd, "install", "-e", ".[dev]"], 
                              cwd=project_path, check=True)
                
            elif config.language in ['javascript', 'typescript']:
                if progress_callback:
                    progress_callback("Installing Node.js dependencies...")
                
                subprocess.run(["npm", "install"], cwd=project_path, check=True)
            
            if progress_callback:
                progress_callback("Dependencies installed successfully")
                
        except subprocess.CalledProcessError as e:
            if progress_callback:
                progress_callback(f"Dependency installation failed: {e}")
            self.logger.warning(f"Dependency installation failed: {e}")
    
    def _generate_automation_configs(self, project_path: Path,
                                    progress_callback: Optional[Callable[[str], None]] = None):
        """Generate automation configuration files."""
        if progress_callback:
            progress_callback("Generating automation configurations...")
        
        # Create .dev_automation.yaml for project-specific settings
        project_config = {
            'project': {
                'name': self.config_manager.project.name,
                'version': self.config_manager.project.version,
                'type': self.config_manager.project.language,
                'framework': self.config_manager.project.framework
            },
            'automation': {
                'auto_commit': self.config_manager.git.auto_commit,
                'auto_test': self.config_manager.cicd.auto_test,
                'auto_format': True,
                'auto_lint': True
            }
        }
        
        with open(project_path / ".dev_automation.yaml", 'w') as f:
            yaml.dump(project_config, f, default_flow_style=False)
        
        if progress_callback:
            progress_callback("Automation configurations generated")
    
    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d") 
#!/usr/bin/env python3
"""
Setup script for Development Automation Suite
A comprehensive tool for automating development workflows with minimal user intervention.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
README_PATH = Path(__file__).parent / "README.md"
if README_PATH.exists():
    with open(README_PATH, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A comprehensive tool for automating development workflows with minimal user intervention."

# Read requirements
REQUIREMENTS_PATH = Path(__file__).parent / "requirements.txt"
if REQUIREMENTS_PATH.exists():
    with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "PyYAML>=6.0",
        "pathlib>=1.0.1",
        "GitPython>=3.1.0",
        "psutil>=5.9.0",
        "watchdog>=2.1.0",
        "requests>=2.28.0"
    ]

setup(
    name="development-automation-suite",
    version="1.0.0",
    author="Development Automation Team",
    author_email="dev@automation-suite.com",
    description="A comprehensive tool for automating development workflows with minimal user intervention",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dev-automation/suite",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: System Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.8.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
            "isort>=5.10.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
        "ci": [
            "PyGithub>=1.55",
            "python-gitlab>=3.0.0",
        ],
        "docs": [
            "Sphinx>=5.0.0",
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.14.0",
        ],
        "database": [
            "SQLAlchemy>=1.4.0",
            "alembic>=1.8.0",
        ],
        "full": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.8.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
            "isort>=5.10.0",
            "docker>=6.0.0",
            "PyGithub>=1.55",
            "python-gitlab>=3.0.0",
            "Sphinx>=5.0.0",
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.0.0",
            "prometheus-client>=0.14.0",
            "SQLAlchemy>=1.4.0",
            "alembic>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dev-automation=main:main",
            "dev-auto=main:main",
        ],
    },
    package_data={
        "src": [
            "templates/*",
            "config/*",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "development",
        "automation",
        "ci-cd",
        "git",
        "testing",
        "deployment",
        "scaffolding",
        "project-generator",
        "code-quality",
        "devops",
        "workflow",
    ],
    project_urls={
        "Bug Reports": "https://github.com/dev-automation/suite/issues",
        "Source": "https://github.com/dev-automation/suite",
        "Documentation": "https://dev-automation.github.io/suite/",
        "Changelog": "https://github.com/dev-automation/suite/blob/main/CHANGELOG.md",
    },
) 
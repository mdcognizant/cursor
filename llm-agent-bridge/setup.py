#!/usr/bin/env python3
"""Setup script for LLM Agent Bridge."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="llm-agent-bridge",
    version="0.1.0",
    author="LLM Agent Bridge Team",
    author_email="contact@example.com",
    description="A Python-based API library bridging REST and gRPC for LLM agent communication",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/llm-agent-bridge",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "llm_agent_bridge": [
            "protos/*.proto",
            "templates/*.yaml",
            "templates/*.json",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
        ]
    },
    entry_points={
        "console_scripts": [
            "agent-bridge=llm_agent_bridge.cli:main",
            "proto-compile=llm_agent_bridge.tools.proto_compiler:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 
"""Setup configuration for Universal API Bridge."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        pass
    return requirements

setup(
    name="universal-api-bridge",
    version="1.0.0",
    author="Universal API Bridge Team",
    author_email="team@universal-api-bridge.com",
    description="Enterprise-grade Universal REST-to-gRPC API Bridge for massive scale (100k+ APIs)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/universal-api-bridge/universal-api-bridge",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "monitoring": [
            "opentelemetry-exporter-jaeger>=1.21.0",
            "opentelemetry-exporter-prometheus>=1.12.0rc1",
            "grafana-api>=1.0.3",
        ],
        "security": [
            "cryptography>=41.0.7",
            "pyjwt[crypto]>=2.8.0",
            "passlib[bcrypt]>=1.7.4",
            "geoip2>=4.7.0",
        ],
        "performance": [
            "uvloop>=0.19.0",
            "orjson>=3.9.10",
            "lz4>=4.3.2",
            "zstandard>=0.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "universal-bridge=universal_api_bridge.cli:main",
        ],
    },
    package_data={
        "universal_api_bridge": [
            "py.typed",
            "config/*.yaml",
            "config/*.json",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "api", "bridge", "grpc", "rest", "microservices", "distributed", 
        "scalability", "performance", "enterprise", "cloud-native"
    ],
    project_urls={
        "Bug Reports": "https://github.com/universal-api-bridge/universal-api-bridge/issues",
        "Source": "https://github.com/universal-api-bridge/universal-api-bridge",
        "Documentation": "https://universal-api-bridge.readthedocs.io/",
    },
) 
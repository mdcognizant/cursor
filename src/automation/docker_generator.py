"""
Docker Generator for Development Automation Suite
Generates Docker configurations for containerization.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from src.core.config_manager import ConfigManager

class DockerGenerator:
    """Generates Docker configurations for projects."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def generate_docker_files(self, project_path: Path):
        """Generate Docker configuration files."""
        config = self.config_manager.project
        language = config.language
        
        if language == 'python':
            self._generate_python_docker(project_path)
        elif language in ['javascript', 'typescript']:
            self._generate_nodejs_docker(project_path)
        else:
            self._generate_generic_docker(project_path)
        
        # Generate docker-compose.yml
        self._generate_docker_compose(project_path)
        
        # Generate .dockerignore
        self._generate_dockerignore(project_path)
    
    def _generate_python_docker(self, project_path: Path):
        """Generate Dockerfile for Python projects."""
        config = self.config_manager.project
        
        dockerfile_content = f'''# Multi-stage Dockerfile for {config.name}
FROM python:{config.python_version.replace('+', '')}-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONHASHSEED=random \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        build-essential \\
        curl \\
        git \\
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "-m", "src.main"]

# Production stage
FROM base as production

# Install production dependencies only
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py pyproject.toml README.md ./

# Install package
RUN pip install .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for production
CMD ["python", "-m", "src.main"]
'''
        
        if config.framework == 'flask':
            dockerfile_content = dockerfile_content.replace(
                'CMD ["python", "-m", "src.main"]',
                'CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]'
            )
        elif config.framework == 'django':
            dockerfile_content = dockerfile_content.replace(
                'CMD ["python", "-m", "src.main"]',
                'CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]'
            )
        elif config.framework == 'fastapi':
            dockerfile_content = dockerfile_content.replace(
                'CMD ["python", "-m", "src.main"]',
                'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'
            )
        
        (project_path / "Dockerfile").write_text(dockerfile_content)
    
    def _generate_nodejs_docker(self, project_path: Path):
        """Generate Dockerfile for Node.js projects."""
        config = self.config_manager.project
        
        dockerfile_content = f'''# Multi-stage Dockerfile for {config.name}
FROM node:18-alpine as base

# Set environment variables
ENV NODE_ENV=production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create app user
RUN addgroup -g 1001 -S appuser \\
    && adduser -S appuser -u 1001

# Set work directory
WORKDIR /app

# Development stage
FROM base as development

# Set development environment
ENV NODE_ENV=development

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci --include=dev

# Copy source code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Default command for development
CMD ["dumb-init", "npm", "run", "dev"]

# Build stage
FROM base as build

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci --include=dev

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM base as production

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production && npm cache clean --force

# Copy built application from build stage
COPY --from=build /app/build ./build/
COPY --from=build /app/public ./public/

# Copy other necessary files
COPY --chown=appuser:appuser src/ ./src/

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:3000/health || exit 1

# Expose port
EXPOSE 3000

# Default command for production
CMD ["dumb-init", "npm", "start"]
'''
        
        (project_path / "Dockerfile").write_text(dockerfile_content)
    
    def _generate_generic_docker(self, project_path: Path):
        """Generate generic Dockerfile."""
        config = self.config_manager.project
        
        dockerfile_content = f'''# Dockerfile for {config.name}
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        curl \\
        wget \\
        git \\
        build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy application files
COPY . .

# Install application dependencies
# Add your installation commands here based on {config.language}

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["echo", "Configure your application command"]
'''
        
        (project_path / "Dockerfile").write_text(dockerfile_content)
    
    def _generate_docker_compose(self, project_path: Path):
        """Generate docker-compose.yml file."""
        config = self.config_manager
        db_config = config.database
        
        compose_content = f'''version: '3.8'

services:
  app:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/node_modules  # Exclude node_modules for Node.js projects
    environment:
      - DEBUG=true
      - DATABASE_URL=${{DATABASE_URL:-{self._get_default_db_url()}}}
    depends_on:
'''

        # Add database service if configured
        if db_config.type == 'postgresql':
            compose_content += f'''      - postgres
    networks:
      - app-network

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: {db_config.name}
      POSTGRES_USER: {db_config.username or 'postgres'}
      POSTGRES_PASSWORD: {db_config.password or 'postgres'}
    ports:
      - "{db_config.port}:{db_config.port}"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

'''
        elif db_config.type == 'mysql':
            compose_content += f'''      - mysql
    networks:
      - app-network

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: {db_config.name}
      MYSQL_USER: {db_config.username or 'mysql'}
      MYSQL_PASSWORD: {db_config.password or 'mysql'}
      MYSQL_ROOT_PASSWORD: {db_config.password or 'rootpassword'}
    ports:
      - "{db_config.port}:{db_config.port}"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - app-network

'''
        elif db_config.type == 'mongodb':
            compose_content += f'''      - mongo
    networks:
      - app-network

  mongo:
    image: mongo:6.0
    environment:
      MONGO_INITDB_DATABASE: {db_config.name}
      MONGO_INITDB_ROOT_USERNAME: {db_config.username or 'mongo'}
      MONGO_INITDB_ROOT_PASSWORD: {db_config.password or 'mongo'}
    ports:
      - "{db_config.port}:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - app-network

'''
        else:
            compose_content += '''    networks:
      - app-network

'''
        
        # Add Redis if caching is enabled
        compose_content += '''  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

'''
        
        # Add monitoring with Prometheus and Grafana
        if config.monitoring.performance_monitoring:
            compose_content += '''  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - app-network

'''
        
        # Add volumes section
        compose_content += '''volumes:
'''
        
        if db_config.type == 'postgresql':
            compose_content += '  postgres_data:\n'
        elif db_config.type == 'mysql':
            compose_content += '  mysql_data:\n'
        elif db_config.type == 'mongodb':
            compose_content += '  mongo_data:\n'
        
        compose_content += '  redis_data:\n'
        
        if config.monitoring.performance_monitoring:
            compose_content += '''  prometheus_data:
  grafana_data:
'''
        
        # Add networks section
        compose_content += '''
networks:
  app-network:
    driver: bridge
'''
        
        (project_path / "docker-compose.yml").write_text(compose_content)
        
        # Generate production docker-compose override
        prod_compose = '''version: '3.8'

services:
  app:
    build:
      target: production
    environment:
      - DEBUG=false
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app-network
'''
        
        (project_path / "docker-compose.prod.yml").write_text(prod_compose)
    
    def _generate_dockerignore(self, project_path: Path):
        """Generate .dockerignore file."""
        config = self.config_manager.project
        
        dockerignore_content = '''# Git
.git
.gitignore

# Documentation
README.md
docs/
*.md

# Development files
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

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
.coverage
.pytest_cache/

# Dev automation
.dev_automation/

# CI/CD
.github/
.gitlab-ci.yml
Jenkinsfile

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

'''
        
        if config.language == 'python':
            dockerignore_content += '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
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
venv/
env/
.venv/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json

'''
        elif config.language in ['javascript', 'typescript']:
            dockerignore_content += '''# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# Build outputs
build/
dist/
.next/
.nuxt/

'''
        
        (project_path / ".dockerignore").write_text(dockerignore_content)
    
    def _get_default_db_url(self) -> str:
        """Get default database URL based on configuration."""
        db_config = self.config_manager.database
        
        if db_config.type == 'postgresql':
            return f"postgresql://{db_config.username or 'postgres'}:postgres@postgres:{db_config.port}/{db_config.name}"
        elif db_config.type == 'mysql':
            return f"mysql://{db_config.username or 'mysql'}:mysql@mysql:{db_config.port}/{db_config.name}"
        elif db_config.type == 'mongodb':
            return f"mongodb://{db_config.username or 'mongo'}:mongo@mongo:27017/{db_config.name}"
        else:
            return "sqlite:///./app.db" 
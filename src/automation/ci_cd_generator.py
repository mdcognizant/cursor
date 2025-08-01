"""
CI/CD Pipeline Generator for Development Automation Suite
Generates CI/CD configurations for different platforms.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from src.core.config_manager import ConfigManager

class CICDGenerator:
    """Generates CI/CD pipeline configurations."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def generate_pipeline(self, project_path: Path):
        """Generate CI/CD pipeline based on configuration."""
        config = self.config_manager.cicd
        
        if config.platform == 'github_actions':
            self._generate_github_actions(project_path)
        elif config.platform == 'gitlab_ci':
            self._generate_gitlab_ci(project_path)
        elif config.platform == 'jenkins':
            self._generate_jenkins(project_path)
        else:
            self._generate_github_actions(project_path)  # Default
    
    def _generate_github_actions(self, project_path: Path):
        """Generate GitHub Actions workflow."""
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        config = self.config_manager
        language = config.project.language
        
        if language == 'python':
            workflow_content = self._get_python_github_workflow()
        elif language in ['javascript', 'typescript']:
            workflow_content = self._get_nodejs_github_workflow()
        else:
            workflow_content = self._get_generic_github_workflow()
        
        (workflows_dir / "ci.yml").write_text(workflow_content)
        
        # Generate additional workflows
        if config.cicd.auto_deploy:
            deploy_workflow = self._get_deploy_github_workflow()
            (workflows_dir / "deploy.yml").write_text(deploy_workflow)
    
    def _get_python_github_workflow(self) -> str:
        """Get Python GitHub Actions workflow."""
        config = self.config_manager
        
        return f'''name: CI/CD Pipeline

on:
  push:
    branches: [ {config.git.default_branch}, develop ]
  pull_request:
    branches: [ {config.git.default_branch} ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements*.txt') }}}}
        restore-keys: |
          ${{{{ runner.os }}}}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
    
    - name: Lint with {config.development.linter}
      run: |
        {config.development.linter} src tests
    
    - name: Format check with {config.development.code_formatter}
      run: |
        {config.development.code_formatter} --check src tests
    
    - name: Type check with {config.development.type_checker}
      run: |
        {config.development.type_checker} src
    
    - name: Test with pytest
      run: |
        {config.cicd.test_command} --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install security tools
      run: |
        pip install bandit safety
    
    - name: Run security scan with bandit
      run: |
        bandit -r src/
    
    - name: Check dependencies with safety
      run: |
        safety check

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/{config.git.default_branch}'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install build tools
      run: |
        pip install build wheel
    
    - name: Build package
      run: |
        python -m build
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist
        path: dist/

  docker:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/{config.git.default_branch}'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to DockerHub
      uses: docker/login-action@v3
      with:
        username: ${{{{ secrets.DOCKER_USERNAME }}}}
        password: ${{{{ secrets.DOCKER_PASSWORD }}}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ${{{{ secrets.DOCKER_USERNAME }}}}/{config.project.name.lower().replace(' ', '-')}:latest
          ${{{{ secrets.DOCKER_USERNAME }}}}/{config.project.name.lower().replace(' ', '-')}:${{{{ github.sha }}}}
        cache-from: type=gha
        cache-to: type=gha,mode=max
'''
    
    def _get_nodejs_github_workflow(self) -> str:
        """Get Node.js GitHub Actions workflow."""
        config = self.config_manager
        
        return f'''name: CI/CD Pipeline

on:
  push:
    branches: [ {config.git.default_branch}, develop ]
  pull_request:
    branches: [ {config.git.default_branch} ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]

    steps:
    - uses: actions/checkout@v4
    
    - name: Use Node.js ${{{{ matrix.node-version }}}}
      uses: actions/setup-node@v4
      with:
        node-version: ${{{{ matrix.node-version }}}}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Lint code
      run: npm run lint
    
    - name: Format check
      run: npm run format:check
    
    - name: Type check
      run: npm run type-check
      if: matrix.node-version == '18.x'
    
    - name: Run tests
      run: npm test -- --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Use Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18.x'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run security audit
      run: npm audit
    
    - name: Run security scan
      run: npx audit-ci --moderate

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/{config.git.default_branch}'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Use Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18.x'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build application
      run: npm run build
    
    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: build
        path: build/
'''
    
    def _get_generic_github_workflow(self) -> str:
        """Get generic GitHub Actions workflow."""
        config = self.config_manager
        
        return f'''name: CI/CD Pipeline

on:
  push:
    branches: [ {config.git.default_branch}, develop ]
  pull_request:
    branches: [ {config.git.default_branch} ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup environment
      run: |
        echo "Setting up environment for {config.project.language}"
    
    - name: Install dependencies
      run: |
        echo "Installing dependencies..."
        # Add your dependency installation commands here
    
    - name: Run tests
      run: |
        echo "Running tests..."
        {config.cicd.test_command if config.cicd.test_command else 'echo "No test command configured"'}
    
    - name: Build application
      run: |
        echo "Building application..."
        {config.cicd.build_command if config.cicd.build_command else 'echo "No build command configured"'}
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: artifacts
        path: .
'''
    
    def _get_deploy_github_workflow(self) -> str:
        """Get deployment GitHub Actions workflow."""
        config = self.config_manager
        
        return f'''name: Deploy

on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types:
      - completed
    branches:
      - {config.git.default_branch}

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{{{ github.event.workflow_run.conclusion == 'success' }}}}
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        echo "Deploying to production..."
        {config.cicd.deploy_command if config.cicd.deploy_command else 'echo "No deploy command configured"'}
    
    - name: Health check
      run: |
        echo "Running health check..."
        # Add health check commands here
    
    - name: Notify deployment
      run: |
        echo "Deployment completed successfully!"
'''
    
    def _generate_gitlab_ci(self, project_path: Path):
        """Generate GitLab CI configuration."""
        config = self.config_manager
        language = config.project.language
        
        if language == 'python':
            ci_content = self._get_python_gitlab_ci()
        elif language in ['javascript', 'typescript']:
            ci_content = self._get_nodejs_gitlab_ci()
        else:
            ci_content = self._get_generic_gitlab_ci()
        
        (project_path / ".gitlab-ci.yml").write_text(ci_content)
    
    def _get_python_gitlab_ci(self) -> str:
        """Get Python GitLab CI configuration."""
        config = self.config_manager
        
        return f'''# GitLab CI/CD Pipeline for {config.project.name}

stages:
  - test
  - security
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python -V
  - pip install virtualenv
  - virtualenv venv
  - source venv/bin/activate
  - pip install -e ".[dev]"

test:
  stage: test
  image: python:3.10
  script:
    - {config.development.linter} src tests
    - {config.development.code_formatter} --check src tests
    - {config.development.type_checker} src
    - {config.cicd.test_command} --cov=src --cov-report=xml
  coverage: '/TOTAL.*\\s+(\\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

security:
  stage: security
  image: python:3.10
  script:
    - pip install bandit safety
    - bandit -r src/
    - safety check
  allow_failure: true

build:
  stage: build
  image: python:3.10
  script:
    - pip install build
    - python -m build
  artifacts:
    paths:
      - dist/
  only:
    - {config.git.default_branch}

deploy:
  stage: deploy
  image: python:3.10
  script:
    - echo "Deploying application..."
    - {config.cicd.deploy_command if config.cicd.deploy_command else 'echo "No deploy command configured"'}
  only:
    - {config.git.default_branch}
  when: manual
'''
    
    def _get_nodejs_gitlab_ci(self) -> str:
        """Get Node.js GitLab CI configuration."""
        config = self.config_manager
        
        return f'''# GitLab CI/CD Pipeline for {config.project.name}

image: node:18

stages:
  - test
  - security
  - build
  - deploy

cache:
  paths:
    - node_modules/

before_script:
  - npm ci

test:
  stage: test
  script:
    - npm run lint
    - npm run format:check
    - npm run type-check
    - npm test -- --coverage
  coverage: '/Lines\\s*:\\s*(\\d+\\.?\\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

security:
  stage: security
  script:
    - npm audit
    - npx audit-ci --moderate
  allow_failure: true

build:
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - build/
  only:
    - {config.git.default_branch}

deploy:
  stage: deploy
  script:
    - echo "Deploying application..."
    - {config.cicd.deploy_command if config.cicd.deploy_command else 'echo "No deploy command configured"'}
  only:
    - {config.git.default_branch}
  when: manual
'''
    
    def _get_generic_gitlab_ci(self) -> str:
        """Get generic GitLab CI configuration."""
        config = self.config_manager
        
        return f'''# GitLab CI/CD Pipeline for {config.project.name}

stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - echo "Running tests for {config.project.language}"
    - {config.cicd.test_command if config.cicd.test_command else 'echo "No test command configured"'}

build:
  stage: build
  script:
    - echo "Building application"
    - {config.cicd.build_command if config.cicd.build_command else 'echo "No build command configured"'}
  artifacts:
    paths:
      - .
  only:
    - {config.git.default_branch}

deploy:
  stage: deploy
  script:
    - echo "Deploying application"
    - {config.cicd.deploy_command if config.cicd.deploy_command else 'echo "No deploy command configured"'}
  only:
    - {config.git.default_branch}
  when: manual
'''
    
    def _generate_jenkins(self, project_path: Path):
        """Generate Jenkins pipeline."""
        config = self.config_manager
        language = config.project.language
        
        if language == 'python':
            pipeline_content = self._get_python_jenkins_pipeline()
        elif language in ['javascript', 'typescript']:
            pipeline_content = self._get_nodejs_jenkins_pipeline()
        else:
            pipeline_content = self._get_generic_jenkins_pipeline()
        
        (project_path / "Jenkinsfile").write_text(pipeline_content)
    
    def _get_python_jenkins_pipeline(self) -> str:
        """Get Python Jenkins pipeline."""
        config = self.config_manager
        
        template = """pipeline {
    agent any
    
    environment {
        PROJECT_NAME = 'PROJECT_NAME_PLACEHOLDER'
        PYTHON_VERSION = '3.10'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh \"\"\"
                    python${PYTHON_VERSION} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -e ".[dev]"
                \"\"\"
            }
        }
        
        stage('Lint') {
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    LINTER_PLACEHOLDER src tests
                \"\"\"
            }
        }
        
        stage('Format Check') {
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    FORMATTER_PLACEHOLDER --check src tests
                \"\"\"
            }
        }
        
        stage('Type Check') {
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    TYPE_CHECKER_PLACEHOLDER src
                \"\"\"
            }
        }
        
        stage('Test') {
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    TEST_COMMAND_PLACEHOLDER --cov=src --cov-report=xml --junitxml=test-results.xml
                \"\"\"
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverageGlobal(coverageResults: [[path: 'coverage.xml']])
                }
            }
        }
        
        stage('Security') {
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    pip install bandit safety
                    bandit -r src/ -f json -o bandit-report.json || true
                    safety check --json --output safety-report.json || true
                \"\"\"
            }
        }
        
        stage('Build') {
            when {
                branch 'DEFAULT_BRANCH_PLACEHOLDER'
            }
            steps {
                sh \"\"\"
                    . venv/bin/activate
                    pip install build
                    python -m build
                \"\"\"
                archiveArtifacts artifacts: 'dist/*', fingerprint: true
            }
        }
        
        stage('Deploy') {
            when {
                branch 'DEFAULT_BRANCH_PLACEHOLDER'
            }
            steps {
                echo 'Deploying to production...'
                // Add deployment steps here
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}"""

        # Replace placeholders
        pipeline = template.replace('PROJECT_NAME_PLACEHOLDER', config.project.name)
        pipeline = pipeline.replace('LINTER_PLACEHOLDER', config.development.linter)
        pipeline = pipeline.replace('FORMATTER_PLACEHOLDER', config.development.code_formatter)
        pipeline = pipeline.replace('TYPE_CHECKER_PLACEHOLDER', config.development.type_checker)
        pipeline = pipeline.replace('TEST_COMMAND_PLACEHOLDER', config.cicd.test_command)
        pipeline = pipeline.replace('DEFAULT_BRANCH_PLACEHOLDER', config.git.default_branch)
        
        return pipeline
    
    def _get_nodejs_jenkins_pipeline(self) -> str:
        """Get Node.js Jenkins pipeline."""
        config = self.config_manager
        
        return f'''pipeline {{
    agent any
    
    environment {{
        PROJECT_NAME = '{config.project.name}'
        NODE_VERSION = '18'
    }}
    
    tools {{
        nodejs "${{NODE_VERSION}}"
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Install') {{
            steps {{
                sh 'npm ci'
            }}
        }}
        
        stage('Lint') {{
            steps {{
                sh 'npm run lint'
            }}
        }}
        
        stage('Format Check') {{
            steps {{
                sh 'npm run format:check'
            }}
        }}
        
        stage('Type Check') {{
            steps {{
                sh 'npm run type-check'
            }}
        }}
        
        stage('Test') {{
            steps {{
                sh 'npm test -- --coverage --reporters=default --reporters=jest-junit'
            }}
            post {{
                always {{
                    junit 'junit.xml'
                    publishCoverageGlobal(coverageResults: [[path: 'coverage/cobertura-coverage.xml']])
                }}
            }}
        }}
        
        stage('Security') {{
            steps {{
                sh '''
                    npm audit --audit-level moderate --json > npm-audit.json || true
                    npx audit-ci --moderate || true
                '''
            }}
        }}
        
        stage('Build') {{
            when {{
                branch '{config.git.default_branch}'
            }}
            steps {{
                sh 'npm run build'
                archiveArtifacts artifacts: 'build/**/*', fingerprint: true
            }}
        }}
        
        stage('Deploy') {{
            when {{
                branch '{config.git.default_branch}'
            }}
            steps {{
                script {{
                    if ('{config.cicd.deploy_command}') {{
                        sh '{config.cicd.deploy_command}'
                    }} else {{
                        echo "No deploy command configured"
                    }}
                }}
            }}
        }}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
        failure {{
            emailext (
                subject: "Build Failed: ${{env.JOB_NAME}} - ${{env.BUILD_NUMBER}}",
                body: "Build failed. Check console output at ${{env.BUILD_URL}}",
                to: "${{env.CHANGE_AUTHOR_EMAIL}}"
            )
        }}
    }}
}}
'''
    
    def _get_generic_jenkins_pipeline(self) -> str:
        """Get generic Jenkins pipeline."""
        config = self.config_manager
        
        return f'''pipeline {{
    agent any
    
    environment {{
        PROJECT_NAME = '{config.project.name}'
        PROJECT_LANGUAGE = '{config.project.language}'
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Setup') {{
            steps {{
                echo "Setting up environment for ${{PROJECT_LANGUAGE}}"
                // Add your setup commands here
            }}
        }}
        
        stage('Test') {{
            steps {{
                script {{
                    if ('{config.cicd.test_command}') {{
                        sh '{config.cicd.test_command}'
                    }} else {{
                        echo "No test command configured"
                    }}
                }}
            }}
        }}
        
        stage('Build') {{
            when {{
                branch '{config.git.default_branch}'
            }}
            steps {{
                script {{
                    if ('{config.cicd.build_command}') {{
                        sh '{config.cicd.build_command}'
                    }} else {{
                        echo "No build command configured"
                    }}
                }}
            }}
        }}
        
        stage('Deploy') {{
            when {{
                branch '{config.git.default_branch}'
            }}
            steps {{
                script {{
                    if ('{config.cicd.deploy_command}') {{
                        sh '{config.cicd.deploy_command}'
                    }} else {{
                        echo "No deploy command configured"
                    }}
                }}
            }}
        }}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
    }}
}}
''' 
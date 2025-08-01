#!/usr/bin/env python3
"""
Dual News Provider Configuration
Manages API keys and settings for currentsapi.services and newsdata.io integration

Features:
- Environment variable support
- API key validation
- Rate limiting configuration
- Provider priority settings
- Development vs Production configs
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class APIProviderConfig:
    """Configuration for individual news API provider"""
    name: str
    api_key: str
    base_url: str
    daily_limit: int
    enabled: bool = True
    priority: int = 1
    timeout: int = 30
    retries: int = 3

@dataclass
class DualNewsConfig:
    """Configuration for dual news provider system"""
    currents: APIProviderConfig
    newsdata: APIProviderConfig
    cache_ttl: int = 300
    cache_enabled: bool = True
    log_level: str = "INFO"
    rate_limit_buffer: int = 5  # Stop N requests before hitting limit
    environment: str = "development"

class DualNewsConfigManager:
    """Manages configuration for dual news provider integration"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or ".env"
        self.config = None
        self.load_configuration()
    
    def load_configuration(self) -> DualNewsConfig:
        """Load configuration from environment or defaults"""
        
        # Load environment variables from .env file if it exists
        self._load_env_file()
        
        # Get API keys from environment
        currents_key = os.getenv('CURRENTS_API_KEY')
        newsdata_key = os.getenv('NEWSDATA_API_KEY')
        
        # Create provider configurations
        currents_config = APIProviderConfig(
            name="Currents API",
            api_key=currents_key or "YOUR_CURRENTS_API_KEY",
            base_url="https://api.currentsapi.services/v1",
            daily_limit=int(os.getenv('CURRENTS_DAILY_LIMIT', '200')),
            enabled=bool(currents_key),
            priority=int(os.getenv('CURRENTS_PRIORITY', '1')),
            timeout=int(os.getenv('CURRENTS_TIMEOUT', '30')),
            retries=int(os.getenv('CURRENTS_RETRIES', '3'))
        )
        
        newsdata_config = APIProviderConfig(
            name="NewsData.io",
            api_key=newsdata_key or "YOUR_NEWSDATA_API_KEY", 
            base_url="https://newsdata.io/api/1",
            daily_limit=int(os.getenv('NEWSDATA_DAILY_LIMIT', '200')),
            enabled=bool(newsdata_key),
            priority=int(os.getenv('NEWSDATA_PRIORITY', '2')),
            timeout=int(os.getenv('NEWSDATA_TIMEOUT', '30')),
            retries=int(os.getenv('NEWSDATA_RETRIES', '3'))
        )
        
        # Create main configuration
        self.config = DualNewsConfig(
            currents=currents_config,
            newsdata=newsdata_config,
            cache_ttl=int(os.getenv('CACHE_TTL', '300')),
            cache_enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            rate_limit_buffer=int(os.getenv('RATE_LIMIT_BUFFER', '5')),
            environment=os.getenv('ENVIRONMENT', 'development')
        )
        
        return self.config
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        env_path = Path(self.config_file)
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "provider_status": {}
        }
        
        # Validate Currents API
        currents_status = self._validate_provider(self.config.currents, "Currents API")
        validation_result["provider_status"]["currents"] = currents_status
        if not currents_status["valid"]:
            validation_result["errors"].extend(currents_status["errors"])
        
        # Validate NewsData.io
        newsdata_status = self._validate_provider(self.config.newsdata, "NewsData.io")
        validation_result["provider_status"]["newsdata"] = newsdata_status
        if not newsdata_status["valid"]:
            validation_result["errors"].extend(newsdata_status["errors"])
        
        # Check if at least one provider is configured
        if not currents_status["valid"] and not newsdata_status["valid"]:
            validation_result["valid"] = False
            validation_result["errors"].append("At least one news provider must be properly configured")
        
        # Warnings
        if not currents_status["valid"] or not newsdata_status["valid"]:
            validation_result["warnings"].append("Only one provider configured - no failover capability")
        
        # Overall validation
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def _validate_provider(self, provider: APIProviderConfig, provider_name: str) -> Dict[str, Any]:
        """Validate individual provider configuration"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check API key
        if not provider.api_key or provider.api_key.startswith("YOUR_"):
            result["valid"] = False
            result["errors"].append(f"{provider_name}: API key not configured")
        elif len(provider.api_key) < 10:
            result["valid"] = False
            result["errors"].append(f"{provider_name}: API key appears invalid (too short)")
        
        # Check URL
        if not provider.base_url or not provider.base_url.startswith('http'):
            result["valid"] = False
            result["errors"].append(f"{provider_name}: Invalid base URL")
        
        # Check limits
        if provider.daily_limit <= 0:
            result["warnings"].append(f"{provider_name}: Daily limit is 0 or negative")
        
        return result
    
    def get_setup_instructions(self) -> str:
        """Generate setup instructions based on current configuration"""
        validation = self.validate_configuration()
        
        instructions = []
        instructions.append("🔑 Dual News Provider Setup Instructions")
        instructions.append("=" * 50)
        
        if validation["valid"]:
            instructions.append("✅ Configuration is valid and ready to use!")
            instructions.append("")
            instructions.append("Configured Providers:")
            for provider_name, status in validation["provider_status"].items():
                if status["valid"]:
                    provider_config = getattr(self.config, provider_name)
                    instructions.append(f"  ✅ {provider_config.name}: {provider_config.daily_limit} requests/day")
            
        else:
            instructions.append("⚠️ Configuration needs attention:")
            instructions.append("")
            for error in validation["errors"]:
                instructions.append(f"  ❌ {error}")
            
            instructions.append("")
            instructions.append("📋 Setup Steps:")
            
            # Currents API setup
            if not validation["provider_status"]["currents"]["valid"]:
                instructions.extend([
                    "",
                    "1. Get Currents API Key:",
                    "   • Visit: https://currentsapi.services/",
                    "   • Sign up for free account",
                    "   • Copy your API key",
                    "   • Set environment variable: CURRENTS_API_KEY=your_key_here"
                ])
            
            # NewsData.io setup  
            if not validation["provider_status"]["newsdata"]["valid"]:
                instructions.extend([
                    "",
                    "2. Get NewsData.io API Key:",
                    "   • Visit: https://newsdata.io/",
                    "   • Sign up for free account", 
                    "   • Copy your API key",
                    "   • Set environment variable: NEWSDATA_API_KEY=your_key_here"
                ])
            
            instructions.extend([
                "",
                "3. Create .env file in universal-api-bridge directory:",
                "   CURRENTS_API_KEY=your_currents_key_here",
                "   NEWSDATA_API_KEY=your_newsdata_key_here",
                "",
                "4. Run the demo:",
                "   python dual_news_provider_integration.py"
            ])
        
        # Add warnings
        if validation["warnings"]:
            instructions.append("")
            instructions.append("⚠️ Warnings:")
            for warning in validation["warnings"]:
                instructions.append(f"  • {warning}")
        
        return "\n".join(instructions)
    
    def create_sample_env_file(self, filename: str = ".env.example"):
        """Create a sample environment file"""
        sample_content = """# Dual News Provider Configuration
# Copy this file to .env and fill in your actual API keys

# Currents API Configuration (https://currentsapi.services/)
CURRENTS_API_KEY=your_currents_api_key_here
CURRENTS_DAILY_LIMIT=200
CURRENTS_PRIORITY=1
CURRENTS_TIMEOUT=30

# NewsData.io Configuration (https://newsdata.io/)
NEWSDATA_API_KEY=your_newsdata_api_key_here
NEWSDATA_DAILY_LIMIT=200
NEWSDATA_PRIORITY=2
NEWSDATA_TIMEOUT=30

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=300

# System Configuration
LOG_LEVEL=INFO
RATE_LIMIT_BUFFER=5
ENVIRONMENT=development

# Optional: Increase limits for paid plans
# CURRENTS_DAILY_LIMIT=1000
# NEWSDATA_DAILY_LIMIT=1000
"""
        
        with open(filename, 'w') as f:
            f.write(sample_content)
        
        return f"Sample configuration file created: {filename}"
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """Get configuration suitable for runtime use"""
        return {
            "providers": {
                "currents": {
                    "name": self.config.currents.name,
                    "enabled": self.config.currents.enabled,
                    "daily_limit": self.config.currents.daily_limit,
                    "priority": self.config.currents.priority
                },
                "newsdata": {
                    "name": self.config.newsdata.name,
                    "enabled": self.config.newsdata.enabled,
                    "daily_limit": self.config.newsdata.daily_limit,
                    "priority": self.config.newsdata.priority
                }
            },
            "cache": {
                "enabled": self.config.cache_enabled,
                "ttl": self.config.cache_ttl
            },
            "system": {
                "log_level": self.config.log_level,
                "environment": self.config.environment,
                "rate_limit_buffer": self.config.rate_limit_buffer
            }
        }

def setup_logging(config: DualNewsConfig):
    """Configure logging based on configuration"""
    log_level = getattr(logging, config.log_level.upper())
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if config.environment == "production":
        # Production logging to file
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler('dual_news.log'),
                logging.StreamHandler()
            ]
        )
    else:
        # Development logging to console
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler()]
        )

def main():
    """Demo configuration management"""
    print("🔧 Dual News Provider Configuration Manager")
    print("=" * 50)
    
    # Initialize configuration manager
    config_manager = DualNewsConfigManager()
    
    # Show current configuration status
    print("\n📊 Current Configuration:")
    validation = config_manager.validate_configuration()
    
    print(f"Valid: {'✅' if validation['valid'] else '❌'}")
    print(f"Currents API: {'✅' if validation['provider_status']['currents']['valid'] else '❌'}")
    print(f"NewsData.io: {'✅' if validation['provider_status']['newsdata']['valid'] else '❌'}")
    
    # Show setup instructions
    print("\n" + config_manager.get_setup_instructions())
    
    # Create sample .env file
    print(f"\n{config_manager.create_sample_env_file()}")
    
    # Show runtime configuration
    print(f"\n📋 Runtime Configuration:")
    runtime_config = config_manager.get_runtime_config()
    import json
    print(json.dumps(runtime_config, indent=2))

if __name__ == "__main__":
    main() 
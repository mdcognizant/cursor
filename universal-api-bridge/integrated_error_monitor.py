#!/usr/bin/env python3
"""
Organization-Friendly Error Monitor
==================================
Lightweight error monitoring for corporate environments.
No localhost dependencies - works with direct file access.

Features:
- Browser console error tracking guidance
- External API monitoring suggestions
- Manual troubleshooting assistance
- Organization-friendly diagnostics

Author: Assistant
Date: 2025-01-27
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class OrganizationFriendlyErrorMonitor:
    def __init__(self):
        self.current_dir = Path(__file__).parent.absolute()
        self.error_log_file = self.current_dir / "organization_errors.json"
        self.start_time = datetime.now()
        self.error_stats = defaultdict(int)
        
        # Setup logging for local errors only
        self.setup_logging()
        
        # Common error patterns for organization environments
        self.organization_error_patterns = {
            'cors_error': [
                'Access to fetch at',
                'CORS policy',
                'Cross-Origin Request',
                'blocked by CORS'
            ],
            'firewall_block': [
                'ERR_NETWORK_ACCESS_DENIED',
                'ERR_INTERNET_DISCONNECTED',
                'ERR_PROXY_CONNECTION_FAILED',
                'Connection refused'
            ],
            'api_key_issue': [
                'API key',
                'Authentication failed',
                'Invalid credentials',
                'Unauthorized'
            ],
            'file_access': [
                'file://',
                'Not allowed to load local resource',
                'Cross origin requests'
            ]
        }

    def setup_logging(self):
        """Setup local error logging"""
        log_file = self.current_dir / "platform_errors.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Organization-friendly error monitor initialized")

    def log_error(self, error_type, message, context=None):
        """Log an error with organization-friendly context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'context': context or {},
            'suggestions': self.get_error_suggestions(error_type, message)
        }
        
        self.error_stats[error_type] += 1
        self.logger.error(f"{error_type}: {message}")
        
        # Save to JSON file for review
        self.save_error_to_file(error_entry)
        
        return error_entry

    def get_error_suggestions(self, error_type, message):
        """Get organization-specific error suggestions"""
        suggestions = {
            'cors_error': [
                "Open platform files directly in browser instead of via localhost",
                "Use file:// protocol for local access",
                "Check if corporate firewall is blocking external APIs",
                "Try using the API test page to verify connectivity"
            ],
            'firewall_block': [
                "Contact IT department about external API access",
                "Check corporate proxy settings",
                "Verify NewsData.io and Currents API domains are allowed",
                "Test with different network connection if possible"
            ],
            'api_key_issue': [
                "Verify API keys are correctly configured in platform",
                "Check if API keys have been rate limited",
                "Test individual APIs using the API test page",
                "Contact API provider if keys appear invalid"
            ],
            'file_access': [
                "Ensure platform files are in accessible directory",
                "Use file:// protocol instead of localhost URLs",
                "Check browser security settings for local file access",
                "Try different browser if file access is blocked"
            ]
        }
        
        return suggestions.get(error_type, [
            "Check browser console for detailed error information",
            "Verify network connectivity to external APIs",
            "Contact IT support if issues persist"
        ])

    def save_error_to_file(self, error_entry):
        """Save error to JSON file for review"""
        try:
            errors = []
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)
            
            errors.append(error_entry)
            
            # Keep only last 100 errors
            if len(errors) > 100:
                errors = errors[-100:]
            
            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not save error to file: {e}")

    def generate_troubleshooting_guide(self):
        """Generate organization-specific troubleshooting guide"""
        guide = {
            'title': 'Organization-Friendly News Platform Troubleshooting',
            'timestamp': datetime.now().isoformat(),
            'common_issues': {
                'api_not_loading': {
                    'symptoms': ['Refresh News shows cached articles', 'API calls = 0'],
                    'causes': ['File:// protocol blocking external requests', 'Corporate firewall'],
                    'solutions': [
                        'Use API test page to verify connectivity',
                        'Check browser console for CORS errors',
                        'Contact IT about external API access',
                        'Try different browser or network'
                    ]
                },
                'images_not_loading': {
                    'symptoms': ['Articles show placeholder images', 'Image load errors'],
                    'causes': ['External image URLs blocked', 'Firewall restrictions'],
                    'solutions': [
                        'Platform includes fallback images',
                        'Check if Unsplash.com is accessible',
                        'Images are non-critical for functionality'
                    ]
                },
                'platform_not_opening': {
                    'symptoms': ['File not found errors', 'Blank page'],
                    'causes': ['File path issues', 'Browser restrictions'],
                    'solutions': [
                        'Verify platform files exist in directory',
                        'Use full file path to open platform',
                        'Check browser local file permissions'
                    ]
                }
            },
            'external_api_status': {
                'newsdata_io': {
                    'endpoint': 'https://newsdata.io/api/1/latest',
                    'test_method': 'Use api_test_external.html',
                    'limits': '200 calls/day, 50 articles per call'
                },
                'currents_api': {
                    'endpoint': 'https://api.currentsapi.services/v1/latest-news',
                    'test_method': 'Use api_test_external.html',
                    'limits': '50 articles per call'
                }
            },
            'browser_console_guide': {
                'how_to_open': 'Press F12 or Ctrl+Shift+I',
                'what_to_check': [
                    'Console tab for JavaScript errors',
                    'Network tab for failed API requests',
                    'Security tab for blocked content'
                ]
            }
        }
        
        try:
            guide_file = self.current_dir / "troubleshooting_guide.json"
            with open(guide_file, 'w') as f:
                json.dump(guide, f, indent=2)
            print(f"📋 Troubleshooting guide saved: {guide_file}")
        except Exception as e:
            print(f"⚠️ Could not save troubleshooting guide: {e}")
        
        return guide

    def check_platform_compatibility(self):
        """Check platform compatibility for organization environment"""
        compatibility = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'Organization-Friendly',
            'localhost_dependencies': False,
            'files': {},
            'recommendations': []
        }
        
        # Check required files
        required_files = [
            'enhanced_news_platform_ultimate_v2.html',
            'api_test_external.html'
        ]
        
        for filename in required_files:
            file_path = self.current_dir / filename
            compatibility['files'][filename] = {
                'exists': file_path.exists(),
                'path': str(file_path),
                'size_kb': file_path.stat().st_size // 1024 if file_path.exists() else 0
            }
        
        # Generate recommendations
        if not compatibility['files']['enhanced_news_platform_ultimate_v2.html']['exists']:
            compatibility['recommendations'].append("Missing main platform file")
        
        if not compatibility['files']['api_test_external.html']['exists']:
            compatibility['recommendations'].append("Missing API test page - create for diagnostics")
        
        compatibility['recommendations'].extend([
            "Use file:// protocol instead of localhost URLs",
            "Test external APIs before using main platform",
            "Check corporate firewall settings for API access",
            "Keep browser console open for error monitoring"
        ])
        
        return compatibility

    def get_status(self):
        """Get monitor status"""
        uptime = datetime.now() - self.start_time
        
        return {
            'running': True,
            'uptime_seconds': int(uptime.total_seconds()),
            'error_count': sum(self.error_stats.values()),
            'error_types': dict(self.error_stats),
            'monitor_type': 'organization_friendly',
            'localhost_dependencies': False
        }

def start_integrated_monitoring():
    """Start organization-friendly monitoring"""
    monitor = OrganizationFriendlyErrorMonitor()
    monitor.logger.info("Organization-friendly error monitoring started")
    
    # Generate initial troubleshooting guide
    monitor.generate_troubleshooting_guide()
    
    # Check platform compatibility
    compatibility = monitor.check_platform_compatibility()
    monitor.logger.info(f"Platform compatibility check completed")
    
    return monitor

def stop_monitoring():
    """Stop monitoring (no-op for organization-friendly version)"""
    pass

def get_monitor_status():
    """Get monitoring status"""
    return {
        'running': True,
        'monitor_type': 'organization_friendly',
        'localhost_dependencies': False,
        'uptime_seconds': 0
    }

def main():
    """Main function for standalone execution"""
    print("🛡️ Organization-Friendly Error Monitor")
    print("=" * 40)
    
    monitor = start_integrated_monitoring()
    
    print("✅ Error monitor initialized")
    print("📋 Troubleshooting guide generated")
    print("🔧 Platform compatibility checked")
    print()
    print("FEATURES:")
    print("  • Browser console error guidance")
    print("  • External API troubleshooting")
    print("  • Corporate firewall diagnostics")
    print("  • No localhost dependencies")
    print()
    print("FILES CREATED:")
    print("  • troubleshooting_guide.json")
    print("  • platform_errors.log")
    
    return monitor

if __name__ == "__main__":
    main() 
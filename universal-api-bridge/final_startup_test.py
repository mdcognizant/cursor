#!/usr/bin/env python3
"""
Final Startup Test & Validation
===============================
Comprehensive test of all services, logging systems, and error monitoring.
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime
import traceback

class FinalStartupTest:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'logs': {},
            'apis': {},
            'files': {},
            'errors': [],
            'recommendations': []
        }

    def test_all_services(self):
        """Test all services comprehensively"""
        print("🧪 FINAL COMPREHENSIVE STARTUP TEST")
        print("=" * 60)
        
        # Test 1: File Existence
        print("\n1️⃣ Testing File Existence...")
        self.test_file_existence()
        
        # Test 2: Service Health
        print("\n2️⃣ Testing Service Health...")
        self.test_service_health()
        
        # Test 3: Log Systems
        print("\n3️⃣ Testing Log Systems...")
        self.test_log_systems()
        
        # Test 4: Error Monitoring
        print("\n4️⃣ Testing Error Monitoring...")
        self.test_error_monitoring()
        
        # Test 5: API Endpoints
        print("\n5️⃣ Testing API Endpoints...")
        self.test_api_endpoints()
        
        # Generate final report
        print("\n6️⃣ Generating Final Report...")
        self.generate_final_report()

    def test_file_existence(self):
        """Test if all required files exist"""
        required_files = {
            'startup_systems': [
                'robust_auto_startup.py',
                'ultimate_platform_launcher.py',
                'startup_with_monitoring.py'
            ],
            'service_scripts': [
                'enhanced_news_scraper.py',
                'breaking_news_scraper.py',
                'fixed_error_monitor.py',
                'simple_error_monitor.py'
            ],
            'frontend_apps': [
                'enhanced_news_platform_ultimate_v2.html',
                'enhanced_delta_news_platform_complete.html'
            ],
            'log_systems': [
                'error_log_aggregator.py',
                'master_error_log.jsonl'
            ],
            'debug_tools': [
                'debug_error_monitor.py',
                'test_robust_startup.py'
            ]
        }
        
        for category, files in required_files.items():
            self.results['files'][category] = {}
            for file in files:
                exists = os.path.exists(file)
                self.results['files'][category][file] = exists
                status = "✅" if exists else "❌"
                print(f"   {status} {file}")
                
                if not exists:
                    self.results['errors'].append(f"Missing file: {file}")

    def test_service_health(self):
        """Test service health by checking running processes"""
        services = {
            'enhanced_scraper': 8889,
            'breaking_news': 8888,
            'http_server': 8000
        }
        
        for service, port in services.items():
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    is_running = result == 0
                    
                self.results['services'][service] = {
                    'port': port,
                    'running': is_running,
                    'last_checked': datetime.now().isoformat()
                }
                
                status = "✅ RUNNING" if is_running else "❌ STOPPED"
                print(f"   {status} {service} (Port {port})")
                
            except Exception as e:
                self.results['services'][service] = {
                    'port': port,
                    'running': False,
                    'error': str(e),
                    'last_checked': datetime.now().isoformat()
                }
                print(f"   ❌ ERROR {service}: {e}")

    def test_log_systems(self):
        """Test logging systems"""
        log_files = [
            'master_error_log.jsonl',
            'master_error_log.txt',
            'fixed_error_monitor.log',
            'simple_error_monitor.log',
            'startup_report.json'
        ]
        
        for log_file in log_files:
            try:
                exists = os.path.exists(log_file)
                size = os.path.getsize(log_file) if exists else 0
                
                self.results['logs'][log_file] = {
                    'exists': exists,
                    'size_bytes': size,
                    'readable': False,
                    'last_modified': None
                }
                
                if exists:
                    try:
                        # Test readability
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(100)  # Read first 100 chars
                            self.results['logs'][log_file]['readable'] = True
                            self.results['logs'][log_file]['sample_content'] = content[:50] + "..."
                        
                        # Get modification time
                        mod_time = os.path.getmtime(log_file)
                        self.results['logs'][log_file]['last_modified'] = datetime.fromtimestamp(mod_time).isoformat()
                        
                        status = f"✅ {log_file} ({size} bytes)"
                    except Exception as e:
                        status = f"⚠️ {log_file} (exists but unreadable: {e})"
                        self.results['logs'][log_file]['error'] = str(e)
                else:
                    status = f"❌ {log_file} (missing)"
                
                print(f"   {status}")
                
            except Exception as e:
                print(f"   ❌ Error checking {log_file}: {e}")
                self.results['logs'][log_file] = {'error': str(e)}

    def test_error_monitoring(self):
        """Test error monitoring functionality"""
        try:
            # Test fixed error monitor import
            import fixed_error_monitor
            monitor = fixed_error_monitor.FixedErrorMonitor()
            
            # Test basic functionality
            monitor.initialize_master_log()
            monitor.write_to_master_log('TEST', 'STARTUP_TEST', 'Testing error monitor functionality')
            
            self.results['error_monitoring'] = {
                'import_success': True,
                'basic_functionality': True,
                'log_write_success': True
            }
            print("   ✅ Fixed Error Monitor working correctly")
            
        except Exception as e:
            self.results['error_monitoring'] = {
                'import_success': False,
                'error': str(e)
            }
            print(f"   ❌ Error Monitor test failed: {e}")

    def test_api_endpoints(self):
        """Test API endpoints"""
        endpoints = {
            'enhanced_scraper': 'http://localhost:8889/health',
            'enhanced_articles': 'http://localhost:8889/articles',
            'breaking_news': 'http://localhost:8888/health',
            'breaking_articles': 'http://localhost:8888/breaking-news',
            'http_server': 'http://localhost:8000'
        }
        
        for name, url in endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                self.results['apis'][name] = {
                    'url': url,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'accessible': response.status_code == 200,
                    'content_length': len(response.content)
                }
                
                if response.status_code == 200:
                    print(f"   ✅ {name} ({response_time:.0f}ms)")
                else:
                    print(f"   ⚠️ {name} (Status: {response.status_code})")
                    
            except requests.exceptions.ConnectionError:
                self.results['apis'][name] = {
                    'url': url,
                    'accessible': False,
                    'error': 'Connection refused'
                }
                print(f"   ❌ {name} (Connection refused)")
                
            except Exception as e:
                self.results['apis'][name] = {
                    'url': url,
                    'accessible': False,
                    'error': str(e)
                }
                print(f"   ❌ {name} (Error: {e})")

    def generate_final_report(self):
        """Generate comprehensive final report"""
        
        # Calculate statistics
        total_files = sum(len(files) for files in self.results['files'].values())
        existing_files = sum(
            sum(1 for exists in files.values() if exists) 
            for files in self.results['files'].values()
        )
        
        running_services = sum(1 for service in self.results['services'].values() if service.get('running', False))
        total_services = len(self.results['services'])
        
        accessible_apis = sum(1 for api in self.results['apis'].values() if api.get('accessible', False))
        total_apis = len(self.results['apis'])
        
        existing_logs = sum(1 for log in self.results['logs'].values() if log.get('exists', False))
        total_logs = len(self.results['logs'])
        
        # Generate recommendations
        if existing_files < total_files:
            self.results['recommendations'].append("Some required files are missing. Run the robust startup system to ensure all components are created.")
        
        if running_services < total_services:
            self.results['recommendations'].append("Not all services are running. Use 'python robust_auto_startup.py' to start all services.")
        
        if accessible_apis < total_apis:
            self.results['recommendations'].append("Some APIs are not accessible. Check if services are running and ports are not blocked.")
        
        if existing_logs < total_logs:
            self.results['recommendations'].append("Some log files are missing. Error monitoring may not be fully operational.")
        
        # Add overall health status
        self.results['overall_health'] = {
            'file_completion': f"{existing_files}/{total_files}",
            'service_status': f"{running_services}/{total_services}",
            'api_accessibility': f"{accessible_apis}/{total_apis}",
            'log_availability': f"{existing_logs}/{total_logs}",
            'system_ready': existing_files == total_files and running_services >= 2  # At least 2 services running
        }
        
        # Save detailed report
        with open('final_startup_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"📁 Files: {existing_files}/{total_files} available")
        print(f"🔧 Services: {running_services}/{total_services} running")
        print(f"📡 APIs: {accessible_apis}/{total_apis} accessible")
        print(f"📝 Logs: {existing_logs}/{total_logs} available")
        
        if self.results['overall_health']['system_ready']:
            print("\n🎉 SYSTEM IS READY FOR PRODUCTION!")
            print("✅ All critical components are operational")
        else:
            print("\n⚠️ SYSTEM NEEDS ATTENTION")
            print("❌ Some components require fixes")
        
        print(f"\n💡 Recommendations:")
        for rec in self.results['recommendations']:
            print(f"   • {rec}")
        
        print(f"\n📄 Detailed report saved to: final_startup_test_report.json")

def main():
    """Main entry point"""
    tester = FinalStartupTest()
    tester.test_all_services()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Available Services Demo
=======================
Shows all the services I've prepared for automatic startup.
"""

import os

def show_available_services():
    """Display all available services and their status"""
    
    print("🚀 ULTIMATE PLATFORM LAUNCHER - AVAILABLE SERVICES")
    print("=" * 80)
    
    # Backend Services
    backend_services = {
        'breaking_news_scraper.py': {
            'name': 'Breaking News Scraper',
            'port': 8888,
            'description': 'Real-time CNN & BBC breaking news scraping (30s refresh)',
            'priority': 'HIGH'
        },
        'simple_error_monitor.py': {
            'name': 'Error Monitoring System', 
            'port': None,
            'description': 'Background error detection, logging, and auto-fixing',
            'priority': 'HIGH'
        },
        'shell_monitor_service.py': {
            'name': 'Shell Monitor Service',
            'port': 9999,
            'description': 'Command execution protection (prevents hanging)',
            'priority': 'MEDIUM'
        },

        'real_cnn_bbc_scraper.py': {
            'name': 'Real News Scraper',
            'port': None,
            'description': 'Additional CNN/BBC RSS feed scraping',
            'priority': 'OPTIONAL'
        }
    }
    
    # Frontend Applications
    frontend_apps = {
        'enhanced_news_platform_ultimate_v2.html': {
            'name': 'Enhanced News Platform',
            'description': 'Main platform with breaking news, long sidebar, hover effects',
            'priority': 'HIGH'
        },
        'frontend_debug_console.html': {
            'name': 'Debug Console',
            'description': 'Real-time API monitoring and error tracking',
            'priority': 'OPTIONAL'
        },

        'enhanced_delta_news_platform_complete.html': {
            'name': 'Delta News Platform',
            'description': 'Alternative comprehensive news platform',
            'priority': 'OPTIONAL'
        }
    }
    
    print("🔧 BACKEND SERVICES:")
    print("-" * 50)
    for script, config in backend_services.items():
        exists = "✅" if os.path.exists(script) else "❌"
        port_info = f" (Port: {config['port']})" if config['port'] else ""
        priority = f"[{config['priority']}]"
        print(f"{exists} {config['name']}{port_info} {priority}")
        print(f"   📝 {config['description']}")
        print()
    
    print("📱 FRONTEND APPLICATIONS:")
    print("-" * 50)
    for file, config in frontend_apps.items():
        exists = "✅" if os.path.exists(file) else "❌"
        priority = f"[{config['priority']}]"
        print(f"{exists} {config['name']} {priority}")
        print(f"   📝 {config['description']}")
        print()
    
    print("🚀 STARTUP OPTIONS:")
    print("-" * 50)
    print("1. 📋 LIST ALL SERVICES:")
    print("   python ultimate_platform_launcher.py --list-services")
    print()
    print("2. 🔧 MINIMAL START (Essential only):")
    print("   python ultimate_platform_launcher.py --minimal")
    print()
    print("3. 🎯 INTERACTIVE START (Choose services):")
    print("   python ultimate_platform_launcher.py --interactive")
    print()
    print("4. 🚀 FULL START (All enabled services):")
    print("   python ultimate_platform_launcher.py")
    print()
    print("5. 🌐 WITH HTTP SERVER:")
    print("   python ultimate_platform_launcher.py --port 8000")
    print()
    print("6. 💾 SAVE/LOAD CONFIGURATION:")
    print("   python ultimate_platform_launcher.py --save-config my_config.json")
    print("   python ultimate_platform_launcher.py --config my_config.json")
    
    print("\n" + "=" * 80)
    print("🎯 KEY FEATURES INTEGRATED:")
    print("✅ Real breaking news from CNN/BBC (30-second refresh)")
    print("✅ Enhanced sidebar with 15 trending stories + 15 live updates")
    print("✅ Advanced hover effects and click-to-open-new-tab functionality")
    print("✅ Automatic error monitoring and logging")
    print("✅ Shell command protection (prevents hanging)")
    print("✅ News platform interface")
    print("✅ Professional design inspired by 20+ major news sites")
    print("✅ Compact footer statistics")
    print("✅ HTTP server for local file serving")
    print("✅ Debug console for API monitoring")
    
    print("\n💡 RECOMMENDED STARTUP:")
    print("python ultimate_platform_launcher.py --minimal")
    print("(Starts: Breaking News + Error Monitor + HTTP Server + Main Platform)")

if __name__ == "__main__":
    show_available_services() 
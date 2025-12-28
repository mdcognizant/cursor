#!/usr/bin/env python3
"""
Smart API Manager for Maximum Article Efficiency
===============================================
Manages the 20 daily API calls to maximize article count and diversity.

Strategy:
1. Enhanced Scraper (primary) - 100+ articles, unlimited calls
2. NewsData.io (secondary) - 10 articles per call, limited usage
3. Smart rotation to maximize diversity within 20 call limit
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class SmartAPIManager:
    def __init__(self):
        self.config_file = 'smart_api_usage.json'
        self.daily_limit = 220  # 200 NewsData + 20 Currents
        self.load_usage_data()
        
        # Source priorities (higher = better)
        self.source_priorities = {
            'enhanced_scraper': {
                'priority': 100,
                'articles_per_call': 100,
                'calls_per_day': 'unlimited',
                'cost': 0,
                'reliability': 95
            },
            'newsdata': {
                'priority': 80,
                'articles_per_call': 50,  # Increased to 50 per call
                'calls_per_day': 200,     # Actual free tier limit
                'cost': 1,
                'reliability': 90
            },
            'currents': {
                'priority': 10,  # Low due to SSL issues
                'articles_per_call': 50,
                'calls_per_day': 5,       # Use 5 of 20 daily calls as fallback
                'cost': 1,
                'reliability': 20  # Low due to SSL problems
            }
        }

    def load_usage_data(self):
        """Load daily usage tracking data"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.reset_daily_usage()
        except Exception:
            self.reset_daily_usage()
        
        # Check if we need to reset for a new day
        today = datetime.now().strftime('%Y-%m-%d')
        if self.usage_data.get('date') != today:
            self.reset_daily_usage()

    def reset_daily_usage(self):
        """Reset usage data for a new day"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.usage_data = {
            'date': today,
            'calls_made': {
                'newsdata': 0,
                'currents': 0,
                'enhanced_scraper': 0
            },
            'articles_fetched': {
                'newsdata': 0,
                'currents': 0,
                'enhanced_scraper': 0
            },
            'total_api_calls': 0,
            'efficiency_score': 0
        }
        self.save_usage_data()

    def save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage data: {e}")

    def get_optimal_sources(self):
        """Get optimal sources for next refresh based on usage and limits"""
        recommendations = []
        
        # Always recommend Enhanced Scraper (unlimited, high reliability)
        recommendations.append({
            'source': 'enhanced_scraper',
            'reason': 'Primary source - 100+ articles, unlimited calls',
            'priority': 100,
            'expected_articles': 100
        })
        
        # Check if we can make more API calls today
        total_api_calls = self.usage_data['total_api_calls']
        remaining_calls = self.daily_limit - total_api_calls
        
        if remaining_calls > 0:
            # Check NewsData.io usage
            newsdata_calls = self.usage_data['calls_made']['newsdata']
            newsdata_limit = self.source_priorities['newsdata']['calls_per_day']
            
            if newsdata_calls < newsdata_limit and remaining_calls > 0:
                recommendations.append({
                    'source': 'newsdata',
                    'reason': f'API calls available ({newsdata_calls}/{newsdata_limit})',
                    'priority': 50,
                    'expected_articles': 10
                })
            
            # Check Currents API as fallback (if NewsData exhausted)
            currents_calls = self.usage_data['calls_made']['currents']
            currents_limit = self.source_priorities['currents']['calls_per_day']
            
            if (newsdata_calls >= newsdata_limit and 
                currents_calls < currents_limit and 
                remaining_calls > 0):
                recommendations.append({
                    'source': 'currents',
                    'reason': f'Fallback API ({currents_calls}/{currents_limit}) - SSL issues possible',
                    'priority': 10,
                    'expected_articles': 50
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations

    def record_api_call(self, source, articles_received, success=True):
        """Record an API call and its results"""
        if source in ['newsdata', 'currents']:
            self.usage_data['calls_made'][source] += 1
            self.usage_data['total_api_calls'] += 1
        
        if success:
            self.usage_data['articles_fetched'][source] += articles_received
        
        # Calculate efficiency score
        total_articles = sum(self.usage_data['articles_fetched'].values())
        total_calls = max(self.usage_data['total_api_calls'], 1)
        self.usage_data['efficiency_score'] = total_articles / total_calls
        
        self.save_usage_data()

    def get_usage_report(self):
        """Get current usage report"""
        total_articles = sum(self.usage_data['articles_fetched'].values())
        total_calls = self.usage_data['total_api_calls']
        remaining_calls = self.daily_limit - total_calls
        
        report = {
            'date': self.usage_data['date'],
            'summary': {
                'total_articles_today': total_articles,
                'total_api_calls_today': total_calls,
                'remaining_api_calls': remaining_calls,
                'efficiency_score': round(self.usage_data['efficiency_score'], 2),
                'daily_limit_used': f"{total_calls}/{self.daily_limit} ({(total_calls/self.daily_limit*100):.1f}%)"
            },
            'by_source': {}
        }
        
        for source in ['enhanced_scraper', 'newsdata', 'currents']:
            calls = self.usage_data['calls_made'][source]
            articles = self.usage_data['articles_fetched'][source]
            limit = self.source_priorities[source]['calls_per_day']
            
            report['by_source'][source] = {
                'calls_made': calls,
                'articles_fetched': articles,
                'daily_limit': limit if limit != 'unlimited' else '∞',
                'articles_per_call': round(articles / calls, 1) if calls > 0 else 0,
                'limit_used': f"{calls}/{limit}" if limit != 'unlimited' else f"{calls}/∞"
            }
        
        return report

    def print_usage_status(self):
        """Print current usage status"""
        report = self.get_usage_report()
        
        print("📊 SMART API MANAGER - DAILY USAGE STATUS")
        print("=" * 50)
        print(f"📅 Date: {report['date']}")
        print(f"📰 Total Articles Today: {report['summary']['total_articles_today']}")
        print(f"📡 API Calls Used: {report['summary']['daily_limit_used']}")
        print(f"⚡ Efficiency Score: {report['summary']['efficiency_score']} articles/call")
        
        print(f"\n📋 BY SOURCE:")
        for source, data in report['by_source'].items():
            icon = '🎯' if source == 'enhanced_scraper' else '📡'
            print(f"   {icon} {source.upper()}:")
            print(f"      Calls: {data['limit_used']}")
            print(f"      Articles: {data['articles_fetched']} ({data['articles_per_call']}/call)")
        
        # Recommendations
        recommendations = self.get_optimal_sources()
        print(f"\n💡 NEXT REFRESH RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['source'].upper()}: {rec['reason']}")
            print(f"      Expected: +{rec['expected_articles']} articles")

    def generate_optimized_config(self):
        """Generate optimized configuration for the frontend"""
        recommendations = self.get_optimal_sources()
        
        config = {
            'optimization_strategy': 'maximize_articles_minimize_api_calls',
            'daily_api_limit': self.daily_limit,
            'current_usage': self.get_usage_report(),
            'recommended_sources': recommendations,
            'frontend_config': {
                'primary_source': 'enhanced_scraper',
                'api_sources': [rec['source'] for rec in recommendations if rec['source'] != 'enhanced_scraper'],
                'expected_total_articles': sum(rec['expected_articles'] for rec in recommendations),
                'cache_fallback': True
            }
        }
        
        return config

def main():
    """Main interface for Smart API Manager"""
    manager = SmartAPIManager()
    
    print("🚀 SMART API MANAGER FOR 20 DAILY CALLS")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Show current usage status")
        print("2. Get optimization recommendations")
        print("3. Record API call")
        print("4. Generate frontend config")
        print("5. Reset daily usage")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            manager.print_usage_status()
            
        elif choice == '2':
            recommendations = manager.get_optimal_sources()
            print("\n🎯 OPTIMIZATION RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['source'].upper()}")
                print(f"   Reason: {rec['reason']}")
                print(f"   Expected: {rec['expected_articles']} articles")
                print(f"   Priority: {rec['priority']}")
            
        elif choice == '3':
            print("\nRecord API Call:")
            source = input("Source (newsdata/currents/enhanced_scraper): ").strip().lower()
            if source in ['newsdata', 'currents', 'enhanced_scraper']:
                try:
                    articles = int(input("Articles received: ").strip())
                    success = input("Success? (y/n): ").strip().lower() == 'y'
                    manager.record_api_call(source, articles, success)
                    print(f"✅ Recorded: {source} → {articles} articles")
                except ValueError:
                    print("❌ Invalid number")
            else:
                print("❌ Invalid source")
                
        elif choice == '4':
            config = manager.generate_optimized_config()
            with open('optimized_frontend_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Frontend config saved to: optimized_frontend_config.json")
            
        elif choice == '5':
            manager.reset_daily_usage()
            print("✅ Daily usage reset")
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main() 
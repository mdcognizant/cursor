#!/usr/bin/env python3
"""
Test All News Sources
====================
Comprehensive test of all news sources to ensure we can get 35+ articles.

Tests:
- NewsData.io API with increased limit
- Currents API with fallback handling  
- Enhanced News Scraper from multiple RSS feeds
- Total article count validation
"""

import asyncio
import aiohttp
import requests
import json
import time
from datetime import datetime

class NewsSourceTester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'total_articles': 0,
            'working_sources': 0,
            'failed_sources': 0
        }

    def test_all_sources(self):
        """Test all news sources comprehensively"""
        print("🧪 TESTING ALL NEWS SOURCES")
        print("=" * 50)
        
        # Test 1: NewsData.io API
        print("\n1️⃣ Testing NewsData.io API...")
        self.test_newsdata_api()
        
        # Test 2: Currents API
        print("\n2️⃣ Testing Currents API...")
        self.test_currents_api()
        
        # Test 3: Enhanced News Scraper
        print("\n3️⃣ Testing Enhanced News Scraper...")
        self.test_enhanced_scraper()
        
        # Test 4: Total Count Validation
        print("\n4️⃣ Validating Total Article Count...")
        self.validate_total_count()
        
        # Generate summary
        print("\n5️⃣ Generating Test Summary...")
        self.generate_summary()

    def test_newsdata_api(self):
        """Test NewsData.io API"""
        try:
            api_key = 'pub_591738e21b1e8d53f8baa5bf79e9a61b9adc8'
            url = f'https://newsdata.io/api/1/latest?apikey={api_key}&language=en&category=top,business,technology,sports&size=50'
            
            print(f"   📡 Fetching from: {url[:80]}...")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' in data and data['results']:
                article_count = len(data['results'])
                self.results['sources']['newsdata'] = {
                    'status': 'success',
                    'articles': article_count,
                    'response_time': response.elapsed.total_seconds(),
                    'api_limit': 50
                }
                self.results['total_articles'] += article_count
                self.results['working_sources'] += 1
                
                print(f"   ✅ NewsData.io: {article_count} articles")
                print(f"   ⏱️ Response time: {response.elapsed.total_seconds():.2f}s")
                
                # Show sample articles
                for i, article in enumerate(data['results'][:3], 1):
                    print(f"   📰 Sample {i}: {article.get('title', 'No title')[:60]}...")
            else:
                raise Exception("No articles in response")
                
        except Exception as e:
            self.results['sources']['newsdata'] = {
                'status': 'failed',
                'error': str(e),
                'articles': 0
            }
            self.results['failed_sources'] += 1
            print(f"   ❌ NewsData.io failed: {e}")

    def test_currents_api(self):
        """Test Currents API with fallback"""
        try:
            api_key = 'WOH5a2RUX_PgPu3sLJfm7tzzgFN6F_Vp9Tf0MhRSJXGdOgPn'
            url = f'https://api.currentsapi.services/v1/latest-news?apiKey={api_key}&language=en&limit=50'
            
            print(f"   📡 Fetching from: {url[:80]}...")
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'news' in data and data['news']:
                    article_count = len(data['news'])
                    self.results['sources']['currents'] = {
                        'status': 'success',
                        'articles': article_count,
                        'response_time': response.elapsed.total_seconds(),
                        'api_limit': 50,
                        'method': 'primary'
                    }
                    self.results['total_articles'] += article_count
                    self.results['working_sources'] += 1
                    
                    print(f"   ✅ Currents API: {article_count} articles")
                    print(f"   ⏱️ Response time: {response.elapsed.total_seconds():.2f}s")
                    
                    # Show sample articles
                    for i, article in enumerate(data['news'][:3], 1):
                        print(f"   📰 Sample {i}: {article.get('title', 'No title')[:60]}...")
                else:
                    raise Exception("No articles in response")
                    
            except Exception as primary_error:
                print(f"   ⚠️ Primary Currents API failed: {primary_error}")
                print("   🔄 Trying fallback method...")
                
                # Try fallback
                fallback_url = f'https://api.currentsapi.services/v1/latest-news?apiKey={api_key}&language=en&limit=30&category=general'
                fallback_response = requests.get(fallback_url, timeout=10, headers={
                    'Accept': 'application/json',
                    'User-Agent': 'NewsHub/1.0'
                })
                
                if fallback_response.ok:
                    fallback_data = fallback_response.json()
                    if 'news' in fallback_data and fallback_data['news']:
                        article_count = len(fallback_data['news'])
                        self.results['sources']['currents'] = {
                            'status': 'success_fallback',
                            'articles': article_count,
                            'response_time': fallback_response.elapsed.total_seconds(),
                            'api_limit': 30,
                            'method': 'fallback'
                        }
                        self.results['total_articles'] += article_count
                        self.results['working_sources'] += 1
                        
                        print(f"   ✅ Currents API (fallback): {article_count} articles")
                        print(f"   ⏱️ Response time: {fallback_response.elapsed.total_seconds():.2f}s")
                    else:
                        raise Exception("Fallback also returned no articles")
                else:
                    raise Exception(f"Fallback failed with status {fallback_response.status_code}")
                
        except Exception as e:
            self.results['sources']['currents'] = {
                'status': 'failed',
                'error': str(e),
                'articles': 0
            }
            self.results['failed_sources'] += 1
            print(f"   ❌ Currents API completely failed: {e}")

    def test_enhanced_scraper(self):
        """Test Enhanced News Scraper"""
        try:
            url = 'http://localhost:8889/articles'
            
            print(f"   📡 Fetching from Enhanced Scraper: {url}")
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'articles' in data and data['articles']:
                    article_count = len(data['articles'])
                    source_count = len(data.get('sources', []))
                    
                    self.results['sources']['enhanced_scraper'] = {
                        'status': 'success',
                        'articles': article_count,
                        'sources': source_count,
                        'response_time': response.elapsed.total_seconds(),
                        'source_list': data.get('sources', [])
                    }
                    self.results['total_articles'] += article_count
                    self.results['working_sources'] += 1
                    
                    print(f"   ✅ Enhanced Scraper: {article_count} articles from {source_count} sources")
                    print(f"   ⏱️ Response time: {response.elapsed.total_seconds():.2f}s")
                    print(f"   📡 Sources: {', '.join(data.get('sources', []))}")
                    
                    # Show sample articles
                    for i, article in enumerate(data['articles'][:3], 1):
                        source = article.get('source', 'Unknown')
                        title = article.get('title', 'No title')[:50]
                        print(f"   📰 Sample {i}: [{source}] {title}...")
                else:
                    raise Exception("No articles in scraper response")
                    
            elif response.status_code == 404:
                raise Exception("Enhanced scraper service not running (404)")
            else:
                raise Exception(f"Scraper returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.results['sources']['enhanced_scraper'] = {
                'status': 'service_not_running',
                'error': 'Connection refused - service not started',
                'articles': 0
            }
            self.results['failed_sources'] += 1
            print(f"   ❌ Enhanced Scraper: Service not running")
            print(f"   💡 Start with: python enhanced_news_scraper.py")
            
        except Exception as e:
            self.results['sources']['enhanced_scraper'] = {
                'status': 'failed',
                'error': str(e),
                'articles': 0
            }
            self.results['failed_sources'] += 1
            print(f"   ❌ Enhanced Scraper failed: {e}")

    def validate_total_count(self):
        """Validate that we have enough articles"""
        target_articles = 35
        
        print(f"   🎯 Target: {target_articles}+ articles")
        print(f"   📊 Actual: {self.results['total_articles']} articles")
        
        if self.results['total_articles'] >= target_articles:
            print(f"   ✅ SUCCESS: {self.results['total_articles']} articles available!")
            self.results['validation'] = 'passed'
        else:
            shortage = target_articles - self.results['total_articles']
            print(f"   ❌ SHORTAGE: Need {shortage} more articles")
            self.results['validation'] = 'failed'
            
            # Suggest fixes
            print(f"   💡 Suggestions:")
            if self.results['sources'].get('enhanced_scraper', {}).get('status') != 'success':
                print(f"      • Start enhanced scraper: python enhanced_news_scraper.py")
            if self.results['sources'].get('currents', {}).get('status') == 'failed':
                print(f"      • Fix Currents API configuration")

    def generate_summary(self):
        """Generate comprehensive summary"""
        print("\n" + "=" * 50)
        print("📊 NEWS SOURCES TEST SUMMARY")
        print("=" * 50)
        
        # Overall status
        total_sources = len(self.results['sources'])
        success_rate = (self.results['working_sources'] / total_sources * 100) if total_sources > 0 else 0
        
        print(f"📈 Overall Status: {self.results['working_sources']}/{total_sources} sources working ({success_rate:.1f}%)")
        print(f"📰 Total Articles: {self.results['total_articles']}")
        print(f"🎯 Target Met: {'✅ YES' if self.results.get('validation') == 'passed' else '❌ NO'}")
        
        # Source breakdown
        print(f"\n📋 Source Breakdown:")
        for source_name, source_info in self.results['sources'].items():
            status_icon = "✅" if source_info['status'].startswith('success') else "❌"
            articles = source_info.get('articles', 0)
            status = source_info['status']
            
            print(f"   {status_icon} {source_name.upper()}: {articles} articles ({status})")
            
            if 'response_time' in source_info:
                print(f"      ⏱️ Response time: {source_info['response_time']:.2f}s")
            
            if 'error' in source_info:
                print(f"      ❌ Error: {source_info['error']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if self.results['total_articles'] >= 35:
            print(f"   🎉 Excellent! You have {self.results['total_articles']} articles available.")
            print(f"   🚀 The news platform will display 35+ articles as requested.")
        else:
            print(f"   ⚠️ Need to fix failing sources to reach 35+ articles.")
            
        # Save results
        with open('news_sources_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: news_sources_test_report.json")

def main():
    """Main entry point"""
    tester = NewsSourceTester()
    tester.test_all_sources()

if __name__ == "__main__":
    main() 
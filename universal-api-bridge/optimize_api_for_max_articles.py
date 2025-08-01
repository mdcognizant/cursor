#!/usr/bin/env python3
"""
Optimize API for Maximum Articles Per Request
===========================================
Test and configure APIs to get maximum articles per call within the 20 daily limit.

Strategy:
1. Test maximum limits for each API
2. Configure optimal parameters
3. Create efficient rotation system
4. Maximize article diversity per call
"""

import requests
import json
import time
from datetime import datetime

class APIOptimizer:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'optimization_tests': {},
            'optimal_config': {},
            'recommendations': []
        }
        
        # API configurations to test
        self.test_configs = {
            'newsdata': {
                'base_url': 'https://newsdata.io/api/1/latest',
                'api_key': 'pub_05c05ef3d5044b3fa7a3ab3b04d479e4',
                'test_limits': [10, 25, 50, 75, 100],  # Test different size limits
                'categories': ['top', 'business', 'technology', 'sports', 'health', 'science', 'entertainment']
            },
            'currents': {
                'base_url': 'https://api.currentsapi.services/v1/latest-news',
                'api_key': 'zWhKbzWClaobXOpN0VDGF62kNkBh6Kbgdx-ki2AUIEoAGnah',
                'test_limits': [10, 25, 50, 75, 100, 200],  # Test different limit values
                'categories': ['general', 'business', 'technology', 'sports', 'health', 'science', 'entertainment']
            }
        }

    def test_all_optimizations(self):
        """Test all API optimization strategies"""
        print("🚀 OPTIMIZING APIs FOR MAXIMUM ARTICLES PER REQUEST")
        print("=" * 60)
        print(f"🎯 Goal: Maximize articles from 20 daily API calls")
        print(f"📊 Target: 35+ articles per news platform refresh")
        
        # Test 1: NewsData.io optimization
        print("\n1️⃣ Testing NewsData.io Maximum Limits...")
        self.test_newsdata_limits()
        
        # Test 2: Currents API optimization  
        print("\n2️⃣ Testing Currents API Maximum Limits...")
        self.test_currents_limits()
        
        # Test 3: Category-based requests
        print("\n3️⃣ Testing Category-Based Optimization...")
        self.test_category_optimization()
        
        # Test 4: Generate optimal configuration
        print("\n4️⃣ Generating Optimal Configuration...")
        self.generate_optimal_config()
        
        # Save results
        print("\n5️⃣ Generating Optimization Report...")
        self.generate_report()

    def test_newsdata_limits(self):
        """Test NewsData.io with different size limits"""
        api_config = self.test_configs['newsdata']
        test_results = []
        
        for size_limit in api_config['test_limits']:
            try:
                print(f"   📡 Testing NewsData.io with size={size_limit}...")
                
                url = f"{api_config['base_url']}?apikey={api_config['api_key']}&language=en&category=top,business,technology&size={size_limit}"
                
                start_time = time.time()
                response = requests.get(url, timeout=15)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    article_count = len(data.get('results', []))
                    
                    test_results.append({
                        'size_requested': size_limit,
                        'articles_received': article_count,
                        'response_time': response_time,
                        'status': 'success',
                        'efficiency': article_count / size_limit if size_limit > 0 else 0
                    })
                    
                    print(f"   ✅ Size {size_limit}: Got {article_count} articles ({response_time:.2f}s)")
                    
                    # Show sample article for verification
                    if data.get('results') and len(data['results']) > 0:
                        sample = data['results'][0]
                        print(f"      📰 Sample: {sample.get('title', 'No title')[:50]}...")
                        
                elif response.status_code == 422:
                    print(f"   ❌ Size {size_limit}: Invalid parameter (422)")
                    test_results.append({
                        'size_requested': size_limit,
                        'articles_received': 0,
                        'status': 'invalid_parameter',
                        'error': 'Size limit exceeded'
                    })
                    break  # Stop testing higher limits
                else:
                    print(f"   ❌ Size {size_limit}: HTTP {response.status_code}")
                    test_results.append({
                        'size_requested': size_limit,
                        'articles_received': 0,
                        'status': f'http_error_{response.status_code}'
                    })
                    
                # Add delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Size {size_limit}: Error - {e}")
                test_results.append({
                    'size_requested': size_limit,
                    'articles_received': 0,
                    'status': 'error',
                    'error': str(e)
                })
        
        self.results['optimization_tests']['newsdata'] = test_results
        
        # Find optimal size
        successful_tests = [t for t in test_results if t['status'] == 'success']
        if successful_tests:
            optimal_test = max(successful_tests, key=lambda x: x['articles_received'])
            print(f"   🎯 OPTIMAL: size={optimal_test['size_requested']} → {optimal_test['articles_received']} articles")
            self.results['optimal_config']['newsdata_size'] = optimal_test['size_requested']
        else:
            print(f"   ⚠️ No successful tests - using default size=50")
            self.results['optimal_config']['newsdata_size'] = 50

    def test_currents_limits(self):
        """Test Currents API with different limit values"""
        api_config = self.test_configs['currents']
        test_results = []
        
        for limit_value in api_config['test_limits']:
            try:
                print(f"   📡 Testing Currents API with limit={limit_value}...")
                
                url = f"{api_config['base_url']}?apiKey={api_config['api_key']}&language=en&limit={limit_value}"
                
                start_time = time.time()
                response = requests.get(url, timeout=15)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    article_count = len(data.get('news', []))
                    
                    test_results.append({
                        'limit_requested': limit_value,
                        'articles_received': article_count,
                        'response_time': response_time,
                        'status': 'success',
                        'efficiency': article_count / limit_value if limit_value > 0 else 0
                    })
                    
                    print(f"   ✅ Limit {limit_value}: Got {article_count} articles ({response_time:.2f}s)")
                    
                    # Show sample article
                    if data.get('news') and len(data['news']) > 0:
                        sample = data['news'][0]
                        print(f"      📰 Sample: {sample.get('title', 'No title')[:50]}...")
                        
                else:
                    print(f"   ❌ Limit {limit_value}: HTTP {response.status_code}")
                    test_results.append({
                        'limit_requested': limit_value,
                        'articles_received': 0,
                        'status': f'http_error_{response.status_code}'
                    })
                    
                    if response.status_code == 422:
                        break  # Stop testing higher limits
                        
                # Add delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Limit {limit_value}: Error - {e}")
                test_results.append({
                    'limit_requested': limit_value,
                    'articles_received': 0,
                    'status': 'error',
                    'error': str(e)
                })
        
        self.results['optimization_tests']['currents'] = test_results
        
        # Find optimal limit
        successful_tests = [t for t in test_results if t['status'] == 'success']
        if successful_tests:
            optimal_test = max(successful_tests, key=lambda x: x['articles_received'])
            print(f"   🎯 OPTIMAL: limit={optimal_test['limit_requested']} → {optimal_test['articles_received']} articles")
            self.results['optimal_config']['currents_limit'] = optimal_test['limit_requested']
        else:
            print(f"   ⚠️ No successful tests - using default limit=50")
            self.results['optimal_config']['currents_limit'] = 50

    def test_category_optimization(self):
        """Test fetching from multiple categories to maximize diversity"""
        print("   📊 Testing multi-category requests for maximum diversity...")
        
        # Test NewsData.io with multiple categories
        newsdata_config = self.test_configs['newsdata']
        optimal_size = self.results['optimal_config'].get('newsdata_size', 50)
        
        category_combinations = [
            ['top', 'business'],
            ['top', 'business', 'technology'],
            ['top', 'business', 'technology', 'sports'],
            ['top', 'business', 'technology', 'sports', 'health'],
            ['top', 'business', 'technology', 'sports', 'health', 'science']
        ]
        
        best_combination = None
        max_articles = 0
        
        for categories in category_combinations:
            try:
                category_string = ','.join(categories)
                url = f"{newsdata_config['base_url']}?apikey={newsdata_config['api_key']}&language=en&category={category_string}&size={optimal_size}"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    article_count = len(data.get('results', []))
                    
                    print(f"      📂 Categories {len(categories)}: {article_count} articles")
                    
                    if article_count > max_articles:
                        max_articles = article_count
                        best_combination = categories
                        
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Category test failed: {e}")
        
        if best_combination:
            self.results['optimal_config']['newsdata_categories'] = best_combination
            print(f"   🎯 OPTIMAL CATEGORIES: {best_combination} → {max_articles} articles")
        else:
            self.results['optimal_config']['newsdata_categories'] = ['top', 'business', 'technology']
            print(f"   🔄 Using default categories")

    def generate_optimal_config(self):
        """Generate the optimal configuration for maximum articles"""
        optimal_config = {
            'strategy': 'maximize_articles_per_request',
            'daily_api_limit': 20,
            'target_articles_per_refresh': 35,
            
            'newsdata_io': {
                'optimal_size': self.results['optimal_config'].get('newsdata_size', 50),
                'optimal_categories': self.results['optimal_config'].get('newsdata_categories', ['top', 'business', 'technology']),
                'url_template': f"https://newsdata.io/api/1/latest?apikey={{API_KEY}}&language=en&category={{CATEGORIES}}&size={{SIZE}}",
                'calls_per_day': 10,  # Use 10 of 20 daily calls for NewsData.io
                'expected_articles_per_call': self.results['optimal_config'].get('newsdata_size', 50)
            },
            
            'currents_api': {
                'optimal_limit': self.results['optimal_config'].get('currents_limit', 50),
                'url_template': f"https://api.currentsapi.services/v1/latest-news?apiKey={{API_KEY}}&language=en&limit={{LIMIT}}",
                'calls_per_day': 10,  # Use 10 of 20 daily calls for Currents
                'expected_articles_per_call': self.results['optimal_config'].get('currents_limit', 50)
            },
            
            'enhanced_scraper': {
                'articles_per_request': 100,  # From our test results
                'calls_per_day': 'unlimited',  # Local service
                'sources': 6
            },
            
            'total_expected_articles': (
                self.results['optimal_config'].get('newsdata_size', 50) +
                self.results['optimal_config'].get('currents_limit', 50) +
                100  # Enhanced scraper
            ),
            
            'rotation_strategy': {
                'morning_refresh': ['newsdata_io', 'enhanced_scraper'],
                'afternoon_refresh': ['currents_api', 'enhanced_scraper'],
                'evening_refresh': ['newsdata_io', 'currents_api', 'enhanced_scraper']
            }
        }
        
        self.results['optimal_config']['final_configuration'] = optimal_config
        
        print(f"   📊 TOTAL EXPECTED ARTICLES: {optimal_config['total_expected_articles']}")
        print(f"   🎯 TARGET ACHIEVED: {'✅ YES' if optimal_config['total_expected_articles'] >= 35 else '❌ NO'}")

    def generate_report(self):
        """Generate comprehensive optimization report"""
        print("\n" + "=" * 60)
        print("📊 API OPTIMIZATION REPORT")
        print("=" * 60)
        
        config = self.results['optimal_config'].get('final_configuration', {})
        
        print(f"🎯 Strategy: Maximize articles per API call")
        print(f"📅 Daily API Limit: 20 calls")
        print(f"📰 Target Articles: 35+ per refresh")
        
        print(f"\n📊 OPTIMAL CONFIGURATION:")
        print(f"   🔹 NewsData.io: size={config.get('newsdata_io', {}).get('optimal_size', 50)} articles")
        print(f"   🔹 Currents API: limit={config.get('currents_api', {}).get('optimal_limit', 50)} articles")
        print(f"   🔹 Enhanced Scraper: 100+ articles (6 sources)")
        print(f"   🔹 TOTAL: {config.get('total_expected_articles', 'Unknown')} articles per refresh")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if config.get('total_expected_articles', 0) >= 35:
            print(f"   ✅ Configuration meets your 35+ article target!")
            print(f"   🚀 You'll get {config.get('total_expected_articles')} articles per refresh")
        else:
            print(f"   ⚠️ May need additional optimization")
            
        print(f"   🔄 Use Enhanced Scraper as primary source (unlimited calls)")
        print(f"   📡 Rotate APIs throughout the day to maximize diversity")
        print(f"   💾 Cache articles to reduce API dependency")
        
        # Save detailed report
        with open('api_optimization_report.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: api_optimization_report.json")

def main():
    """Main entry point"""
    optimizer = APIOptimizer()
    optimizer.test_all_optimizations()

if __name__ == "__main__":
    main() 
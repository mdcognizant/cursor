#!/usr/bin/env python3
"""
Enhanced Triple News Provider Integration with Smart Article Processing

Compatible with existing news platform and frontend systems.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import os

# Import existing dual provider integration
try:
    from dual_news_api_config import load_api_config
    DUAL_CONFIG_AVAILABLE = True
except ImportError:
    DUAL_CONFIG_AVAILABLE = False

# Import CNN integration
try:
    from cnn_news_integration import fetch_cnn_news
    CNN_INTEGRATION_AVAILABLE = True
except ImportError:
    CNN_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TripleNewsResult:
    """Triple provider news fetch result."""
    success: bool
    total_articles: int
    newsdata_articles: int
    currents_articles: int
    cnn_articles: int
    response_time_ms: float
    providers_used: List[str]
    cache_used: bool
    provider_performance: Dict[str, Dict]
    error_message: Optional[str] = None

class TripleNewsProviderIntegration:
    """
    Triple News Provider Integration System
    Combines API-based and web scraping sources for maximum coverage
    """
    
    def __init__(self):
        # Load configuration
        self.config = self.load_configuration()
        
        # Provider settings
        self.providers = {
            'newsdata': {
                'name': 'NewsData.io',
                'type': 'api',
                'enabled': bool(self.config.get('newsdata_api_key')),
                'url': 'https://newsdata.io/api/1/news',
                'daily_limit': 200,
                'requests_made': 0
            },
            'currents': {
                'name': 'Currents API',
                'type': 'api', 
                'enabled': bool(self.config.get('currents_api_key')),
                'url': 'https://api.currentsapi.services/v1/latest-news',
                'daily_limit': 20,
                'requests_made': 0
            },
            'cnn': {
                'name': 'CNN.com',
                'type': 'scraping',
                'enabled': CNN_INTEGRATION_AVAILABLE,
                'url': 'https://www.cnn.com',
                'daily_limit': 100,  # Self-imposed limit
                'requests_made': 0
            }
        }
        
        # Performance tracking
        self.metrics = {
            'total_triple_requests': 0,
            'successful_triple_fetches': 0,
            'provider_failures': {'newsdata': 0, 'currents': 0, 'cnn': 0},
            'average_response_time': 0.0,
            'content_deduplication_saves': 0
        }
        
        # Article cache and deduplication
        self.article_cache = {}
        self.seen_titles = set()
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("🎯 Triple News Provider Integration initialized")
        logger.info(f"   📡 Enabled providers: {[name for name, config in self.providers.items() if config['enabled']]}")
    
    def load_configuration(self) -> Dict[str, str]:
        """Load API configuration from various sources."""
        config = {}
        
        # Try to load from config file
        try:
            if DUAL_CONFIG_AVAILABLE:
                dual_config = load_api_config()
                if dual_config:
                    config.update(dual_config)
        except Exception as e:
            logger.warning(f"⚠️ Could not load dual config: {e}")
        
        # Try to load from JSON file
        try:
            config_file = "dual_news_api_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    json_config = json.load(f)
                    if 'newsdata' in json_config:
                        config['newsdata_api_key'] = json_config['newsdata'].get('api_key')
                    if 'currents' in json_config:
                        config['currents_api_key'] = json_config['currents'].get('api_key')
        except Exception as e:
            logger.warning(f"⚠️ Could not load JSON config: {e}")
        
        # Environment variables fallback
        config.setdefault('newsdata_api_key', os.getenv('NEWSDATA_API_KEY'))
        config.setdefault('currents_api_key', os.getenv('CURRENTS_API_KEY'))
        
        return config
    
    async def fetch_triple_news(self, 
                               category: Optional[str] = None,
                               language: str = "en",
                               limit_per_provider: int = 10) -> TripleNewsResult:
        """
        Fetch news from all three providers simultaneously.
        """
        start_time = time.perf_counter()
        
        try:
            logger.info(f"🚀 Starting triple news fetch (category: {category}, language: {language})")
            self.metrics['total_triple_requests'] += 1
            
            # Prepare tasks for all enabled providers
            tasks = []
            provider_tasks = {}
            
            if self.providers['newsdata']['enabled']:
                task = self.fetch_from_newsdata(category, language, limit_per_provider)
                provider_tasks['newsdata'] = task
                tasks.append(('newsdata', task))
            
            if self.providers['currents']['enabled']:
                task = self.fetch_from_currents(category, language, limit_per_provider)
                provider_tasks['currents'] = task
                tasks.append(('currents', task))
            
            if self.providers['cnn']['enabled']:
                task = self.fetch_from_cnn(category, limit_per_provider)
                provider_tasks['cnn'] = task
                tasks.append(('cnn', task))
            
            if not tasks:
                return TripleNewsResult(
                    success=False,
                    total_articles=0,
                    newsdata_articles=0,
                    currents_articles=0,
                    cnn_articles=0,
                    response_time_ms=0,
                    providers_used=[],
                    cache_used=False,
                    provider_performance={},
                    error_message="No providers enabled"
                )
            
            # Execute all provider fetches simultaneously
            logger.info(f"📡 Fetching from {len(tasks)} providers simultaneously")
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # Process results
            all_articles = []
            provider_stats = {'newsdata': 0, 'currents': 0, 'cnn': 0}
            provider_performance = {}
            successful_providers = []
            
            for i, (provider_name, _) in enumerate(tasks):
                result = results[i]
                
                if isinstance(result, Exception):
                    logger.error(f"❌ {provider_name} failed: {result}")
                    self.metrics['provider_failures'][provider_name] += 1
                    provider_performance[provider_name] = {
                        'success': False,
                        'error': str(result),
                        'articles': 0,
                        'response_time_ms': 0
                    }
                    continue
                
                if result.get('success'):
                    articles = result.get('articles', [])
                    
                    # Tag articles with provider
                    for article in articles:
                        article['source_provider'] = provider_name
                        article['provider_type'] = self.providers[provider_name]['type']
                    
                    # Deduplicate articles
                    unique_articles = self.deduplicate_articles(articles)
                    all_articles.extend(unique_articles)
                    
                    provider_stats[provider_name] = len(unique_articles)
                    successful_providers.append(provider_name)
                    
                    provider_performance[provider_name] = {
                        'success': True,
                        'articles': len(articles),
                        'unique_articles': len(unique_articles),
                        'response_time_ms': result.get('response_time_ms', 0),
                        'source': result.get('source', 'live')
                    }
                    
                    logger.info(f"✅ {provider_name}: {len(articles)} articles ({len(unique_articles)} unique)")
                
                else:
                    logger.warning(f"⚠️ {provider_name} failed: {result.get('error', 'Unknown error')}")
                    self.metrics['provider_failures'][provider_name] += 1
                    provider_performance[provider_name] = {
                        'success': False,
                        'error': result.get('error', 'Unknown error'),
                        'articles': 0,
                        'response_time_ms': result.get('response_time_ms', 0)
                    }
            
            # Final processing
            end_time = time.perf_counter()
            total_response_time = (end_time - start_time) * 1000
            
            # Sort articles by provider and recency
            all_articles = self.sort_and_optimize_articles(all_articles)
            
            # Update metrics
            if len(all_articles) > 0:
                self.metrics['successful_triple_fetches'] += 1
                self.update_average_response_time(total_response_time)
            
            result = TripleNewsResult(
                success=len(all_articles) > 0,
                total_articles=len(all_articles),
                newsdata_articles=provider_stats['newsdata'],
                currents_articles=provider_stats['currents'],
                cnn_articles=provider_stats['cnn'],
                response_time_ms=total_response_time,
                providers_used=successful_providers,
                cache_used=any(perf.get('source') == 'cached' for perf in provider_performance.values()),
                provider_performance=provider_performance
            )
            
            logger.info(f"🏁 Triple fetch completed: {len(all_articles)} total articles from {len(successful_providers)} providers")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Triple news fetch failed: {e}")
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000
            
            return TripleNewsResult(
                success=False,
                total_articles=0,
                newsdata_articles=0,
                currents_articles=0,
                cnn_articles=0,
                response_time_ms=response_time,
                providers_used=[],
                cache_used=False,
                provider_performance={},
                error_message=str(e)
            )
    
    async def fetch_from_newsdata(self, category: Optional[str], language: str, limit: int) -> Dict[str, Any]:
        """Fetch from NewsData.io API."""
        try:
            if not self.config.get('newsdata_api_key'):
                return {'success': False, 'error': 'No API key', 'articles': []}
            
            url = self.providers['newsdata']['url']
            params = {
                'apikey': self.config['newsdata_api_key'],
                'language': language,
                'size': min(limit, 10)
            }
            
            if category:
                params['category'] = category
            
            start_time = time.perf_counter()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('results', [])
                        
                        end_time = time.perf_counter()
                        response_time = (end_time - start_time) * 1000
                        
                        return {
                            'success': True,
                            'articles': articles,
                            'response_time_ms': response_time,
                            'source': 'live'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}",
                            'articles': []
                        }
                        
        except Exception as e:
            logger.error(f"❌ NewsData fetch failed: {e}")
            return {'success': False, 'error': str(e), 'articles': []}
    
    async def fetch_from_currents(self, category: Optional[str], language: str, limit: int) -> Dict[str, Any]:
        """Fetch from Currents API."""
        try:
            if not self.config.get('currents_api_key'):
                return {'success': False, 'error': 'No API key', 'articles': []}
            
            url = self.providers['currents']['url']
            params = {
                'apiKey': self.config['currents_api_key'],
                'language': language,
                'limit': min(limit, 20)
            }
            
            if category:
                params['category'] = category
            
            start_time = time.perf_counter()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('news', [])
                        
                        end_time = time.perf_counter()
                        response_time = (end_time - start_time) * 1000
                        
                        return {
                            'success': True,
                            'articles': articles,
                            'response_time_ms': response_time,
                            'source': 'live'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}",
                            'articles': []
                        }
                        
        except Exception as e:
            logger.error(f"❌ Currents fetch failed: {e}")
            return {'success': False, 'error': str(e), 'articles': []}
    
    async def fetch_from_cnn(self, category: Optional[str], limit: int) -> Dict[str, Any]:
        """Fetch from CNN.com via web scraping."""
        try:
            if not CNN_INTEGRATION_AVAILABLE:
                return {'success': False, 'error': 'CNN integration not available', 'articles': []}
            
            # Use the CNN integration function
            result = await fetch_cnn_news(limit, category)
            return result
            
        except Exception as e:
            logger.error(f"❌ CNN fetch failed: {e}")
            return {'success': False, 'error': str(e), 'articles': []}
    
    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity."""
        unique_articles = []
        
        for article in articles:
            title = article.get('title', '').lower().strip()
            
            # Create a simplified title for comparison
            simple_title = ' '.join(title.split()[:5])  # First 5 words
            
            # Check if we've seen a similar title
            is_duplicate = False
            for seen_title in self.seen_titles:
                if simple_title in seen_title or seen_title in simple_title:
                    is_duplicate = True
                    self.metrics['content_deduplication_saves'] += 1
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                self.seen_titles.add(simple_title)
        
        return unique_articles
    
    def sort_and_optimize_articles(self, articles: List[Dict]) -> List[Dict]:
        """Sort articles by provider priority and quality."""
        
        # Provider priority (higher score = higher priority)
        provider_priority = {'cnn': 3, 'newsdata': 2, 'currents': 1}
        
        def article_score(article):
            # Base score from provider
            provider = article.get('source_provider', 'unknown')
            score = provider_priority.get(provider, 0)
            
            # Bonus for having image
            if article.get('urlToImage') or article.get('image_url'):
                score += 0.5
            
            # Bonus for longer description
            description = article.get('description', '')
            if len(description) > 100:
                score += 0.3
            
            # Bonus for content preview
            if article.get('content'):
                score += 0.2
            
            return score
        
        # Sort by score (highest first)
        articles.sort(key=article_score, reverse=True)
        
        return articles
    
    def update_average_response_time(self, new_time: float):
        """Update average response time metric."""
        current_avg = self.metrics['average_response_time']
        total_requests = self.metrics['successful_triple_fetches']
        
        if total_requests == 1:
            self.metrics['average_response_time'] = new_time
        else:
            self.metrics['average_response_time'] = (
                (current_avg * (total_requests - 1) + new_time) / total_requests
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        total_requests = self.metrics['total_triple_requests']
        success_rate = (self.metrics['successful_triple_fetches'] / 
                       max(total_requests, 1)) * 100
        
        return {
            **self.metrics,
            'success_rate_percent': round(success_rate, 2),
            'enabled_providers': [name for name, config in self.providers.items() if config['enabled']],
            'provider_availability': {
                name: config['enabled'] for name, config in self.providers.items()
            },
            'deduplication_efficiency': round(
                (self.metrics['content_deduplication_saves'] / max(total_requests, 1)) * 100, 2
            )
        }

# Main integration function for use with news platform and frontend
async def fetch_triple_provider_news(category: Optional[str] = None, 
                                   language: str = "en",
                                   limit_per_provider: int = 8) -> Dict[str, Any]:
    """
    Main function to fetch news from all three providers.
    Compatible with existing news platform and frontend systems.
    """
    integration = TripleNewsProviderIntegration()
    
    try:
        result = await integration.fetch_triple_news(category, language, limit_per_provider)
        
        # Format for existing systems
        return {
            'success': result.success,
            'total_articles': result.total_articles,
            'newsdata_articles': result.newsdata_articles,
            'currents_articles': result.currents_articles,
            'cnn_articles': result.cnn_articles,
            'providers_used': result.providers_used,
            'response_time_ms': result.response_time_ms,
            'cache_used': result.cache_used,
            'provider_performance': result.provider_performance,
            'error_message': result.error_message,
            'metrics': integration.get_performance_metrics()
        }
        
    except Exception as e:
        logger.error(f"❌ Triple provider fetch failed: {e}")
        return {
            'success': False,
            'total_articles': 0,
            'newsdata_articles': 0,
            'currents_articles': 0,
            'cnn_articles': 0,
            'providers_used': [],
            'response_time_ms': 0,
            'cache_used': False,
            'provider_performance': {},
            'error_message': str(e),
            'metrics': {}
        }

# Test function
async def test_triple_integration():
    """Test the triple news provider integration."""
    print("🧪 Testing Triple News Provider Integration...")
    print("=" * 60)
    
    # Test general news
    print("\n📰 Testing: General News")
    result = await fetch_triple_provider_news(limit_per_provider=5)
    
    print(f"   Success: {result['success']}")
    print(f"   Total Articles: {result['total_articles']}")
    print(f"   NewsData: {result['newsdata_articles']}")
    print(f"   Currents: {result['currents_articles']}")
    print(f"   CNN: {result['cnn_articles']}")
    print(f"   Providers Used: {result['providers_used']}")
    print(f"   Response Time: {result['response_time_ms']:.1f}ms")
    
    # Test technology news
    print("\n📱 Testing: Technology News")
    tech_result = await fetch_triple_provider_news(category="technology", limit_per_provider=3)
    print(f"   Success: {tech_result['success']}")
    print(f"   Total Articles: {tech_result['total_articles']}")
    print(f"   Providers Used: {tech_result['providers_used']}")
    
    # Show performance metrics
    if 'metrics' in result:
        metrics = result['metrics']
        print(f"\n📊 Performance Metrics:")
        print(f"   Success Rate: {metrics.get('success_rate_percent', 0)}%")
        print(f"   Enabled Providers: {metrics.get('enabled_providers', [])}")
        print(f"   Deduplication Efficiency: {metrics.get('deduplication_efficiency', 0)}%")
    
    print("\n✅ Triple integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_triple_integration()) 
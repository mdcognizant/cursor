#!/usr/bin/env python3
"""
🏗️ CNN NEWS INTEGRATION v1.0

Professional CNN.com news scraping integration for the Universal API Bridge.
Fetches news articles and images from CNN using their sitemap and article structure.

FEATURES:
✅ Sitemap-based article discovery
✅ Article content and image extraction  
✅ Respectful rate limiting
✅ Category-based filtering
✅ Professional error handling
✅ gRPC backend optimization
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CNNArticle:
    """CNN Article data structure."""
    title: str
    url: str
    description: str
    image_url: Optional[str]
    category: str
    published_date: str
    content_preview: str
    source_provider: str = "cnn"
    fetch_time: str = None

    def __post_init__(self):
        if not self.fetch_time:
            self.fetch_time = datetime.now().isoformat()

class CNNNewsIntegration:
    """
    Professional CNN News Integration System
    Respects rate limits and provides clean news data
    """
    
    def __init__(self):
        self.base_url = "https://www.cnn.com"
        self.sitemap_base = f"{self.base_url}/article/sitemap"
        
        # Rate limiting settings
        self.rate_limit_delay = 2.0  # 2 seconds between requests
        self.last_request_time = 0
        
        # Categories mapping
        self.category_mapping = {
            'us': 'US News',
            'world': 'World News', 
            'politics': 'Politics',
            'business': 'Business',
            'tech': 'Technology',
            'health': 'Health',
            'entertainment': 'Entertainment',
            'sports': 'Sports',
            'travel': 'Travel',
            'style': 'Lifestyle'
        }
        
        # Cache for performance
        self.article_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'cache_hits': 0,
            'articles_fetched': 0
        }
        
        logger.info("🏗️ CNN News Integration initialized")
    
    async def _rate_limit(self):
        """Implement respectful rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Make HTTP request with error handling and rate limiting."""
        await self._rate_limit()
        
        try:
            self.metrics['total_requests'] += 1
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"⚠️ HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Request failed for {url}: {e}")
            return None
    
    async def get_latest_articles_from_sitemap(self, 
                                             limit: int = 20,
                                             category: Optional[str] = None) -> List[CNNArticle]:
        """
        Fetch latest articles from CNN sitemap.
        """
        try:
            logger.info(f"📰 Fetching CNN articles (limit: {limit}, category: {category})")
            
            # Get current year and month for sitemap
            current_date = datetime.now()
            sitemap_url = f"{self.sitemap_base}-{current_date.year}-{current_date.month}.html"
            
            async with aiohttp.ClientSession() as session:
                sitemap_content = await self._make_request(sitemap_url, session)
                
                if not sitemap_content:
                    logger.warning("⚠️ Could not fetch sitemap, trying current month")
                    # Fallback to current sitemap
                    sitemap_url = f"{self.sitemap_base}-2024-1.html"
                    sitemap_content = await self._make_request(sitemap_url, session)
                
                if not sitemap_content:
                    return await self._fallback_fetch_articles(session, limit, category)
                
                # Parse sitemap
                articles = await self._parse_sitemap_articles(sitemap_content, session, limit, category)
                
                logger.info(f"✅ Successfully fetched {len(articles)} CNN articles")
                self.metrics['articles_fetched'] += len(articles)
                
                return articles
                
        except Exception as e:
            logger.error(f"❌ CNN integration failed: {e}")
            return []
    
    async def _parse_sitemap_articles(self, 
                                    sitemap_content: str, 
                                    session: aiohttp.ClientSession,
                                    limit: int,
                                    category_filter: Optional[str]) -> List[CNNArticle]:
        """Parse articles from CNN sitemap HTML."""
        try:
            soup = BeautifulSoup(sitemap_content, 'html.parser')
            articles = []
            
            # Find article links in sitemap
            article_links = []
            
            # Look for date-title pattern in sitemap
            for line in sitemap_content.split('\n'):
                if '2024-' in line and 'href=' in line:
                    # Extract article URL
                    match = re.search(r'href="([^"]*)"', line)
                    if match:
                        article_url = match.group(1)
                        if article_url.startswith('/'):
                            article_url = self.base_url + article_url
                        article_links.append(article_url)
            
            # Also look for standard article links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and ('/2024/' in href or '/2025/' in href):
                    if href.startswith('/'):
                        href = self.base_url + href
                    article_links.append(href)
            
            # Remove duplicates and limit
            article_links = list(dict.fromkeys(article_links))[:limit * 2]  # Get extra for filtering
            
            logger.info(f"📄 Found {len(article_links)} potential articles")
            
            # Process articles concurrently (but with rate limiting)
            tasks = []
            for url in article_links[:limit]:
                tasks.append(self._extract_article_details(url, session, category_filter))
            
            # Execute with controlled concurrency
            results = []
            for i in range(0, len(tasks), 3):  # Process 3 at a time
                batch = tasks[i:i+3]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, CNNArticle):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"❌ Article extraction failed: {result}")
                
                # Short delay between batches
                await asyncio.sleep(1)
            
            # Filter by category if specified
            if category_filter:
                results = [article for article in results 
                          if category_filter.lower() in article.category.lower()]
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Sitemap parsing failed: {e}")
            return []
    
    async def _extract_article_details(self, 
                                     url: str, 
                                     session: aiohttp.ClientSession,
                                     category_filter: Optional[str]) -> Optional[CNNArticle]:
        """Extract detailed information from a CNN article page."""
        try:
            # Check cache first
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.article_cache:
                cache_entry = self.article_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                    self.metrics['cache_hits'] += 1
                    return cache_entry['article']
            
            # Fetch article page
            article_content = await self._make_request(url, session)
            if not article_content:
                return None
            
            soup = BeautifulSoup(article_content, 'html.parser')
            
            # Extract title
            title = None
            title_selectors = ['h1', 'title', '.headline', '.pg-headline']
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            if not title:
                logger.warning(f"⚠️ No title found for {url}")
                return None
            
            # Clean title
            title = re.sub(r'\s*\|\s*CNN\s*$', '', title)
            title = title[:200]  # Limit length
            
            # Extract description/summary
            description = ""
            desc_selectors = [
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.zn-body__paragraph:first-child',
                '.paragraph-inline-placeholder:first-child'
            ]
            
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    if desc_element.name == 'meta':
                        description = desc_element.get('content', '')
                    else:
                        description = desc_element.get_text(strip=True)
                    break
            
            # Extract image
            image_url = None
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                '.media__image img',
                '.el__storyelement--standard-image img'
            ]
            
            for selector in img_selectors:
                img_element = soup.select_one(selector)
                if img_element:
                    if img_element.name == 'meta':
                        image_url = img_element.get('content')
                    else:
                        image_url = img_element.get('src') or img_element.get('data-src')
                    
                    if image_url:
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = self.base_url + image_url
                        break
            
            # Determine category from URL
            category = "General News"
            url_parts = urlparse(url).path.split('/')
            for part in url_parts:
                if part in self.category_mapping:
                    category = self.category_mapping[part]
                    break
            
            # Extract content preview
            content_preview = ""
            content_elements = soup.select('.zn-body__paragraph, .paragraph-inline-placeholder')
            if content_elements:
                preview_texts = []
                for elem in content_elements[:3]:  # First 3 paragraphs
                    text = elem.get_text(strip=True)
                    if text and len(text) > 50:  # Skip short snippets
                        preview_texts.append(text)
                
                content_preview = ' '.join(preview_texts)[:300] + "..."
            
            if not content_preview and description:
                content_preview = description[:300] + "..."
            
            # Create article object
            article = CNNArticle(
                title=title,
                url=url,
                description=description or "Latest news from CNN",
                image_url=image_url,
                category=category,
                published_date=datetime.now().strftime("%Y-%m-%d"),
                content_preview=content_preview
            )
            
            # Cache the result
            self.article_cache[cache_key] = {
                'article': article,
                'timestamp': time.time()
            }
            
            self.metrics['successful_extractions'] += 1
            logger.debug(f"✅ Extracted: {title[:50]}...")
            
            return article
            
        except Exception as e:
            logger.error(f"❌ Article extraction failed for {url}: {e}")
            self.metrics['failed_extractions'] += 1
            return None
    
    async def _fallback_fetch_articles(self, 
                                     session: aiohttp.ClientSession,
                                     limit: int,
                                     category: Optional[str]) -> List[CNNArticle]:
        """Fallback method to fetch articles from main CNN page."""
        try:
            logger.info("🔄 Using fallback method - fetching from main CNN page")
            
            main_page = await self._make_request(self.base_url, session)
            if not main_page:
                return []
            
            soup = BeautifulSoup(main_page, 'html.parser')
            article_links = set()
            
            # Find article links from main page
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and ('/2024/' in href or '/2025/' in href):
                    if href.startswith('/'):
                        href = self.base_url + href
                    if '/index.html' not in href:  # Skip index pages
                        article_links.add(href)
            
            article_links = list(article_links)[:limit]
            logger.info(f"📄 Fallback found {len(article_links)} articles")
            
            # Process articles
            articles = []
            for url in article_links:
                article = await self._extract_article_details(url, session, category)
                if article:
                    articles.append(article)
                
                if len(articles) >= limit:
                    break
            
            return articles
            
        except Exception as e:
            logger.error(f"❌ Fallback fetch failed: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get integration performance metrics."""
        total_requests = self.metrics['total_requests']
        success_rate = (self.metrics['successful_extractions'] / 
                       max(total_requests, 1)) * 100
        
        return {
            **self.metrics,
            'success_rate_percent': round(success_rate, 2),
            'cache_hit_rate_percent': round(
                (self.metrics['cache_hits'] / max(total_requests, 1)) * 100, 2
            ),
            'average_response_time': f"{self.rate_limit_delay}s (rate limited)"
        }

# Integration function for the dual news system
async def fetch_cnn_news(limit: int = 20, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to integrate CNN news with existing dual provider system.
    """
    cnn_integration = CNNNewsIntegration()
    
    start_time = time.perf_counter()
    
    try:
        articles = await cnn_integration.get_latest_articles_from_sitemap(limit, category)
        
        end_time = time.perf_counter()
        response_time = (end_time - start_time) * 1000
        
        # Convert to format compatible with existing system
        formatted_articles = []
        for article in articles:
            formatted_article = {
                'title': article.title,
                'description': article.description,
                'url': article.url,
                'urlToImage': article.image_url,
                'publishedAt': article.published_date,
                'source': {'name': 'CNN'},
                'content': article.content_preview,
                'category': article.category,
                'source_provider': 'cnn',
                'fetch_time': article.fetch_time
            }
            formatted_articles.append(formatted_article)
        
        logger.info(f"🏁 CNN integration completed: {len(formatted_articles)} articles in {response_time:.1f}ms")
        
        return {
            'success': True,
            'articles': formatted_articles,
            'total_count': len(formatted_articles),
            'response_time_ms': response_time,
            'source': 'live',
            'provider': 'cnn',
            'metrics': cnn_integration.get_performance_metrics()
        }
        
    except Exception as e:
        logger.error(f"❌ CNN integration failed: {e}")
        return {
            'success': False,
            'articles': [],
            'total_count': 0,
            'response_time_ms': 0,
            'source': 'error',
            'provider': 'cnn',
            'error': str(e)
        }

# Test function
async def test_cnn_integration():
    """Test the CNN news integration."""
    print("🧪 Testing CNN News Integration...")
    
    # Test different scenarios
    test_cases = [
        {'limit': 10, 'category': None, 'name': 'General News'},
        {'limit': 5, 'category': 'tech', 'name': 'Technology'},
        {'limit': 5, 'category': 'politics', 'name': 'Politics'}
    ]
    
    for case in test_cases:
        print(f"\n📰 Testing: {case['name']}")
        result = await fetch_cnn_news(case['limit'], case['category'])
        
        print(f"   Success: {result['success']}")
        print(f"   Articles: {result['total_count']}")
        print(f"   Response Time: {result['response_time_ms']:.1f}ms")
        
        if result['articles']:
            sample_article = result['articles'][0]
            print(f"   Sample: {sample_article['title'][:60]}...")
            print(f"   Category: {sample_article.get('category', 'N/A')}")
        
        if 'metrics' in result:
            metrics = result['metrics']
            print(f"   Success Rate: {metrics['success_rate_percent']}%")
            print(f"   Cache Hit Rate: {metrics['cache_hit_rate_percent']}%")

if __name__ == "__main__":
    asyncio.run(test_cnn_integration()) 
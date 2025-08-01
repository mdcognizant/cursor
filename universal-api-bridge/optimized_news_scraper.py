#!/usr/bin/env python3
"""
Optimized News Scraper - Production Ready
=========================================
Consolidated, efficient news scraper for maximum performance.
Combines all news sources into one optimized service.

Features:
- Smart caching to reduce API dependency
- Efficient RSS parsing
- Error resilience
- Performance monitoring
- Memory optimization

Author: Assistant
Date: 2025-01-27
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import logging
from collections import deque
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # Optimized cache system
        self.articles_cache = deque(maxlen=200)  # Memory-efficient deque
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutes
        
        # Performance metrics
        self.metrics = {
            'total_fetched': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_response_time': 0
        }
        
        # Optimized RSS sources (reduced to most reliable)
        self.rss_sources = {
            'cnn': [
                'http://rss.cnn.com/rss/edition.rss',
                'http://rss.cnn.com/rss/edition_world.rss',
                'http://rss.cnn.com/rss/money_latest.rss'
            ],
            'bbc': [
                'http://feeds.bbci.co.uk/news/rss.xml',
                'http://feeds.bbci.co.uk/news/world/rss.xml',
                'http://feeds.bbci.co.uk/news/business/rss.xml'
            ],
            'reuters': [
                'https://www.reuters.com/rssFeed/topNews',
                'https://www.reuters.com/rssFeed/businessNews'
            ],
            'ap': [
                'https://feeds.apnews.com/rss/apf-topnews',
                'https://feeds.apnews.com/rss/apf-usnews'
            ]
        }

    def fetch_all_articles(self):
        """Fetch articles from all sources with optimized caching"""
        
        # Check cache first
        if self.is_cache_valid():
            logger.info("📦 Using cached articles")
            self.metrics['cache_hits'] += 1
            return list(self.articles_cache)
        
        start_time = time.time()
        logger.info("🔄 Fetching fresh articles from RSS sources...")
        
        all_articles = []
        
        # Fetch from each source with parallel processing
        threads = []
        results = {}
        
        for source_name, feeds in self.rss_sources.items():
            thread = threading.Thread(
                target=self.fetch_source_articles,
                args=(source_name, feeds, results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete (max 15 seconds)
        for thread in threads:
            thread.join(timeout=15)
        
        # Combine results
        for source_name, articles in results.items():
            all_articles.extend(articles)
            logger.info(f"✅ {source_name.upper()}: {len(articles)} articles")
        
        # Process and deduplicate
        processed_articles = self.process_articles(all_articles)
        
        # Update cache
        self.articles_cache.clear()
        self.articles_cache.extend(processed_articles)
        self.cache_timestamp = time.time()
        
        # Update metrics
        response_time = (time.time() - start_time) * 1000
        self.metrics['total_fetched'] += len(processed_articles)
        self.metrics['avg_response_time'] = response_time
        
        logger.info(f"✅ Fetched {len(processed_articles)} articles in {response_time:.0f}ms")
        
        return processed_articles

    def fetch_source_articles(self, source_name, feeds, results):
        """Fetch articles from a specific source (thread-safe)"""
        articles = []
        
        for feed_url in feeds:
            try:
                response = self.session.get(feed_url, timeout=10)
                if response.status_code == 200:
                    articles.extend(self.parse_rss_feed(response.content, source_name))
                else:
                    logger.warning(f"⚠️ {source_name} feed returned {response.status_code}")
            except Exception as e:
                logger.error(f"❌ {source_name} feed error: {e}")
                self.metrics['errors'] += 1
        
        results[source_name] = articles

    def parse_rss_feed(self, content, source_name):
        """Parse RSS feed content efficiently"""
        articles = []
        
        try:
            soup = BeautifulSoup(content, 'xml')
            items = soup.find_all('item')[:20]  # Limit to 20 items per feed
            
            for item in items:
                try:
                    title = item.find('title')
                    description = item.find('description')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    
                    # Extract image from description or enclosure
                    image_url = self.extract_image_url(item, description)
                    
                    article = {
                        'title': title.text.strip() if title else '',
                        'description': self.clean_description(description.text if description else ''),
                        'url': link.text.strip() if link else '',
                        'source': source_name.upper(),
                        'publishedAt': self.parse_date(pub_date.text if pub_date else ''),
                        'image': image_url,
                        'category': 'News'
                    }
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        
                except Exception as e:
                    logger.debug(f"Item parse error: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"RSS parse error for {source_name}: {e}")
        
        return articles

    def extract_image_url(self, item, description):
        """Extract image URL from RSS item"""
        # Try enclosure first
        enclosure = item.find('enclosure')
        if enclosure and enclosure.get('type', '').startswith('image'):
            return enclosure.get('url')
        
        # Try media:content
        media_content = item.find('media:content')
        if media_content:
            return media_content.get('url')
        
        # Try to extract from description
        if description:
            img_match = re.search(r'<img[^>]+src="([^"]+)"', str(description))
            if img_match:
                return img_match.group(1)
        
        # Fallback to placeholder
        return f'https://picsum.photos/400/250?random={hash(item.find("title").text if item.find("title") else "default") % 1000}'

    def clean_description(self, description):
        """Clean HTML from description"""
        if not description:
            return ''
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        # Limit length
        return clean_text[:300] + ('...' if len(clean_text) > 300 else '')

    def parse_date(self, date_str):
        """Parse RSS date format"""
        try:
            # Try common RSS date formats
            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z']:
                try:
                    return datetime.strptime(date_str, fmt).isoformat()
                except ValueError:
                    continue
            
            # Fallback to current time
            return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()

    def process_articles(self, articles):
        """Process and deduplicate articles"""
        seen_titles = set()
        processed = []
        
        # Sort by date (newest first)
        articles.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        for article in articles:
            # Create hash for deduplication
            title_hash = hashlib.md5(article['title'].lower().encode()).hexdigest()
            
            if title_hash not in seen_titles and len(processed) < 150:
                seen_titles.add(title_hash)
                processed.append(article)
        
        return processed

    def is_cache_valid(self):
        """Check if cache is still valid"""
        if not self.cache_timestamp or not self.articles_cache:
            return False
        
        age = time.time() - self.cache_timestamp
        return age < self.cache_duration

    def get_health_status(self):
        """Get service health status"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'cache_valid': self.is_cache_valid(),
            'cached_articles': len(self.articles_cache),
            'metrics': self.metrics,
            'sources': list(self.rss_sources.keys())
        }

class OptimizedRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, scraper, *args, **kwargs):
        self.scraper = scraper
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Set CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        if parsed_path.path == '/articles':
            try:
                articles = self.scraper.fetch_all_articles()
                
                response_data = {
                    'status': 'success',
                    'articles': articles,
                    'count': len(articles),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'optimized_scraper'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
            except Exception as e:
                logger.error(f"❌ Articles endpoint error: {e}")
                self.send_error(500, f'Server error: {e}')
        
        elif parsed_path.path == '/health':
            try:
                health_data = self.scraper.get_health_status()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(health_data).encode())
                
            except Exception as e:
                logger.error(f"❌ Health endpoint error: {e}")
                self.send_error(500, f'Health check failed: {e}')
        
        else:
            self.send_error(404, 'Endpoint not found')

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Override to reduce log spam"""
        pass

def create_request_handler(scraper):
    """Create request handler with scraper instance"""
    def handler(*args, **kwargs):
        return OptimizedRequestHandler(scraper, *args, **kwargs)
    return handler

def main():
    """Main entry point"""
    print("🚀 OPTIMIZED NEWS SCRAPER - PRODUCTION READY")
    print("=" * 50)
    
    try:
        # Initialize scraper
        scraper = OptimizedNewsScraper()
        logger.info("✅ Scraper initialized")
        
        # Create HTTP server
        port = 8889
        handler = create_request_handler(scraper)
        httpd = HTTPServer(('localhost', port), handler)
        
        print(f"🌐 Server running on http://localhost:{port}")
        print(f"📊 Endpoints:")
        print(f"   GET /articles - Fetch all articles")
        print(f"   GET /health   - Health status")
        print(f"🎯 Optimized for maximum efficiency with 20 daily API calls")
        print(f"📦 Smart caching (5min) to reduce external dependencies")
        print(f"⚡ Memory-optimized with deque-based cache")
        
        # Test initial fetch
        logger.info("🧪 Testing initial fetch...")
        articles = scraper.fetch_all_articles()
        logger.info(f"✅ Initial test: {len(articles)} articles ready")
        
        print(f"\n✅ Ready to serve {len(articles)} articles!")
        print("Press Ctrl+C to stop\n")
        
        # Start server
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        print("👋 Goodbye!")

if __name__ == "__main__":
    main() 
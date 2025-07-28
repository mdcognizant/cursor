#!/usr/bin/env python3
"""
Breaking News Scraper for CNN.com and BBC.com
=============================================
Real-time breaking news scraper that fetches latest headlines from CNN and BBC.
Serves the data via HTTP endpoint for the frontend to consume.

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BreakingNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.breaking_news_cache = []
        self.last_update = None
        
        # RSS feeds for reliable news fetching from multiple sources
        self.news_sources = {
            'cnn': {
                'name': 'CNN',
                'rss_feeds': [
                    'http://rss.cnn.com/rss/edition.rss',
                    'http://rss.cnn.com/rss/edition_world.rss',
                    'http://rss.cnn.com/rss/money_latest.rss',
                    'http://rss.cnn.com/rss/edition_technology.rss',
                    'http://rss.cnn.com/rss/edition_us.rss',
                    'http://rss.cnn.com/rss/edition_entertainment.rss'
                ],
                'breaking_keywords': ['breaking', 'urgent', 'alert', 'developing', 'live']
            },
            'bbc': {
                'name': 'BBC',
                'rss_feeds': [
                    'http://feeds.bbci.co.uk/news/rss.xml',
                    'http://feeds.bbci.co.uk/news/world/rss.xml',
                    'http://feeds.bbci.co.uk/news/business/rss.xml',
                    'http://feeds.bbci.co.uk/news/technology/rss.xml',
                    'http://feeds.bbci.co.uk/news/entertainment/rss.xml',
                    'http://feeds.bbci.co.uk/news/health/rss.xml'
                ],
                'breaking_keywords': ['breaking', 'live', 'urgent', 'latest', 'developing']
            },
            'npr': {
                'name': 'NPR',
                'rss_feeds': [
                    'https://feeds.npr.org/1001/rss.xml',
                    'https://feeds.npr.org/1003/rss.xml',
                    'https://feeds.npr.org/1020/rss.xml'
                ],
                'breaking_keywords': ['breaking', 'live', 'urgent', 'latest', 'developing']
            },
            'guardian': {
                'name': 'The Guardian',
                'rss_feeds': [
                    'https://www.theguardian.com/world/rss',
                    'https://www.theguardian.com/business/rss',
                    'https://www.theguardian.com/technology/rss'
                ],
                'breaking_keywords': ['breaking', 'live', 'urgent', 'latest', 'developing']
            },
            'sky_news': {
                'name': 'Sky News',
                'rss_feeds': [
                    'http://feeds.skynews.com/feeds/rss/home.xml',
                    'http://feeds.skynews.com/feeds/rss/world.xml',
                    'http://feeds.skynews.com/feeds/rss/business.xml'
                ],
                'breaking_keywords': ['breaking', 'live', 'urgent', 'latest', 'developing']
            },
            'yahoo_news': {
                'name': 'Yahoo News',
                'rss_feeds': [
                    'https://www.yahoo.com/news/rss',
                    'https://www.yahoo.com/news/rss/world',
                    'https://www.yahoo.com/news/rss/business'
                ],
                'breaking_keywords': ['breaking', 'live', 'urgent', 'latest', 'developing']
            }
        }

    def fetch_breaking_news(self):
        """Fetch breaking news from all sources"""
        logger.info("🔄 Fetching breaking news from multiple sources...")
        
        all_breaking_news = []
        
        # Fetch from all news sources
        for source_key, source_config in self.news_sources.items():
            try:
                logger.info(f"📡 Fetching from {source_config['name']}...")
                source_news = self.fetch_from_source(source_key)
                all_breaking_news.extend(source_news)
                logger.info(f"✅ {source_config['name']}: {len(source_news)} articles")
            except Exception as e:
                logger.error(f"❌ Failed to fetch from {source_config['name']}: {e}")
                continue
        
        # Filter for breaking news and sort by recency
        breaking_news = self.filter_breaking_news(all_breaking_news)
        
        # Cache more results for the enhanced platform
        self.breaking_news_cache = breaking_news[:15]  # Increased from 5 to 15
        self.last_update = datetime.now()
        
        logger.info(f"✅ Found {len(breaking_news)} breaking news items from {len(self.news_sources)} sources")
        return self.breaking_news_cache

    def fetch_from_source(self, source_key):
        """Fetch news from a specific source"""
        source_config = self.news_sources[source_key]
        articles = []
        
        for rss_url in source_config['rss_feeds']:
            try:
                logger.info(f"📡 Fetching from {source_config['name']}: {rss_url}")
                
                response = self.session.get(rss_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                
                for item in items[:25]:  # Get latest 25 from each feed (increased from 10)
                    article = self.parse_rss_item(item, source_config['name'])
                    if article:
                        articles.append(article)
                        
            except Exception as e:
                logger.error(f"❌ Failed to fetch from {rss_url}: {e}")
                continue
        
        return articles

    def parse_rss_item(self, item, source_name):
        """Parse individual RSS item"""
        try:
            title = item.find('title')
            title = title.text.strip() if title else None
            
            description = item.find('description')
            description = description.text.strip() if description else None
            
            link = item.find('link')
            link = link.text.strip() if link else None
            
            pub_date = item.find('pubDate')
            pub_date = pub_date.text.strip() if pub_date else None
            
            if not title:
                return None
            
            return {
                'title': self.clean_text(title),
                'description': self.clean_text(description) if description else '',
                'link': link,
                'published': pub_date,
                'source': source_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse RSS item: {e}")
            return None

    def clean_text(self, text):
        """Clean and format text"""
        if not text:
            return ''
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common RSS artifacts
        text = re.sub(r'&lt;.*?&gt;', '', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&quot;', '"', text)
        
        return text.strip()

    def filter_breaking_news(self, articles):
        """Filter articles that are likely breaking news"""
        breaking_news = []
        
        for article in articles:
            score = self.calculate_breaking_score(article)
            if score > 0:
                article['breaking_score'] = score
                breaking_news.append(article)
        
        # Sort by breaking score and recency
        breaking_news.sort(key=lambda x: (x['breaking_score'], x['timestamp']), reverse=True)
        
        return breaking_news

    def calculate_breaking_score(self, article):
        """Calculate how likely an article is breaking news"""
        score = 0
        title_lower = article['title'].lower()
        desc_lower = article.get('description', '').lower()
        
        # Check for breaking news keywords
        breaking_keywords = ['breaking', 'urgent', 'alert', 'developing', 'live', 'latest']
        for keyword in breaking_keywords:
            if keyword in title_lower:
                score += 3
            if keyword in desc_lower:
                score += 1
        
        # Check for time-sensitive words
        time_keywords = ['today', 'now', 'just', 'minutes', 'hours', 'update']
        for keyword in time_keywords:
            if keyword in title_lower:
                score += 2
        
        # Check for importance indicators
        importance_keywords = ['major', 'significant', 'massive', 'historic', 'unprecedented']
        for keyword in importance_keywords:
            if keyword in title_lower:
                score += 2
        
        # Boost recent articles
        try:
            if article.get('published'):
                # Simple boost for articles (exact parsing would be more complex)
                score += 1
        except:
            pass
        
        return score

    def get_cached_breaking_news(self):
        """Get cached breaking news"""
        if not self.breaking_news_cache or not self.last_update:
            return self.fetch_breaking_news()
        
        # Refresh if cache is older than 30 seconds
        if datetime.now() - self.last_update > timedelta(seconds=30):
            return self.fetch_breaking_news()
        
        return self.breaking_news_cache

    def format_for_frontend(self, breaking_news):
        """Format breaking news for frontend consumption"""
        formatted = []
        
        for article in breaking_news[:5]:  # Top 5 breaking news
            # Create compelling breaking news text
            title = article['title']
            source = article['source']
            
            # Add breaking news prefix if not already present
            if not any(keyword in title.lower() for keyword in ['breaking', 'live', 'urgent']):
                prefixes = ['BREAKING:', 'LIVE:', 'UPDATE:', 'DEVELOPING:']
                prefix = prefixes[len(formatted) % len(prefixes)]
                text = f"{prefix} {title}"
            else:
                text = title
            
            formatted.append({
                'text': text,
                'source': source,
                'link': article.get('link', '#'),
                'timestamp': article['timestamp']
            })
        
        return formatted

class BreakingNewsHandler(BaseHTTPRequestHandler):
    def __init__(self, scraper, *args, **kwargs):
        self.scraper = scraper
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/breaking-news':
                # Get breaking news
                breaking_news = self.scraper.get_cached_breaking_news()
                formatted_news = self.scraper.format_for_frontend(breaking_news)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                response_data = {
                    'breaking_news': formatted_news,
                    'last_updated': self.scraper.last_update.isoformat() if self.scraper.last_update else None,
                    'total_items': len(formatted_news)
                }
                
                self.wfile.write(json.dumps(response_data, indent=2).encode())
                
            elif self.path == '/health':
                # Health check endpoint
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                health_data = {
                    'status': 'healthy',
                    'last_update': self.scraper.last_update.isoformat() if self.scraper.last_update else None,
                    'cached_items': len(self.scraper.breaking_news_cache)
                }
                
                self.wfile.write(json.dumps(health_data).encode())
                
            else:
                # 404 for other paths
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            logger.error(f"❌ Request handling error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Internal Server Error: {str(e)}'.encode())

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def create_handler_class(scraper):
    """Create handler class with scraper instance"""
    def handler(*args, **kwargs):
        return BreakingNewsHandler(scraper, *args, **kwargs)
    return handler

def start_breaking_news_service(port=8888):
    """Start the breaking news scraper service"""
    logger.info(f"🚀 Starting Breaking News Scraper Service on port {port}")
    
    # Create scraper instance
    scraper = BreakingNewsScraper()
    
    # Initial fetch
    logger.info("📡 Performing initial breaking news fetch...")
    scraper.fetch_breaking_news()
    
    # Create HTTP server (avoiding localhost for corporate environments)
    handler_class = create_handler_class(scraper)
    server = HTTPServer(('0.0.0.0', port), handler_class)
    
    logger.info(f"✅ Breaking News Service running on http://0.0.0.0:{port}")
    logger.info("📡 Endpoints available:")
    logger.info(f"   - http://0.0.0.0:{port}/breaking-news")
    logger.info(f"   - http://0.0.0.0:{port}/health")
    logger.info("🏢 Corporate environment compatible - no localhost dependency")
    
    # Start background refresh
    def background_refresh():
        while True:
            try:
                time.sleep(30)  # Refresh every 30 seconds
                scraper.fetch_breaking_news()
            except Exception as e:
                logger.error(f"❌ Background refresh error: {e}")
    
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()
    
    # Start server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Breaking News Service shutting down...")
        server.shutdown()

if __name__ == "__main__":
    start_breaking_news_service() 
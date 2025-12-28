#!/usr/bin/env python3
"""
📈 LIVE FINANCIAL TICKER v1.0

Real-time financial market data ticker with multiple data sources.
Updates every 30 seconds with Dow Jones, S&P 500, NASDAQ, and more.

FEATURES:
✅ Multiple financial data APIs (FMP, Alpha Vantage, Yahoo Finance)
✅ Real-time market indices (DOW, S&P 500, NASDAQ, etc.)
✅ Automatic updates every 30 seconds
✅ Fallback sources for reliability
✅ Professional formatting
✅ Error handling and recovery
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from enum import Enum

logger = logging.getLogger(__name__)

class MarketStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"

@dataclass
class MarketIndex:
    """Market index data structure."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    high: float
    low: float
    volume: Optional[int]
    market_cap: Optional[str]
    last_update: str
    source: str
    status: MarketStatus = MarketStatus.OPEN

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': round(self.price, 2),
            'change': round(self.change, 2),
            'change_percent': round(self.change_percent, 2),
            'high': round(self.high, 2),
            'low': round(self.low, 2),
            'volume': self.volume,
            'market_cap': self.market_cap,
            'last_update': self.last_update,
            'source': self.source,
            'status': self.status.value,
            'is_positive': self.change >= 0
        }

class LiveFinancialTicker:
    """
    Live Financial Ticker System
    Fetches real-time market data from multiple sources
    """
    
    def __init__(self):
        # API Keys (can be set via environment variables)
        self.api_keys = {
            'fmp': os.getenv('FMP_API_KEY', 'demo'),  # Financial Modeling Prep
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', 'demo'),
            'polygon': os.getenv('POLYGON_API_KEY', 'demo')
        }
        
        # Major market indices to track
        self.indices = {
            # US Major Indices
            '^DJI': {'name': 'Dow Jones', 'fmp': 'DJI', 'yahoo': '^DJI'},
            '^GSPC': {'name': 'S&P 500', 'fmp': 'SPX', 'yahoo': '^GSPC'},
            '^IXIC': {'name': 'NASDAQ', 'fmp': 'IXIC', 'yahoo': '^IXIC'},
            '^RUT': {'name': 'Russell 2000', 'fmp': 'RUT', 'yahoo': '^RUT'},
            
            # Global Indices  
            '^FTSE': {'name': 'FTSE 100', 'fmp': 'UKX', 'yahoo': '^FTSE'},
            '^GDAXI': {'name': 'DAX', 'fmp': 'DAX', 'yahoo': '^GDAXI'},
            '^N225': {'name': 'Nikkei 225', 'fmp': 'N225', 'yahoo': '^N225'},
            
            # Crypto
            'BTC-USD': {'name': 'Bitcoin', 'fmp': 'BTCUSD', 'yahoo': 'BTC-USD'},
            'ETH-USD': {'name': 'Ethereum', 'fmp': 'ETHUSD', 'yahoo': 'ETH-USD'},
            
            # Commodities
            'GC=F': {'name': 'Gold', 'fmp': 'XAUUSD', 'yahoo': 'GC=F'},
            'CL=F': {'name': 'Crude Oil', 'fmp': 'USOIL', 'yahoo': 'CL=F'}
        }
        
        # Data sources in priority order
        self.data_sources = [
            self.fetch_from_fmp,
            self.fetch_from_yahoo_finance,
            self.fetch_from_alpha_vantage
        ]
        
        # Rate limiting
        self.last_fetch_time = 0
        self.min_fetch_interval = 30  # 30 seconds minimum
        
        # Cache and metrics
        self.current_data = {}
        self.fetch_count = 0
        self.error_count = 0
        self.last_successful_fetch = None
        
        # Update interval
        self.update_interval = 30  # 30 seconds
        self.is_running = False
        
        logger.info("📈 Live Financial Ticker initialized")
        logger.info(f"   📊 Tracking {len(self.indices)} market indices")
        logger.info(f"   ⏱️ Update interval: {self.update_interval} seconds")
    
    async def start_ticker(self):
        """Start the live ticker with automatic updates."""
        if self.is_running:
            logger.warning("⚠️ Ticker is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting live financial ticker...")
        
        while self.is_running:
            try:
                # Fetch latest market data
                await self.fetch_all_market_data()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"❌ Ticker error: {e}")
                self.error_count += 1
                await asyncio.sleep(10)  # Short delay on error
    
    def stop_ticker(self):
        """Stop the live ticker."""
        self.is_running = False
        logger.info("⏹️ Financial ticker stopped")
    
    async def fetch_all_market_data(self) -> Dict[str, MarketIndex]:
        """Fetch market data from all available sources."""
        current_time = time.time()
        
        # Rate limiting check
        if current_time - self.last_fetch_time < self.min_fetch_interval:
            logger.debug("⏱️ Rate limiting: using cached data")
            return self.current_data
        
        logger.info("📊 Fetching live market data...")
        self.fetch_count += 1
        self.last_fetch_time = current_time
        
        # Try each data source until we get successful results
        for source_func in self.data_sources:
            try:
                logger.debug(f"🔍 Trying source: {source_func.__name__}")
                market_data = await source_func()
                
                if market_data:
                    self.current_data = market_data
                    self.last_successful_fetch = datetime.now()
                    
                    logger.info(f"✅ Successfully fetched {len(market_data)} market indices")
                    return market_data
                    
            except Exception as e:
                logger.warning(f"⚠️ Source {source_func.__name__} failed: {e}")
                continue
        
        # If all sources fail, return cached data
        logger.warning("❌ All data sources failed, using cached data")
        self.error_count += 1
        return self.current_data
    
    async def fetch_from_fmp(self) -> Dict[str, MarketIndex]:
        """Fetch data from Financial Modeling Prep API."""
        try:
            base_url = "https://financialmodelingprep.com/api/v3"
            
            # Get major indices
            indices_url = f"{base_url}/quotes/index?apikey={self.api_keys['fmp']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(indices_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_fmp_data(data)
                    else:
                        logger.warning(f"⚠️ FMP API returned status {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"❌ FMP fetch failed: {e}")
            return {}
    
    def parse_fmp_data(self, data: List[Dict]) -> Dict[str, MarketIndex]:
        """Parse Financial Modeling Prep API response."""
        results = {}
        
        try:
            for item in data:
                symbol = item.get('symbol', '')
                
                # Map FMP symbols to our standard symbols
                standard_symbol = self.map_fmp_symbol(symbol)
                if not standard_symbol:
                    continue
                
                index_info = self.indices.get(standard_symbol, {})
                
                market_index = MarketIndex(
                    symbol=standard_symbol,
                    name=index_info.get('name', item.get('name', symbol)),
                    price=float(item.get('price', 0)),
                    change=float(item.get('change', 0)),
                    change_percent=float(item.get('changesPercentage', 0)),
                    high=float(item.get('dayHigh', 0)),
                    low=float(item.get('dayLow', 0)),
                    volume=item.get('volume'),
                    market_cap=item.get('marketCap'),
                    last_update=datetime.now().isoformat(),
                    source='Financial Modeling Prep'
                )
                
                results[standard_symbol] = market_index
                
        except Exception as e:
            logger.error(f"❌ Error parsing FMP data: {e}")
        
        return results
    
    def map_fmp_symbol(self, fmp_symbol: str) -> Optional[str]:
        """Map FMP symbols to standard symbols."""
        symbol_mapping = {
            'DJI': '^DJI',
            'SPX': '^GSPC', 
            'IXIC': '^IXIC',
            'RUT': '^RUT',
            'UKX': '^FTSE',
            'DAX': '^GDAXI',
            'N225': '^N225',
            'BTCUSD': 'BTC-USD',
            'ETHUSD': 'ETH-USD',
            'XAUUSD': 'GC=F',
            'USOIL': 'CL=F'
        }
        return symbol_mapping.get(fmp_symbol)
    
    async def fetch_from_yahoo_finance(self) -> Dict[str, MarketIndex]:
        """Fetch data from Yahoo Finance (via unofficial API)."""
        try:
            # Yahoo Finance query API
            symbols = ','.join(self.indices.keys())
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_yahoo_data(data)
                    else:
                        logger.warning(f"⚠️ Yahoo Finance returned status {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"❌ Yahoo Finance fetch failed: {e}")
            return {}
    
    def parse_yahoo_data(self, data: Dict) -> Dict[str, MarketIndex]:
        """Parse Yahoo Finance API response."""
        results = {}
        
        try:
            quotes = data.get('quoteResponse', {}).get('result', [])
            
            for quote in quotes:
                symbol = quote.get('symbol', '')
                if symbol not in self.indices:
                    continue
                
                index_info = self.indices[symbol]
                
                # Calculate change percent
                price = quote.get('regularMarketPrice', 0)
                previous_close = quote.get('regularMarketPreviousClose', price)
                change = price - previous_close
                change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                
                market_index = MarketIndex(
                    symbol=symbol,
                    name=index_info.get('name', quote.get('shortName', symbol)),
                    price=float(price),
                    change=float(change),
                    change_percent=float(change_percent),
                    high=float(quote.get('regularMarketDayHigh', 0)),
                    low=float(quote.get('regularMarketDayLow', 0)),
                    volume=quote.get('regularMarketVolume'),
                    market_cap=quote.get('marketCap'),
                    last_update=datetime.now().isoformat(),
                    source='Yahoo Finance'
                )
                
                results[symbol] = market_index
                
        except Exception as e:
            logger.error(f"❌ Error parsing Yahoo data: {e}")
        
        return results
    
    async def fetch_from_alpha_vantage(self) -> Dict[str, MarketIndex]:
        """Fetch data from Alpha Vantage API."""
        try:
            # Alpha Vantage doesn't have a single endpoint for all indices
            # We'll fetch major ones individually (simplified for demo)
            results = {}
            
            major_symbols = ['^GSPC', '^DJI', '^IXIC']  # Focus on major US indices
            
            async with aiohttp.ClientSession() as session:
                for symbol in major_symbols:
                    try:
                        # Use TIME_SERIES_DAILY for index data
                        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_keys['alpha_vantage']}"
                        
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                data = await response.json()
                                parsed = self.parse_alpha_vantage_data(symbol, data)
                                if parsed:
                                    results[symbol] = parsed
                                    
                        # Rate limit: Alpha Vantage free tier is limited
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error fetching {symbol} from Alpha Vantage: {e}")
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Alpha Vantage fetch failed: {e}")
            return {}
    
    def parse_alpha_vantage_data(self, symbol: str, data: Dict) -> Optional[MarketIndex]:
        """Parse Alpha Vantage API response."""
        try:
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                return None
            
            # Get the latest trading day
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            
            # Get previous day for change calculation
            dates = sorted(time_series.keys(), reverse=True)
            if len(dates) < 2:
                return None
            
            previous_data = time_series[dates[1]]
            
            current_price = float(latest_data['4. close'])
            previous_price = float(previous_data['4. close'])
            change = current_price - previous_price
            change_percent = (change / previous_price * 100) if previous_price != 0 else 0
            
            index_info = self.indices.get(symbol, {})
            
            return MarketIndex(
                symbol=symbol,
                name=index_info.get('name', symbol),
                price=current_price,
                change=change,
                change_percent=change_percent,
                high=float(latest_data['2. high']),
                low=float(latest_data['3. low']),
                volume=int(latest_data['5. volume']) if latest_data.get('5. volume') else None,
                market_cap=None,
                last_update=datetime.now().isoformat(),
                source='Alpha Vantage'
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing Alpha Vantage data for {symbol}: {e}")
            return None
    
    def get_current_data(self) -> Dict[str, Dict[str, Any]]:
        """Get current market data in JSON format."""
        return {symbol: index.to_dict() for symbol, index in self.current_data.items()}
    
    def get_ticker_html(self) -> str:
        """Generate HTML for the financial ticker."""
        if not self.current_data:
            return '<div class="financial-ticker-empty">Loading market data...</div>'
        
        ticker_items = []
        for symbol, index in self.current_data.items():
            color_class = 'positive' if index.change >= 0 else 'negative'
            arrow = '▲' if index.change >= 0 else '▼'
            sign = '+' if index.change >= 0 else ''
            
            ticker_items.append(f'''
                <div class="ticker-item {color_class}">
                    <span class="ticker-symbol">{index.name}</span>
                    <span class="ticker-price">${index.price:,.2f}</span>
                    <span class="ticker-change">{arrow} {sign}{index.change:.2f} ({sign}{index.change_percent:.2f}%)</span>
                </div>
            ''')
        
        return f'<div class="financial-ticker-scroll">{"".join(ticker_items)}</div>'
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get ticker performance metrics."""
        return {
            'total_fetches': self.fetch_count,
            'error_count': self.error_count,
            'success_rate': round((self.fetch_count - self.error_count) / max(self.fetch_count, 1) * 100, 2),
            'last_successful_fetch': self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            'indices_tracked': len(self.indices),
            'current_data_count': len(self.current_data),
            'update_interval_seconds': self.update_interval,
            'is_running': self.is_running
        }

# Global ticker instance
financial_ticker = LiveFinancialTicker()

# API functions for integration
async def get_market_data() -> Dict[str, Any]:
    """Get current market data (main API function)."""
    try:
        data = await financial_ticker.fetch_all_market_data()
        
        return {
            'success': True,
            'data': {symbol: index.to_dict() for symbol, index in data.items()},
            'count': len(data),
            'last_update': datetime.now().isoformat(),
            'source': 'live_financial_ticker'
        }
    except Exception as e:
        logger.error(f"❌ Get market data failed: {e}")
        return {
            'success': False,
            'data': {},
            'count': 0,
            'error': str(e),
            'source': 'live_financial_ticker'
        }

async def start_live_ticker():
    """Start the live ticker (for background tasks)."""
    await financial_ticker.start_ticker()

def stop_live_ticker():
    """Stop the live ticker."""
    financial_ticker.stop_ticker()

def get_ticker_status() -> Dict[str, Any]:
    """Get ticker status and metrics."""
    return financial_ticker.get_performance_metrics()

# Test function
async def test_financial_ticker():
    """Test the financial ticker system."""
    print("📈 Testing Live Financial Ticker...")
    print("=" * 50)
    
    # Test data fetching
    print("\n📊 Testing market data fetch...")
    data = await get_market_data()
    
    print(f"   Success: {data['success']}")
    print(f"   Indices count: {data['count']}")
    
    if data['success'] and data['data']:
        print("\n📈 Sample market data:")
        for symbol, index_data in list(data['data'].items())[:5]:  # Show first 5
            print(f"   {index_data['name']}: ${index_data['price']:,.2f} "
                  f"({index_data['change']:+.2f}, {index_data['change_percent']:+.2f}%)")
    
    # Test ticker HTML generation
    print(f"\n🎨 HTML ticker preview:")
    html = financial_ticker.get_ticker_html()
    print(f"   Generated {len(html)} characters of HTML")
    
    # Show performance metrics
    metrics = get_ticker_status()
    print(f"\n📊 Performance metrics:")
    print(f"   Fetches: {metrics['total_fetches']}")
    print(f"   Success rate: {metrics['success_rate']}%")
    print(f"   Indices tracked: {metrics['indices_tracked']}")
    print(f"   Update interval: {metrics['update_interval_seconds']}s")
    
    print("\n✅ Financial ticker test completed!")

if __name__ == "__main__":
    asyncio.run(test_financial_ticker()) 
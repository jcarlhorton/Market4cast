import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from data_utils import calculate_price_gap, calculate_volume_spike, get_day_two_open, clean_ticker_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionEngine:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.gap_threshold = 5.0
        self.volume_threshold = 2.0

    def get_recent_earnings_tickers(self):
        """
        In a real production environment, this would scrape a calendar.
        For this implementation, we can use a watchlist or query yfinance
        for common high-volume tickers to check for recent earnings.
        """
        # Placeholder: In a full implementation, this would query an earnings API or scrape
        # yahoo finance earnings calendar.
        logger.info("Scanning for recent earnings events...")
        return ["NVDA", "TSLA", "AMD", "MSFT", "GOOGL", "AAPL", "META", "AMZN"]

    def process_ticker(self, ticker):
        """
        Analyzes a single ticker for an earnings anomaly.
        """
        logger.info(f"Analyzing {ticker} for anomalies...")
        stock = yf.Ticker(ticker)
        
        # Get last 5 days of data to check for very recent gaps
        hist = stock.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        
        hist = clean_ticker_data(hist)
        
        # Calculate gap and volume spike for the most recent day
        latest_day = hist.iloc[-1]
        gap = calculate_price_gap(hist).iloc[-1]
        vol_mult = calculate_volume_spike(hist, window=30).iloc[-1] if len(hist) >= 30 else 1.0
        # If we only have 5 days, calculate_volume_spike might need fallback or we need more data
        if len(hist) < 30:
            full_hist = stock.history(period="60d")
            vol_mult = calculate_volume_spike(full_hist).iloc[-1]
        
        if gap > self.gap_threshold and vol_mult > self.volume_threshold:
            logger.info(f"ANOMALY DETECTED: {ticker} (Gap: {gap:.2f}%, Vol Mult: {vol_mult:.2f})")
            
            # Entry logic: Day 2 Open (if we are at end of Day 1)
            # If the market just closed on Day 1, Day 2 Open hasn't happened yet.
            # We track this as a 'PENDING' entry.
            return {
                'ticker': ticker,
                'announcement_date': hist.index[-1].strftime('%Y-%m-%d'),
                'gap_pct': gap,
                'volume_mult': vol_mult,
                'last_close': latest_day['Close']
            }
        
        return None

    def scan_universe(self):
        tickers = self.get_recent_earnings_tickers()
        anomalies = []
        for ticker in tickers:
            result = self.process_ticker(ticker)
            if result:
                anomalies.append(result)
        return anomalies

if __name__ == "__main__":
    engine = IngestionEngine()
    results = engine.scan_universe()
    print(f"Found {len(results)} anomalies.")

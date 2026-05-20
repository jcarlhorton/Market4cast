import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    @staticmethod
    def validate_ohlcv(df):
        """
        Ensures the dataframe has required columns and handles missing values.
        """
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return None
        
        # Check for non-numeric or infinite values
        if not np.all(np.isfinite(df[required_cols])):
            logger.warning("Found non-finite values in OHLCV data. Attempting to clean...")
            df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=required_cols)
            
        # Ensure positive prices and volume
        if (df[required_cols] < 0).any().any():
            logger.error("Negative prices or volume detected in data.")
            return None
            
        return df

    @staticmethod
    def handle_api_holes(df, ticker):
        """
        Detects significant gaps in the time series that might indicate API failure.
        """
        if df.empty:
            return df
            
        # Check for gap between index dates (assuming daily data)
        # We expect gaps for weekends/holidays, but more than 4-5 days might be a 'hole'.
        date_diffs = pd.Series(df.index).diff().dt.days
        if (date_diffs > 5).any():
            logger.warning(f"Significant data hole detected for {ticker} (>5 days).")
            # In a more advanced version, we might trigger a re-fetch or mark the ticker as UNRELIABLE
            
        return df

    @staticmethod
    def sanitize_prediction_input(data):
        """
        Sanitizes data before it is sent to the ML model or stored in DB.
        """
        sanitized = data.copy()
        # Ensure percentage values are within logical bounds
        if 'gap_pct' in sanitized:
            sanitized['gap_pct'] = max(-100.0, min(500.0, sanitized['gap_pct']))
            
        return sanitized

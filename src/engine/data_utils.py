import pandas as pd
import numpy as np

def calculate_price_gap(df):
    """
    Calculates the gap percentage between the current Close and previous Close.
    Assumes df has a 'Close' column.
    """
    if len(df) < 2:
        return 0.0
    
    prev_close = df['Close'].shift(1)
    gap_pct = ((df['Close'] - prev_close) / prev_close) * 100
    return gap_pct

def calculate_volume_spike(df, window=30):
    """
    Calculates the volume spike multiplier relative to a moving average.
    Assumes df has a 'Volume' column.
    """
    if len(df) < window:
        return 1.0
    
    avg_volume = df['Volume'].rolling(window=window).mean()
    volume_multiplier = df['Volume'] / avg_volume
    return volume_multiplier

def get_day_two_open(df, announcement_index):
    """
    Returns the Open price of the day AFTER the announcement.
    If announcement_index is the last day in df, returns None.
    """
    try:
        # announcement_index is the integer index of the day the news hit
        entry_index = announcement_index + 1
        if entry_index < len(df):
            return df.iloc[entry_index]['Open']
    except Exception:
        pass
    return None

def clean_ticker_data(df):
    """
    Basic cleaning: handle NaNs, ensure numeric types.
    """
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[cols].copy()
    df = df.dropna()
    return df

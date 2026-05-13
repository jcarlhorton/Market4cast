import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_utils import calculate_price_gap, calculate_volume_spike, get_day_two_open, clean_ticker_data

# Heuristic V1 Constants
W_GAP = 0.3
W_VOL = 0.2
BASE_DRIFT = 5.0  # Base expected percentage increase

def run_backtest(tickers, start_year=2023, end_year=2024):
    results = []
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        stock = yf.Ticker(ticker)
        
        # Get historical data
        hist = stock.history(start=f"{start_year}-01-01", end=f"{end_year}-12-31")
        if hist.empty:
            continue
        
        hist = clean_ticker_data(hist)
        
        # Calculate technical filters
        hist['Gap_Pct'] = calculate_price_gap(hist)
        hist['Vol_Mult'] = calculate_volume_spike(hist)
        
        # Identify Anomalies (>5% gap AND >200% volume)
        anomalies = hist[(hist['Gap_Pct'] > 5.0) & (hist['Vol_Mult'] > 2.0)].copy()
        
        for idx, row in anomalies.iterrows():
            announcement_date = idx
            announcement_idx = hist.index.get_loc(idx)
            
            # Entry: Day 2 Open
            entry_price = get_day_two_open(hist, announcement_idx)
            if entry_price is None:
                continue
            
            # Prediction: Heuristic V1
            # Note: We don't have LLM scores for historical backtests without API calls,
            # so we use a placeholder or assume a neutral score for backtesting baseline.
            llm_score = 0.5 # Placeholder
            target_pct = BASE_DRIFT + (W_GAP * row['Gap_Pct']) + (W_VOL * row['Vol_Mult'])
            target_price = entry_price * (1 + (target_pct / 100))
            
            # Outcome: Track for 30 days
            end_tracking_idx = announcement_idx + 30
            if end_tracking_idx >= len(hist):
                end_tracking_idx = len(hist) - 1
            
            outcome_period = hist.iloc[announcement_idx+1 : end_tracking_idx+1]
            if outcome_period.empty:
                continue
            
            max_price = outcome_period['High'].max()
            final_price = outcome_period.iloc[-1]['Close']
            
            results.append({
                'Ticker': ticker,
                'Date': announcement_date,
                'Gap': row['Gap_Pct'],
                'Volume_Mult': row['Vol_Mult'],
                'Entry_Price': entry_price,
                'Predicted_Target_%': target_pct,
                'Actual_Max_%': ((max_price - entry_price) / entry_price) * 100,
                'Actual_Final_%': ((final_price - entry_price) / entry_price) * 100,
                'Success': max_price >= target_price
            })
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test with a few control tickers
    control_tickers = ["NVDA", "TSLA", "AMD", "MSFT", "GOOGL", "AAPL"]
    df_results = run_backtest(control_tickers)
    
    if not df_results.empty:
        print("\n--- Backtest Results ---")
        print(df_results[['Ticker', 'Date', 'Predicted_Target_%', 'Actual_Max_%', 'Success']])
        
        accuracy = df_results['Success'].mean() * 100
        print(f"\nOverall Heuristic Accuracy: {accuracy:.2f}%")
        
        # Save results
        df_results.to_csv("backtest_results.csv", index=False)
        print("Detailed results saved to backtest_results.csv")
    else:
        print("No anomalies found in the specified range.")

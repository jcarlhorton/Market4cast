import pandas as pd
import sqlite3
import os

DB_PATH = "market4cast.db"
CSV_PATH = "backtest_results.csv"

def import_csv_to_db():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Please run backtest.py first.")
        return

    print(f"Reading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Establish SQLite connection
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing mock data first to avoid overlapping primary keys
    cursor.execute("DELETE FROM active_predictions;")
    
    inserted_count = 0
    for _, row in df.iterrows():
        ticker = row['Ticker']
        date_str = str(row['Date']).split()[0] # get YYYY-MM-DD
        entry_price = float(row['Entry_Price'])
        target_pct = float(row['Predicted_Target_%'])
        target_price = entry_price * (1 + (target_pct / 100))
        stop_loss = entry_price * 0.93 # 7% stop loss
        
        # Sector lookup helper
        sectors = {
            "NVDA": "Technology",
            "TSLA": "Consumer Cyclical",
            "AMD": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Communication Services",
            "AAPL": "Technology"
        }
        sector = sectors.get(ticker, "Technology")
        
        # Construct catalyst summary based on backtest stats
        catalyst = f"Historical PEAD Anomaly. Gap: {row['Gap']:.2f}%, Vol Mult: {row['Volume_Mult']:.2f}x."
        
        query = """
            INSERT OR REPLACE INTO active_predictions 
            (ticker, announcement_date, entry_date, entry_price, predicted_target_price, 
             predicted_target_pct, stop_loss_price, suggested_position_size, sector, 
             catalyst_summary, llm_guidance_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
        """
        try:
            cursor.execute(query, (
                ticker,
                date_str,
                date_str,
                entry_price,
                target_price,
                target_pct,
                stop_loss,
                0.02, # Neutral position size
                sector,
                catalyst,
                0.5 # Neutral score
            ))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting {ticker} on {date_str}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {inserted_count} historical anomalies into {DB_PATH} as ACTIVE predictions.")

if __name__ == "__main__":
    import_csv_to_db()

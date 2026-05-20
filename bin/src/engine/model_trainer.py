import sqlite3
import pandas as pd
import xgboost as xgb
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "market4cast.db"
MODEL_PATH = "src/engine/models/market4cast_v2.json"
SAMPLE_THRESHOLD = 500

class ModelTrainer:
    def __init__(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    def get_training_data(self):
        """
        Fetches closed prediction outcomes from the database.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM historical_performance"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to fetch training data: {e}")
            return pd.DataFrame()

    def train_v2_model(self):
        """
        Trains the XGBoost regressor if the sample threshold is met.
        """
        df = self.get_training_data()
        
        if len(df) < SAMPLE_THRESHOLD:
            logger.info(f"Insufficient data for XGBoost training ({len(df)}/{SAMPLE_THRESHOLD} samples).")
            return False
            
        logger.info(f"Starting XGBoost retraining with {len(df)} samples...")
        
        # Feature Engineering: In a real app, we'd include sector, gap, volume, llm_score
        X = df[['gap_pct', 'volume_mult', 'llm_guidance_score']] # Example features
        y = df['actual_return_pct']
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            objective='reg:squarederror'
        )
        
        model.fit(X, y)
        model.save_model(MODEL_PATH)
        
        logger.info("XGBoost model saved successfully.")
        return True

    def run_scheduled_retrain(self):
        """
        This would be triggered by the main loop on Saturdays at 2:00 AM.
        """
        now = datetime.now()
        # Saturday is 5 (0 is Monday)
        if now.weekday() == 5 and now.hour == 2:
            self.train_v2_model()

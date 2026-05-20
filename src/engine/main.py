import time
import logging
import sqlite3
import os
from ingestion import IngestionEngine
from validator import DataValidator
from analysis import FilingAnalyzer
from risk_engine import RiskEngine
from model_predictor import ModelPredictor
from model_trainer import ModelTrainer

# Enhanced Logging for Unattended Operation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market4cast_sidecar.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Market4castSidecar")

DB_PATH = "market4cast.db"
SCHEMA_PATH = "src/engine/db_schema.sql"

class Market4castSidecar:
    def __init__(self):
        self.db_conn = self._init_db()
        self.ingestion = IngestionEngine(db_manager=self)
        self.analyzer = FilingAnalyzer()
        self.risk_engine = RiskEngine()
        self.predictor = ModelPredictor()
        self.trainer = ModelTrainer()
        self.running = True

    def _init_db(self):
        """
        Initializes the SQLite database with WAL mode and schema.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # Check if table exists (avoids race condition where JDBC creates empty file first)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='active_predictions';")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.info("Database tables missing. Initializing schema...")
            with open(SCHEMA_PATH, 'r') as f:
                conn.executescript(f.read())
        return conn

    def poll_for_anomalies(self):
        """
        Main polling logic: Scans, analyzes, and calculates risk for anomalies.
        """
        logger.info("Scanning universe for new earnings anomalies...")
        try:
            anomalies = self.ingestion.scan_universe()
            
            for anomaly in anomalies:
                try:
                    # Step 1: Qualitative Analysis
                    analysis = self.analyzer.analyze_ticker(anomaly['ticker'])
                    
                    # Step 2: Target Prediction (Hybrid Model)
                    target_pct = self.predictor.calculate_target(
                        anomaly['gap_pct'], 
                        anomaly['volume_mult'], 
                        analysis['guidance_score']
                    )
                    
                    # Step 3: Risk Calculation
                    risk_profile = self.risk_engine.generate_risk_profile(
                        anomaly['ticker'],
                        anomaly['last_close'],
                        analysis['guidance_score'],
                        0.8, 
                        [], # Active list placeholder
                        "Technology"
                    )
                    
                    self._save_full_prediction(anomaly, analysis, target_pct, risk_profile)
                except Exception as e:
                    logger.error(f"Failed to process ticker {anomaly.get('ticker')}: {e}")

            # Step 4: Scheduled Retraining (Only on Saturdays at 2 AM)
            self.trainer.run_scheduled_retrain()
            
        except Exception as e:
            logger.error(f"Critical error during market scan: {e}")

    def run(self):
        logger.info("Market4cast Sidecar started in UNATTENDED mode.")
        while self.running:
            try:
                self.poll_for_anomalies()
                logger.info("Scan cycle complete. Sleeping for 1 hour...")
                time.sleep(3600)
            except KeyboardInterrupt:
                logger.info("Sidecar received shutdown signal.")
                self.running = False
            except Exception as e:
                logger.error(f"Loop error: {e}. Retrying in 5 minutes...")
                time.sleep(300) # Wait 5 mins on critical loop failure

    def _save_full_prediction(self, anomaly, analysis, target_pct, risk):
        """
        Saves the complete prediction record to the database.
        """
        try:
            cursor = self.db_conn.cursor()
            query = """
                INSERT OR REPLACE INTO active_predictions 
                (ticker, announcement_date, entry_date, entry_price, predicted_target_price, 
                 predicted_target_pct, stop_loss_price, suggested_position_size, sector, 
                 catalyst_summary, llm_guidance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                anomaly['ticker'],
                anomaly['announcement_date'],
                anomaly['announcement_date'], # Entry date same for now
                anomaly['last_close'],
                anomaly['last_close'] * (1 + target_pct/100),
                target_pct,
                risk['stop_loss'],
                risk['position_size'],
                "Technology",
                analysis['catalyst_summary'],
                analysis['guidance_score']
            ))
            self.db_conn.commit()
            logger.info(f"Full prediction saved for {anomaly['ticker']}.")
        except Exception as e:
            logger.error(f"Error saving full prediction: {e}")

if __name__ == "__main__":
    sidecar = Market4castSidecar()
    sidecar.run()

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        exists = os.path.exists(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        
        if not exists:
            logger.info("Initializing new database...")
            with open(SCHEMA_PATH, 'r') as f:
                conn.executescript(f.read())
        return conn

    def poll_for_anomalies(self):
        """
        Main polling logic: Scans, analyzes, and calculates risk for anomalies.
        """
        logger.info("Starting market scan...")
        anomalies = self.ingestion.scan_universe()
        
        for anomaly in anomalies:
            # Step 1: Qualitative Analysis
            analysis = self.analyzer.analyze_ticker(anomaly['ticker'])
            
            # Step 2: Target Prediction (Hybrid Model)
            target_pct = self.predictor.calculate_target(
                anomaly['gap_pct'], 
                anomaly['volume_mult'], 
                analysis['guidance_score']
            )
            
            # Step 3: Risk Calculation
            # In a real app, we'd fetch active predictions from DB for sector correlation
            active_list = [] # Placeholder
            risk_profile = self.risk_engine.generate_risk_profile(
                anomaly['ticker'],
                anomaly['last_close'],
                analysis['guidance_score'],
                0.8, # Placeholder system confidence
                active_list,
                "Technology" # Placeholder sector
            )
            
            self._save_full_prediction(anomaly, analysis, target_pct, risk_profile)
            
        # Step 4: Scheduled Retraining
        self.trainer.run_scheduled_retrain()

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

    def run(self):
        logger.info("Market4cast Sidecar is now running.")
        while self.running:
            try:
                self.poll_for_anomalies()
                # Poll every hour (3600 seconds) or as needed
                logger.info("Market scan complete. Sleeping for 1 hour...")
                time.sleep(3600)
            except KeyboardInterrupt:
                logger.info("Sidecar shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")
                time.sleep(60) # Wait a minute before retrying

if __name__ == "__main__":
    sidecar = Market4castSidecar()
    sidecar.run()

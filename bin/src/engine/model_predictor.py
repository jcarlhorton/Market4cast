import xgboost as xgb
import os
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = "src/engine/models/market4cast_v2.json"

class ModelPredictor:
    def __init__(self):
        self.model = None
        self._load_model()
        
        # Heuristic V1 Constants
        self.W_GAP = 0.3
        self.W_VOL = 0.2
        self.W_LLM = 2.0
        self.BASE_DRIFT = 5.0

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = xgb.XGBRegressor()
                self.model.load_model(MODEL_PATH)
                logger.info("XGBoost V2 model loaded.")
            except Exception as e:
                logger.error(f"Failed to load XGBoost model: {e}")
                self.model = None

    def calculate_target(self, gap_pct, vol_mult, llm_score):
        """
        Hybrid prediction: Uses XGBoost if available, otherwise falls back to Heuristic V1.
        """
        if self.model:
            try:
                # Features must match training order
                features = [[gap_pct, vol_mult, llm_score]]
                prediction = self.model.predict(features)[0]
                logger.info(f"Using XGBoost V2: Predicted {prediction:.2f}%")
                return prediction
            except Exception as e:
                logger.error(f"XGBoost prediction failed, falling back to heuristic: {e}")
        
        # Heuristic V1 Fallback
        # target = Base + (Gap weight) + (Vol weight) + (LLM weight * score)
        prediction = self.BASE_DRIFT + (self.W_GAP * gap_pct) + (self.W_VOL * vol_mult) + (self.W_LLM * llm_score)
        logger.info(f"Using Heuristic V1: Predicted {prediction:.2f}%")
        return prediction

import logging

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self):
        self.max_sector_exposure = 0.20  # Max 20% in one sector
        self.default_stop_loss_pct = 0.07 # -7% Stop Loss
        self.base_position_size = 0.02   # 2% Base position size

    def calculate_stop_loss(self, entry_price):
        """
        Calculates the stop loss price based on entry.
        """
        return entry_price * (1 - self.default_stop_loss_pct)

    def calculate_position_size(self, guidance_score, confidence_score):
        """
        Adjusts position size based on LLM guidance and overall system confidence.
        Range: 1% to 5%
        """
        # score is -1 to 1. 1 is very bullish.
        adjustment = (guidance_score + 1) / 2 # Scale to 0-1
        size = self.base_position_size * (0.5 + adjustment)
        
        # Scale by system confidence
        size = size * (0.5 + confidence_score)
        
        # Clamp between 1% and 5%
        return max(0.01, min(0.05, size))

    def check_sector_correlation(self, active_predictions, new_sector):
        """
        Returns True if adding a new ticker in this sector exceeds exposure limits.
        """
        if not active_predictions:
            return True # Safe to add
            
        sector_count = sum(1 for p in active_predictions if p.get('sector') == new_sector)
        total_count = len(active_predictions)
        
        current_exposure = sector_count / total_count if total_count > 0 else 0
        
        if current_exposure >= self.max_sector_exposure:
            logger.warning(f"Sector exposure limit reached for {new_sector}.")
            return False
            
        return True

    def generate_risk_profile(self, ticker, entry_price, guidance_score, confidence_score, active_predictions, sector):
        """
        Compiles a full risk profile for a new prediction.
        """
        return {
            'ticker': ticker,
            'stop_loss': self.calculate_stop_loss(entry_price),
            'position_size': self.calculate_position_size(guidance_score, confidence_score),
            'sector_safe': self.check_sector_correlation(active_predictions, sector)
        }

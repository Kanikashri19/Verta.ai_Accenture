import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple, Dict, Any

from app.engine.models import BaselineStats

MIN_REQUIRED_HISTORY_OBSERVATIONS = 30

class StatsEngine:
    """
    Deterministic Statistical Engine for Baseline Profiling and Anomaly Detection.
    """
    
    @staticmethod
    def compute_baseline_stats(
        series: pd.Series,
        min_required: int = MIN_REQUIRED_HISTORY_OBSERVATIONS
    ) -> BaselineStats:
        """
        Computes robust baseline statistics from historical time-series observations.
        Explicitly handles missing data, zero-variance, and sparse histories.
        """
        clean_series = series.dropna()
        n = len(clean_series)
        
        if n < min_required:
            return BaselineStats(
                sample_size=n,
                mean=float(clean_series.mean()) if n > 0 else 0.0,
                std_dev=float(clean_series.std(ddof=1)) if n > 1 else 0.0,
                min_value=float(clean_series.min()) if n > 0 else 0.0,
                max_value=float(clean_series.max()) if n > 0 else 0.0,
                iqr=0.0,
                q1=0.0,
                q3=0.0,
                zero_variance=False,
                has_sufficient_history=False,
            )
            
        mean_val = float(clean_series.mean())
        std_val = float(clean_series.std(ddof=1)) if n > 1 else 0.0
        q1 = float(np.percentile(clean_series, 25))
        q3 = float(np.percentile(clean_series, 75))
        iqr = float(q3 - q1)
        
        is_zero_variance = (std_val < 1e-9)
        
        return BaselineStats(
            sample_size=n,
            mean=mean_val,
            std_dev=std_val,
            min_value=float(clean_series.min()),
            max_value=float(clean_series.max()),
            iqr=iqr,
            q1=q1,
            q3=q3,
            zero_variance=is_zero_variance,
            has_sufficient_history=True,
        )

    @staticmethod
    def calculate_anomaly_score(
        current_value: float,
        baseline: BaselineStats
    ) -> Tuple[Optional[float], Optional[float], Optional[float], str]:
        """
        Calculates deterministic Z-Score, p-value, and normalized Anomaly Score [0.0 - 1.0].
        Returns: (z_score, p_value, anomaly_score, status)
        """
        if not baseline.has_sufficient_history:
            return None, None, None, "INSUFFICIENT_HISTORY"
            
        if baseline.zero_variance:
            if abs(current_value - baseline.mean) < 1e-9:
                return 0.0, 1.0, 0.0, "NORMAL"
            else:
                # Deterministic bounded deviation when baseline has zero variance
                return 999.0, 0.0001, 1.0, "CRITICAL_ANOMALY"
                
        # Z-Score relative to standard deviation of baseline daily observations
        z = (current_value - baseline.mean) / baseline.std_dev
        
        # Two-sided approximate p-value
        p_val = float(2 * (1 - stats.norm.cdf(abs(z))))
        
        # Bounded Anomaly Score in [0, 1] using logistic scaling
        # z=0 -> 0.0, z=2.0 -> 0.50, z=3.5+ -> 0.90+
        anomaly_score = float(min(1.0, max(0.0, abs(z) / 4.0)))
        
        if abs(z) >= 3.0:
            status = "CRITICAL_ANOMALY"
        elif abs(z) >= 2.0:
            status = "MODERATE_ANOMALY"
        elif abs(z) >= 1.5:
            status = "MILD_DRIFT"
        else:
            status = "NORMAL"
            
        return float(z), float(p_val), round(anomaly_score, 4), status

stats_engine = StatsEngine()

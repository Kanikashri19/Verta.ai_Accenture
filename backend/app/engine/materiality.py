from typing import Optional
from app.engine.models import BaselineStats, MaterialityAssessment
from app.engine.stats import stats_engine

class MaterialityEngine:
    """
    Evaluates dual-gate business materiality and statistical significance.
    Guarantees that statistical noise is not confused with actionable business impact.
    """

    @staticmethod
    def evaluate(
        baseline_value: float,
        current_value: float,
        threshold_pct: float,
        baseline_stats: BaselineStats,
        z_threshold: float = 2.0
    ) -> MaterialityAssessment:
        """
        Evaluates materiality by combining relative business delta % against contract thresholds
        and statistical Z-score significance.
        """
        abs_change = current_value - baseline_value
        rel_change_pct = (abs_change / baseline_value * 100.0) if baseline_value != 0 else 0.0
        
        # Check historical sufficiency
        if not baseline_stats.has_sufficient_history:
            return MaterialityAssessment(
                business_materiality="MATERIAL" if abs(rel_change_pct) >= threshold_pct else "NON_MATERIAL",
                statistical_significance="INSUFFICIENT_HISTORY",
                overall_materiality="INSUFFICIENT_HISTORY",
                relative_change_pct=round(rel_change_pct, 2),
                absolute_change=round(abs_change, 2),
                threshold_pct=threshold_pct,
                z_score=None,
                p_value_approx=None,
                materiality_explanation=(
                    f"Cold-start: Insufficient historical observations ({baseline_stats.sample_size}/30 days). "
                    "Statistical anomaly detection is withheld to prevent false alarms."
                )
            )

        z_score, p_val, _, _ = stats_engine.calculate_anomaly_score(current_value, baseline_stats)
        
        is_business_material = abs(rel_change_pct) >= threshold_pct
        is_statistically_significant = (z_score is not None and abs(z_score) >= z_threshold)

        # Dual-gate overall classification
        if is_business_material and is_statistically_significant:
            overall = "CRITICAL_ACTIONABLE"
            explanation = (
                f"Movement is actionable and material. The observed delta of {rel_change_pct:+.2f}% exceeds "
                f"the {threshold_pct:.1f}% business contract threshold and is statistically significant (Z = {z_score:+.2f}, p < {p_val:.4f})."
            )
        elif is_business_material and not is_statistically_significant:
            overall = "BUSINESS_WARNING"
            explanation = (
                f"Business materiality threshold breached ({rel_change_pct:+.2f}% vs {threshold_pct:.1f}%), "
                f"but statistical variation is within normal baseline noise (Z = {z_score:+.2f})."
            )
        elif not is_business_material and is_statistically_significant:
            overall = "STATISTICAL_NOISE"
            explanation = (
                f"Statistical anomaly detected (Z = {z_score:+.2f}), but the relative business impact of "
                f"{rel_change_pct:+.2f}% is below the {threshold_pct:.1f}% materiality threshold."
            )
        else:
            overall = "NORMAL"
            explanation = (
                f"KPI movement ({rel_change_pct:+.2f}%) is within expected operational tolerance and baseline variance."
            )

        return MaterialityAssessment(
            business_materiality="MATERIAL" if is_business_material else "NON_MATERIAL",
            statistical_significance="STATISTICALLY_SIGNIFICANT" if is_statistically_significant else "STATISTICAL_NOISE",
            overall_materiality=overall,
            relative_change_pct=round(rel_change_pct, 2),
            absolute_change=round(abs_change, 2),
            threshold_pct=threshold_pct,
            z_score=round(z_score, 2) if z_score is not None else None,
            p_value_approx=round(p_val, 4) if p_val is not None else None,
            materiality_explanation=explanation
        )

materiality_engine = MaterialityEngine()

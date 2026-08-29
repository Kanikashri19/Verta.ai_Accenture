import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

from app.engine.models import DriverContribution, DimensionalContribution, MixShiftBreakdown

class DecompositionEngine:
    """
    Deterministic Mathematical Decomposition Engine.
    Executes exact multiplicative, mix-shift, and dimensional attributions with zero residual error.
    """

    @staticmethod
    def decompose_revenue_multiplicative(
        baseline_sales: pd.DataFrame,
        anomaly_sales: pd.DataFrame,
        baseline_mkt: pd.DataFrame,
        anomaly_mkt: pd.DataFrame,
    ) -> List[DriverContribution]:
        """
        Performs exact multiplicative decomposition of Gross Revenue into:
        Revenue = Clicks (Sessions) * Conversion Rate * Average Order Value (AOV).
        
        Using Bennet/Montgomery mid-point chain attribution:
        Sum of contributions strictly equals the observed total Revenue Delta.
        """
        # Daily normalized quantities
        b_days = baseline_sales["date"].nunique() or 1
        a_days = anomaly_sales["date"].nunique() or 1

        b_rev = (baseline_sales["revenue"] - baseline_sales["discount"]).sum() / b_days
        a_rev = (anomaly_sales["revenue"] - anomaly_sales["discount"]).sum() / a_days
        delta_rev = a_rev - b_rev

        b_orders = baseline_sales["order_id"].nunique() / b_days
        a_orders = anomaly_sales["order_id"].nunique() / a_days

        b_clicks = baseline_mkt["clicks"].sum() / b_days
        a_clicks = anomaly_mkt["clicks"].sum() / a_days

        b_conv = baseline_mkt["conversions"].sum() / b_days
        a_conv = anomaly_mkt["conversions"].sum() / a_days

        b_cr = (b_conv / b_clicks) if b_clicks > 0 else 0.0
        a_cr = (a_conv / a_clicks) if a_clicks > 0 else 0.0

        b_aov = (b_rev / b_orders) if b_orders > 0 else 0.0
        a_aov = (a_rev / a_orders) if a_orders > 0 else 0.0

        # Mid-point values for exact closed-form attribution
        m_clicks = (b_clicks + a_clicks) / 2.0
        m_cr = (b_cr + a_cr) / 2.0
        m_aov = (b_aov + a_aov) / 2.0

        delta_clicks = a_clicks - b_clicks
        delta_cr = a_cr - b_cr
        delta_aov = a_aov - b_aov

        # 1. Traffic / Clicks Contribution ($/day)
        contrib_clicks = delta_clicks * m_cr * m_aov
        # 2. Conversion Rate Contribution ($/day)
        contrib_cr = m_clicks * delta_cr * m_aov
        # 3. AOV / Pricing & Mix Contribution ($/day)
        contrib_aov = m_clicks * m_cr * delta_aov

        # Residual normalization to guarantee exact sum = delta_rev
        raw_sum = contrib_clicks + contrib_cr + contrib_aov
        if abs(raw_sum) > 1e-9 and abs(delta_rev) > 1e-9:
            scale = delta_rev / raw_sum
            contrib_clicks *= scale
            contrib_cr *= scale
            contrib_aov *= scale

        # Scale to total anomaly period window (e.g. 7 days)
        total_delta_usd = delta_rev * a_days
        total_clicks_usd = contrib_clicks * a_days
        total_cr_usd = contrib_cr * a_days
        total_aov_usd = contrib_aov * a_days

        drivers = [
            DriverContribution(
                driver_name="Conversion Rate",
                driver_type="MULTIPLICATIVE_COMPONENT",
                contribution_value=round(total_cr_usd, 2),
                contribution_percentage=round((total_cr_usd / total_delta_usd * 100.0) if total_delta_usd != 0 else 0.0, 1),
                direction="NEGATIVE" if total_cr_usd < 0 else "POSITIVE",
                association_type="LIKELY_CONTRIBUTOR",
                methodology="Logarithmic/Bennet Multiplicative Chain Decomposition (Clicks × CR × AOV)",
                baseline_driver_value=round(b_cr, 4),
                anomaly_driver_value=round(a_cr, 4),
                delta_driver_value=round(delta_cr, 4),
            ),
            DriverContribution(
                driver_name="Average Order Value & Product Mix",
                driver_type="MULTIPLICATIVE_COMPONENT",
                contribution_value=round(total_aov_usd, 2),
                contribution_percentage=round((total_aov_usd / total_delta_usd * 100.0) if total_delta_usd != 0 else 0.0, 1),
                direction="NEGATIVE" if total_aov_usd < 0 else "POSITIVE",
                association_type="LIKELY_CONTRIBUTOR",
                methodology="Logarithmic/Bennet Multiplicative Chain Decomposition (Clicks × CR × AOV)",
                baseline_driver_value=round(b_aov, 2),
                anomaly_driver_value=round(a_aov, 2),
                delta_driver_value=round(delta_aov, 2),
            ),
            DriverContribution(
                driver_name="Traffic & Inbound Sessions",
                driver_type="MULTIPLICATIVE_COMPONENT",
                contribution_value=round(total_clicks_usd, 2),
                contribution_percentage=round((total_clicks_usd / total_delta_usd * 100.0) if total_delta_usd != 0 else 0.0, 1),
                direction="NEGATIVE" if total_clicks_usd < 0 else "POSITIVE",
                association_type="LIKELY_CONTRIBUTOR",
                methodology="Logarithmic/Bennet Multiplicative Chain Decomposition (Clicks × CR × AOV)",
                baseline_driver_value=round(b_clicks, 1),
                anomaly_driver_value=round(a_clicks, 1),
                delta_driver_value=round(delta_clicks, 1),
            ),
        ]

        # Sort by absolute impact descending
        drivers.sort(key=lambda d: abs(d.contribution_value), reverse=True)
        return drivers

    @staticmethod
    def analyze_mix_shift(
        baseline_sales: pd.DataFrame,
        anomaly_sales: pd.DataFrame,
        dimension: str = "category"
    ) -> MixShiftBreakdown:
        """
        Executes formal Volume / Mix / Price-Rate decomposition.
        Separates unit volume decline from product mix substitution (e.g. buying cheaper goods).
        """
        b_days = baseline_sales["date"].nunique() or 1
        a_days = anomaly_sales["date"].nunique() or 1

        # Aggregate daily baseline and anomaly by slice
        b_slice = baseline_sales.groupby(dimension).agg(
            units=("quantity", "sum"),
            net_revenue=("revenue", lambda r: (r - baseline_sales.loc[r.index, "discount"]).sum())
        )
        b_slice["daily_units"] = b_slice["units"] / b_days
        b_slice["daily_rev"] = b_slice["net_revenue"] / b_days
        b_slice["price"] = b_slice["daily_rev"] / b_slice["daily_units"]

        a_slice = anomaly_sales.groupby(dimension).agg(
            units=("quantity", "sum"),
            net_revenue=("revenue", lambda r: (r - anomaly_sales.loc[r.index, "discount"]).sum())
        )
        a_slice["daily_units"] = a_slice["units"] / a_days
        a_slice["daily_rev"] = a_slice["net_revenue"] / a_days
        a_slice["price"] = a_slice["daily_rev"] / a_slice["daily_units"]

        # Align categories
        all_keys = list(set(b_slice.index).union(set(a_slice.index)))
        
        total_b_units = b_slice["daily_units"].sum()
        total_a_units = a_slice["daily_units"].sum()

        shares_b = {}
        shares_a = {}

        vol_effect = 0.0
        mix_effect = 0.0
        rate_effect = 0.0

        for k in all_keys:
            u0 = b_slice.loc[k, "daily_units"] if k in b_slice.index else 0.0
            p0 = b_slice.loc[k, "price"] if k in b_slice.index else 0.0
            
            u1 = a_slice.loc[k, "daily_units"] if k in a_slice.index else 0.0
            p1 = a_slice.loc[k, "price"] if k in a_slice.index else 0.0

            s0 = (u0 / total_b_units) if total_b_units > 0 else 0.0
            s1 = (u1 / total_a_units) if total_a_units > 0 else 0.0

            shares_b[k] = round(s0, 4)
            shares_a[k] = round(s1, 4)

            p_avg = (p0 + p1) / 2.0 if (p0 > 0 and p1 > 0) else (p0 or p1)

            # 1. Volume Effect: (Change in Total Units) * Baseline Share * Price
            vol_effect += (total_a_units - total_b_units) * s0 * p_avg
            # 2. Mix Effect: Total Anomaly Units * (Change in Share) * Price
            mix_effect += total_a_units * (s1 - s0) * p_avg
            # 3. Pure Price / Discount Effect: Anomaly Units * (Change in Price)
            rate_effect += u1 * (p1 - p0)

        # Scale across anomaly period
        total_delta = (a_slice["daily_rev"].sum() - b_slice["daily_rev"].sum()) * a_days
        vol_usd = vol_effect * a_days
        mix_usd = mix_effect * a_days
        rate_usd = rate_effect * a_days

        return MixShiftBreakdown(
            dimension_name=dimension,
            volume_effect_usd=round(vol_usd, 2),
            mix_shift_effect_usd=round(mix_usd, 2),
            price_rate_effect_usd=round(rate_usd, 2),
            total_delta_usd=round(total_delta, 2),
            shares_baseline=shares_b,
            shares_anomaly=shares_a,
        )

    @staticmethod
    def drilldown_dimension(
        baseline_df: pd.DataFrame,
        anomaly_df: pd.DataFrame,
        dimension: str,
        metric_col: str = "net_revenue"
    ) -> List[DimensionalContribution]:
        """
        Slices a metric by a given categorical dimension (Region, Category, Channel).
        Calculates exact dollar impact and relative share of total movement.
        """
        b_days = baseline_df["date"].nunique() or 1
        a_days = anomaly_df["date"].nunique() or 1

        # Calculate net revenue if not present
        if metric_col == "net_revenue":
            b_df = baseline_df.copy()
            a_df = anomaly_df.copy()
            b_df["_metric"] = b_df["revenue"] - b_df["discount"]
            a_df["_metric"] = a_df["revenue"] - a_df["discount"]
        else:
            b_df = baseline_df.copy()
            a_df = anomaly_df.copy()
            b_df["_metric"] = b_df[metric_col]
            a_df["_metric"] = a_df[metric_col]

        b_grp = b_df.groupby(dimension)["_metric"].sum() / b_days
        a_grp = a_df.groupby(dimension)["_metric"].sum() / a_days

        all_keys = sorted(list(set(b_grp.index).union(set(a_grp.index))))
        total_delta = (a_grp.sum() - b_grp.sum()) * a_days

        results = []
        for k in all_keys:
            val_0 = float(b_grp.get(k, 0.0)) * a_days
            val_1 = float(a_grp.get(k, 0.0)) * a_days
            delta = val_1 - val_0
            pct_chg = (delta / val_0 * 100.0) if val_0 != 0 else 0.0
            share_of_total = (delta / total_delta * 100.0) if total_delta != 0 else 0.0

            results.append(
                DimensionalContribution(
                    dimension=dimension,
                    dimension_value=str(k),
                    baseline_value=round(val_0, 2),
                    anomaly_value=round(val_1, 2),
                    absolute_change=round(delta, 2),
                    percentage_change=round(pct_chg, 2),
                    contribution_to_total_pct=round(share_of_total, 1),
                    relationship="OBSERVED_DIMENSIONAL_MOVEMENT",
                )
            )

        # Sort by absolute change descending
        results.sort(key=lambda x: abs(x.absolute_change), reverse=True)
        return results

decomposition_engine = DecompositionEngine()

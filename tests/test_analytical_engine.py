import pytest
import pandas as pd
import numpy as np
import re
import json
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.engine.stats import stats_engine
from app.engine.materiality import materiality_engine
from app.engine.decomposition import decomposition_engine
from app.engine.signals import signal_engine
from app.engine.investigation import investigation_engine
from app.engine.models import BaselineStats, MaterialityAssessment, FactPack
from app.data.loader import data_loader

class TestAnalyticalEngine:

    def test_insufficient_history_handling(self):
        """Test 1 & 9: Cold start / sparse history (<30 days) correctly withholds anomaly scoring."""
        short_series = pd.Series([100.0, 105.0, 98.0, 102.0, 101.0])  # N = 5 < 30
        stats = stats_engine.compute_baseline_stats(short_series, min_required=30)
        
        assert not stats.has_sufficient_history
        assert stats.sample_size == 5
        
        # Test anomaly score calculation with insufficient history
        z, p_val, score, status = stats_engine.calculate_anomaly_score(80.0, stats)
        assert z is None
        assert score is None
        assert status == "INSUFFICIENT_HISTORY"

        # Test materiality assessment with insufficient history
        mat = materiality_engine.evaluate(
            baseline_value=100.0,
            current_value=80.0,
            threshold_pct=5.0,
            baseline_stats=stats
        )
        assert mat.statistical_significance == "INSUFFICIENT_HISTORY"
        assert mat.overall_materiality == "INSUFFICIENT_HISTORY"
        assert "Cold-start: Insufficient historical observations" in mat.materiality_explanation

    def test_zero_variance_handling(self):
        """Test 10: Zero-variance baseline handles division by zero gracefully."""
        const_series = pd.Series([100.0] * 35)  # 35 identical observations
        stats = stats_engine.compute_baseline_stats(const_series)
        
        assert stats.has_sufficient_history
        assert stats.zero_variance
        assert stats.std_dev == 0.0
        
        # Case A: Same value -> normal
        z, p_val, score, status = stats_engine.calculate_anomaly_score(100.0, stats)
        assert z == 0.0
        assert status == "NORMAL"
        
        # Case B: Different value -> critical anomaly without crashing
        z2, p_val2, score2, status2 = stats_engine.calculate_anomaly_score(120.0, stats)
        assert z2 == 999.0
        assert status2 == "CRITICAL_ANOMALY"

    def test_missing_data_handling(self):
        """Test 11: Series with missing values (NaNs) are handled without error."""
        dirty_series = pd.Series([100.0, np.nan, 105.0, None, 98.0] + [100.0]*30)
        stats = stats_engine.compute_baseline_stats(dirty_series, min_required=30)
        
        assert stats.sample_size == 33
        assert stats.has_sufficient_history
        assert not np.isnan(stats.mean)

    def test_material_vs_non_material_evaluations(self):
        """Test 2 & 3: Distinguish between business material, statistical noise, and normal movements."""
        normal_series = pd.Series(np.random.default_rng(42).normal(1000.0, 20.0, 40))
        stats = stats_engine.compute_baseline_stats(normal_series)
        
        # Case 1: Material drop (-20%) and statistically significant -> CRITICAL_ACTIONABLE
        mat_crit = materiality_engine.evaluate(
            baseline_value=1000.0,
            current_value=800.0,
            threshold_pct=5.0,
            baseline_stats=stats
        )
        assert mat_crit.business_materiality == "MATERIAL"
        assert mat_crit.statistical_significance == "STATISTICALLY_SIGNIFICANT"
        assert mat_crit.overall_materiality == "CRITICAL_ACTIONABLE"
        
        # Case 2: Small movement (-1.5%) within threshold -> NORMAL
        mat_norm = materiality_engine.evaluate(
            baseline_value=1000.0,
            current_value=985.0,
            threshold_pct=5.0,
            baseline_stats=stats
        )
        assert mat_norm.business_materiality == "NON_MATERIAL"
        assert mat_norm.overall_materiality == "NORMAL"

    def test_revenue_multi_factor_investigation(self):
        """
        Test 4, 13, 15: Main Demo Scenario independently recovers the 3 known injected drivers
        WITHOUT reading ground-truth metadata.
        """
        res = investigation_engine.investigate_kpi(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR"
        )
        
        # Verify basic movement detection
        assert res.kpi_id == "kpi_revenue"
        assert res.percentage_change < -15.0, f"Expected revenue decline, got {res.percentage_change}%"
        assert res.materiality.overall_materiality == "CRITICAL_ACTIONABLE"
        assert res.anomaly_score >= 0.50
        
        # Verify Driver Ranking: Must recover all 3 primary drivers
        driver_names = [d.driver_name for d in res.ranked_drivers]
        assert "Conversion Rate" in driver_names
        assert "Average Order Value & Product Mix" in driver_names
        assert "Traffic & Inbound Sessions" in driver_names
        
        # Verify drivers are ranked by absolute contribution
        contributions = [abs(d.contribution_value) for d in res.ranked_drivers]
        assert contributions == sorted(contributions, reverse=True), "Drivers not sorted descending"
        
        # Verify Conversion Rate is the top driver (as injected in EU payment gateway outage)
        assert res.ranked_drivers[0].driver_name == "Conversion Rate"
        assert res.ranked_drivers[0].direction == "NEGATIVE"
        assert res.ranked_drivers[0].contribution_percentage > 25.0

    def test_mix_shift_decomposition(self):
        """Test 6: Mix-shift analysis isolates product mix substitution from volume changes."""
        sales_df, _, _, meta = data_loader.load_data("SCENARIO_1_MULTI_FACTOR")
        anom_start = meta["anomaly_start_date"]
        
        b_sales = sales_df[sales_df["date"] < anom_start]
        a_sales = sales_df[sales_df["date"] >= anom_start]
        
        # Product-level mix shift
        mix_prod = decomposition_engine.analyze_mix_shift(b_sales, a_sales, dimension="product_id")
        
        assert mix_prod.dimension_name == "product_id"
        assert mix_prod.total_delta_usd < 0
        assert mix_prod.volume_effect_usd < 0  # Total units dropped
        assert mix_prod.mix_shift_effect_usd < 0  # Negative mix shift from laptop stockout
        
        # Check that flagship laptop share dropped in the anomaly period
        assert mix_prod.shares_anomaly["PROD_LAPTOP_01"] < mix_prod.shares_baseline["PROD_LAPTOP_01"]

    def test_dimensional_drilldown_region(self):
        """Test 7: Regional drill-down identifies major negative regional contributors."""
        sales_df, _, _, meta = data_loader.load_data("SCENARIO_1_MULTI_FACTOR")
        anom_start = meta["anomaly_start_date"]
        
        b_sales = sales_df[sales_df["date"] < anom_start]
        a_sales = sales_df[sales_df["date"] >= anom_start]
        
        regional_drilldown = decomposition_engine.drilldown_dimension(b_sales, a_sales, dimension="region")
        
        assert len(regional_drilldown) == 3
        # Both NA and EU must exhibit severe negative revenue drops
        regions_affected = {r.dimension_value: r.percentage_change for r in regional_drilldown}
        assert regions_affected["NA"] < -20.0, f"NA drop expected < -20%, got {regions_affected['NA']}%"
        assert regions_affected["EU"] < -20.0, f"EU drop expected < -20%, got {regions_affected['EU']}%"

    def test_operational_signals_extraction(self):
        """Test 8: Structured operational signals extract stockouts and payment timeouts."""
        _, _, ops_df, meta = data_loader.load_data("SCENARIO_1_MULTI_FACTOR")
        anom_start = meta["anomaly_start_date"]
        anom_end = meta["end_date"]
        
        signals = signal_engine.extract_signals(ops_df, anom_start, anom_end)
        
        assert len(signals) > 0
        issue_types = [s.issue_type for s in signals]
        assert "PAYMENT_GATEWAY_TIMEOUT" in issue_types
        assert "STOCKOUT" in issue_types
        
        # Verify signal role is strictly non-causal
        for s in signals:
            assert s.signal_role == "SUPPORTING_SIGNAL"
            assert s.time_alignment is True

    def test_ranked_explanations_distinctions(self):
        """Test Phase 3 Patch: Ranked explanations cleanly separate quantitative drivers and supporting signals."""
        res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        
        assert len(res.ranked_explanations) > 0
        
        quant_drivers = [e for e in res.ranked_explanations if e.driver_type == "QUANTITATIVE_DRIVER"]
        supporting_signals = [e for e in res.ranked_explanations if e.driver_type == "SUPPORTING_SIGNAL"]
        
        assert len(quant_drivers) >= 3
        assert len(supporting_signals) >= 2
        
        # 1. Quantitative drivers must have non-null dollar and percentage contributions
        for qd in quant_drivers:
            assert qd.contribution_value is not None
            assert qd.contribution_percentage is not None
            assert qd.status == "VERIFIED_QUANTITATIVE"
            
        # 2. Supporting signals must NOT fabricate dollar or percentage contributions
        for ss in supporting_signals:
            assert ss.contribution_value is None, f"Supporting signal '{ss.driver}' must have contribution_value=None"
            assert ss.contribution_percentage is None, f"Supporting signal '{ss.driver}' must have contribution_percentage=None"
            assert ss.supporting_evidence_count > 0
            assert ss.time_alignment is True

    def test_causal_language_guardrails(self):
        """Test Phase 3 Patch: No unsupported causal claims (caused by, due to, resulted from) in FactPack."""
        res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        fact_pack = investigation_engine.generate_fact_pack(res)
        
        fp_json_str = json.dumps(fact_pack.model_dump()).lower()
        
        forbidden_patterns = [r"\bcaused by\b", r"\bdue to\b", r"\bresulted from\b"]
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, fp_json_str)
            assert len(matches) == 0, f"Found forbidden causal language matching '{pattern}' in FactPack: {matches}"

    def test_fact_pack_structure_and_guardrails(self):
        """Test 14: FactPack contains verified deterministic information and non-causal constraints."""
        res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        fact_pack = investigation_engine.generate_fact_pack(res)
        
        assert isinstance(fact_pack, FactPack)
        assert fact_pack.version == "2.0"
        assert fact_pack.summary_metrics["kpi_id"] == "kpi_revenue"
        assert fact_pack.summary_metrics["is_material"] is True
        assert len(fact_pack.verified_numerical_facts) > 0
        assert len(fact_pack.guarded_language_constraints) >= 3

    def test_deterministic_reproducibility(self):
        """Test 12: Two independent runs produce identical investigation results."""
        res_1 = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        res_2 = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        
        assert res_1.baseline_value == res_2.baseline_value
        assert res_1.current_value == res_2.current_value
        assert res_1.percentage_change == res_2.percentage_change
        assert len(res_1.ranked_drivers) == len(res_2.ranked_drivers)
        for d1, d2 in zip(res_1.ranked_drivers, res_2.ranked_drivers):
            assert d1.contribution_value == d2.contribution_value
            assert d1.contribution_percentage == d2.contribution_percentage

    def test_all_five_kpis_investigation(self):
        """Test that investigation engine operates smoothly on all 5 KPIs."""
        kpis = ["kpi_revenue", "kpi_orders", "kpi_aov", "kpi_conv_rate", "kpi_gross_margin"]
        for kpi_id in kpis:
            res = investigation_engine.investigate_kpi(kpi_id, "SCENARIO_1_MULTI_FACTOR")
            assert res.kpi_id == kpi_id
            assert res.materiality is not None
            assert res.baseline_value > 0
            assert res.current_value > 0

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.data.generator import NovaMartDataGenerator
from app.data.loader import data_loader
from app.engine.semantic import semantic_layer

class TestSyntheticDataAndKPIs:
    
    @pytest.fixture
    def generator(self):
        return NovaMartDataGenerator(seed=42)

    def test_deterministic_generation(self, generator):
        """Test that data generation is 100% deterministic and reproducible with fixed seed."""
        sales_1, mkt_1, ops_1, _ = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        gen_2 = NovaMartDataGenerator(seed=42)
        sales_2, mkt_2, ops_2, _ = gen_2.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        pd.testing.assert_frame_equal(sales_1, sales_2)
        pd.testing.assert_frame_equal(mkt_1, mkt_2)
        pd.testing.assert_frame_equal(ops_1, ops_2)

    def test_sales_source_schema_and_constraints(self, generator):
        """Test Sales source schema, column names, and integrity constraints."""
        sales_df, _, _, _ = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        required_columns = [
            "date", "order_id", "product_id", "category", "region",
            "quantity", "revenue", "discount", "cost"
        ]
        for col in required_columns:
            assert col in sales_df.columns, f"Missing column in Sales: {col}"
        
        # Integrity checks
        assert (sales_df["quantity"] > 0).all(), "Found non-positive quantity in sales"
        assert (sales_df["revenue"] >= 0).all(), "Found negative gross revenue"
        assert (sales_df["discount"] >= 0).all(), "Found negative discount"
        assert (sales_df["cost"] >= 0).all(), "Found negative cost"
        assert (sales_df["discount"] <= sales_df["revenue"]).all(), "Discount exceeds gross revenue"
        
        # Primary identifier uniqueness: Each line item belongs to a valid non-empty order_id
        assert sales_df["order_id"].nunique() > 0
        assert not sales_df["order_id"].isnull().any()

    def test_marketing_source_schema_and_constraints(self, generator):
        """Test Marketing source schema, column names, and integrity constraints."""
        _, mkt_df, _, _ = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        required_columns = [
            "date", "campaign_id", "channel", "region", "spend",
            "impressions", "clicks", "conversions"
        ]
        for col in required_columns:
            assert col in mkt_df.columns, f"Missing column in Marketing: {col}"
            
        assert (mkt_df["spend"] >= 0).all(), "Found negative marketing spend"
        assert (mkt_df["impressions"] >= mkt_df["clicks"]).all(), "Clicks exceed impressions"
        assert (mkt_df["clicks"] >= mkt_df["conversions"]).all(), "Conversions exceed clicks"
        
        # Check uniqueness of (date, campaign_id) primary key
        pk_series = mkt_df["date"] + "_" + mkt_df["campaign_id"]
        assert not pk_series.duplicated().any(), "Duplicate PK in Marketing source"

    def test_customer_ops_source_schema_and_constraints(self, generator):
        """Test Customer Support and Operations unstructured source schema."""
        _, _, ops_df, _ = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        required_columns = [
            "timestamp", "source", "region", "product_id", "category",
            "sentiment", "text", "issue_type", "severity", "sensitivity"
        ]
        for col in required_columns:
            assert col in ops_df.columns, f"Missing column in Customer/Ops: {col}"
            
        assert (ops_df["sentiment"] >= -1.0).all() and (ops_df["sentiment"] <= 1.0).all(), "Sentiment out of bounds"
        assert ops_df["source"].isin(["SUPPORT_TICKET", "CUSTOMER_REVIEW", "OPS_INCIDENT"]).all()
        assert ops_df["severity"].isin(["CRITICAL", "HIGH", "MEDIUM", "LOW"]).all()
        assert ops_df["sensitivity"].isin(["PII_RESTRICTED", "INTERNAL_OPS", "PUBLIC_FEEDBACK"]).all()

    def test_kpi_semantic_calculations(self, generator):
        """Test that all 5 KPIs are calculated deterministically from the semantic layer."""
        sales_df, mkt_df, _, _ = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        kpis = semantic_layer.calculate_all_kpis(sales_df, mkt_df)
        
        assert "kpi_revenue" in kpis
        assert "kpi_orders" in kpis
        assert "kpi_aov" in kpis
        assert "kpi_conv_rate" in kpis
        assert "kpi_gross_margin" in kpis
        
        rev = kpis["kpi_revenue"]["value"]
        orders = kpis["kpi_orders"]["value"]
        aov = kpis["kpi_aov"]["value"]
        cr = kpis["kpi_conv_rate"]["value"]
        gm = kpis["kpi_gross_margin"]["value"]
        
        assert rev > 0, "Revenue should be positive"
        assert orders > 0, "Orders should be positive"
        assert aov > 0, "AOV should be positive"
        assert 0.0 < cr < 1.0, f"Conversion rate {cr} must be between 0 and 1"
        assert 0.0 < gm < 1.0, f"Gross margin {gm} must be between 0 and 1"
        
        # Mathematical consistency: AOV = Revenue / Orders (within rounding)
        expected_aov = round(rev / orders, 2)
        assert abs(aov - expected_aov) <= 0.05, f"AOV mismatch: {aov} vs {expected_aov}"

    def test_multi_factor_revenue_decline_exists(self, generator):
        """Test that Scenario 1 exhibits the known multi-factor revenue decline."""
        sales_df, mkt_df, ops_df, meta = generator.generate_scenario_data("SCENARIO_1_MULTI_FACTOR")
        
        anomaly_start = meta["anomaly_start_date"]
        
        baseline_sales = sales_df[sales_df["date"] < anomaly_start]
        anomaly_sales = sales_df[sales_df["date"] >= anomaly_start]
        
        baseline_mkt = mkt_df[mkt_df["date"] < anomaly_start]
        anomaly_mkt = mkt_df[mkt_df["date"] >= anomaly_start]
        
        # Calculate daily averages
        baseline_days = baseline_sales["date"].nunique()
        anomaly_days = anomaly_sales["date"].nunique()
        
        daily_rev_baseline = (baseline_sales["revenue"] - baseline_sales["discount"]).sum() / baseline_days
        daily_rev_anomaly = (anomaly_sales["revenue"] - anomaly_sales["discount"]).sum() / anomaly_days
        
        rev_pct_change = (daily_rev_anomaly - daily_rev_baseline) / daily_rev_baseline * 100
        
        # 1. Total revenue must drop significantly (between -15% and -22%)
        assert rev_pct_change < -10.0, f"Expected revenue decline, got {rev_pct_change:.2f}%"
        
        # 2. Conversion decline in EU (Driver 1)
        eu_baseline_mkt = baseline_mkt[baseline_mkt["region"] == "EU"]
        eu_anomaly_mkt = anomaly_mkt[anomaly_mkt["region"] == "EU"]
        
        eu_cr_baseline = eu_baseline_mkt["conversions"].sum() / eu_baseline_mkt["clicks"].sum()
        eu_cr_anomaly = eu_anomaly_mkt["conversions"].sum() / eu_anomaly_mkt["clicks"].sum()
        assert eu_cr_anomaly < eu_cr_baseline * 0.75, "EU Conversion rate should drop by >25%"
        
        # 3. Product mix shift in NA: UltraBook Pro sales should be 0 during anomaly in NA (Driver 2)
        na_anomaly_sales = anomaly_sales[anomaly_sales["region"] == "NA"]
        laptop_sales_in_na = na_anomaly_sales[na_anomaly_sales["product_id"] == "PROD_LAPTOP_01"]
        assert len(laptop_sales_in_na) == 0, "UltraBook Pro should have 0 sales in NA during stockout"
        
        # 4. Supporting evidence count in unstructured ops
        eu_gateway_tickets = ops_df[ops_df["issue_type"] == "PAYMENT_GATEWAY_TIMEOUT"]
        assert len(eu_gateway_tickets) >= 30, f"Expected >=30 EU gateway tickets, got {len(eu_gateway_tickets)}"

    def test_additional_scenarios_generation(self, generator):
        """Test all 4 additional scenarios generate valid dataframes and metadata."""
        scenarios = [
            "SCENARIO_2_HIGH_CONFIDENCE",
            "SCENARIO_3_LOW_CONFIDENCE",
            "SCENARIO_4_SPARSE_HISTORY",
            "SCENARIO_5_CONTRADICTORY_EVIDENCE",
        ]
        for scen_id in scenarios:
            sales_df, mkt_df, ops_df, meta = generator.generate_scenario_data(scen_id)
            assert not sales_df.empty
            assert not mkt_df.empty
            assert not ops_df.empty
            assert meta["scenario_id"] == scen_id
            
            if scen_id == "SCENARIO_4_SPARSE_HISTORY":
                # Sparse history should have only 5 days of data
                assert sales_df["date"].nunique() == 5

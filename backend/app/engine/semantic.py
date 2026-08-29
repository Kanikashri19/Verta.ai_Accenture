from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from app.core.config import config

class KPIAccessRestriction(BaseModel):
    roles: List[str]
    sensitivity: str

class KPIMaterialityThreshold(BaseModel):
    relative_delta_pct: float
    z_score: float
    direction: str = "two_sided"

class KPIDriverHierarchy(BaseModel):
    type: str
    formula: Optional[str] = None
    drivers: Optional[List[Dict[str, Any]]] = None
    dimensional_breakdowns: Optional[List[str]] = None

class KPILineage(BaseModel):
    upstream_sources: List[Dict[str, Any]]
    downstream_kpis: List[str]

class KPIContract(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    unit: str
    aggregation: str
    grain: str
    refresh_cadence: str
    owner: str
    access_restrictions: KPIAccessRestriction
    formula: Dict[str, Any]
    dimensions: List[str]
    materiality_threshold: KPIMaterialityThreshold
    driver_hierarchy: KPIDriverHierarchy
    lineage: KPILineage

class SemanticLayer:
    """
    KPI Semantic Layer.
    Single source of truth for KPI contracts, formulas, lineage, and deterministic calculations.
    """
    def __init__(self, contract_path: Optional[Path] = None):
        self.contract_path = contract_path or config.kpi_contracts_path
        self.contracts: Dict[str, KPIContract] = {}
        self._load_contracts()

    def _load_contracts(self):
        if not self.contract_path.exists():
            raise FileNotFoundError(f"KPI contract file not found at {self.contract_path}")
        with open(self.contract_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        for kpi_id, kpi_data in raw_data.get("kpis", {}).items():
            self.contracts[kpi_id] = KPIContract(**kpi_data)

    def list_kpis(self) -> List[KPIContract]:
        return list(self.contracts.values())

    def get_contract(self, kpi_id: str) -> KPIContract:
        if kpi_id not in self.contracts:
            raise KeyError(f"KPI '{kpi_id}' not found in semantic registry. Valid KPIs: {list(self.contracts.keys())}")
        return self.contracts[kpi_id]

    def calculate_kpi_value(
        self,
        kpi_id: str,
        sales_df: Optional[pd.DataFrame] = None,
        marketing_df: Optional[pd.DataFrame] = None,
    ) -> float:
        """
        Deterministically evaluates a KPI according to its semantic contract definition.
        """
        contract = self.get_contract(kpi_id)

        if kpi_id == "kpi_revenue":
            if sales_df is None or sales_df.empty:
                return 0.0
            # formula: SUM(revenue - discount)
            net_rev = (sales_df["revenue"] - sales_df["discount"]).sum()
            return float(net_rev)

        elif kpi_id == "kpi_orders":
            if sales_df is None or sales_df.empty:
                return 0.0
            # formula: COUNT(DISTINCT order_id)
            orders_count = sales_df["order_id"].nunique()
            return float(orders_count)

        elif kpi_id == "kpi_aov":
            # formula: kpi_revenue / kpi_orders
            rev = self.calculate_kpi_value("kpi_revenue", sales_df, marketing_df)
            orders = self.calculate_kpi_value("kpi_orders", sales_df, marketing_df)
            if orders == 0:
                return 0.0
            return float(rev / orders)

        elif kpi_id == "kpi_conv_rate":
            # formula: SUM(conversions) / SUM(clicks)
            if marketing_df is None or marketing_df.empty:
                return 0.0
            total_clicks = marketing_df["clicks"].sum()
            total_conversions = marketing_df["conversions"].sum()
            if total_clicks == 0:
                return 0.0
            return float(total_conversions / total_clicks)

        elif kpi_id == "kpi_gross_margin":
            # formula: SUM(revenue - discount - cost) / SUM(revenue - discount)
            if sales_df is None or sales_df.empty:
                return 0.0
            net_revenue = (sales_df["revenue"] - sales_df["discount"]).sum()
            total_cost = sales_df["cost"].sum()
            if net_revenue == 0:
                return 0.0
            gross_profit = net_revenue - total_cost
            return float(gross_profit / net_revenue)

        raise NotImplementedError(f"Formula evaluation for '{kpi_id}' is not implemented.")

    def calculate_all_kpis(
        self,
        sales_df: Optional[pd.DataFrame] = None,
        marketing_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates all 5 core KPIs for given dataframe slices with unit and metadata.
        """
        results = {}
        for kpi_id, contract in self.contracts.items():
            val = self.calculate_kpi_value(kpi_id, sales_df, marketing_df)
            results[kpi_id] = {
                "kpi_id": kpi_id,
                "name": contract.name,
                "display_name": contract.display_name,
                "value": round(val, 4 if contract.unit == "percentage" else 2),
                "unit": contract.unit,
                "aggregation": contract.aggregation,
                "owner": contract.owner,
            }
        return results

    def calculate_daily_time_series(
        self,
        kpi_id: str,
        sales_df: pd.DataFrame,
        marketing_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generates daily time-series values for a given KPI across the date range.
        """
        contract = self.get_contract(kpi_id)
        
        if kpi_id in ["kpi_revenue", "kpi_orders", "kpi_aov", "kpi_gross_margin"]:
            if "date" not in sales_df.columns:
                raise ValueError("sales_df missing 'date' column")
            
            dates = sorted(sales_df["date"].unique())
            records = []
            for d in dates:
                d_sales = sales_df[sales_df["date"] == d]
                val = self.calculate_kpi_value(kpi_id, sales_df=d_sales)
                records.append({"date": d, "kpi_id": kpi_id, "value": val})
            return pd.DataFrame(records)

        elif kpi_id == "kpi_conv_rate":
            if "date" not in marketing_df.columns:
                raise ValueError("marketing_df missing 'date' column")
            
            dates = sorted(marketing_df["date"].unique())
            records = []
            for d in dates:
                d_mkt = marketing_df[marketing_df["date"] == d]
                val = self.calculate_kpi_value(kpi_id, marketing_df=d_mkt)
                records.append({"date": d, "kpi_id": kpi_id, "value": val})
            return pd.DataFrame(records)

        raise NotImplementedError(f"Time series calculation for '{kpi_id}' not implemented.")

# Singleton instance
semantic_layer = SemanticLayer()

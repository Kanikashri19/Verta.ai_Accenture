from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml
import pandas as pd

from app.core.config import config
from app.data.generator import data_generator

class DataLoader:
    """
    Data Access & Management Layer for Verta.ai.
    Loads and provides structured/unstructured source tables and metadata.
    """
    def __init__(self):
        self.current_scenario_id = "SCENARIO_1_MULTI_FACTOR"
        self._cache: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]] = {}
        self._source_metadata = self._load_source_metadata()
        self._scenarios_metadata = self._load_scenarios_metadata()

    def _load_source_metadata(self) -> Dict[str, Any]:
        if not config.source_metadata_path.exists():
            return {}
        with open(config.source_metadata_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("sources", {})

    def _load_scenarios_metadata(self) -> Dict[str, Any]:
        if not config.scenarios_path.exists():
            return {}
        with open(config.scenarios_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("scenarios", {})

    def get_source_metadata(self) -> Dict[str, Any]:
        return self._source_metadata

    def list_scenarios(self) -> Dict[str, Any]:
        return self._scenarios_metadata

    def get_scenario_metadata(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        scen_id = scenario_id or self.current_scenario_id
        if scen_id not in self._scenarios_metadata:
            raise KeyError(f"Scenario '{scen_id}' not found. Available: {list(self._scenarios_metadata.keys())}")
        return self._scenarios_metadata[scen_id]

    def get_ground_truth(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves ground-truth cause breakdown (For unit testing and validation ONLY).
        """
        scen_data = self.get_scenario_metadata(scenario_id)
        return scen_data.get("ground_truth", {})

    def set_scenario(self, scenario_id: str):
        if scenario_id not in self._scenarios_metadata:
            raise KeyError(f"Invalid scenario '{scenario_id}'. Available: {list(self._scenarios_metadata.keys())}")
        self.current_scenario_id = scenario_id

    def load_data(self, scenario_id: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        scen_id = scenario_id or self.current_scenario_id
        if scen_id not in self._cache:
            sales_df, marketing_df, ops_df, meta = data_generator.generate_scenario_data(scen_id)
            self._cache[scen_id] = (sales_df, marketing_df, ops_df, meta)
        return self._cache[scen_id]

    def get_sales_data(self, scenario_id: Optional[str] = None) -> pd.DataFrame:
        sales_df, _, _, _ = self.load_data(scenario_id)
        return sales_df

    def get_marketing_data(self, scenario_id: Optional[str] = None) -> pd.DataFrame:
        _, marketing_df, _, _ = self.load_data(scenario_id)
        return marketing_df

    def get_customer_ops_data(self, scenario_id: Optional[str] = None) -> pd.DataFrame:
        _, _, ops_df, _ = self.load_data(scenario_id)
        return ops_df

# Singleton instance
data_loader = DataLoader()

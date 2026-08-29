import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_DIR = BASE_DIR / "app" / "data" / "catalog"
DATA_STORAGE_DIR = BASE_DIR / "data_store"

class AppConfig(BaseModel):
    app_name: str = "Verta.ai"
    version: str = "2.0.0"
    random_seed: int = 42
    baseline_days: int = 90
    anomaly_window_days: int = 7
    min_required_history_days: int = 30
    
    kpi_contracts_path: Path = CATALOG_DIR / "kpi_contracts.yaml"
    source_metadata_path: Path = CATALOG_DIR / "source_metadata.yaml"
    scenarios_path: Path = CATALOG_DIR / "scenarios.yaml"
    storage_dir: Path = DATA_STORAGE_DIR

config = AppConfig()
os.makedirs(config.storage_dir, exist_ok=True)

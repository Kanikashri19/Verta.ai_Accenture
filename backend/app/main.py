from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

from app.core.config import config
from app.engine.semantic import semantic_layer
from app.engine.investigation import investigation_engine
from app.data.loader import data_loader

app = FastAPI(
    title="Verta.ai — KPI Intelligence-to-Action API",
    description="Deterministic quantitative intelligence engine for NovaMart E-Commerce.",
    version=config.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "app": config.app_name,
        "version": config.version,
    }

@app.get("/api/kpi/list")
def list_kpis() -> List[Dict[str, Any]]:
    contracts = semantic_layer.list_kpis()
    return [c.model_dump() for c in contracts]

@app.get("/api/kpi/{kpi_id}/contract")
def get_kpi_contract(kpi_id: str) -> Dict[str, Any]:
    try:
        contract = semantic_layer.get_contract(kpi_id)
        return contract.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/sources/metadata")
def get_source_metadata() -> Dict[str, Any]:
    return data_loader.get_source_metadata()

@app.get("/api/scenarios/list")
def list_scenarios() -> Dict[str, Any]:
    return data_loader.list_scenarios()

@app.get("/api/kpi/summary")
def get_kpi_summary(scenario_id: str = "SCENARIO_1_MULTI_FACTOR") -> Dict[str, Any]:
    try:
        sales_df, marketing_df, _, _ = data_loader.load_data(scenario_id)
        kpi_metrics = semantic_layer.calculate_all_kpis(sales_df, marketing_df)
        return {
            "scenario_id": scenario_id,
            "kpis": kpi_metrics,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/analysis/investigate/{kpi_id}")
def investigate_kpi(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    baseline_start: Optional[str] = None,
    baseline_end: Optional[str] = None,
    anomaly_start: Optional[str] = None,
    anomaly_end: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a deterministic quantitative investigation of a target KPI.
    Returns: InvestigationResult
    """
    try:
        res = investigation_engine.investigate_kpi(
            kpi_id=kpi_id,
            scenario_id=scenario_id,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            anomaly_start=anomaly_start,
            anomaly_end=anomaly_end,
        )
        return res.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/factpack/{kpi_id}")
def get_fact_pack(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
) -> Dict[str, Any]:
    """
    Compiles the verified quantitative FactPack for RAG/LLM synthesis.
    """
    try:
        res = investigation_engine.investigate_kpi(
            kpi_id=kpi_id,
            scenario_id=scenario_id,
        )
        fact_pack = investigation_engine.generate_fact_pack(res)
        return fact_pack.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

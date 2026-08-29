from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

from app.core.config import config
from app.engine.semantic import semantic_layer
from app.engine.investigation import investigation_engine
from app.data.loader import data_loader
from app.evidence.service import evidence_service
from app.governance.service import governance_service
from app.narrative.service import narrative_service
from app.narrative.models import Persona, NarrativeRequest, ActionRecommendationRequest
from app.narrative.action_catalog import action_catalog_engine
from app.narrative.gateway import llm_gateway
from app.narrative.cache import narrative_cache

app = FastAPI(
    title="Verta.ai — KPI Intelligence-to-Action API",
    description="Deterministic quantitative intelligence, Evidence RAG & Governance engine for NovaMart E-Commerce.",
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

# ==========================================
# PHASE 4: EVIDENCE INTELLIGENCE & RAG ROUTES
# ==========================================

@app.get("/api/evidence/status")
def get_evidence_status() -> Dict[str, Any]:
    """
    Returns vector store health, document count, and local embedding details.
    """
    status = evidence_service.get_status()
    return status.model_dump()

@app.post("/api/evidence/ingest")
def ingest_evidence(scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR")) -> Dict[str, Any]:
    """
    Ingests, normalizes, masks PII, and indexes operational evidence documents into ChromaDB.
    """
    try:
        indexed_count = evidence_service.ingest_scenario_evidence(scenario_id)
        return {
            "status": "success",
            "scenario_id": scenario_id,
            "documents_indexed": indexed_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/{kpi_id}")
def get_kpi_evidence(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    role: str = Query("ANALYST", description="RBAC role: EXECUTIVE, ANALYST, OPERATIONS"),
    top_k: int = Query(5, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Retrieves evidence documents matching a KPI anomaly window and its primary drivers.
    """
    try:
        res = investigation_engine.investigate_kpi(kpi_id=kpi_id, scenario_id=scenario_id)
        fact_pack = investigation_engine.generate_fact_pack(res)
        evidence_pack = evidence_service.get_evidence_for_factpack(fact_pack, user_role=role, top_k=top_k)
        return evidence_pack.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/{kpi_id}/{driver}")
def get_driver_evidence(
    kpi_id: str,
    driver: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    region: Optional[str] = None,
    product_id: Optional[str] = None,
    role: str = Query("ANALYST", description="RBAC role: EXECUTIVE, ANALYST, OPERATIONS"),
    top_k: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Retrieves evidence specifically for a single driver (e.g. conversion_rate, availability).
    """
    try:
        evidence_pack = evidence_service.retrieve_evidence(
            kpi_id=kpi_id,
            driver=driver,
            region=region,
            product_id=product_id,
            user_role=role,
            scenario_id=scenario_id,
            top_k=top_k,
        )
        return evidence_pack.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/telemetry/recent")
def get_recent_telemetry() -> List[Dict[str, Any]]:
    """
    Returns recent evidence retrieval telemetry records.
    """
    logs = evidence_service.get_telemetry()
    return [l.model_dump() for l in logs[-20:]]

# ==========================================
# PHASE 5: GOVERNANCE & CONFIDENCE ROUTES
# ==========================================

@app.get("/api/governance/assess/{kpi_id}")
def assess_kpi_governance(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    role: str = Query("ANALYST", description="RBAC role: EXECUTIVE, ANALYST, OPERATIONS"),
    top_k: int = Query(5, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Evaluates calibrated confidence score, circuit breaker status, allowed actions,
    and auditable governance decision for a target KPI.
    """
    try:
        assessment, decision = governance_service.assess_kpi(
            kpi_id=kpi_id,
            scenario_id=scenario_id,
            user_role=role,
            top_k=top_k
        )
        return {
            "assessment": assessment.model_dump(),
            "decision": decision.model_dump()
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/governance/status")
def get_governance_status() -> Dict[str, Any]:
    """
    Returns system governance health, active policy version, formula weights, and thresholds.
    """
    return governance_service.get_governance_status()

@app.get("/api/governance/assessments")
def get_governance_assessments(limit: int = Query(50, ge=1, le=200)) -> List[Dict[str, Any]]:
    """
    Returns auditable history of governance decisions.
    """
    records = governance_service.get_audit_history(limit=limit)
    return [r.model_dump() for r in records]

# ==========================================
# PHASE 6: GOVERNED NARRATIVE & ACTIONS ROUTES
# ==========================================

@app.post("/api/narrative/generate/{kpi_id}")
def generate_narrative(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    persona: str = Query("EXECUTIVE", description="EXECUTIVE or ANALYST"),
    role: str = Query("ANALYST", description="RBAC role: EXECUTIVE, ANALYST, OPERATIONS"),
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> Dict[str, Any]:
    """
    Synthesizes a governed, persona-specific KPI narrative with traceable evidence citations,
    uncertainty caveats, and approved action recommendations. Strictly respects Phase 5 governance.
    """
    try:
        p_enum = Persona(persona.upper())
        resp = narrative_service.assess_and_generate_narrative(
            kpi_id=kpi_id,
            scenario_id=scenario_id,
            persona=p_enum,
            user_role=role,
            force_refresh=force_refresh,
        )
        return resp.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/narrative/status")
def get_narrative_status() -> Dict[str, Any]:
    """
    Returns status of LLM provider abstraction, active model, pricing, and cache size.
    """
    return {
        "status": "active",
        "provider": llm_gateway.provider,
        "model": llm_gateway.model,
        "temperature": llm_gateway.temperature,
        "max_tokens": llm_gateway.max_tokens,
        "timeout_seconds": llm_gateway.timeout_seconds,
        "pricing": {
            "input_cost_per_1k": llm_gateway.input_cost_per_1k,
            "output_cost_per_1k": llm_gateway.output_cost_per_1k,
        },
        "cache_size": narrative_cache.size,
    }

@app.get("/api/narrative/telemetry")
def get_narrative_telemetry() -> List[Dict[str, Any]]:
    """
    Returns telemetry logs for recent narrative synthesis calls (latencies, token counts, costs).
    """
    return narrative_service.get_telemetry()

@app.post("/api/actions/recommend/{kpi_id}")
def recommend_actions(
    kpi_id: str,
    scenario_id: str = Query("SCENARIO_1_MULTI_FACTOR"),
    role: str = Query("ANALYST", description="RBAC role: EXECUTIVE, ANALYST, OPERATIONS"),
) -> List[Dict[str, Any]]:
    """
    Returns approved, actionable recommendations from the deterministic catalog matched to the KPI's verified drivers.
    """
    try:
        factpack = investigation_engine.get_factpack(kpi_id, scenario_id)
        evidence_pack = evidence_service.get_evidence_for_factpack(factpack, user_role=role)
        assessment, _ = governance_service.assess_kpi(kpi_id=kpi_id, scenario_id=scenario_id, user_role=role)
        actions = action_catalog_engine.select_actions(factpack, evidence_pack, assessment)
        return [a.model_dump() for a in actions]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

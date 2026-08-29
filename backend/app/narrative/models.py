from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class Persona(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    ANALYST = "ANALYST"

class GenerationMode(str, Enum):
    LLM_DIRECT = "LLM_DIRECT"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"
    MOCK_LLM = "MOCK_LLM"

class EvidenceCitation(BaseModel):
    """
    Traceable citation connecting a narrative explanation to concrete EvidencePack items.
    """
    statement: str
    evidence_ids: List[str] = Field(default_factory=list)
    driver: Optional[str] = None
    lineage_sources: List[str] = Field(default_factory=list)
    snippet_summary: Optional[str] = None

class RecommendedAction(BaseModel):
    """
    Structured action recommendation following the Accenture paradigm:
    driver -> controllable lever -> action -> expected impact -> owner -> confidence -> monitoring plan -> decision right.
    """
    action_id: str
    driver: str
    controllable_lever: str
    action: str
    owner: str
    expected_impact: str
    confidence_band: str
    monitoring_plan: str
    decision_right: str
    evidence_ids: List[str] = Field(default_factory=list)

class NarrativeTelemetry(BaseModel):
    """
    Observability telemetry recording model latency, token economics, and fallback usage.
    """
    request_id: str
    timestamp: str
    model_provider: str
    model: str
    persona: str
    governance_decision: str
    latency_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    retry_count: int = 0
    fallback_used: bool = False
    cache_hit: bool = False

class NarrativeResponse(BaseModel):
    """
    Complete, validated narrative output synthesized according to Persona and Governance rules.
    """
    request_id: str
    kpi_id: str
    kpi_name: str
    persona: Persona
    generation_mode: str
    headline: str
    summary: str
    kpi_movement: Dict[str, Any]
    key_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_citations: List[EvidenceCitation] = Field(default_factory=list)
    confidence_score: float
    confidence_band: str
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    alternative_hypotheses: List[str] = Field(default_factory=list)
    data_lineage: List[Dict[str, Any]] = Field(default_factory=list)
    governance_decision: str
    clarification_questions: List[str] = Field(default_factory=list)
    conflict_summary: Optional[str] = None
    generated_at: str
    telemetry: Optional[NarrativeTelemetry] = None

class NarrativeRequest(BaseModel):
    """
    API payload for requesting narrative synthesis for a specific KPI and persona.
    """
    kpi_id: str
    scenario_id: str = "SCENARIO_1_MULTI_FACTOR"
    persona: Persona = Persona.EXECUTIVE
    user_role: str = "ANALYST"
    force_refresh: bool = False

class ActionRecommendationRequest(BaseModel):
    """
    API payload for dedicated action recommendation retrieval.
    """
    kpi_id: str
    scenario_id: str = "SCENARIO_1_MULTI_FACTOR"
    user_role: str = "ANALYST"

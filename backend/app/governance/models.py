from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class ConfidenceBand(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ABSTAIN = "ABSTAIN"

class GovernanceDecisionEnum(str, Enum):
    PROCEED = "PROCEED"
    PROCEED_WITH_CAUTION = "PROCEED_WITH_CAUTION"
    ABSTAIN = "ABSTAIN"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"

class ConfidenceWeights(BaseModel):
    """
    Configurable weights for the deterministic confidence formula.
    Weights must sum to 1.00.
    """
    weight_statistical: float = 0.25
    weight_materiality: float = 0.20
    weight_evidence: float = 0.20
    weight_data_quality: float = 0.15
    weight_freshness: float = 0.10
    weight_lineage: float = 0.10

class GovernanceThresholds(BaseModel):
    """
    Configurable decision thresholds for confidence bands.
    """
    high_threshold: float = 80.0
    medium_threshold: float = 60.0
    low_threshold: float = 35.0
    contradiction_ratio_threshold: float = 0.35
    minimum_baseline_days: int = 15

class DriverConfidenceAssessment(BaseModel):
    """
    Confidence assessment evaluated per individual explanatory driver.
    """
    driver_name: str
    driver_type: str
    confidence_score: float  # [0.0 - 100.0]
    confidence_band: ConfidenceBand
    supporting_evidence_count: int
    contradictory_evidence_count: int
    is_statistically_aligned: bool
    justification: str

class ConfidenceAssessment(BaseModel):
    """
    Deterministic confidence assessment evaluated across FactPack, EvidencePack, and Source Metadata.
    """
    assessment_id: str
    kpi_id: str
    scenario_id: str
    overall_confidence: float  # [0.0 - 100.0]
    confidence_band: ConfidenceBand
    decision: GovernanceDecisionEnum
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    driver_assessments: Dict[str, DriverConfidenceAssessment] = Field(default_factory=dict)
    data_quality_score: float
    statistical_confidence: float
    materiality_score: float
    evidence_score: float
    freshness_score: float
    lineage_score: float
    contradiction_penalty: float
    lineage_complete: bool
    clarification_questions: List[str] = Field(default_factory=list)
    evaluated_at: str

class GovernanceDecision(BaseModel):
    """
    Formal, auditable governance decision governing downstream LLM synthesis and actions.
    """
    decision: GovernanceDecisionEnum
    allowed_actions: List[str]
    blocked_actions: List[str]
    reason_codes: List[str]
    policy_version: str = "1.0.0"
    formula_version: str = "1.0.0"
    confidence_threshold: float
    audit_metadata: Dict[str, Any]

class AuditRecord(BaseModel):
    """
    Auditable log of a governance decision for compliance and traceability.
    """
    assessment_id: str
    timestamp: str
    kpi_id: str
    scenario_id: str
    user_role: str
    input_factpack_hash: str
    input_evidencepack_hash: str
    formula_version: str
    policy_version: str
    overall_confidence: float
    confidence_band: str
    decision: str
    reason_codes: List[str]
    clarification_count: int

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class EvidenceDocument(BaseModel):
    """
    Normalized, PII-masked operational evidence document ready for chunking and vector storage.
    """
    evidence_id: str
    document_type: str  # "SUPPORT_TICKET" | "CUSTOMER_REVIEW" | "OPS_INCIDENT"
    timestamp: str  # ISO UTC
    date: str  # YYYY-MM-DD
    source: str
    region: Optional[str] = None
    product_id: Optional[str] = None
    category: str
    issue_type: str
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    sensitivity: str  # "PII_RESTRICTED" | "INTERNAL_OPS" | "PUBLIC_FEEDBACK"
    text: str  # Must be PII-masked
    kpi_ids: List[str]
    driver_tags: List[str]
    scenario_id: str
    lineage: Dict[str, Any]
    access_roles: List[str]  # e.g., ["ANALYST", "OPERATIONS"]

class EvidenceItem(BaseModel):
    """
    Retrieved evidence item formatted for inclusion in an EvidencePack.
    """
    evidence_id: str
    source: str
    timestamp: str
    date: str
    snippet: str
    driver: str
    classification: str  # "SUPPORTING" | "CONTRADICTORY" | "NEUTRAL"
    score: float  # Deterministic score [0.0 - 100.0]
    region: Optional[str] = None
    product_id: Optional[str] = None
    category: Optional[str] = None
    issue_type: str
    severity: str
    sensitivity: str
    temporal_alignment: str  # "EXACT_WINDOW" | "NEAR_WINDOW" | "OUTSIDE_WINDOW"
    lineage: Dict[str, Any]
    access_roles: List[str]

class EvidencePack(BaseModel):
    """
    Structured Evidence Pack returned for a target KPI investigation and its drivers.
    """
    kpi_id: str
    investigation_window: Dict[str, str]  # {"start": "...", "end": "..."}
    user_role: str
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradictory_evidence: List[EvidenceItem] = Field(default_factory=list)
    neutral_evidence: List[EvidenceItem] = Field(default_factory=list)
    evidence_summary: Dict[str, int] = Field(default_factory=dict)
    confidence_components: Dict[str, float] = Field(default_factory=dict)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "SUCCESS"  # "SUCCESS" | "INSUFFICIENT_EVIDENCE"
    explanation: Optional[str] = None

class EvidenceTelemetry(BaseModel):
    """
    Deterministic telemetry metadata recorded per retrieval execution.
    """
    retrieval_id: str
    timestamp: str
    kpi_id: str
    driver: str
    user_role: str
    top_k: int
    candidate_count: int
    returned_count: int
    latency_ms: float
    embedding_model: str
    filters_applied: Dict[str, Any]

class EvidenceStatus(BaseModel):
    """
    Health and status report for the local vector store.
    """
    vector_store_status: str
    document_count: int
    embedding_model: str
    embedding_dimension: int
    indexed_sources: List[str]
    last_indexed_at: Optional[str] = None
    storage_path: str

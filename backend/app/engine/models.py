from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime

class BaselineStats(BaseModel):
    sample_size: int
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    iqr: float
    q1: float
    q3: float
    zero_variance: bool = False
    has_sufficient_history: bool = True

class MaterialityAssessment(BaseModel):
    business_materiality: str  # "MATERIAL" | "NON_MATERIAL"
    statistical_significance: str  # "STATISTICALLY_SIGNIFICANT" | "STATISTICALLY_INSIGNIFICANT" | "INSUFFICIENT_HISTORY"
    overall_materiality: str  # "CRITICAL_ACTIONABLE" | "BUSINESS_WARNING" | "STATISTICAL_NOISE" | "NORMAL" | "INSUFFICIENT_HISTORY"
    relative_change_pct: float
    absolute_change: float
    threshold_pct: float
    z_score: Optional[float] = None
    p_value_approx: Optional[float] = None
    materiality_explanation: str

class DriverContribution(BaseModel):
    driver_name: str
    driver_type: str = "QUANTITATIVE_DRIVER"  # "QUANTITATIVE_DRIVER" | "MULTIPLICATIVE_COMPONENT" | "MIX_SHIFT"
    dimension: Optional[str] = None
    contribution_value: Optional[float] = None
    contribution_percentage: Optional[float] = None
    direction: str = "NEGATIVE"  # "NEGATIVE" | "POSITIVE" | "NEUTRAL"
    association_type: str = "LIKELY_CONTRIBUTOR"  # Explicitly NOT "CAUSAL"
    methodology: str
    baseline_driver_value: float
    anomaly_driver_value: float
    delta_driver_value: float

class MixShiftBreakdown(BaseModel):
    dimension_name: str  # e.g., "category" or "product_id"
    volume_effect_usd: float
    mix_shift_effect_usd: float
    price_rate_effect_usd: float
    total_delta_usd: float
    methodology: str = "Logarithmic/Bennet Volume-Mix-Rate Exact Decomposition"
    shares_baseline: Dict[str, float]
    shares_anomaly: Dict[str, float]
    description: str = ""

class DimensionalContribution(BaseModel):
    dimension: str
    dimension_value: str
    baseline_value: float
    anomaly_value: float
    absolute_change: float
    percentage_change: float
    contribution_to_total_pct: float
    relationship: str = "OBSERVED_DIMENSIONAL_MOVEMENT"

class OperationalSignal(BaseModel):
    signal_id: str
    issue_type: str
    source_type: str
    region: Optional[str] = None
    product_id: Optional[str] = None
    category: Optional[str] = None
    event_count: int
    severity: str
    avg_sentiment: float
    time_alignment: bool = True
    description: str
    signal_role: str = "SUPPORTING_SIGNAL"  # Explicit non-causal label

class RankedExplanation(BaseModel):
    rank: int
    driver: str
    driver_type: str  # "QUANTITATIVE_DRIVER" | "DIMENSIONAL_DRIVER" | "SUPPORTING_SIGNAL"
    direction: str  # "NEGATIVE" | "POSITIVE" | "NEUTRAL"
    contribution_value: Optional[float] = None  # None for supporting signals / non-quantified
    contribution_percentage: Optional[float] = None  # None for supporting signals
    signal_strength: Optional[str] = None  # "HIGH" | "MEDIUM" | "LOW" | None
    supporting_evidence_count: int = 0
    time_alignment: bool = True
    affected_dimensions: Optional[Dict[str, str]] = None
    confidence_component: str
    method: str
    status: str
    description: str

class DataFreshnessReport(BaseModel):
    source_id: str
    last_refresh_timestamp: str
    sla_minutes: int
    staleness_minutes: int
    sla_met: bool
    status: str

class InvestigationResult(BaseModel):
    investigation_id: str
    kpi_id: str
    kpi_name: str
    scenario_id: str
    baseline_period: Dict[str, str]
    anomaly_period: Dict[str, str]
    baseline_value: float
    current_value: float
    absolute_change: float
    percentage_change: float
    unit: str
    materiality: MaterialityAssessment
    anomaly_score: Optional[float] = None
    analytical_method: str
    ranked_drivers: List[DriverContribution] = Field(default_factory=list)
    ranked_explanations: List[RankedExplanation] = Field(default_factory=list)
    mix_shift_analysis: Optional[MixShiftBreakdown] = None
    dimensional_drilldowns: Dict[str, List[DimensionalContribution]] = Field(default_factory=dict)
    supporting_signals: List[OperationalSignal] = Field(default_factory=list)
    data_freshness: Dict[str, DataFreshnessReport] = Field(default_factory=dict)

class FactPack(BaseModel):
    """
    Strict, verified quantitative payload for RAG and LLM consumption.
    Guaranteed to contain zero LLM-hallucinated narrative or unverified math.
    """
    version: str = "2.0"
    created_at: str
    investigation: InvestigationResult
    summary_metrics: Dict[str, Any]
    verified_numerical_facts: List[Dict[str, Any]]
    guarded_language_constraints: List[str]

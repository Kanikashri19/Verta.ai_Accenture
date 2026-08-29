import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from app.engine.investigation import investigation_engine
from app.engine.models import FactPack, InvestigationResult
from app.engine.semantic import semantic_layer
from app.data.loader import data_loader
from app.evidence.service import evidence_service
from app.evidence.models import EvidencePack
from app.governance.models import (
    ConfidenceAssessment, GovernanceDecision, AuditRecord, DriverConfidenceAssessment
)
from app.governance.evaluator import confidence_evaluator
from app.governance.circuit_breaker import governance_circuit_breaker


class GovernanceService:
    """
    High-Level Governance & Confidence Service.
    Orchestrates quantitative FactPacks and qualitative EvidencePacks to produce
    auditable, binding confidence evaluations and action policies.
    Downstream LLM synthesis (Phase 6) may only act within GovernanceDecision.allowed_actions.
    """

    def _compute_payload_hash(self, payload: Any) -> str:
        """Computes deterministic SHA-256 hash for audit traceability."""
        try:
            if hasattr(payload, "model_dump_json"):
                serialized = payload.model_dump_json()
            elif isinstance(payload, dict):
                serialized = json.dumps(payload, sort_keys=True)
            else:
                serialized = str(payload)
            return hashlib.sha256(serialized.encode()).hexdigest()[:16]
        except Exception:
            return "unknown_hash"

    def _sanitize_assessment_for_role(
        self,
        assessment: ConfidenceAssessment,
        user_role: str,
    ) -> ConfidenceAssessment:
        """
        Role-scoped view of the assessment. Does not change scores or the binding decision.
        Never attaches EvidencePack snippets (PII lives in Phase 4 evidence APIs only).
        """
        role = user_role.upper()
        if role == "EXECUTIVE":
            slim: Dict[str, DriverConfidenceAssessment] = {}
            for name, drv in assessment.driver_assessments.items():
                slim[name] = DriverConfidenceAssessment(
                    driver_name=drv.driver_name,
                    driver_type=drv.driver_type,
                    confidence_score=drv.confidence_score,
                    confidence_band=drv.confidence_band,
                    supporting_evidence_count=drv.supporting_evidence_count,
                    contradictory_evidence_count=drv.contradictory_evidence_count,
                    is_statistically_aligned=drv.is_statistically_aligned,
                    justification="Executive summary: driver confidence band and score only.",
                )
            assessment.driver_assessments = slim
            # Do not expose raw evidence identifiers to executives
            assessment.conflicting_evidence_ids = []
        elif role == "OPERATIONS":
            ops_only = {
                k: v for k, v in assessment.driver_assessments.items()
                if "operational" in v.driver_type.lower() or "signal" in v.driver_type.lower()
            }
            if ops_only:
                assessment.driver_assessments = ops_only
        return assessment

    def assess_kpi(
        self,
        kpi_id: str,
        scenario_id: str = "SCENARIO_1_MULTI_FACTOR",
        user_role: str = "ANALYST",
        top_k: int = 10,
    ) -> Tuple[ConfidenceAssessment, GovernanceDecision]:
        """
        Executes end-to-end quantitative investigation, evidence retrieval,
        confidence evaluation, and governance arbitration for a target KPI.
        """
        started = time.perf_counter()

        # 1. Phase 3 Quantitative Investigation
        inv_res = investigation_engine.investigate_kpi(kpi_id, scenario_id=scenario_id)
        fact_pack = investigation_engine.generate_fact_pack(inv_res)
        factpack_hash = self._compute_payload_hash(fact_pack)

        # 2. Phase 4 Evidence Retrieval (RBAC enforced inside retriever)
        evidence_pack = evidence_service.get_evidence_for_factpack(
            fact_pack=fact_pack,
            user_role=user_role,
            top_k=top_k
        )
        evidencepack_hash = self._compute_payload_hash(evidence_pack)

        contract = None
        try:
            contract = semantic_layer.get_contract(kpi_id)
        except KeyError:
            contract = None
        source_metadata = data_loader.get_source_metadata()

        # 3. Phase 5 Confidence Evaluation
        assessment_id = f"CONF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        assessment = confidence_evaluator.assess_confidence(
            investigation=inv_res,
            evidence_pack=evidence_pack,
            assessment_id=assessment_id,
            scenario_id=scenario_id,
            source_metadata=source_metadata,
            kpi_contract=contract,
        )

        latency_ms = (time.perf_counter() - started) * 1000.0

        # 4. Governance Arbitration & Audit
        decision = governance_circuit_breaker.arbitrate(
            assessment=assessment,
            user_role=user_role,
            factpack_hash=factpack_hash,
            evidencepack_hash=evidencepack_hash,
            assessment_latency_ms=latency_ms,
        )

        # 5. RBAC view sanitization (scores/decision unchanged; no evidence snippets leaked)
        assessment = self._sanitize_assessment_for_role(assessment, user_role)

        return assessment, decision

    def assess_factpack_and_evidence(
        self,
        fact_pack: FactPack,
        evidence_pack: Optional[EvidencePack],
        user_role: str = "ANALYST",
    ) -> Tuple[ConfidenceAssessment, GovernanceDecision]:
        """
        Assesses pre-computed FactPack and EvidencePack directly.
        """
        started = time.perf_counter()
        factpack_hash = self._compute_payload_hash(fact_pack)
        evidencepack_hash = self._compute_payload_hash(evidence_pack) if evidence_pack else "none"

        assessment_id = f"CONF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        scenario_id = fact_pack.investigation.scenario_id
        kpi_id = fact_pack.investigation.kpi_id

        contract = None
        try:
            contract = semantic_layer.get_contract(kpi_id)
        except KeyError:
            contract = None

        assessment = confidence_evaluator.assess_confidence(
            investigation=fact_pack.investigation,
            evidence_pack=evidence_pack,
            assessment_id=assessment_id,
            scenario_id=scenario_id,
            source_metadata=data_loader.get_source_metadata(),
            kpi_contract=contract,
        )

        latency_ms = (time.perf_counter() - started) * 1000.0
        decision = governance_circuit_breaker.arbitrate(
            assessment=assessment,
            user_role=user_role,
            factpack_hash=factpack_hash,
            evidencepack_hash=evidencepack_hash,
            assessment_latency_ms=latency_ms,
        )
        assessment = self._sanitize_assessment_for_role(assessment, user_role)
        return assessment, decision

    def get_governance_status(self) -> Dict[str, Any]:
        """Returns runtime governance configuration, thresholds, and health status."""
        latest = governance_circuit_breaker.get_audit_history(limit=5)
        return {
            "status": "OPERATIONAL",
            "policy_version": governance_circuit_breaker.POLICY_VERSION,
            "formula_version": governance_circuit_breaker.FORMULA_VERSION,
            "weights": confidence_evaluator.weights.model_dump(),
            "thresholds": confidence_evaluator.thresholds.model_dump(),
            "total_assessments_logged": len(governance_circuit_breaker.audit_log),
            "latest_assessments": [r.model_dump() for r in latest],
            "llm_override_allowed": False,
        }

    def get_audit_history(self, limit: int = 50) -> List[AuditRecord]:
        """Returns audit trail history."""
        return governance_circuit_breaker.get_audit_history(limit=limit)


governance_service = GovernanceService()

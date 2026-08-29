import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from app.engine.investigation import investigation_engine
from app.engine.models import FactPack, InvestigationResult
from app.evidence.service import evidence_service
from app.evidence.models import EvidencePack
from app.governance.models import (
    ConfidenceAssessment, GovernanceDecision, AuditRecord
)
from app.governance.evaluator import confidence_evaluator
from app.governance.circuit_breaker import governance_circuit_breaker

class GovernanceService:
    """
    High-Level Governance & Confidence Service.
    Orchestrates quantitative FactPacks and qualitative EvidencePacks to produce
    auditable, binding confidence evaluations and action policies.
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
        # 1. Phase 3 Quantitative Investigation
        inv_res = investigation_engine.investigate_kpi(kpi_id, scenario_id=scenario_id)
        fact_pack = investigation_engine.generate_fact_pack(inv_res)
        factpack_hash = self._compute_payload_hash(fact_pack)

        # 2. Phase 4 Evidence Retrieval
        evidence_pack = evidence_service.get_evidence_for_factpack(
            fact_pack=fact_pack,
            user_role=user_role,
            top_k=top_k
        )
        evidencepack_hash = self._compute_payload_hash(evidence_pack)

        # 3. Phase 5 Confidence Evaluation
        assessment_id = f"CONF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        assessment = confidence_evaluator.assess_confidence(
            investigation=inv_res,
            evidence_pack=evidence_pack,
            assessment_id=assessment_id,
            scenario_id=scenario_id
        )

        # 4. Governance Arbitration & Audit
        decision = governance_circuit_breaker.arbitrate(
            assessment=assessment,
            user_role=user_role,
            factpack_hash=factpack_hash,
            evidencepack_hash=evidencepack_hash
        )

        # 5. RBAC Sanitization on response
        if user_role.upper() == "EXECUTIVE":
            # Executive view: omit granular driver debug internals
            sanitized_drivers = {
                k: v for k, v in assessment.driver_assessments.items()
            }
            assessment.driver_assessments = sanitized_drivers

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
        factpack_hash = self._compute_payload_hash(fact_pack)
        evidencepack_hash = self._compute_payload_hash(evidence_pack) if evidence_pack else "none"

        assessment_id = f"CONF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        scenario_id = fact_pack.investigation.scenario_id

        assessment = confidence_evaluator.assess_confidence(
            investigation=fact_pack.investigation,
            evidence_pack=evidence_pack,
            assessment_id=assessment_id,
            scenario_id=scenario_id
        )

        decision = governance_circuit_breaker.arbitrate(
            assessment=assessment,
            user_role=user_role,
            factpack_hash=factpack_hash,
            evidencepack_hash=evidencepack_hash
        )

        return assessment, decision

    def get_governance_status(self) -> Dict[str, Any]:
        """Returns runtime governance configuration, thresholds, and health status."""
        return {
            "status": "OPERATIONAL",
            "policy_version": governance_circuit_breaker.POLICY_VERSION,
            "formula_version": governance_circuit_breaker.FORMULA_VERSION,
            "weights": confidence_evaluator.weights.model_dump(),
            "thresholds": confidence_evaluator.thresholds.model_dump(),
            "total_assessments_logged": len(governance_circuit_breaker.audit_log),
        }

    def get_audit_history(self, limit: int = 50) -> List[AuditRecord]:
        """Returns audit trail history."""
        return governance_circuit_breaker.get_audit_history(limit=limit)

governance_service = GovernanceService()

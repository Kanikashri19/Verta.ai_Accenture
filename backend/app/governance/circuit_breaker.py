from typing import Dict, List, Any, Optional
import hashlib
from datetime import datetime, timezone

from app.governance.models import (
    ConfidenceAssessment, GovernanceDecision, GovernanceDecisionEnum, AuditRecord
)

class GovernanceCircuitBreaker:
    """
    Binding Governance Arbiter & Circuit Breaker.
    Determines permitted and blocked downstream actions for narrative synthesis,
    executive briefings, and automated recommendations. Future LLM personas
    cannot bypass or override these deterministic constraints.
    """

    POLICY_VERSION = "1.0.0"
    FORMULA_VERSION = "1.0.0"

    # Action permission matrices
    PERMISSIONS = {
        GovernanceDecisionEnum.PROCEED: {
            "allowed": [
                "GENERATE_EXECUTIVE_BRIEF",
                "GENERATE_ANALYST_DEEPDIVE",
                "SYNTHESIZE_EXPLANATION",
                "RECOMMEND_ACTION",
                "DRILL_DOWN_DIMENSIONS",
                "AUTOMATE_ALERTING"
            ],
            "blocked": []
        },
        GovernanceDecisionEnum.PROCEED_WITH_CAUTION: {
            "allowed": [
                "GENERATE_CAVEATED_ANALYST_BRIEF",
                "SYNTHESIZE_HYPOTHESIS",
                "DRILL_DOWN_DIMENSIONS",
                "REQUEST_SUPPLEMENTAL_VERIFICATION"
            ],
            "blocked": [
                "RECOMMEND_HIGH_IMPACT_ACTION",
                "AUTOMATE_EXECUTION",
                "GENERATE_UNCAVEATED_EXECUTIVE_CLAIM"
            ]
        },
        GovernanceDecisionEnum.REQUEST_CLARIFICATION: {
            "allowed": [
                "GENERATE_CLARIFICATION_PROMPT",
                "REQUEST_OPERATIONAL_INVESTIGATION",
                "REQUEST_ADDITIONAL_DATA",
                "DISPLAY_DIAGNOSTIC_DRILLDOWN"
            ],
            "blocked": [
                "GENERATE_EXECUTIVE_CLAIM",
                "RECOMMEND_ACTION",
                "SYNTHESIZE_EXPLANATION",
                "AUTOMATE_EXECUTION"
            ]
        },
        GovernanceDecisionEnum.ABSTAIN: {
            "allowed": [
                "GENERATE_ABSTENTION_NOTICE",
                "FLAG_DATA_QUALITY_ALERT",
                "REQUEST_MANUAL_REVIEW",
                "DISPLAY_RAW_METRICS"
            ],
            "blocked": [
                "GENERATE_EXECUTIVE_CLAIM",
                "GENERATE_EXECUTIVE_BRIEF",
                "RECOMMEND_ACTION",
                "SYNTHESIZE_EXPLANATION",
                "AUTOMATE_EXECUTION"
            ]
        }
    }

    def __init__(self):
        self.audit_log: List[AuditRecord] = []

    def arbitrate(
        self,
        assessment: ConfidenceAssessment,
        user_role: str = "ANALYST",
        factpack_hash: str = "",
        evidencepack_hash: str = ""
    ) -> GovernanceDecision:
        """
        Arbitrates the assessment into a binding GovernanceDecision and records an audit log.
        """
        decision = assessment.decision
        perms = self.PERMISSIONS.get(decision, self.PERMISSIONS[GovernanceDecisionEnum.ABSTAIN])
        
        # Derive structured reason codes
        reason_codes = []
        if assessment.contradiction_penalty >= 30.0:
            reason_codes.append("CONTRADICTORY_EVIDENCE")
        if "sparse" in assessment.scenario_id.lower() or assessment.statistical_confidence <= 30.0:
            reason_codes.append("SPARSE_HISTORY")
        if assessment.evidence_score == 0.0:
            reason_codes.append("INSUFFICIENT_EVIDENCE")
        if assessment.freshness_score < 80.0:
            reason_codes.append("STALE_DATA")
        if assessment.overall_confidence >= 80.0:
            reason_codes.append("HIGH_CONFIDENCE_MULTI_FACTOR_CORROBORATION")
        elif assessment.overall_confidence >= 60.0:
            reason_codes.append("MODERATE_CONFIDENCE_CAVEATED")

        if not reason_codes:
            reason_codes.append("STANDARD_EVALUATION")

        audit_meta = {
            "assessment_id": assessment.assessment_id,
            "evaluated_at": assessment.evaluated_at,
            "overall_confidence": assessment.overall_confidence,
            "confidence_band": assessment.confidence_band.value,
            "user_role": user_role,
            "factpack_hash": factpack_hash,
            "evidencepack_hash": evidencepack_hash,
            "warnings_count": len(assessment.warnings),
            "clarifications_count": len(assessment.clarification_questions),
        }

        gov_decision = GovernanceDecision(
            decision=decision,
            allowed_actions=perms["allowed"],
            blocked_actions=perms["blocked"],
            reason_codes=reason_codes,
            policy_version=self.POLICY_VERSION,
            formula_version=self.FORMULA_VERSION,
            confidence_threshold=assessment.overall_confidence,
            audit_metadata=audit_meta
        )

        # Log audit record
        audit_record = AuditRecord(
            assessment_id=assessment.assessment_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            kpi_id=assessment.kpi_id,
            scenario_id=assessment.scenario_id,
            user_role=user_role,
            input_factpack_hash=factpack_hash,
            input_evidencepack_hash=evidencepack_hash,
            formula_version=self.FORMULA_VERSION,
            policy_version=self.POLICY_VERSION,
            overall_confidence=assessment.overall_confidence,
            confidence_band=assessment.confidence_band.value,
            decision=decision.value,
            reason_codes=reason_codes,
            clarification_count=len(assessment.clarification_questions)
        )
        self.audit_log.append(audit_record)

        return gov_decision

    def get_audit_history(self, limit: int = 50) -> List[AuditRecord]:
        """Returns recent audit history records."""
        return self.audit_log[-limit:]

governance_circuit_breaker = GovernanceCircuitBreaker()

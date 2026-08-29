import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.governance.service import governance_service
from app.governance.models import GovernanceDecisionEnum, ConfidenceBand
from app.evidence.service import evidence_service

class TestAbstentionAndCircuitBreaker:

    def test_contradictory_evidence_abstention(self):
        """
        Scenario 5 contains freight surcharge memos contradicting discount-driven margin drops.
        Must detect contradiction, apply penalty, and trigger ABSTAIN or REQUEST_CLARIFICATION.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_5_CONTRADICTORY_EVIDENCE")
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_gross_margin",
            scenario_id="SCENARIO_5_CONTRADICTORY_EVIDENCE",
            user_role="ANALYST"
        )
        
        assert assessment.contradiction_penalty >= 35.0
        assert assessment.confidence_band in [ConfidenceBand.ABSTAIN, ConfidenceBand.LOW]
        assert decision.decision in [GovernanceDecisionEnum.ABSTAIN, GovernanceDecisionEnum.REQUEST_CLARIFICATION]
        assert len(assessment.clarification_questions) > 0
        assert any("conflict" in q.lower() or "freight" in q.lower() for q in assessment.clarification_questions)

    def test_sparse_history_abstention(self):
        """
        Scenario 4 has only 10 days of historical data.
        Must constrain statistical confidence and force REQUEST_CLARIFICATION / ABSTAIN.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_4_SPARSE_HISTORY")
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_4_SPARSE_HISTORY",
            user_role="ANALYST"
        )
        
        assert assessment.statistical_confidence <= 30.0
        assert assessment.confidence_band in [ConfidenceBand.LOW, ConfidenceBand.ABSTAIN]
        assert decision.decision in [GovernanceDecisionEnum.REQUEST_CLARIFICATION, GovernanceDecisionEnum.ABSTAIN]
        assert any("sparse" in w.lower() or "limited" in w.lower() or "baseline" in w.lower() for w in assessment.warnings)

    def test_insufficient_evidence_handling(self):
        """
        When evidence score is zero, confidence is reduced and clarification is requested.
        """
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_conv_rate",
            scenario_id="SCENARIO_4_SPARSE_HISTORY",
            user_role="ANALYST"
        )
        assert assessment.evidence_score == 0.0
        assert decision.decision in [GovernanceDecisionEnum.REQUEST_CLARIFICATION, GovernanceDecisionEnum.ABSTAIN]

    def test_deterministic_clarification_generation(self):
        """
        Clarification questions must be generated deterministically without an LLM.
        """
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_gross_margin",
            scenario_id="SCENARIO_5_CONTRADICTORY_EVIDENCE",
            user_role="ANALYST"
        )
        assert len(assessment.clarification_questions) > 0
        for q in assessment.clarification_questions:
            assert isinstance(q, str)
            assert len(q) > 20
            assert "?" in q

    def test_abstention_explains_conflict(self):
        """Abstention on contradiction must explain what conflicts and why a single explanation is unsafe."""
        evidence_service.ingest_scenario_evidence("SCENARIO_5_CONTRADICTORY_EVIDENCE")
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_gross_margin",
            scenario_id="SCENARIO_5_CONTRADICTORY_EVIDENCE",
            user_role="ANALYST",
        )
        if decision.decision == GovernanceDecisionEnum.ABSTAIN:
            assert assessment.conflict_summary is not None
            assert "cannot safely" in assessment.conflict_summary.lower() or "conflict" in assessment.conflict_summary.lower()
            assert "CONTRADICTORY_EVIDENCE" in decision.reason_codes
            assert "GENERATE_EXECUTIVE_CLAIM" in decision.blocked_actions

    def test_audit_trail_includes_hashes_and_latency(self):
        """Audit records capture hashes, formula version, and assessment latency."""
        _, decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")
        history = governance_service.get_audit_history(limit=5)
        latest = history[-1]
        assert latest.input_factpack_hash
        assert latest.input_evidencepack_hash
        assert latest.formula_version
        assert latest.policy_version
        assert latest.assessment_latency_ms >= 0.0
        assert decision.audit_metadata.get("llm_override_allowed") is False


import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.governance.service import governance_service
from app.governance.models import GovernanceDecisionEnum, ConfidenceBand

class TestGovernanceEngine:

    @pytest.fixture(autouse=True)
    def setup_scenario_indexes(self):
        from app.evidence.service import evidence_service
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_governance_decision_proceed_actions(self):
        """When confidence is high, allowed actions include narrative synthesis and briefs."""
        assessment, decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")
        
        assert decision.decision in [GovernanceDecisionEnum.PROCEED, GovernanceDecisionEnum.PROCEED_WITH_CAUTION]
        assert "GENERATE_ANALYST_DEEPDIVE" in decision.allowed_actions or "GENERATE_CAVEATED_ANALYST_BRIEF" in decision.allowed_actions
        assert "DRILL_DOWN_DIMENSIONS" in decision.allowed_actions

    def test_governance_decision_abstain_blocked_actions(self):
        """When an ABSTAIN decision is triggered, critical synthesis actions must be blocked."""
        assessment, decision = governance_service.assess_kpi("kpi_gross_margin", "SCENARIO_5_CONTRADICTORY_EVIDENCE", user_role="ANALYST")
        
        if decision.decision == GovernanceDecisionEnum.ABSTAIN:
            assert "GENERATE_EXECUTIVE_CLAIM" in decision.blocked_actions
            assert "RECOMMEND_ACTION" in decision.blocked_actions
            assert "GENERATE_ABSTENTION_NOTICE" in decision.allowed_actions

    def test_governance_audit_trail_logging(self):
        """Every assessment must log an immutable audit record."""
        initial_count = len(governance_service.get_audit_history(limit=100))
        assessment, decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")
        
        history = governance_service.get_audit_history(limit=100)
        assert len(history) == initial_count + 1
        
        latest_record = history[-1]
        assert latest_record.assessment_id == assessment.assessment_id
        assert latest_record.kpi_id == "kpi_revenue"
        assert latest_record.scenario_id == "SCENARIO_1_MULTI_FACTOR"
        assert latest_record.decision == decision.decision.value
        assert latest_record.input_factpack_hash != ""
        assert latest_record.input_evidencepack_hash != ""

    def test_governance_rbac_integration(self):
        """Executive persona receives policy-compliant high-level briefing while Analyst receives full details."""
        exec_assessment, exec_decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="EXECUTIVE")
        analyst_assessment, analyst_decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")
        
        assert exec_assessment.confidence_band == analyst_assessment.confidence_band
        assert exec_decision.decision == analyst_decision.decision
        assert exec_assessment.overall_confidence >= 80.0
        assert analyst_assessment.overall_confidence >= 80.0

    def test_executive_view_omits_restricted_detail(self):
        """Executive persona must not receive evidence identifiers or analyst-grade justifications."""
        exec_assessment, _ = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="EXECUTIVE")
        assert exec_assessment.conflicting_evidence_ids == []
        if exec_assessment.driver_assessments:
            assert all(
                "Executive summary" in d.justification
                for d in exec_assessment.driver_assessments.values()
            )

    def test_ground_truth_independence(self):
        """Governance engine never accesses ground_truth sections of scenarios.yaml."""
        import inspect
        from app.governance import evaluator, circuit_breaker, service
        
        evaluator_code = inspect.getsource(evaluator)
        circuit_code = inspect.getsource(circuit_breaker)
        service_code = inspect.getsource(service)
        
        for code_str in [evaluator_code, circuit_code, service_code]:
            assert "ground_truth" not in code_str, "Governance layer must never read ground_truth!"

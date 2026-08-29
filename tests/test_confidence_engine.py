import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.engine.investigation import investigation_engine
from app.evidence.service import evidence_service
from app.governance.service import governance_service
from app.governance.evaluator import confidence_evaluator
from app.governance.models import ConfidenceBand, GovernanceDecisionEnum

class TestConfidenceEngine:

    @pytest.fixture(autouse=True)
    def setup_scenario_indexes(self):
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_high_confidence_multi_factor_scenario(self):
        """
        Scenario 1 has strong statistical separation, high materiality, and verified operational tickets.
        Should produce high/medium-high calibrated confidence and PROCEED / PROCEED_WITH_CAUTION.
        """
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            user_role="ANALYST"
        )
        assert assessment.kpi_id == "kpi_revenue"
        assert assessment.overall_confidence >= 70.0
        assert assessment.confidence_band in [ConfidenceBand.HIGH, ConfidenceBand.MEDIUM]
        assert decision.decision in [GovernanceDecisionEnum.PROCEED, GovernanceDecisionEnum.PROCEED_WITH_CAUTION]
        assert assessment.statistical_confidence >= 80.0
        assert assessment.materiality_score >= 80.0
        assert assessment.evidence_score >= 70.0
        assert assessment.contradiction_penalty == 0.0

    def test_statistical_confidence_component(self):
        """Verifies statistical component calculation across different z-scores."""
        inv_res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        score, reasons, warnings = confidence_evaluator.evaluate_statistical_confidence(inv_res)
        
        assert score >= 80.0
        assert any("statistical significance" in r.lower() for r in reasons)
        assert len(warnings) == 0

    def test_materiality_vs_significance_distinction(self):
        """Ensures business materiality is scored distinctly from statistical significance."""
        inv_res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        mat_score, mat_reasons = confidence_evaluator.evaluate_materiality_score(inv_res)
        
        assert mat_score >= 80.0
        assert any("materiality" in r.lower() or "material" in r.lower() for r in mat_reasons)

    def test_data_quality_and_freshness_components(self):
        """Verifies source health, completeness, and SLA compliance scores."""
        inv_res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        dq_score, dq_reasons = confidence_evaluator.evaluate_data_quality(inv_res)
        fresh_score, fresh_reasons, fresh_warnings = confidence_evaluator.evaluate_freshness_score(inv_res)
        
        assert dq_score >= 90.0
        assert fresh_score >= 90.0
        assert len(fresh_warnings) == 0

    def test_driver_level_confidence_evaluations(self):
        """Verifies driver-by-driver confidence assessment."""
        assessment, _ = governance_service.assess_kpi(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            user_role="ANALYST"
        )
        assert len(assessment.driver_assessments) > 0
        for driver_name, d_assess in assessment.driver_assessments.items():
            assert 0.0 <= d_assess.confidence_score <= 100.0
            assert d_assess.confidence_band in [ConfidenceBand.HIGH, ConfidenceBand.MEDIUM, ConfidenceBand.LOW, ConfidenceBand.ABSTAIN]
            assert d_assess.is_statistically_aligned is True

    def test_confidence_formula_determinism(self):
        """Ensures that two identical evaluations produce identical confidence scores down to float precision."""
        assessment1, decision1 = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        assessment2, decision2 = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        
        assert assessment1.overall_confidence == assessment2.overall_confidence
        assert assessment1.statistical_confidence == assessment2.statistical_confidence
        assert assessment1.evidence_score == assessment2.evidence_score
        assert decision1.decision == decision2.decision

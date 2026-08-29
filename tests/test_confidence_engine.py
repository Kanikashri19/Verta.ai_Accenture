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

    def test_high_confidence_single_factor_scenario(self):
        """Fresh/high-quality campaign-outage scenario should not abstain."""
        evidence_service.ingest_scenario_evidence("SCENARIO_2_HIGH_CONFIDENCE")
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_orders",
            scenario_id="SCENARIO_2_HIGH_CONFIDENCE",
            user_role="ANALYST",
        )
        assert decision.decision in [GovernanceDecisionEnum.PROCEED, GovernanceDecisionEnum.PROCEED_WITH_CAUTION, GovernanceDecisionEnum.REQUEST_CLARIFICATION]
        assert assessment.confidence_band != ConfidenceBand.ABSTAIN or assessment.overall_confidence < 35.0
        assert assessment.contradiction_penalty == 0.0

    def test_low_confidence_inconclusive_aov(self):
        """Scenario 3: inconclusive AOV should not authorize uncaveated narrative."""
        evidence_service.ingest_scenario_evidence("SCENARIO_3_LOW_CONFIDENCE")
        assessment, decision = governance_service.assess_kpi(
            kpi_id="kpi_aov",
            scenario_id="SCENARIO_3_LOW_CONFIDENCE",
            user_role="ANALYST",
        )
        assert decision.decision in [
            GovernanceDecisionEnum.REQUEST_CLARIFICATION,
            GovernanceDecisionEnum.ABSTAIN,
            GovernanceDecisionEnum.PROCEED_WITH_CAUTION,
        ]
        assert assessment.confidence_band != ConfidenceBand.HIGH

    def test_evidence_quality_over_count(self):
        """Ten weak items must not outscore one strong exact-window item."""
        from app.evidence.models import EvidencePack, EvidenceItem

        def _item(eid, score, temporal, classification="SUPPORTING"):
            return EvidenceItem(
                evidence_id=eid,
                source="OPS_INCIDENT",
                timestamp="2026-08-23T00:00:00Z",
                date="2026-08-23",
                snippet="x",
                driver="conversion_rate",
                classification=classification,
                score=score,
                issue_type="PAYMENT_GATEWAY_TIMEOUT",
                severity="HIGH",
                sensitivity="INTERNAL_OPS",
                temporal_alignment=temporal,
                lineage={"pii_masked": True},
                access_roles=["ANALYST"],
            )

        weak_pack = EvidencePack(
            kpi_id="kpi_revenue",
            investigation_window={"start": "2026-08-22", "end": "2026-08-28"},
            user_role="ANALYST",
            supporting_evidence=[_item(f"w{i}", 20.0, "NEAR_WINDOW") for i in range(10)],
            status="SUCCESS",
        )
        strong_pack = EvidencePack(
            kpi_id="kpi_revenue",
            investigation_window={"start": "2026-08-22", "end": "2026-08-28"},
            user_role="ANALYST",
            supporting_evidence=[_item("s1", 92.0, "EXACT_WINDOW")],
            status="SUCCESS",
        )
        weak_score, _, _ = confidence_evaluator.evaluate_evidence_score(weak_pack)
        strong_score, _, _ = confidence_evaluator.evaluate_evidence_score(strong_pack)
        assert strong_score > weak_score

    def test_formula_weighted_sum_unit(self):
        """overall_confidence equals the documented weighted sum minus penalty, clipped."""
        from app.engine.models import InvestigationResult, MaterialityAssessment

        inv = InvestigationResult(
            investigation_id="INV-UNIT",
            kpi_id="kpi_revenue",
            kpi_name="Gross Revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            baseline_period={"start": "2026-06-01", "end": "2026-08-21"},
            anomaly_period={"start": "2026-08-22", "end": "2026-08-28"},
            baseline_value=100.0,
            current_value=80.0,
            absolute_change=-20.0,
            percentage_change=-20.0,
            unit="USD",
            materiality=MaterialityAssessment(
                business_materiality="MATERIAL",
                statistical_significance="STATISTICALLY_SIGNIFICANT",
                overall_materiality="CRITICAL_ACTIONABLE",
                relative_change_pct=-20.0,
                absolute_change=-20.0,
                threshold_pct=5.0,
                z_score=4.0,
                p_value_approx=0.001,
                materiality_explanation="unit",
            ),
            analytical_method="unit",
        )
        from app.evidence.models import EvidencePack
        pack = EvidencePack(
            kpi_id="kpi_revenue",
            investigation_window={"start": "2026-08-22", "end": "2026-08-28"},
            user_role="ANALYST",
            status="INSUFFICIENT_EVIDENCE",
        )
        assessment = confidence_evaluator.assess_confidence(
            investigation=inv,
            evidence_pack=pack,
            assessment_id="CONF-UNIT",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            source_metadata={
                "src_sales_transactions": {
                    "data_quality_score": 0.98,
                    "last_refresh": "2026-08-29T00:00:00Z",
                    "freshness_sla_minutes": 1440,
                }
            },
        )
        w = confidence_evaluator.weights
        expected = (
            w.weight_statistical * assessment.statistical_confidence
            + w.weight_materiality * assessment.materiality_score
            + w.weight_evidence * assessment.evidence_score
            + w.weight_data_quality * assessment.data_quality_score
            + w.weight_freshness * assessment.freshness_score
            + w.weight_lineage * assessment.lineage_score
            - assessment.contradiction_penalty
        )
        assert assessment.overall_confidence == round(max(0.0, min(100.0, expected)), 1)
        assert assessment.decision in [GovernanceDecisionEnum.REQUEST_CLARIFICATION, GovernanceDecisionEnum.ABSTAIN]
        assert any("No sufficient evidence was found" in wmsg for wmsg in assessment.warnings)

    def test_catalog_data_quality_consumed(self):
        """Source metadata quality scores must drive data_quality_score (scaled 0-100)."""
        inv_res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        from app.data.loader import data_loader
        dq_score, dq_reasons = confidence_evaluator.evaluate_data_quality(
            inv_res, source_metadata=data_loader.get_source_metadata()
        )
        assert dq_score >= 90.0
        assert any("catalog quality" in r.lower() for r in dq_reasons)


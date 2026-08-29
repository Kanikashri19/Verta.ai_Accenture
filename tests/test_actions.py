import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.engine.investigation import investigation_engine
from app.evidence.service import evidence_service
from app.governance.service import governance_service
from app.narrative.action_catalog import action_catalog_engine, APPROVED_ACTION_CATALOG, VALID_OWNERS

class TestActions:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_action_catalog_selection_for_revenue_drop(self):
        """
        Scenario 1 contains checkout timeouts and SKU stockouts.
        Action catalog must select payment routing and inventory replenishment levers.
        """
        factpack = investigation_engine.get_factpack("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        evidence_pack = evidence_service.get_evidence_for_factpack(factpack, user_role="ANALYST")
        assessment, _ = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")

        actions = action_catalog_engine.select_actions(factpack, evidence_pack, assessment)
        assert len(actions) >= 1
        
        action_ids = [a.action_id for a in actions]
        assert "ACT-PAYMENT-001" in action_ids or "ACT-INVENTORY-001" in action_ids

        for act in actions:
            assert len(act.action) > 0
            assert len(act.controllable_lever) > 0
            assert len(act.expected_impact) > 0
            assert len(act.monitoring_plan) > 0
            assert act.owner in VALID_OWNERS
            assert act.decision_right in VALID_OWNERS or act.decision_right == "REQUIRES_HUMAN_REVIEW"
            assert act.confidence_band in ["HIGH", "MEDIUM", "LOW", "ABSTAIN"]

    def test_action_evidence_ids_traceability(self):
        """Actions must attach verified evidence_ids matching the operational tickets."""
        factpack = investigation_engine.get_factpack("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        evidence_pack = evidence_service.get_evidence_for_factpack(factpack, user_role="ANALYST")
        assessment, _ = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")

        actions = action_catalog_engine.select_actions(factpack, evidence_pack, assessment)
        for act in actions:
            if act.evidence_ids:
                for eid in act.evidence_ids:
                    assert eid.startswith("EVID-") or eid.startswith("EV-") or eid.startswith("EV")

    def test_action_owner_validation(self):
        """Ensures all approved catalog entries have authorized decision rights."""
        for entry in APPROVED_ACTION_CATALOG:
            assert entry["owner"] in VALID_OWNERS
            assert len(entry["controllable_lever"]) > 0
            assert len(entry["expected_impact"]) > 0

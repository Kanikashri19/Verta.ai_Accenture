import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.narrative.service import narrative_service
from app.narrative.models import Persona, GenerationMode
from app.evidence.service import evidence_service

class TestLLMGovernance:

    def test_governance_abstain_on_contradictory_evidence(self):
        """
        Scenario 5 (Contradictory freight vs discount memos) triggers ABSTAIN.
        The LLM must be strictly bypassed, producing an auditable abstention response.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_5_CONTRADICTORY_EVIDENCE")

        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_gross_margin",
            scenario_id="SCENARIO_5_CONTRADICTORY_EVIDENCE",
            persona=Persona.EXECUTIVE,
            user_role="ANALYST",
            force_refresh=True
        )

        assert response.governance_decision == "ABSTAIN"
        assert response.generation_mode == GenerationMode.DETERMINISTIC_FALLBACK.value
        assert "Abstention:" in response.headline or "Contradictory" in response.headline
        assert response.conflict_summary is not None
        assert len(response.recommended_actions) == 0  # High-impact actions blocked
        assert len(response.clarification_questions) > 0

    def test_governance_request_clarification_on_sparse_history(self):
        """
        Scenario 4 (Sparse 10-day history) triggers REQUEST_CLARIFICATION.
        Must return deterministic clarification questions and pause narrative.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_4_SPARSE_HISTORY")

        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_4_SPARSE_HISTORY",
            persona=Persona.ANALYST,
            user_role="ANALYST",
            force_refresh=True
        )

        assert response.governance_decision == "REQUEST_CLARIFICATION"
        assert "Clarification" in response.headline or "Insufficient" in response.headline
        assert len(response.clarification_questions) > 0
        assert any("baseline" in q.lower() or "window" in q.lower() for q in response.clarification_questions)

    def test_rbac_pre_filtering_executive_isolation(self):
        """
        Executive persona requests sanitized view; restricted operational detail and PII are masked before synthesis.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.EXECUTIVE,
            user_role="EXECUTIVE",
            force_refresh=True
        )

        assert response.persona == Persona.EXECUTIVE
        text_payload = response.headline + " " + response.summary
        assert "@" not in text_payload  # No unmasked email addresses
        assert "4111" not in text_payload  # No card numbers

    def test_proceed_with_caution_uncertainty_caveats(self):
        """
        Scenarios evaluated with PROCEED_WITH_CAUTION must include explicit confidence caveats.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.ANALYST,
            user_role="ANALYST"
        )
        assert len(response.caveats) > 0

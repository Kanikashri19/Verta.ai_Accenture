import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.narrative.service import narrative_service
from app.narrative.models import Persona
from app.evidence.service import evidence_service

class TestPersonas:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_persona_differentiation_content_and_depth(self):
        """
        Executive and Analyst narratives must be meaningfully different in length, focus, and technical depth.
        """
        exec_resp = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.EXECUTIVE,
            user_role="ANALYST",
            force_refresh=True
        )

        analyst_resp = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.ANALYST,
            user_role="ANALYST",
            force_refresh=True
        )

        assert exec_resp.persona == Persona.EXECUTIVE
        assert analyst_resp.persona == Persona.ANALYST

        # Executive summary is more concise and decision-focused
        exec_word_count = len(exec_resp.summary.split())
        analyst_word_count = len(analyst_resp.summary.split())
        assert analyst_word_count >= exec_word_count

        # Analyst contains explicit statistical or decomposition terminology
        analyst_text = (analyst_resp.headline + " " + analyst_resp.summary).lower()
        assert any(term in analyst_text for term in ["statistical", "baseline", "|z|", "p <", "decomposition", "delta"])

        # Headlines must be distinct
        assert exec_resp.headline != analyst_resp.headline

    def test_persona_schema_conformity(self):
        """Both personas must adhere completely to the structured NarrativeResponse Pydantic schema."""
        for p in [Persona.EXECUTIVE, Persona.ANALYST]:
            resp = narrative_service.assess_and_generate_narrative(
                kpi_id="kpi_revenue",
                scenario_id="SCENARIO_1_MULTI_FACTOR",
                persona=p,
                user_role="ANALYST"
            )
            assert resp.kpi_id == "kpi_revenue"
            assert resp.kpi_movement["percentage_change"] != 0.0
            assert isinstance(resp.caveats, list)
            assert isinstance(resp.recommended_actions, list)
            assert isinstance(resp.data_lineage, list)

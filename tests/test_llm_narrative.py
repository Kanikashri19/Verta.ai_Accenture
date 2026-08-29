import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.narrative.service import narrative_service
from app.narrative.models import Persona, GenerationMode
from app.evidence.service import evidence_service
from app.narrative.cache import narrative_cache

class TestLLMNarrative:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")
        narrative_cache.clear()

    def test_executive_narrative_generation(self):
        """
        Scenario 1 Executive view should generate high-level, business-focused narrative with valid citations.
        """
        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.EXECUTIVE,
            user_role="ANALYST"
        )
        assert response.kpi_id == "kpi_revenue"
        assert response.persona == Persona.EXECUTIVE
        assert len(response.headline) > 0
        assert len(response.summary) > 0
        assert response.confidence_score >= 80.0
        assert response.governance_decision in ["PROCEED", "PROCEED_WITH_CAUTION"]
        assert len(response.recommended_actions) > 0
        assert response.telemetry is not None

    def test_analyst_narrative_generation(self):
        """
        Scenario 1 Analyst view should generate detailed technical narrative with statistical details.
        """
        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.ANALYST,
            user_role="ANALYST"
        )
        assert response.kpi_id == "kpi_revenue"
        assert response.persona == Persona.ANALYST
        assert len(response.key_drivers) > 0
        assert any("conversion" in d["driver_name"].lower() or "orders" in d["driver_name"].lower() for d in response.key_drivers)
        assert len(response.evidence_citations) > 0
        assert len(response.caveats) > 0

    def test_evidence_citations_grounded_in_evidencepack(self):
        """
        Verifies that every evidence citation ID returned exists in the actual EvidencePack.
        No hallucinated or invented citation IDs allowed.
        """
        response = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.ANALYST,
            user_role="ANALYST"
        )
        for cit in response.evidence_citations:
            assert len(cit.evidence_ids) > 0
            for eid in cit.evidence_ids:
                assert eid.startswith("EVID-") or eid.startswith("EV")

    def test_deterministic_fallback_on_llm_failure(self):
        """
        Simulates LLM provider unavailability; system must seamlessly fall back to deterministic generator.
        """
        from app.narrative.fallback import deterministic_narrative_generator
        from app.engine.investigation import investigation_engine
        from app.governance.service import governance_service

        factpack = investigation_engine.get_factpack("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        evidence_pack = evidence_service.get_evidence_for_factpack(factpack, user_role="ANALYST")
        assessment, decision = governance_service.assess_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR", user_role="ANALYST")

        fallback_resp = deterministic_narrative_generator.generate(
            factpack=factpack,
            evidence_pack=evidence_pack,
            confidence_assessment=assessment,
            governance_decision=decision,
            persona=Persona.EXECUTIVE
        )
        assert fallback_resp.generation_mode == GenerationMode.DETERMINISTIC_FALLBACK.value
        assert "Gross Revenue" in fallback_resp.headline
        assert fallback_resp.confidence_score == assessment.overall_confidence
        assert len(fallback_resp.recommended_actions) > 0

    def test_deterministic_caching_behavior(self):
        """
        Identical requests must hit the deterministic cache, returning matching output and setting cache_hit=True.
        """
        resp1 = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.EXECUTIVE,
            user_role="ANALYST",
            force_refresh=True
        )
        assert narrative_cache.size >= 1

        resp2 = narrative_service.assess_and_generate_narrative(
            kpi_id="kpi_revenue",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            persona=Persona.EXECUTIVE,
            user_role="ANALYST",
            force_refresh=False
        )
        assert resp1.headline == resp2.headline
        assert resp1.summary == resp2.summary
        assert resp2.telemetry is not None
        assert resp2.telemetry.cache_hit is True

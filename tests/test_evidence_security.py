import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.evidence.service import evidence_service
from app.evidence.store import evidence_store
from app.evidence.pii import pii_masker

class TestEvidenceSecurity:

    @pytest.fixture(autouse=True)
    def ensure_security_index(self):
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_raw_pii_never_in_vector_store(self):
        """Verifies that 100% of documents in ChromaDB have zero raw PII."""
        results = evidence_store.collection.get(include=["documents", "metadatas"])
        docs = results.get("documents", [])
        
        assert len(docs) > 0
        for doc_text in docs:
            assert pii_masker.contains_pii(doc_text) is False, f"Found unmasked PII in vector document: {doc_text}"

    def test_executive_role_rbac_restriction(self):
        """Executive role must not receive PII_RESTRICTED documents."""
        exec_pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            user_role="EXECUTIVE",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            top_k=20,
        )
        
        all_items = exec_pack.supporting_evidence + exec_pack.contradictory_evidence + exec_pack.neutral_evidence
        for item in all_items:
            assert item.sensitivity != "PII_RESTRICTED", "Executive received PII_RESTRICTED document!"

    def test_analyst_role_access(self):
        """Analyst role can access operational and customer feedback documents."""
        analyst_pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            user_role="ANALYST",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            top_k=10,
        )
        assert len(analyst_pack.supporting_evidence) > 0
        assert any(e.sensitivity in ["PII_RESTRICTED", "INTERNAL_OPS"] for e in analyst_pack.supporting_evidence)

    def test_unauthorized_role_isolation(self):
        """Unknown or unpermitted role gets zero evidence."""
        guest_pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            user_role="UNAUTHORIZED_GUEST",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
        )
        assert len(guest_pack.supporting_evidence) == 0
        assert guest_pack.status == "INSUFFICIENT_EVIDENCE"

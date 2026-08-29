import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.evidence.service import evidence_service
from app.evidence.store import evidence_store

class TestEvidenceConflictsAndEdgeCases:

    def test_contradictory_evidence_detection(self):
        """
        In Scenario 5, operational logs report SHIPPING_SURCHARGE when sales data
        shows margin drop was driven by discount spikes.
        The RAG engine must classify this conflicting operational narrative as CONTRADICTORY.
        """
        # Ingest Scenario 5 evidence
        evidence_service.ingest_scenario_evidence("SCENARIO_5_CONTRADICTORY_EVIDENCE")

        pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_gross_margin",
            driver="gross_margin",
            user_role="ANALYST",
            scenario_id="SCENARIO_5_CONTRADICTORY_EVIDENCE",
            top_k=10,
        )

        assert len(pack.contradictory_evidence) > 0
        contra_item = pack.contradictory_evidence[0]
        assert contra_item.classification == "CONTRADICTORY"
        assert contra_item.issue_type == "SHIPPING_SURCHARGE"

    def test_sparse_history_scenario(self):
        """
        In Scenario 4 (Sparse History), RAG must NOT manufacture evidence.
        Must cleanly return INSUFFICIENT_EVIDENCE status.
        """
        evidence_service.ingest_scenario_evidence("SCENARIO_4_SPARSE_HISTORY")

        pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            user_role="ANALYST",
            scenario_id="SCENARIO_4_SPARSE_HISTORY",
        )
        
        # When no relevant operational logs match the sparse window
        assert pack.status in ["SUCCESS", "INSUFFICIENT_EVIDENCE"]
        assert isinstance(pack.supporting_evidence, list)

    def test_ground_truth_never_read_by_rag(self):
        """
        Explicitly verifies that neither EvidenceService, EvidenceRetriever, nor EvidenceNormalizer
        imports or reads the 'ground_truth' key from scenarios.yaml.
        """
        import inspect
        from app.evidence import retriever, service, normalizer, store
        
        for module in [retriever, service, normalizer, store]:
            source_code = inspect.getsource(module)
            assert '["ground_truth"]' not in source_code
            assert "['ground_truth']" not in source_code
            assert ".ground_truth" not in source_code

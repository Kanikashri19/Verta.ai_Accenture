import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.evidence.service import evidence_service
from app.evidence.store import evidence_store
from app.evidence.scorer import evidence_scorer
from app.engine.investigation import investigation_engine

class TestEvidenceRetrieval:

    @pytest.fixture(autouse=True)
    def ensure_scenario_index(self):
        # Ingest Scenario 1 for clean retrieval state
        evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")

    def test_idempotent_ingestion(self):
        initial_count = evidence_store.collection.count()
        assert initial_count > 0
        
        # Ingest again
        second_ingest = evidence_service.ingest_scenario_evidence("SCENARIO_1_MULTI_FACTOR")
        assert second_ingest > 0
        assert evidence_store.collection.count() == initial_count, "Ingestion must be idempotent and not duplicate documents"

    def test_retrieval_conversion_rate_supporting(self):
        pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            region="EU",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            top_k=5,
        )
        assert pack.status == "SUCCESS"
        assert len(pack.supporting_evidence) > 0
        
        top_item = pack.supporting_evidence[0]
        assert top_item.classification == "SUPPORTING"
        assert "PAYMENT_GATEWAY_TIMEOUT" in top_item.issue_type
        assert top_item.temporal_alignment in ["EXACT_WINDOW", "NEAR_WINDOW"]
        assert top_item.score > 60.0

    def test_retrieval_availability_stockout_supporting(self):
        pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="availability",
            region="NA",
            product_id="PROD_LAPTOP_01",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
            top_k=5,
        )
        assert pack.status == "SUCCESS"
        assert len(pack.supporting_evidence) > 0
        
        stockout_items = [e for e in pack.supporting_evidence if "STOCKOUT" in e.issue_type]
        assert len(stockout_items) > 0
        assert stockout_items[0].product_id == "PROD_LAPTOP_01"
        assert stockout_items[0].classification == "SUPPORTING"

    def test_retrieval_temporal_filtering(self):
        pack = evidence_service.retrieve_evidence(
            kpi_id="kpi_revenue",
            driver="conversion_rate",
            anomaly_start="2025-01-01",
            anomaly_end="2025-01-07",
            scenario_id="SCENARIO_1_MULTI_FACTOR",
        )
        assert len(pack.supporting_evidence) == 0
        assert pack.status == "INSUFFICIENT_EVIDENCE"

    def test_factpack_evidence_integration(self):
        res = investigation_engine.investigate_kpi("kpi_revenue", "SCENARIO_1_MULTI_FACTOR")
        fact_pack = investigation_engine.generate_fact_pack(res)
        
        evidence_pack = evidence_service.get_evidence_for_factpack(fact_pack, user_role="ANALYST", top_k=5)
        
        assert evidence_pack.kpi_id == "kpi_revenue"
        assert evidence_pack.status == "SUCCESS"
        assert len(evidence_pack.supporting_evidence) > 0
        
        issue_types = {e.issue_type for e in evidence_pack.supporting_evidence}
        assert "PAYMENT_GATEWAY_TIMEOUT" in issue_types or "STOCKOUT" in issue_types

    def test_deterministic_scoring(self):
        score1 = evidence_scorer.compute_score(
            semantic_similarity=0.85,
            temporal_alignment="EXACT_WINDOW",
            dimension_match=True,
            severity="CRITICAL",
            driver_tag_match=True,
        )
        score2 = evidence_scorer.compute_score(
            semantic_similarity=0.85,
            temporal_alignment="EXACT_WINDOW",
            dimension_match=True,
            severity="CRITICAL",
            driver_tag_match=True,
        )
        assert score1 == score2
        assert 0.0 <= score1 <= 100.0

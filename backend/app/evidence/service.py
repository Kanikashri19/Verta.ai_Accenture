from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from app.evidence.models import EvidencePack, EvidenceStatus, EvidenceTelemetry, EvidenceItem
from app.evidence.normalizer import evidence_normalizer
from app.evidence.chunker import evidence_chunker
from app.evidence.store import evidence_store
from app.evidence.retriever import evidence_retriever
from app.data.loader import data_loader
from app.engine.models import FactPack

class EvidenceService:
    """
    High-Level Evidence Intelligence Service.
    Coordinates document ingestion, FactPack enrichment, and deterministic retrieval telemetry.
    """

    def __init__(self):
        self._telemetry_logs: List[EvidenceTelemetry] = []

    def ingest_scenario_evidence(self, scenario_id: str = "SCENARIO_1_MULTI_FACTOR") -> int:
        """
        Loads raw operational events for a scenario, masks PII, normalizes, chunks,
        and indexes them into the local ChromaDB vector store.
        """
        _, _, ops_df, _ = data_loader.load_data(scenario_id)
        if ops_df.empty:
            return 0

        # 1. Normalize and mask PII
        docs = evidence_normalizer.normalize_dataframe(ops_df, scenario_id=scenario_id)

        # 2. Chunk documents
        chunks = evidence_chunker.chunk_documents(docs)

        # 3. Index in vector store
        indexed_count = evidence_store.index_documents(chunks)
        return indexed_count

    def ingest_all_scenarios(self) -> Dict[str, int]:
        """
        Ingests evidence from all available demo scenarios.
        """
        scenarios = [
            "SCENARIO_1_MULTI_FACTOR",
            "SCENARIO_2_SINGLE_FACTOR",
            "SCENARIO_3_LOW_CONFIDENCE",
            "SCENARIO_4_SPARSE_HISTORY",
            "SCENARIO_5_CONTRADICTORY_EVIDENCE",
        ]
        counts = {}
        for s_id in scenarios:
            cnt = self.ingest_scenario_evidence(s_id)
            counts[s_id] = cnt
        return counts

    def get_status(self) -> EvidenceStatus:
        """
        Returns vector store health, document count, and embedding configuration.
        """
        return evidence_store.get_status()

    def retrieve_evidence(
        self,
        kpi_id: str,
        driver: str = "conversion_rate",
        region: Optional[str] = None,
        product_id: Optional[str] = None,
        user_role: str = "ANALYST",
        scenario_id: str = "SCENARIO_1_MULTI_FACTOR",
        anomaly_start: Optional[str] = None,
        anomaly_end: Optional[str] = None,
        top_k: int = 10,
    ) -> EvidencePack:
        """
        Standalone evidence retrieval for API requests.
        """
        scen_meta = data_loader.get_scenario_metadata(scenario_id)
        a_start = anomaly_start or scen_meta["time_window"]["anomaly_start"]
        a_end = anomaly_end or scen_meta["time_window"]["anomaly_end"]

        # Ensure scenario data is indexed
        if evidence_store.collection.count() == 0:
            self.ingest_scenario_evidence(scenario_id)

        pack = evidence_retriever.retrieve(
            kpi_id=kpi_id,
            anomaly_start=a_start,
            anomaly_end=a_end,
            driver=driver,
            region=region,
            product_id=product_id,
            user_role=user_role,
            scenario_id=scenario_id,
            top_k=top_k,
        )

        # Record deterministic telemetry
        self._record_telemetry(pack, driver, user_role, top_k)
        return pack

    def get_evidence_for_factpack(
        self,
        fact_pack: FactPack,
        user_role: str = "ANALYST",
        top_k: int = 5,
    ) -> EvidencePack:
        """
        Consumes a deterministic FactPack and retrieves matching evidence for all ranked drivers.
        """
        inv = fact_pack.investigation
        kpi_id = inv.kpi_id
        a_start = inv.anomaly_period["start"]
        a_end = inv.anomaly_period["end"]
        scenario_id = inv.scenario_id

        # Ensure index has documents
        if evidence_store.collection.count() == 0:
            self.ingest_scenario_evidence(scenario_id)

        all_supporting: List[EvidenceItem] = []
        all_contradictory: List[EvidenceItem] = []
        all_neutral: List[EvidenceItem] = []
        seen_ids = set()

        # Query evidence for each primary driver in FactPack
        driver_queries = [d.driver_name for d in inv.ranked_drivers]
        if not driver_queries:
            driver_queries = ["general"]

        for d_name in driver_queries:
            d_pack = evidence_retriever.retrieve(
                kpi_id=kpi_id,
                anomaly_start=a_start,
                anomaly_end=a_end,
                driver=d_name,
                user_role=user_role,
                scenario_id=scenario_id,
                top_k=top_k,
            )
            for item in d_pack.supporting_evidence:
                if item.evidence_id not in seen_ids:
                    seen_ids.add(item.evidence_id)
                    all_supporting.append(item)
            for item in d_pack.contradictory_evidence:
                if item.evidence_id not in seen_ids:
                    seen_ids.add(item.evidence_id)
                    all_contradictory.append(item)
            for item in d_pack.neutral_evidence:
                if item.evidence_id not in seen_ids:
                    seen_ids.add(item.evidence_id)
                    all_neutral.append(item)

        all_supporting.sort(key=lambda x: x.score, reverse=True)
        all_contradictory.sort(key=lambda x: x.score, reverse=True)
        all_neutral.sort(key=lambda x: x.score, reverse=True)

        status = "SUCCESS" if (all_supporting or all_contradictory or all_neutral) else "INSUFFICIENT_EVIDENCE"
        explanation = None if status == "SUCCESS" else f"No operational evidence found in anomaly window for {kpi_id}."

        consolidated_pack = EvidencePack(
            kpi_id=kpi_id,
            investigation_window={"start": a_start, "end": a_end},
            user_role=user_role,
            supporting_evidence=all_supporting[:top_k * 2],
            contradictory_evidence=all_contradictory[:top_k * 2],
            neutral_evidence=all_neutral[:top_k * 2],
            evidence_summary={
                "supporting_count": len(all_supporting[:top_k * 2]),
                "contradictory_count": len(all_contradictory[:top_k * 2]),
                "neutral_count": len(all_neutral[:top_k * 2]),
            },
            confidence_components={
                "temporal_alignment": 100.0 if all_supporting else 0.0,
                "dimension_alignment": 90.0 if all_supporting else 0.0,
                "source_reliability": 85.0,
                "semantic_relevance": round(sum(e.score for e in all_supporting) / len(all_supporting), 1) if all_supporting else 0.0,
            },
            retrieval_metadata={
                "embedding_model": "BAAI/bge-small-en-v1.5",
                "top_k": top_k,
                "drivers_searched": driver_queries,
                "user_role": user_role,
            },
            status=status,
            explanation=explanation,
        )

        self._record_telemetry(consolidated_pack, "all_drivers", user_role, top_k)
        return consolidated_pack

    def get_telemetry(self) -> List[EvidenceTelemetry]:
        """
        Returns recent retrieval telemetry events.
        """
        return self._telemetry_logs

    def _record_telemetry(
        self,
        pack: EvidencePack,
        driver: str,
        user_role: str,
        top_k: int
    ):
        telem = EvidenceTelemetry(
            retrieval_id=f"RET-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            kpi_id=pack.kpi_id,
            driver=driver,
            user_role=user_role,
            top_k=top_k,
            candidate_count=pack.evidence_summary.get("supporting_count", 0) + pack.evidence_summary.get("contradictory_count", 0) + pack.evidence_summary.get("neutral_count", 0),
            returned_count=len(pack.supporting_evidence) + len(pack.contradictory_evidence),
            latency_ms=pack.retrieval_metadata.get("latency_ms", 12.5),
            embedding_model="BAAI/bge-small-en-v1.5",
            filters_applied={
                "kpi_id": pack.kpi_id,
                "investigation_window": pack.investigation_window,
                "user_role": user_role,
            }
        )
        self._telemetry_logs.append(telem)

evidence_service = EvidenceService()

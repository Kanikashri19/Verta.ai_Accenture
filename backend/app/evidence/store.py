import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

from app.evidence.models import EvidenceDocument, EvidenceStatus
from app.evidence.embedder import local_embedder
from app.core.config import config, BASE_DIR

class EvidenceStore:
    """
    ChromaDB-backed Persistent Vector Store for Verta.ai operational evidence.
    Ensures idempotent indexing, metadata enrichment, and fast cosine similarity retrieval.
    """

    COLLECTION_NAME = "verta_evidence_documents"

    def __init__(self, persist_dir: Optional[str] = None):
        if persist_dir:
            self.persist_dir = persist_dir
        else:
            self.persist_dir = str(BASE_DIR.parent / "data" / "vector_store")

        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.last_indexed_at: Optional[str] = None

    @property
    def collection(self):
        """
        Dynamically gets or creates the live collection reference to prevent stale UUID errors.
        """
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def index_documents(self, documents: List[EvidenceDocument]) -> int:
        """
        Idempotently indexes EvidenceDocuments into ChromaDB with metadata and embeddings.
        """
        if not documents:
            return 0

        ids = [doc.evidence_id for doc in documents]
        texts = [doc.text for doc in documents]
        embeddings = local_embedder.embed_texts(texts)

        metadatas = []
        for doc in documents:
            meta = {
                "evidence_id": doc.evidence_id,
                "document_type": doc.document_type,
                "timestamp": doc.timestamp,
                "date": doc.date,
                "source": doc.source,
                "region": doc.region or "GLOBAL",
                "product_id": doc.product_id or "ALL_PRODUCTS",
                "category": doc.category,
                "issue_type": doc.issue_type,
                "severity": doc.severity,
                "sensitivity": doc.sensitivity,
                "scenario_id": doc.scenario_id,
                "kpi_ids_str": ",".join(doc.kpi_ids),
                "driver_tags_str": ",".join(doc.driver_tags),
                "access_roles_str": ",".join(doc.access_roles),
                "lineage_json": json.dumps(doc.lineage),
            }
            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        self.last_indexed_at = datetime.now().isoformat()
        return len(documents)

    def query(
        self,
        query_text: str,
        n_results: int = 50,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against ChromaDB with optional metadata filtering.
        """
        count = self.collection.count()
        if count == 0:
            return []

        query_emb = local_embedder.embed_query(query_text)
        
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_emb],
            "n_results": min(n_results, count),
            "include": ["metadatas", "documents", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)

        items = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                items.append({
                    "id": ids[i],
                    "metadata": metas[i],
                    "document": docs[i],
                    "distance": distances[i],
                    "similarity": 1.0 - max(0.0, min(1.0, distances[i]))
                })

        return items

    def get_status(self) -> EvidenceStatus:
        """
        Returns the current state and document count of the vector database.
        """
        count = self.collection.count()
        return EvidenceStatus(
            vector_store_status="ONLINE" if count > 0 else "EMPTY_READY",
            document_count=count,
            embedding_model=local_embedder.model_name,
            embedding_dimension=384,
            indexed_sources=["customer_operations_events"],
            last_indexed_at=self.last_indexed_at,
            storage_path=self.persist_dir,
        )

    def clear(self):
        """
        Safely clears all documents by deleting all ids.
        """
        try:
            res = self.collection.get(include=[])
            if res and res.get("ids") and len(res["ids"]) > 0:
                self.collection.delete(ids=res["ids"])
        except Exception:
            pass

evidence_store = EvidenceStore()

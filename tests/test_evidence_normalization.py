import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.evidence.normalizer import evidence_normalizer
from app.evidence.chunker import evidence_chunker
from app.data.loader import data_loader

class TestEvidenceNormalization:

    def test_record_normalization(self):
        record = {
            "timestamp": "2026-08-25T14:30:00Z",
            "source": "SUPPORT_TICKET",
            "region": "EU",
            "product_id": None,
            "category": "Checkout",
            "issue_type": "PAYMENT_GATEWAY_TIMEOUT",
            "severity": "CRITICAL",
            "sensitivity": "PII_RESTRICTED",
            "text": "Customer Alice Brown alice@mail.com encountered payment timeout on step 3.",
            "sentiment": -0.9,
        }
        doc = evidence_normalizer.normalize_record(record, scenario_id="SCENARIO_1_MULTI_FACTOR", record_idx=1)
        
        assert doc.evidence_id.startswith("EVID-SUP-20260825-")
        assert doc.document_type == "SUPPORT_TICKET"
        assert doc.region == "EU"
        assert doc.severity == "CRITICAL"
        assert "conversion_rate" in doc.driver_tags
        assert "checkout" in doc.driver_tags
        assert "kpi_revenue" in doc.kpi_ids
        assert "kpi_conv_rate" in doc.kpi_ids
        # Verify PII is redacted
        assert "alice@mail.com" not in doc.text
        assert "[EMAIL_REDACTED]" in doc.text
        assert "[NAME_REDACTED]" in doc.text
        # Verify lineage
        assert doc.lineage["source_table"] == "customer_operations_events"
        assert doc.lineage["pii_masked"] is True

    def test_stockout_normalization_tags(self):
        record = {
            "timestamp": "2026-08-26T10:00:00Z",
            "source": "OPS_INCIDENT",
            "region": "NA",
            "product_id": "PROD_LAPTOP_01",
            "category": "Electronics",
            "issue_type": "STOCKOUT",
            "severity": "HIGH",
            "sensitivity": "INTERNAL_OPS",
            "text": "Warehouse NA East zero-inventory on flagship UltraBook Pro 15.",
            "sentiment": -0.8,
        }
        doc = evidence_normalizer.normalize_record(record, scenario_id="SCENARIO_1_MULTI_FACTOR", record_idx=2)
        
        assert "availability" in doc.driver_tags
        assert "product_mix" in doc.driver_tags
        assert "kpi_revenue" in doc.kpi_ids
        assert "kpi_aov" in doc.kpi_ids
        assert doc.product_id == "PROD_LAPTOP_01"

    def test_dataframe_normalization(self):
        _, _, ops_df, _ = data_loader.load_data("SCENARIO_1_MULTI_FACTOR")
        docs = evidence_normalizer.normalize_dataframe(ops_df, scenario_id="SCENARIO_1_MULTI_FACTOR")
        
        assert len(docs) == len(ops_df)
        assert all(d.evidence_id for d in docs)
        # Ensure all docs have masked text
        for d in docs:
            assert "@" not in d.text or "[EMAIL_REDACTED]" in d.text

    def test_chunking_short_document(self):
        record = {
            "timestamp": "2026-08-25T14:30:00Z",
            "source": "SUPPORT_TICKET",
            "issue_type": "STOCKOUT",
            "severity": "HIGH",
            "text": "Short log about laptop out of stock.",
        }
        doc = evidence_normalizer.normalize_record(record)
        chunks = evidence_chunker.chunk_document(doc)
        assert len(chunks) == 1
        assert chunks[0].evidence_id == doc.evidence_id

    def test_chunking_long_document(self):
        long_text = "This is sentence one. " * 40  # ~880 characters
        record = {
            "timestamp": "2026-08-25T14:30:00Z",
            "source": "OPS_INCIDENT",
            "issue_type": "PAYMENT_GATEWAY_TIMEOUT",
            "severity": "CRITICAL",
            "text": long_text,
        }
        doc = evidence_normalizer.normalize_record(record)
        chunks = evidence_chunker.chunk_document(doc)
        assert len(chunks) > 1
        assert all(c.lineage for c in chunks)
        assert all(c.evidence_id.startswith(doc.evidence_id) for c in chunks)

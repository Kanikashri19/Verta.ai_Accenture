import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

from app.evidence.models import EvidenceDocument
from app.evidence.pii import pii_masker

class EvidenceNormalizer:
    """
    Normalizes raw operational event records into structured, PII-masked EvidenceDocuments.
    Uses deterministic business rules for driver and KPI tagging.
    """

    # Deterministic driver tag mappings
    DRIVER_TAG_RULES = {
        "PAYMENT_GATEWAY_TIMEOUT": ["conversion_rate", "checkout", "payment", "gateway"],
        "STOCKOUT": ["volume", "availability", "product_mix", "aov", "inventory"],
        "CAMPAIGN_OUTAGE": ["traffic", "marketing", "sessions", "clicks"],
        "SHIPPING_SURCHARGE": ["cost", "margin", "gross_margin", "shipping", "freight"],
        "PRICING_ERROR": ["discount", "aov", "gross_margin", "pricing"],
        "GENERAL_INQUIRY": ["general", "feedback", "customer_service"],
    }

    # Deterministic KPI mappings
    KPI_MAPPING_RULES = {
        "PAYMENT_GATEWAY_TIMEOUT": ["kpi_revenue", "kpi_conv_rate", "kpi_orders"],
        "STOCKOUT": ["kpi_revenue", "kpi_orders", "kpi_aov"],
        "CAMPAIGN_OUTAGE": ["kpi_revenue", "kpi_orders", "kpi_conv_rate"],
        "SHIPPING_SURCHARGE": ["kpi_gross_margin", "kpi_revenue"],
        "PRICING_ERROR": ["kpi_revenue", "kpi_gross_margin", "kpi_aov"],
        "GENERAL_INQUIRY": ["kpi_revenue"],
    }

    @classmethod
    def normalize_record(
        cls,
        record: Dict[str, Any],
        scenario_id: str = "SCENARIO_1_MULTI_FACTOR",
        record_idx: int = 0
    ) -> EvidenceDocument:
        """
        Normalizes a single dictionary row into an EvidenceDocument.
        """
        ts_str = str(record.get("timestamp", datetime.now().isoformat()))
        if "T" in ts_str:
            date_str = ts_str.split("T")[0]
        else:
            date_str = ts_str[:10]

        issue_type = str(record.get("issue_type", "GENERAL_INQUIRY")).upper()
        source = str(record.get("source", "SUPPORT_TICKET")).upper()
        severity = str(record.get("severity", "MEDIUM")).upper()
        sensitivity = str(record.get("sensitivity", "INTERNAL_OPS")).upper()
        raw_text = str(record.get("text", ""))

        # 1. Mask PII deterministically
        masked_text = pii_masker.mask_text(raw_text)

        # 2. Generate deterministic evidence ID
        content_hash = hashlib.sha256(f"{ts_str}_{source}_{issue_type}_{record_idx}_{raw_text[:20]}".encode()).hexdigest()[:8]
        evidence_id = f"EVID-{source[:3]}-{date_str.replace('-', '')}-{content_hash}"

        # 3. Derive driver tags & KPI associations
        driver_tags = cls.DRIVER_TAG_RULES.get(issue_type, ["general"])
        kpi_ids = cls.KPI_MAPPING_RULES.get(issue_type, ["kpi_revenue"])

        # 4. Determine RBAC access roles
        if sensitivity == "PII_RESTRICTED":
            access_roles = ["ANALYST", "OPERATIONS"]
        else:
            access_roles = ["EXECUTIVE", "ANALYST", "OPERATIONS"]

        # 5. Build traceable lineage
        lineage = {
            "source_table": "customer_operations_events",
            "source_record_id": f"rec_{record_idx:05d}",
            "source_timestamp": ts_str,
            "ingested_at": datetime.now().isoformat(),
            "pii_masked": True,
        }

        return EvidenceDocument(
            evidence_id=evidence_id,
            document_type=source,
            timestamp=ts_str,
            date=date_str,
            source=source,
            region=record.get("region") if pd.notna(record.get("region")) else None,
            product_id=record.get("product_id") if pd.notna(record.get("product_id")) else None,
            category=str(record.get("category", "General")),
            issue_type=issue_type,
            severity=severity,
            sensitivity=sensitivity,
            text=masked_text,
            kpi_ids=kpi_ids,
            driver_tags=driver_tags,
            scenario_id=scenario_id,
            lineage=lineage,
            access_roles=access_roles,
        )

    @classmethod
    def normalize_dataframe(
        cls,
        df: pd.DataFrame,
        scenario_id: str = "SCENARIO_1_MULTI_FACTOR"
    ) -> List[EvidenceDocument]:
        """
        Normalizes an entire operational events DataFrame into EvidenceDocuments.
        """
        documents = []
        for idx, row in df.iterrows():
            doc = cls.normalize_record(row.to_dict(), scenario_id=scenario_id, record_idx=int(idx))
            documents.append(doc)
        return documents

evidence_normalizer = EvidenceNormalizer()

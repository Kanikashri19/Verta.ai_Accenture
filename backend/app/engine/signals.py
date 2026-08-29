import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.engine.models import OperationalSignal

class SignalEngine:
    """
    Consumes structured operational events (support tickets, SRE logs, incident reports).
    Extracts time-aligned supporting signals without asserting unverified causal claims.
    """

    @staticmethod
    def extract_signals(
        ops_df: pd.DataFrame,
        anomaly_start_iso: str,
        anomaly_end_iso: str,
        min_event_count: int = 1
    ) -> List[OperationalSignal]:
        """
        Extracts structured signals from the operations source within the anomaly window.
        """
        if ops_df.empty:
            return []

        # Filter by anomaly date window
        ops_df = ops_df.copy()
        # Parse timestamp dates
        ops_df["_event_date"] = ops_df["timestamp"].str.slice(0, 10)
        anom_events = ops_df[(ops_df["_event_date"] >= anomaly_start_iso) & (ops_df["_event_date"] <= anomaly_end_iso)]

        if anom_events.empty:
            return []

        signals = []
        # Group by issue type and dimensions
        grouped = anom_events.groupby(["issue_type", "source", "region", "product_id", "severity"], dropna=False)

        signal_idx = 0
        for (issue_type, source, region, product_id, severity), group in grouped:
            count = len(group)
            if count < min_event_count or issue_type == "GENERAL_INQUIRY":
                continue

            signal_idx += 1
            avg_sentiment = float(group["sentiment"].mean())
            sample_text = group["text"].iloc[0]

            # Non-causal explanatory description
            product_desc = f" for SKU '{product_id}'" if pd.notna(product_id) and product_id else ""
            region_desc = f" in region '{region}'" if pd.notna(region) and region else ""
            
            desc = (
                f"Observed {count} time-aligned {source} event(s) tagged with '{issue_type}'{product_desc}{region_desc}. "
                f"Severity: {severity}, Avg Sentiment: {avg_sentiment:.2f}."
            )

            signals.append(
                OperationalSignal(
                    signal_id=f"SIG-2026-{signal_idx:03d}",
                    issue_type=str(issue_type),
                    source_type=str(source),
                    region=str(region) if pd.notna(region) else None,
                    product_id=str(product_id) if pd.notna(product_id) else None,
                    category=str(group["category"].iloc[0]) if "category" in group.columns else None,
                    event_count=count,
                    severity=str(severity),
                    avg_sentiment=round(avg_sentiment, 2),
                    time_alignment=True,
                    description=desc,
                    signal_role="SUPPORTING_SIGNAL",
                )
            )

        # Sort signals by severity and count descending
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        signals.sort(key=lambda s: (severity_order.get(s.severity, 99), -s.event_count))
        return signals

signal_engine = SignalEngine()

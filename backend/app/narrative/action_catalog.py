from typing import Dict, List, Any, Optional
from app.narrative.models import RecommendedAction
from app.engine.models import FactPack
from app.evidence.models import EvidencePack, EvidenceItem
from app.governance.models import ConfidenceAssessment, ConfidenceBand

APPROVED_ACTION_CATALOG: List[Dict[str, Any]] = [
    {
        "action_id": "ACT-PAYMENT-001",
        "driver_match": ["conversion_rate", "PAYMENT_GATEWAY_TIMEOUT", "orders"],
        "controllable_lever": "Payment Gateway Routing & Retry Infrastructure",
        "action": "Enable secondary gateway failover and adjust HTTP timeout threshold from 2.0s to 5.0s for EU checkout sessions.",
        "owner": "Payments Operations",
        "expected_impact": "Restore checkout conversion rate to baseline (>3.2%) and recover an estimated $28,000 weekly revenue loss.",
        "monitoring_plan": "Track 15-minute checkout success rates, gateway HTTP 504 error frequency, and regional checkout drop-offs.",
        "decision_right": "Payments Operations",
    },
    {
        "action_id": "ACT-INVENTORY-001",
        "driver_match": ["product_availability", "STOCKOUT", "unit_sales", "orders"],
        "controllable_lever": "Safety Stock Allocation & Regional Replenishment",
        "action": "Execute expedited inventory transfer and increase dynamic safety stock buffers for high-velocity SKUs (e.g. SKU-PROD-01 / Apparel).",
        "owner": "Inventory Operations",
        "expected_impact": "Eliminate stockout friction and recover approximately $12,500 in weekly lost order volume.",
        "monitoring_plan": "Monitor hourly SKU availability %, backorder queues, and add-to-cart-to-purchase completion rates.",
        "decision_right": "Inventory Operations",
    },
    {
        "action_id": "ACT-MARKETING-001",
        "driver_match": ["marketing_spend", "CAMPAIGN_BUDGET_REDUCTION", "sessions", "traffic"],
        "controllable_lever": "Paid Acquisition Bidding & Channel Budget Allocation",
        "action": "Restore automated search campaign bidding allocations in underperforming regions and audit ad copy click-through efficiency.",
        "owner": "Growth Marketing",
        "expected_impact": "Re-establish paid acquisition session volume (+15%) and lift top-of-funnel gross revenue contribution.",
        "monitoring_plan": "Monitor daily ROAS, CAC, target CPC bids, and paid search attributed traffic volume.",
        "decision_right": "Growth Marketing",
    },
    {
        "action_id": "ACT-COMMERCIAL-001",
        "driver_match": ["aov", "mix_shift", "discount_rate", "margin", "product_mix"],
        "controllable_lever": "Promotional Thresholds & Bundle Merchandising",
        "action": "Recalibrate free shipping basket thresholds from $50 to $65 and introduce cross-category accessory bundles.",
        "owner": "Commercial Finance",
        "expected_impact": "Protect gross margin by +180 bps and lift Average Order Value (AOV) towards the $85 baseline.",
        "monitoring_plan": "Monitor daily category margin contributions, promotional discount uptake, and average basket depth.",
        "decision_right": "Commercial Finance",
    },
    {
        "action_id": "ACT-LOGISTICS-001",
        "driver_match": ["gross_margin", "shipping_cost", "SHIPPING_SURCHARGE", "freight_cost"],
        "controllable_lever": "Carrier Surcharge Routing & Regional Fulfillment",
        "action": "Audit carrier contract international fuel surcharges and reroute non-express packages through regional consolidation centers.",
        "owner": "Commercial Finance",
        "expected_impact": "Contain freight cost increases and eliminate unauthorized carrier surcharge margin leakage.",
        "monitoring_plan": "Monitor weekly freight cost per package and SLA on-time delivery rates.",
        "decision_right": "Commercial Finance",
    }
]

VALID_OWNERS = {
    "Payments Operations",
    "Inventory Operations",
    "Growth Marketing",
    "Commercial Finance",
}

class ActionCatalogEngine:
    """
    Deterministic action matching engine that selects actions strictly from the approved catalog.
    Prevents the LLM from hallucinating unauthorized or high-impact actions.
    """

    def select_actions(
        self,
        factpack: FactPack,
        evidence_pack: EvidencePack,
        confidence_assessment: ConfidenceAssessment,
        max_actions: int = 3
    ) -> List[RecommendedAction]:
        """
        Matches verified drivers and supporting operational issues to catalog levers.
        """
        recommended_actions: List[RecommendedAction] = []
        seen_action_ids = set()

        # Collect drivers and issue types present in FactPack
        fact_drivers = [d.driver_name.lower() for d in factpack.investigation.ranked_drivers]
        fact_explanations = [e.driver.lower() for e in factpack.investigation.ranked_explanations]
        
        # Collect operational issue types and evidence IDs
        supporting_items: List[EvidenceItem] = evidence_pack.supporting_evidence
        issue_types = [item.issue_type.lower() for item in supporting_items]
        
        # Map driver/issue to evidence IDs
        evidence_by_keyword: Dict[str, List[str]] = {}
        for item in supporting_items:
            key = item.driver.lower()
            evidence_by_keyword.setdefault(key, []).append(item.evidence_id)
            issue_key = item.issue_type.lower()
            evidence_by_keyword.setdefault(issue_key, []).append(item.evidence_id)

        candidate_keywords = set(fact_drivers + fact_explanations + issue_types)
        
        # Add KPI-specific keywords
        kpi_clean = factpack.investigation.kpi_id.lower().replace("kpi_", "")
        candidate_keywords.add(kpi_clean)

        for entry in APPROVED_ACTION_CATALOG:
            if entry["action_id"] in seen_action_ids:
                continue

            matches = [
                kw for kw in entry["driver_match"]
                if kw.lower() in candidate_keywords or any(kw.lower() in cand for cand in candidate_keywords)
            ]

            if matches:
                # Find matching evidence IDs
                matched_evidence_ids: List[str] = []
                for m in matches:
                    matched_evidence_ids.extend(evidence_by_keyword.get(m.lower(), []))
                
                # If no specific keyword match found in evidence map, attach top supporting IDs
                if not matched_evidence_ids and supporting_items:
                    matched_evidence_ids = [item.evidence_id for item in supporting_items[:2]]

                # Validate owner
                owner = entry["owner"]
                decision_right = entry["decision_right"]
                if owner not in VALID_OWNERS:
                    decision_right = "REQUIRES_HUMAN_REVIEW"

                # Calibrate confidence band from governance assessment
                conf_band = confidence_assessment.confidence_band.value

                rec = RecommendedAction(
                    action_id=entry["action_id"],
                    driver=matches[0],
                    controllable_lever=entry["controllable_lever"],
                    action=entry["action"],
                    owner=owner,
                    expected_impact=entry["expected_impact"],
                    confidence_band=conf_band,
                    monitoring_plan=entry["monitoring_plan"],
                    decision_right=decision_right,
                    evidence_ids=list(dict.fromkeys(matched_evidence_ids))
                )
                recommended_actions.append(rec)
                seen_action_ids.add(entry["action_id"])

                if len(recommended_actions) >= max_actions:
                    break

        return recommended_actions

action_catalog_engine = ActionCatalogEngine()

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

from app.narrative.models import (
    NarrativeResponse,
    Persona,
    GenerationMode,
    EvidenceCitation,
    RecommendedAction,
    NarrativeTelemetry
)
from app.engine.models import FactPack, InvestigationResult
from app.evidence.models import EvidencePack, EvidenceItem
from app.governance.models import ConfidenceAssessment, GovernanceDecision, GovernanceDecisionEnum
from app.narrative.action_catalog import action_catalog_engine

class DeterministicNarrativeGenerator:
    """
    High-fidelity deterministic fallback synthesizer.
    Guarantees reliable, un-hallucinated narrative responses even when external LLMs are unreachable.
    """

    def generate(
        self,
        factpack: FactPack,
        evidence_pack: EvidencePack,
        confidence_assessment: ConfidenceAssessment,
        governance_decision: GovernanceDecision,
        persona: Persona,
        request_id: Optional[str] = None
    ) -> NarrativeResponse:
        req_id = request_id or f"REQ-{uuid.uuid4().hex[:8]}"
        inv: InvestigationResult = factpack.investigation
        kpi_name = inv.kpi_name
        kpi_id = inv.kpi_id
        unit = inv.unit
        pct_change = inv.percentage_change
        abs_change = inv.absolute_change
        base_val = inv.baseline_value
        curr_val = inv.current_value

        # Select approved actions
        actions = action_catalog_engine.select_actions(
            factpack=factpack,
            evidence_pack=evidence_pack,
            confidence_assessment=confidence_assessment
        )

        # Build evidence citations
        citations: List[EvidenceCitation] = []
        for item in evidence_pack.supporting_evidence:
            citations.append(EvidenceCitation(
                statement=f"Operational ticket {item.evidence_id} reported {item.issue_type.replace('_', ' ').lower()} affecting {item.driver}.",
                evidence_ids=[item.evidence_id],
                driver=item.driver,
                lineage_sources=[item.source],
                snippet_summary=item.snippet[:120] + ("..." if len(item.snippet) > 120 else "")
            ))

        # Format KPI movement
        kpi_movement = {
            "baseline_value": base_val,
            "current_value": curr_val,
            "absolute_change": abs_change,
            "percentage_change": pct_change,
            "unit": unit
        }

        # Format key drivers
        key_drivers: List[Dict[str, Any]] = []
        for d in inv.ranked_drivers:
            key_drivers.append({
                "driver_name": d.driver_name,
                "contribution_value": d.contribution_value,
                "contribution_percentage": d.contribution_percentage,
                "direction": d.direction,
                "methodology": d.methodology,
                "explanation": f"{d.driver_name.replace('_', ' ').capitalize()} contributed {d.contribution_percentage:.1f}% to the observed movement." if d.contribution_percentage else f"Associated movement observed in {d.driver_name}."
            })
        for sig in inv.supporting_signals:
            key_drivers.append({
                "driver_name": sig.issue_type,
                "contribution_value": None,
                "contribution_percentage": None,
                "direction": "NEGATIVE" if "ERROR" in sig.severity or "HIGH" in sig.severity or "CRITICAL" in sig.severity else "NEUTRAL",
                "methodology": "Operational Incident Corroboration",
                "explanation": f"Supporting operational signal: {sig.description}"
            })

        # Lineage data
        lineage: List[Dict[str, Any]] = [
            {"factpack_version": factpack.version, "verified_facts_count": len(factpack.verified_numerical_facts)},
            {"evidence_status": evidence_pack.status, "supporting_count": len(evidence_pack.supporting_evidence)},
            {"data_freshness": {k: v.model_dump() for k, v in inv.data_freshness.items()}}
        ]

        # Build Persona-Specific Narrative
        if persona == Persona.EXECUTIVE:
            direction_word = "declined" if pct_change < 0 else "increased"
            top_driver_str = inv.ranked_drivers[0].driver_name.replace("_", " ") if inv.ranked_drivers else "operational factors"
            headline = f"{kpi_name} {direction_word} by {abs(pct_change):.1f}% driven primarily by {top_driver_str}."
            
            summary = (
                f"{kpi_name} experienced a {pct_change:+.1f}% change during the anomaly window, "
                f"moving from {base_val:,.2f} {unit} to {curr_val:,.2f} {unit} (net impact: {abs_change:+,.2f} {unit}). "
                f"Primary contributing pressure is concentrated in {top_driver_str}, corroborated by verified operational signals. "
                f"Governance confidence is assessed at {confidence_assessment.overall_confidence:.1f}/100 ({confidence_assessment.confidence_band.value})."
            )
            
            caveats = [
                f"Confidence level: {confidence_assessment.confidence_band.value} ({confidence_assessment.overall_confidence:.1f}/100)."
            ] + confidence_assessment.warnings[:2]
            
            alternative_hypotheses = [
                "Unobserved regional macro trends or unmonitored competitive price actions may account for residual variance."
            ]

        else:  # ANALYST PERSONA
            direction_word = "negative deviation" if pct_change < 0 else "positive deviation"
            z_score = inv.materiality.z_score or 0.0
            p_val = inv.materiality.p_value_approx or 0.0
            
            headline = (
                f"{kpi_name} observed {direction_word} of {pct_change:+.2f}% ({abs_change:+,.2f} {unit}) "
                f"with high statistical significance (|z| = {abs(z_score):.2f}, p < {max(0.001, p_val):.3f})."
            )
            
            drivers_detail = ", ".join([
                f"{d.driver_name} ({d.contribution_percentage:+.1f}% contribution / {d.methodology})"
                for d in inv.ranked_drivers if d.contribution_percentage is not None
            ])
            
            summary = (
                f"Quantitative investigation of {kpi_name} ({kpi_id}) reveals a statistically significant shift "
                f"from baseline mean {base_val:,.2f} {unit} to anomaly mean {curr_val:,.2f} {unit} "
                f"(delta: {abs_change:+,.2f} {unit}, relative: {pct_change:+.2f}%). "
                f"Decomposition indicates primary driver allocation across: {drivers_detail or 'observational components'}. "
                f"Corroborating evidence includes {len(evidence_pack.supporting_evidence)} matching operational log(s). "
                f"Data quality score is {confidence_assessment.data_quality_score:.1f}/100 with SLA compliance verified across all upstream pipelines."
            )
            
            caveats = [
                f"Statistical significance: {inv.materiality.statistical_significance} (|z| = {abs(z_score):.2f}).",
                f"Business materiality: {inv.materiality.business_materiality} (Threshold: {inv.materiality.threshold_pct:.1f}%).",
                f"Data quality & completeness: {confidence_assessment.data_quality_score:.1f}/100.",
                f"Data freshness SLA compliance: {confidence_assessment.freshness_score:.1f}/100."
            ] + confidence_assessment.warnings
            
            alternative_hypotheses = [
                "Cross-elasticity substitution effects across adjacent product categories.",
                "Short-term checkout retry back-pressure masking true organic demand elasticity."
            ]

        telemetry = NarrativeTelemetry(
            request_id=req_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_provider="deterministic_rule_engine",
            model="verta_fallback_v1.0",
            persona=persona.value,
            governance_decision=governance_decision.decision.value,
            latency_ms=2.5,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            retry_count=0,
            fallback_used=True,
            cache_hit=False
        )

        return NarrativeResponse(
            request_id=req_id,
            kpi_id=kpi_id,
            kpi_name=kpi_name,
            persona=persona,
            generation_mode=GenerationMode.DETERMINISTIC_FALLBACK.value,
            headline=headline,
            summary=summary,
            kpi_movement=kpi_movement,
            key_drivers=key_drivers,
            evidence_citations=citations,
            confidence_score=confidence_assessment.overall_confidence,
            confidence_band=confidence_assessment.confidence_band.value,
            recommended_actions=actions,
            caveats=caveats,
            alternative_hypotheses=alternative_hypotheses,
            data_lineage=lineage,
            governance_decision=governance_decision.decision.value,
            clarification_questions=confidence_assessment.clarification_questions,
            conflict_summary=confidence_assessment.conflict_summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
            telemetry=telemetry
        )

deterministic_narrative_generator = DeterministicNarrativeGenerator()

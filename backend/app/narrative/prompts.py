import json
from typing import Dict, Any, List
from app.narrative.models import Persona
from app.engine.models import FactPack
from app.evidence.models import EvidencePack
from app.governance.models import ConfidenceAssessment, GovernanceDecision

SYSTEM_FACTUALITY_GUARDRAIL = """You are a narrative synthesis system for Verta.ai.
The supplied FactPack and EvidencePack are the only source of quantitative truth.
Do not invent metrics.
Do not recalculate metrics.
Do not introduce drivers not present in the supplied context.
Do not claim causality unless the supplied analysis explicitly supports causal inference.
Use supporting evidence as evidence, not proof of causality.
If evidence is contradictory or insufficient, communicate uncertainty.

Return ONLY a valid JSON object matching the requested schema without markdown formatting or code blocks."""

EXECUTIVE_PROMPT_TEMPLATE = """Synthesize an EXECUTIVE narrative for KPI: {kpi_name} ({kpi_id}).

Governance Decision: {governance_decision}
Confidence Score: {confidence_score}/100 ({confidence_band})
Caveat/Caution Required: {caution_required}

=== VERIFIED FACTPACK (READ-ONLY) ===
{factpack_json}

=== VERIFIED EVIDENCEPACK (READ-ONLY) ===
{evidencepack_json}

=== CONFIDENCE & GOVERNANCE ===
{governance_json}

=== APPROVED ACTIONS TO CONSIDER ===
{approved_actions_json}

EXECUTIVE REQUIREMENTS:
1. Headline: Concise, high-level business takeaway (< 15 words).
2. Summary: 2-3 sentence executive synthesis explaining what moved, why it matters, and top drivers.
3. Keep focus on business impact, top drivers, and strategic actions.
4. Omit deep mathematical formulas, z-score derivations, or raw SQL details.
5. Emphasize confidence level and key business risks.
6. Provide citations to real evidence_ids present in the context.

JSON SCHEMA TO RETURN:
{{
  "headline": "string",
  "summary": "string",
  "kpi_movement": {{
    "baseline_value": float,
    "current_value": float,
    "absolute_change": float,
    "percentage_change": float,
    "unit": "string"
  }},
  "key_drivers": [
    {{
      "driver_name": "string",
      "contribution_value": float or null,
      "contribution_percentage": float or null,
      "direction": "NEGATIVE" or "POSITIVE",
      "explanation": "string"
    }}
  ],
  "evidence_citations": [
    {{
      "statement": "string",
      "evidence_ids": ["string"],
      "driver": "string",
      "snippet_summary": "string"
    }}
  ],
  "caveats": ["string"],
  "alternative_hypotheses": ["string"]
}}
"""

ANALYST_PROMPT_TEMPLATE = """Synthesize a detailed ANALYST narrative for KPI: {kpi_name} ({kpi_id}).

Governance Decision: {governance_decision}
Confidence Score: {confidence_score}/100 ({confidence_band})
Caution Required: {caution_required}

=== VERIFIED FACTPACK (READ-ONLY) ===
{factpack_json}

=== VERIFIED EVIDENCEPACK (READ-ONLY) ===
{evidencepack_json}

=== CONFIDENCE & GOVERNANCE ===
{governance_json}

=== APPROVED ACTIONS TO CONSIDER ===
{approved_actions_json}

ANALYST REQUIREMENTS:
1. Headline: Detailed technical finding with exact percentage movement and primary driver.
2. Summary: Comprehensive analytical breakdown covering baseline distribution, anomaly window, statistical significance, and decomposed drivers.
3. Quantified Drivers: Report exact dollar and percentage contributions and analytical methods.
4. Statistical & Quality Lineage: Detail z-score, p-value approximation, sample sizes, and data source SLA freshness.
5. Evidence & Citations: Connect each identified driver to specific supporting/contradictory evidence_ids and source logs.
6. Alternative Hypotheses & Data Caveats: Enumerate technical caveats, variance limitations, or residual effects.

JSON SCHEMA TO RETURN:
{{
  "headline": "string",
  "summary": "string",
  "kpi_movement": {{
    "baseline_value": float,
    "current_value": float,
    "absolute_change": float,
    "percentage_change": float,
    "unit": "string"
  }},
  "key_drivers": [
    {{
      "driver_name": "string",
      "contribution_value": float or null,
      "contribution_percentage": float or null,
      "direction": "NEGATIVE" or "POSITIVE",
      "explanation": "string"
    }}
  ],
  "evidence_citations": [
    {{
      "statement": "string",
      "evidence_ids": ["string"],
      "driver": "string",
      "snippet_summary": "string"
    }}
  ],
  "caveats": ["string"],
  "alternative_hypotheses": ["string"]
}}
"""

def build_prompt_context(
    factpack: FactPack,
    evidence_pack: EvidencePack,
    confidence_assessment: ConfidenceAssessment,
    governance_decision: GovernanceDecision,
    approved_actions: List[Dict[str, Any]],
    persona: Persona
) -> Dict[str, str]:
    """
    Constructs safe, read-only JSON context strings for LLM prompt interpolation.
    """
    factpack_dict = factpack.model_dump()
    evidence_dict = evidence_pack.model_dump()
    governance_dict = {
        "overall_confidence": confidence_assessment.overall_confidence,
        "confidence_band": confidence_assessment.confidence_band.value,
        "decision": governance_decision.decision.value,
        "reasons": confidence_assessment.reasons,
        "warnings": confidence_assessment.warnings,
        "allowed_actions": governance_decision.allowed_actions,
        "blocked_actions": governance_decision.blocked_actions,
    }

    caution_required = governance_decision.decision.value == "PROCEED_WITH_CAUTION"

    template = EXECUTIVE_PROMPT_TEMPLATE if persona == Persona.EXECUTIVE else ANALYST_PROMPT_TEMPLATE
    
    prompt = template.format(
        kpi_name=factpack.investigation.kpi_name,
        kpi_id=factpack.investigation.kpi_id,
        governance_decision=governance_decision.decision.value,
        confidence_score=confidence_assessment.overall_confidence,
        confidence_band=confidence_assessment.confidence_band.value,
        caution_required=caution_required,
        factpack_json=json.dumps(factpack_dict, indent=2),
        evidencepack_json=json.dumps(evidence_dict, indent=2),
        governance_json=json.dumps(governance_dict, indent=2),
        approved_actions_json=json.dumps(approved_actions, indent=2)
    )

    return {
        "system_prompt": SYSTEM_FACTUALITY_GUARDRAIL,
        "user_prompt": prompt
    }

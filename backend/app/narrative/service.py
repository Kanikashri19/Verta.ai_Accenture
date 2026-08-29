import uuid
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

from app.narrative.models import (
    NarrativeResponse,
    NarrativeRequest,
    Persona,
    GenerationMode,
    EvidenceCitation,
    RecommendedAction,
    NarrativeTelemetry
)
from app.engine.models import FactPack, InvestigationResult
from app.engine.investigation import investigation_engine
from app.evidence.service import evidence_service
from app.governance.service import governance_service
from app.governance.models import ConfidenceBand, GovernanceDecisionEnum, ConfidenceAssessment, GovernanceDecision
from app.narrative.action_catalog import action_catalog_engine
from app.narrative.gateway import llm_gateway
from app.narrative.prompts import build_prompt_context
from app.narrative.fallback import deterministic_narrative_generator
from app.narrative.cache import narrative_cache

logger = logging.getLogger(__name__)

class NarrativeService:
    """
    Main orchestration service for governed narrative synthesis and action recommendations.
    Strictly enforces Phase 5 governance circuit breakers and RBAC security boundaries.
    """

    def __init__(self):
        self._telemetry_log: List[NarrativeTelemetry] = []

    def assess_and_generate_narrative(
        self,
        kpi_id: str,
        scenario_id: str = "SCENARIO_1_MULTI_FACTOR",
        persona: Persona = Persona.EXECUTIVE,
        user_role: str = "ANALYST",
        force_refresh: bool = False
    ) -> NarrativeResponse:
        req_id = f"REQ-{uuid.uuid4().hex[:8]}"

        # Step 1: Execute deterministic governance assessment (Phases 3-5)
        assessment, decision = governance_service.assess_kpi(
            kpi_id=kpi_id,
            scenario_id=scenario_id,
            user_role=user_role
        )

        factpack = investigation_engine.get_factpack(kpi_id, scenario_id)
        evidence_pack = evidence_service.get_evidence_for_factpack(factpack, user_role=user_role)

        # Step 2: STRICT GOVERNANCE CIRCUIT BREAKER CHECK
        # If governance dictates ABSTAIN or REQUEST_CLARIFICATION, NEVER call LLM for causal narrative
        if decision.decision in [GovernanceDecisionEnum.ABSTAIN, GovernanceDecisionEnum.REQUEST_CLARIFICATION]:
            logger.info(f"Governance circuit breaker active ({decision.decision.value}) for {kpi_id}. Bypassing LLM generation.")
            return self._build_governance_abstention_response(
                req_id=req_id,
                factpack=factpack,
                assessment=assessment,
                decision=decision,
                persona=persona
            )

        # Step 3: Compute deterministic cache key & check cache
        inv_data = factpack.investigation
        factpack_key = f"{inv_data.kpi_id}:{inv_data.scenario_id}:{inv_data.percentage_change:.4f}:{inv_data.current_value:.4f}:{len(inv_data.ranked_drivers)}"
        evidence_key = f"{evidence_pack.kpi_id}:{evidence_pack.status}:{len(evidence_pack.supporting_evidence)}:{[e.evidence_id for e in evidence_pack.supporting_evidence]}"
        factpack_hash = hashlib.sha256(factpack_key.encode("utf-8")).hexdigest()
        evidencepack_hash = hashlib.sha256(evidence_key.encode("utf-8")).hexdigest()
        cache_key = narrative_cache.compute_cache_key(
            factpack_hash=factpack_hash,
            evidencepack_hash=evidencepack_hash,
            governance_decision=decision.decision.value,
            persona=persona,
            model=llm_gateway.model
        )

        if not force_refresh:
            cached_resp = narrative_cache.get(cache_key)
            if cached_resp is not None:
                # Mark cache hit in telemetry
                if cached_resp.telemetry:
                    cached_resp.telemetry.cache_hit = True
                return cached_resp

        # Step 4: Select approved actions
        approved_actions = action_catalog_engine.select_actions(
            factpack=factpack,
            evidence_pack=evidence_pack,
            confidence_assessment=assessment
        )
        approved_actions_dict = [a.model_dump() for a in approved_actions]

        # Step 5: Attempt LLM generation with fallback
        try:
            prompt_context = build_prompt_context(
                factpack=factpack,
                evidence_pack=evidence_pack,
                confidence_assessment=assessment,
                governance_decision=decision,
                approved_actions=approved_actions_dict,
                persona=persona
            )

            raw_json, telemetry_data = llm_gateway.generate_completion(
                system_prompt=prompt_context["system_prompt"],
                user_prompt=prompt_context["user_prompt"]
            )

            # Validate real evidence citation IDs (no hallucinated IDs permitted)
            valid_evidence_ids = {item.evidence_id for item in evidence_pack.supporting_evidence + evidence_pack.contradictory_evidence}
            sanitized_citations: List[EvidenceCitation] = []
            for cit in raw_json.get("evidence_citations", []):
                cleaned_ids = [eid for eid in cit.get("evidence_ids", []) if eid in valid_evidence_ids]
                if cleaned_ids:
                    sanitized_citations.append(EvidenceCitation(
                        statement=cit.get("statement", ""),
                        evidence_ids=cleaned_ids,
                        driver=cit.get("driver"),
                        snippet_summary=cit.get("snippet_summary")
                    ))

            # Build structured NarrativeResponse
            mode = GenerationMode.MOCK_LLM.value if llm_gateway.provider == "mock" else GenerationMode.LLM_DIRECT.value

            telemetry = NarrativeTelemetry(
                request_id=req_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_provider=telemetry_data["model_provider"],
                model=telemetry_data["model"],
                persona=persona.value,
                governance_decision=decision.decision.value,
                latency_ms=telemetry_data["latency_ms"],
                input_tokens=telemetry_data.get("input_tokens"),
                output_tokens=telemetry_data.get("output_tokens"),
                total_tokens=telemetry_data.get("total_tokens"),
                estimated_cost=telemetry_data.get("estimated_cost"),
                retry_count=telemetry_data.get("retry_count", 0),
                fallback_used=False,
                cache_hit=False
            )
            self._telemetry_log.append(telemetry)

            narrative_resp = NarrativeResponse(
                request_id=req_id,
                kpi_id=factpack.investigation.kpi_id,
                kpi_name=factpack.investigation.kpi_name,
                persona=persona,
                generation_mode=mode,
                headline=raw_json.get("headline", ""),
                summary=raw_json.get("summary", ""),
                kpi_movement=raw_json.get("kpi_movement", {
                    "baseline_value": factpack.investigation.baseline_value,
                    "current_value": factpack.investigation.current_value,
                    "absolute_change": factpack.investigation.absolute_change,
                    "percentage_change": factpack.investigation.percentage_change,
                    "unit": factpack.investigation.unit
                }),
                key_drivers=raw_json.get("key_drivers", []),
                evidence_citations=sanitized_citations,
                confidence_score=assessment.overall_confidence,
                confidence_band=assessment.confidence_band.value,
                recommended_actions=approved_actions,
                caveats=raw_json.get("caveats", []) + assessment.warnings,
                alternative_hypotheses=raw_json.get("alternative_hypotheses", []),
                data_lineage=[
                    {"factpack_version": factpack.version},
                    {"evidence_status": evidence_pack.status}
                ],
                governance_decision=decision.decision.value,
                clarification_questions=assessment.clarification_questions,
                conflict_summary=assessment.conflict_summary,
                generated_at=datetime.now(timezone.utc).isoformat(),
                telemetry=telemetry
            )

            narrative_cache.set(cache_key, narrative_resp)
            return narrative_resp

        except Exception as e:
            logger.warning(f"LLM generation failed ({e}); invoking deterministic fallback synthesizer.")
            fallback_resp = deterministic_narrative_generator.generate(
                factpack=factpack,
                evidence_pack=evidence_pack,
                confidence_assessment=assessment,
                governance_decision=decision,
                persona=persona,
                request_id=req_id
            )
            if fallback_resp.telemetry:
                self._telemetry_log.append(fallback_resp.telemetry)
            narrative_cache.set(cache_key, fallback_resp)
            return fallback_resp

    def _build_governance_abstention_response(
        self,
        req_id: str,
        factpack: FactPack,
        assessment: ConfidenceAssessment,
        decision: GovernanceDecision,
        persona: Persona
    ) -> NarrativeResponse:
        """
        Constructs a legally compliant, deterministic abstention/clarification response.
        Zero LLM hallucination or unsupported causal narrative.
        """
        inv = factpack.investigation
        is_contradictory = decision.decision == GovernanceDecisionEnum.ABSTAIN and assessment.contradiction_penalty > 0
        
        if is_contradictory:
            headline = f"Abstention: Contradictory operational evidence detected for {inv.kpi_name}."
            summary = (
                f"The system cannot synthesize a causal narrative for {inv.kpi_name} ({inv.kpi_id}). "
                f"{assessment.conflict_summary or 'Operational evidence directly contradicts quantitative driver models.'} "
                f"Governance decision: ABSTAIN (Confidence: {assessment.overall_confidence:.1f}/100)."
            )
        else:
            headline = f"Clarification Required: Insufficient baseline history or uncorroborated evidence for {inv.kpi_name}."
            summary = (
                f"The system has paused autonomous narrative generation for {inv.kpi_name} ({inv.kpi_id}) "
                f"due to low confidence ({assessment.overall_confidence:.1f}/100, {assessment.confidence_band.value}). "
                f"Reason: {assessment.reasons[0] if assessment.reasons else 'Insufficient historical baseline data.'}."
            )

        telemetry = NarrativeTelemetry(
            request_id=req_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_provider="governance_circuit_breaker",
            model="deterministic_policy_v1.0",
            persona=persona.value,
            governance_decision=decision.decision.value,
            latency_ms=1.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            retry_count=0,
            fallback_used=True,
            cache_hit=False
        )
        self._telemetry_log.append(telemetry)

        return NarrativeResponse(
            request_id=req_id,
            kpi_id=inv.kpi_id,
            kpi_name=inv.kpi_name,
            persona=persona,
            generation_mode=GenerationMode.DETERMINISTIC_FALLBACK.value,
            headline=headline,
            summary=summary,
            kpi_movement={
                "baseline_value": inv.baseline_value,
                "current_value": inv.current_value,
                "absolute_change": inv.absolute_change,
                "percentage_change": inv.percentage_change,
                "unit": inv.unit
            },
            key_drivers=[],
            evidence_citations=[],
            confidence_score=assessment.overall_confidence,
            confidence_band=assessment.confidence_band.value,
            recommended_actions=[],  # Blocked actions
            caveats=assessment.warnings + [f"Reason codes: {', '.join(decision.reason_codes)}"],
            alternative_hypotheses=[],
            data_lineage=[{"factpack_version": factpack.version}],
            governance_decision=decision.decision.value,
            clarification_questions=assessment.clarification_questions,
            conflict_summary=assessment.conflict_summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
            telemetry=telemetry
        )

    def get_telemetry(self) -> List[Dict[str, Any]]:
        return [t.model_dump() for t in self._telemetry_log[-50:]]

narrative_service = NarrativeService()

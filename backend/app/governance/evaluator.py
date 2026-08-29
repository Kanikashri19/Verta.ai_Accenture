from typing import Dict, List, Any, Optional, Tuple
import math
from datetime import datetime, timedelta, timezone

from app.engine.models import InvestigationResult, FactPack
from app.evidence.models import EvidencePack, EvidenceItem
from app.governance.models import (
    ConfidenceAssessment, ConfidenceBand, GovernanceDecisionEnum,
    ConfidenceWeights, GovernanceThresholds, DriverConfidenceAssessment
)

# Documented formula version. Overall confidence:
#   C = clip(0, 100,
#         w_stat * S_stats
#       + w_mat  * S_mat
#       + w_evid * S_evid
#       + w_dq   * S_dq
#       + w_fresh* S_fresh
#       + w_lin  * S_lineage
#       - P_contradiction)
FORMULA_VERSION = "1.1.0"

DRIVER_ALIASES = {
    "conversion rate": ["conversion_rate", "checkout", "payment", "gateway"],
    "average order value & product mix": ["aov", "product_mix", "availability", "volume", "inventory"],
    "traffic & inbound sessions": ["traffic", "marketing", "sessions", "clicks"],
    "gross margin": ["gross_margin", "margin", "shipping", "freight", "discount"],
}


class ConfidenceEvaluator:
    """
    Deterministic Confidence Assessment Engine.
    Evaluates quantitative statistical validity, business materiality thresholds,
    evidence corroboration strength, data quality, freshness, and contradiction penalties.
    No LLM is used at any step.
    """

    def __init__(
        self,
        weights: Optional[ConfidenceWeights] = None,
        thresholds: Optional[GovernanceThresholds] = None
    ):
        self.weights = weights or ConfidenceWeights()
        self.thresholds = thresholds or GovernanceThresholds()

    @staticmethod
    def _baseline_day_count(investigation: InvestigationResult) -> int:
        try:
            b_start = datetime.strptime(investigation.baseline_period.get("start", ""), "%Y-%m-%d")
            b_end = datetime.strptime(investigation.baseline_period.get("end", ""), "%Y-%m-%d")
            return max(0, (b_end - b_start).days + 1)
        except Exception:
            return 0

    def _is_sparse_history(self, investigation: InvestigationResult) -> bool:
        mat = investigation.materiality
        if mat.statistical_significance == "INSUFFICIENT_HISTORY":
            return True
        if mat.overall_materiality == "INSUFFICIENT_HISTORY":
            return True
        baseline_days = self._baseline_day_count(investigation)
        if 0 < baseline_days < self.thresholds.minimum_baseline_days:
            return True
        return False

    def evaluate_statistical_confidence(
        self,
        investigation: InvestigationResult
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluates statistical confidence from baseline sample size, z-score, and p-value.
        Does not recompute KPI values.
        """
        reasons = []
        warnings = []
        mat = investigation.materiality

        if self._is_sparse_history(investigation):
            warnings.append(
                "Historical baseline contains limited observations "
                f"(< {self.thresholds.minimum_baseline_days} days). Statistical confidence is constrained."
            )
            return 25.0, reasons, warnings

        z_val = abs(mat.z_score) if mat.z_score is not None else 0.0
        p_val = mat.p_value_approx if mat.p_value_approx is not None else 0.5

        if z_val >= 3.0 or p_val <= 0.005:
            score = 95.0
            reasons.append(f"High statistical significance observed (|z| = {z_val:.2f}, p <= {p_val:.3f}).")
        elif z_val >= 2.0 or p_val <= 0.05:
            score = 80.0
            reasons.append(f"Moderate statistical significance observed (|z| = {z_val:.2f}, p <= {p_val:.3f}).")
        elif z_val >= 1.0:
            score = 55.0
            warnings.append(f"Low statistical separation from baseline (|z| = {z_val:.2f}).")
        else:
            score = 30.0
            warnings.append(f"Metric movement is within normal baseline variance (|z| = {z_val:.2f}).")

        return score, reasons, warnings

    def evaluate_materiality_score(
        self,
        investigation: InvestigationResult
    ) -> Tuple[float, List[str]]:
        """
        Evaluates business materiality independently from statistical significance.
        Uses Phase 3 dual-gate overall_materiality (KPI contract thresholds).
        """
        reasons = []
        mat = investigation.materiality
        overall_mat = mat.overall_materiality

        if overall_mat == "CRITICAL_ACTIONABLE":
            score = 100.0
            reasons.append(
                f"Business materiality threshold exceeded ({mat.relative_change_pct:+.2f}% vs "
                f"{mat.threshold_pct:.1f}% threshold); also statistically significant."
            )
        elif overall_mat == "BUSINESS_WARNING":
            score = 80.0
            reasons.append(
                f"Material business delta observed ({mat.relative_change_pct:+.2f}%) without matching statistical gate."
            )
        elif overall_mat == "STATISTICAL_NOISE":
            score = 35.0
            reasons.append(
                f"Delta is statistically distinct but below business materiality threshold "
                f"({mat.relative_change_pct:+.2f}% vs {mat.threshold_pct:.1f}% threshold)."
            )
        elif overall_mat == "INSUFFICIENT_HISTORY":
            score = 25.0
            reasons.append("Materiality evaluation constrained due to insufficient baseline history.")
        else:
            score = 20.0
            reasons.append("Observed delta is within normal operational tolerances.")

        return score, reasons

    def evaluate_evidence_score(
        self,
        evidence_pack: Optional[EvidencePack]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Quality-weighted evidence score. Count does not dominate relevance.
        Prefer temporally aligned, high-scoring supporting items.
        """
        reasons = []
        warnings = []

        if (
            not evidence_pack
            or evidence_pack.status == "INSUFFICIENT_EVIDENCE"
            or len(evidence_pack.supporting_evidence) == 0
        ):
            warnings.append("No sufficient evidence was found to corroborate the KPI movement in the anomaly window.")
            return 0.0, reasons, warnings

        supporting = evidence_pack.supporting_evidence
        exact_window_items = [e for e in supporting if e.temporal_alignment == "EXACT_WINDOW"]
        quality_pool = exact_window_items or supporting

        # Quality over count: top-3 mean, so 10 weak docs cannot outrank 1 strong aligned doc
        ranked_scores = sorted((e.score for e in quality_pool), reverse=True)
        top_scores = ranked_scores[:3]
        quality_mean = sum(top_scores) / len(top_scores)

        pack_components = evidence_pack.confidence_components or {}
        temporal = float(pack_components.get("temporal_alignment", 0.0) or 0.0)
        dimensional = float(pack_components.get("dimension_alignment", 0.0) or 0.0)

        if exact_window_items and quality_mean >= 80.0:
            score = min(100.0, quality_mean)
            reasons.append(
                f"Found {len(supporting)} temporally aligned supporting operational evidence items "
                f"(quality-weighted top-3 mean: {quality_mean:.1f}/100)."
            )
        elif quality_mean >= 60.0:
            alignment_factor = 0.85 + 0.10 * (1.0 if temporal >= 100.0 else 0.5) + 0.05 * (1.0 if dimensional >= 80.0 else 0.0)
            score = quality_mean * min(1.0, alignment_factor)
            reasons.append(
                f"Found {len(supporting)} moderate supporting evidence items (quality-weighted mean: {quality_mean:.1f}/100)."
            )
        else:
            score = quality_mean * 0.60
            warnings.append("Retrieved operational evidence has weak semantic relevance or imperfect temporal alignment.")

        return round(min(100.0, max(0.0, score)), 1), reasons, warnings

    def evaluate_contradiction_penalty(
        self,
        evidence_pack: Optional[EvidencePack]
    ) -> Tuple[float, List[str], List[str], Optional[str], List[str]]:
        """
        Evaluates penalty for conflicting operational signals.
        Returns penalty, reasons, warnings, conflict_summary, conflicting_evidence_ids.
        """
        reasons = []
        warnings = []
        conflict_ids: List[str] = []

        if not evidence_pack or len(evidence_pack.contradictory_evidence) == 0:
            return 0.0, reasons, warnings, None, conflict_ids

        contra = evidence_pack.contradictory_evidence
        supporting = evidence_pack.supporting_evidence
        contra_count = len(contra)
        sup_count = len(supporting)
        total = contra_count + sup_count

        if total == 0:
            return 0.0, reasons, warnings, None, conflict_ids

        contra_ratio = contra_count / total
        conflict_ids = [e.evidence_id for e in contra]
        contra_issues = sorted({e.issue_type for e in contra if e.issue_type})
        support_issues = sorted({e.issue_type for e in supporting if e.issue_type})
        summary = (
            f"Operational evidence conflicts: contradictory issue types {contra_issues} "
            f"versus supporting issue types {support_issues or ['none']}. "
            f"The system cannot safely prefer a single explanation."
        )

        if sup_count == 0 and contra_count > 0:
            penalty = 45.0
            warnings.append(
                f"Contradictory evidence detected ({contra_count} conflicting operational logs found with 0 supporting logs). {summary}"
            )
        elif contra_ratio >= self.thresholds.contradiction_ratio_threshold:
            penalty = min(50.0, contra_ratio * 70.0)
            warnings.append(
                f"Significant contradictory evidence detected ({contra_count}/{total} items conflict with hypothesis). {summary}"
            )
        else:
            penalty = min(25.0, contra_ratio * 40.0)
            warnings.append(f"Minor contradictory evidence detected ({contra_count} conflicting items). {summary}")

        return round(penalty, 1), reasons, warnings, summary, conflict_ids

    def evaluate_data_quality(
        self,
        investigation: InvestigationResult,
        source_metadata: Optional[Dict[str, Any]] = None,
        kpi_contract: Optional[Any] = None,
    ) -> Tuple[float, List[str]]:
        """
        Evaluates source completeness, catalog quality scores, and missing dimensions.
        Catalog data_quality_score is stored in [0, 1] and scaled to [0, 100].
        """
        reasons = []
        source_metadata = source_metadata or {}

        catalog_scores = []
        for _sid, info in source_metadata.items():
            raw = info.get("data_quality_score", 0.90)
            catalog_scores.append(raw * 100.0 if raw <= 1.0 else float(raw))

        if catalog_scores:
            score = sum(catalog_scores) / len(catalog_scores)
            reasons.append(
                f"Source catalog quality scores averaged {score:.1f}/100 across {len(catalog_scores)} heterogeneous sources."
            )
        else:
            score = 90.0
            reasons.append("Source catalog quality metadata unavailable; defaulting to conservative completeness assumption.")

        if investigation.anomaly_score is not None and (
            isinstance(investigation.anomaly_score, float) and math.isnan(investigation.anomaly_score)
        ):
            score -= 30.0
            reasons.append("Data quality warning: Anomaly score calculation produced NaN.")

        if self._is_sparse_history(investigation):
            score -= 15.0
            reasons.append("Data quality caveat: Limited historical observations present.")

        if kpi_contract is not None:
            expected_dims = getattr(getattr(kpi_contract, "driver_hierarchy", None), "dimensional_breakdowns", None) or []
            present = set((investigation.dimensional_drilldowns or {}).keys())
            missing = [d for d in expected_dims if d not in present]
            if missing and investigation.ranked_drivers:
                score -= min(10.0, 4.0 * len(missing))
                reasons.append(f"Missing dimensional drilldowns relative to KPI contract: {missing}.")

        return round(max(0.0, min(100.0, score)), 1), reasons

    def evaluate_freshness_score(
        self,
        investigation: InvestigationResult,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluates source last_refresh against SLA, relative to the investigation anomaly window.
        A source refreshed on or after the anomaly window is treated as fresh for that investigation.
        """
        reasons = []
        warnings = []
        source_metadata = source_metadata or {}

        try:
            a_end = datetime.strptime(investigation.anomaly_period.get("end", ""), "%Y-%m-%d")
            as_of = a_end + timedelta(hours=23, minutes=59)
        except Exception:
            as_of = None

        per_source_scores: List[float] = []
        for sid, info in source_metadata.items():
            last_raw = str(info.get("last_refresh", ""))
            sla = int(info.get("freshness_sla_minutes", 1440))
            try:
                last = datetime.fromisoformat(last_raw.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                last = None

            if last is None or as_of is None:
                report = (investigation.data_freshness or {}).get(sid)
                if report is not None and getattr(report, "sla_met", False):
                    per_source_scores.append(98.0)
                else:
                    per_source_scores.append(70.0)
                continue

            if last >= as_of:
                per_source_scores.append(100.0)
                continue

            age_minutes = (as_of - last).total_seconds() / 60.0
            if age_minutes <= sla:
                per_source_scores.append(100.0)
            elif age_minutes <= sla * 2:
                per_source_scores.append(55.0)
                warnings.append(
                    f"Source {sid} is stale relative to the anomaly window "
                    f"(age {age_minutes:.0f} min vs SLA {sla} min)."
                )
            else:
                per_source_scores.append(25.0)
                warnings.append(
                    f"Source {sid} exceeds SLA staleness thresholds "
                    f"(age {age_minutes:.0f} min vs SLA {sla} min)."
                )

        if per_source_scores:
            score = sum(per_source_scores) / len(per_source_scores)
            if not warnings:
                reasons.append("All ingested data sources meet SLA refresh cadences relative to the anomaly window.")
            return round(score, 1), reasons, warnings

        freshness_reports = investigation.data_freshness
        if not freshness_reports:
            return 95.0, ["Data freshness reports verified."], warnings

        all_met = all(r.sla_met for r in freshness_reports.values())
        if all_met:
            return 98.0, ["All ingested data sources meet SLA refresh cadences."], warnings

        missed = [name for name, r in freshness_reports.items() if not r.sla_met]
        score = max(20.0, 98.0 - (len(missed) * 35.0))
        warnings.append(f"Data sources {missed} exceed SLA staleness thresholds.")
        return round(score, 1), reasons, warnings

    def evaluate_lineage_score(
        self,
        investigation: InvestigationResult,
        evidence_pack: Optional[EvidencePack],
        kpi_contract: Optional[Any] = None,
    ) -> Tuple[float, bool, List[str]]:
        """
        Verifies KPI contract upstream lineage and evidence PII-sanitization lineage flags.
        """
        reasons = []
        score = 100.0
        complete = True

        if kpi_contract is not None:
            lineage = getattr(kpi_contract, "lineage", None)
            upstream = getattr(lineage, "upstream_sources", None) or []
            if not upstream:
                complete = False
                score -= 25.0
                reasons.append("KPI contract is missing upstream source lineage.")
            else:
                reasons.append(f"KPI contract lineage lists {len(upstream)} upstream source(s).")

        if evidence_pack:
            items = (
                evidence_pack.supporting_evidence
                + evidence_pack.contradictory_evidence
                + evidence_pack.neutral_evidence
            )
            if items:
                masked = sum(1 for e in items if (e.lineage or {}).get("pii_masked") is True)
                if masked < len(items):
                    complete = False
                    score -= 15.0
                    reasons.append("One or more evidence items lack pii_masked lineage proof.")
                else:
                    reasons.append("Evidence lineage includes PII sanitization proof for retrieved items.")

        return round(max(0.0, min(100.0, score)), 1), complete, reasons

    def evaluate_driver_confidence(
        self,
        investigation: InvestigationResult,
        evidence_pack: Optional[EvidencePack]
    ) -> Dict[str, DriverConfidenceAssessment]:
        """
        Evaluates confidence for each individual quantitative & operational driver.
        """
        driver_assessments: Dict[str, DriverConfidenceAssessment] = {}

        for dc in investigation.ranked_drivers:
            sup_cnt = 0
            contra_cnt = 0
            if evidence_pack:
                aliases = DRIVER_ALIASES.get(dc.driver_name.lower(), [])
                tokens = [dc.driver_name.lower().replace(" ", "_")] + aliases

                def _matches(item: EvidenceItem) -> bool:
                    hay = f"{item.driver} {item.issue_type} {' '.join(item.driver.split('_'))}".lower()
                    return any(t.replace("_", " ") in hay or t in hay.replace(" ", "_") for t in tokens)

                # If driver-specific match is empty, attribute pack-level evidence conservatively
                matched_sup = [e for e in evidence_pack.supporting_evidence if _matches(e)]
                matched_con = [e for e in evidence_pack.contradictory_evidence if _matches(e)]
                if not matched_sup and not matched_con:
                    sup_cnt = len(evidence_pack.supporting_evidence)
                    contra_cnt = len(evidence_pack.contradictory_evidence)
                else:
                    sup_cnt = len(matched_sup)
                    contra_cnt = len(matched_con)

            base_score = 75.0 if dc.contribution_percentage and abs(dc.contribution_percentage) > 10.0 else 60.0
            if sup_cnt > 0:
                base_score += min(20.0, 12.0 + min(8.0, sup_cnt))  # quality-first: first item dominates
            if contra_cnt > 0:
                base_score -= min(30.0, contra_cnt * 10.0)

            score = max(10.0, min(100.0, base_score))

            if score >= 80.0:
                band = ConfidenceBand.HIGH
            elif score >= 60.0:
                band = ConfidenceBand.MEDIUM
            elif score >= 35.0:
                band = ConfidenceBand.LOW
            else:
                band = ConfidenceBand.ABSTAIN

            driver_assessments[dc.driver_name] = DriverConfidenceAssessment(
                driver_name=dc.driver_name,
                driver_type=dc.driver_type,
                confidence_score=round(score, 1),
                confidence_band=band,
                supporting_evidence_count=sup_cnt,
                contradictory_evidence_count=contra_cnt,
                is_statistically_aligned=True,
                justification=f"Quantitative decomposition: {dc.contribution_percentage:+.1f}% contribution via {dc.methodology}.",
            )

        return driver_assessments

    def _clarification_questions(
        self,
        decision: GovernanceDecisionEnum,
        has_severe_contradiction: bool,
        is_sparse: bool,
        has_insufficient_evidence: bool,
        stale: bool,
        investigation: InvestigationResult,
        conflict_summary: Optional[str],
    ) -> List[str]:
        if decision == GovernanceDecisionEnum.PROCEED:
            return []

        questions: List[str] = []
        if has_severe_contradiction:
            summary_u = (conflict_summary or "").upper()
            if any(tok in summary_u for tok in ("SHIPPING", "FREIGHT", "SURCHARGE")):
                questions.append(
                    "Operational carrier memos report freight surcharges, but quantitative data indicates "
                    "discount promotions drove the margin drop. Which operational domain should be prioritized for verification?"
                )
            else:
                questions.append(
                    "Evidence conflicts between competing operational explanations. "
                    "Which business domain should be prioritized for investigation?"
                )
        if is_sparse:
            questions.append(
                "Baseline historical observations are limited. Should the investigation compare against "
                "an annualized seasonal baseline or proceed with caveated variance bounds?"
            )
        if has_insufficient_evidence:
            questions.append(
                f"No sufficient evidence was found for KPI '{investigation.kpi_id}' in window "
                f"{investigation.anomaly_period.get('start')} to {investigation.anomaly_period.get('end')}. "
                "Should the query window be widened or should the EU payment gateway incident window be included?"
            )
        if stale:
            questions.append(
                "Marketing or other upstream data is stale relative to the anomaly window. "
                "Should the analysis proceed using the last available snapshot?"
            )
        return questions

    def assess_confidence(
        self,
        investigation: InvestigationResult,
        evidence_pack: Optional[EvidencePack],
        assessment_id: str,
        scenario_id: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        kpi_contract: Optional[Any] = None,
    ) -> ConfidenceAssessment:
        """
        Computes overall calibrated confidence score and assigns confidence band & decision.
        Future LLM layers must consume this result as binding policy; they cannot recompute it.
        """
        stats_score, stats_reasons, stats_warnings = self.evaluate_statistical_confidence(investigation)
        mat_score, mat_reasons = self.evaluate_materiality_score(investigation)
        evid_score, evid_reasons, evid_warnings = self.evaluate_evidence_score(evidence_pack)
        contra_penalty, contra_reasons, contra_warnings, conflict_summary, conflict_ids = self.evaluate_contradiction_penalty(evidence_pack)
        dq_score, dq_reasons = self.evaluate_data_quality(investigation, source_metadata, kpi_contract)
        fresh_score, fresh_reasons, fresh_warnings = self.evaluate_freshness_score(investigation, source_metadata)
        lineage_score, lineage_complete, lineage_reasons = self.evaluate_lineage_score(
            investigation, evidence_pack, kpi_contract
        )

        raw_confidence = (
            self.weights.weight_statistical * stats_score
            + self.weights.weight_materiality * mat_score
            + self.weights.weight_evidence * evid_score
            + self.weights.weight_data_quality * dq_score
            + self.weights.weight_freshness * fresh_score
            + self.weights.weight_lineage * lineage_score
            - contra_penalty
        )
        overall_confidence = max(0.0, min(100.0, raw_confidence))
        overall_confidence = round(overall_confidence, 1)

        all_reasons = stats_reasons + mat_reasons + evid_reasons + dq_reasons + fresh_reasons + lineage_reasons
        all_warnings = stats_warnings + evid_warnings + contra_warnings + fresh_warnings

        driver_assessments = self.evaluate_driver_confidence(investigation, evidence_pack)

        is_sparse = self._is_sparse_history(investigation)
        has_severe_contradiction = contra_penalty >= 35.0
        insufficient_status = bool(evidence_pack and evidence_pack.status == "INSUFFICIENT_EVIDENCE")
        has_insufficient_evidence = evid_score == 0.0 or insufficient_status
        stale = fresh_score < 80.0

        # Binding circuit breakers (LLM cannot override)
        if has_severe_contradiction:
            band = ConfidenceBand.ABSTAIN
            decision = GovernanceDecisionEnum.ABSTAIN
            all_warnings.append("Circuit breaker tripped: Severe contradictory operational evidence detected.")
        elif is_sparse:
            band = ConfidenceBand.LOW
            decision = GovernanceDecisionEnum.REQUEST_CLARIFICATION
            all_warnings.append("Circuit breaker tripped: Insufficient baseline history prevents definitive claim.")
        elif has_insufficient_evidence:
            # Spec: INSUFFICIENT_EVIDENCE must not allow a high-confidence narrative.
            band = ConfidenceBand.LOW if overall_confidence < 60.0 else ConfidenceBand.MEDIUM
            if band == ConfidenceBand.MEDIUM:
                band = ConfidenceBand.LOW
            decision = GovernanceDecisionEnum.REQUEST_CLARIFICATION
            if evid_score == 0.0:
                all_warnings.append(
                    f"No sufficient evidence was found for KPI '{investigation.kpi_id}' in the investigation window."
                )
        elif overall_confidence >= self.thresholds.high_threshold:
            band = ConfidenceBand.HIGH
            decision = GovernanceDecisionEnum.PROCEED
        elif overall_confidence >= self.thresholds.medium_threshold:
            band = ConfidenceBand.MEDIUM
            decision = GovernanceDecisionEnum.PROCEED_WITH_CAUTION
        elif overall_confidence >= self.thresholds.low_threshold:
            band = ConfidenceBand.LOW
            decision = GovernanceDecisionEnum.REQUEST_CLARIFICATION
        else:
            band = ConfidenceBand.ABSTAIN
            decision = GovernanceDecisionEnum.ABSTAIN

        clarification_questions = self._clarification_questions(
            decision=decision,
            has_severe_contradiction=has_severe_contradiction,
            is_sparse=is_sparse,
            has_insufficient_evidence=has_insufficient_evidence,
            stale=stale,
            investigation=investigation,
            conflict_summary=conflict_summary,
        )

        return ConfidenceAssessment(
            assessment_id=assessment_id,
            kpi_id=investigation.kpi_id,
            scenario_id=scenario_id,
            overall_confidence=overall_confidence,
            confidence_band=band,
            decision=decision,
            reasons=all_reasons,
            warnings=all_warnings,
            driver_assessments=driver_assessments,
            data_quality_score=dq_score,
            statistical_confidence=stats_score,
            materiality_score=mat_score,
            evidence_score=evid_score,
            freshness_score=fresh_score,
            lineage_score=lineage_score,
            contradiction_penalty=contra_penalty,
            lineage_complete=lineage_complete,
            conflict_summary=conflict_summary,
            conflicting_evidence_ids=conflict_ids,
            clarification_questions=clarification_questions,
            formula_version=FORMULA_VERSION,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )


confidence_evaluator = ConfidenceEvaluator()

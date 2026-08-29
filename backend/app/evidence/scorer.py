from typing import Dict, Any, Optional

class EvidenceScorer:
    """
    Deterministic Evidence Scoring Engine.
    Calculates normalized relevance scores [0.0 - 100.0] based on:
      1. Semantic Cosine Similarity (35% weight)
      2. Temporal Window Alignment (25% weight)
      3. Dimensional Match (Region/Product) (15% weight)
      4. Severity Level (15% weight)
      5. Driver Tag Match (10% weight)
    Zero LLM involvement; 100% reproducible.
    """

    WEIGHT_SIMILARITY = 0.35
    WEIGHT_TEMPORAL = 0.25
    WEIGHT_DIMENSIONAL = 0.15
    WEIGHT_SEVERITY = 0.15
    WEIGHT_DRIVER = 0.10

    SEVERITY_SCORES = {
        "CRITICAL": 100.0,
        "HIGH": 75.0,
        "MEDIUM": 50.0,
        "LOW": 25.0,
    }

    @classmethod
    def compute_score(
        cls,
        semantic_similarity: float,
        temporal_alignment: str,
        dimension_match: bool,
        severity: str,
        driver_tag_match: bool
    ) -> float:
        """
        Calculates the composite deterministic evidence score.
        """
        # 1. Similarity component: [0 - 1.0] -> [0 - 100]
        s_sim = max(0.0, min(1.0, semantic_similarity)) * 100.0

        # 2. Temporal component
        if temporal_alignment == "EXACT_WINDOW":
            s_temp = 100.0
        elif temporal_alignment == "NEAR_WINDOW":
            s_temp = 50.0
        else:
            s_temp = 0.0

        # 3. Dimensional component
        s_dim = 100.0 if dimension_match else 40.0

        # 4. Severity component
        s_sev = cls.SEVERITY_SCORES.get(severity.upper(), 50.0)

        # 5. Driver tag component
        s_driver = 100.0 if driver_tag_match else 30.0

        # Weighted sum
        score = (
            cls.WEIGHT_SIMILARITY * s_sim
            + cls.WEIGHT_TEMPORAL * s_temp
            + cls.WEIGHT_DIMENSIONAL * s_dim
            + cls.WEIGHT_SEVERITY * s_sev
            + cls.WEIGHT_DRIVER * s_driver
        )

        return round(float(score), 1)

evidence_scorer = EvidenceScorer()

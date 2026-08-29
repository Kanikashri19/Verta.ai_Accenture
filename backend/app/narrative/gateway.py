import os
import time
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import logging

try:
    import litellm
except ImportError:
    litellm = None

logger = logging.getLogger(__name__)

class LLMGateway:
    """
    Unified LLM Gateway abstraction supporting LiteLLM, mock providers, and token accounting.
    Guarantees that no external API keys are hardcoded and isolates the application from provider specifics.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.model = os.getenv("LLM_MODEL", "mock-llm-v1")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.input_cost_per_1k = float(os.getenv("LLM_INPUT_COST_PER_1K", "0.00125"))
        self.output_cost_per_1k = float(os.getenv("LLM_OUTPUT_COST_PER_1K", "0.00500"))

    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 1
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Executes completion with structured JSON output, retries, and telemetry extraction.
        Returns: (parsed_json_dict, telemetry_dict)
        """
        start_time = time.perf_counter()
        retries_used = 0
        current_user_prompt = user_prompt

        # Check if mock mode is active
        if self.provider == "mock" or os.getenv("VERTA_MOCK_LLM", "false").lower() == "true":
            return self._generate_mock_completion(system_prompt, user_prompt, start_time)

        if litellm is None:
            raise RuntimeError("LiteLLM is not installed; falling back to deterministic synthesis.")

        for attempt in range(max_retries + 1):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_user_prompt}
                ]
                
                # Format model string for litellm
                model_str = self.model
                if self.provider == "gemini" and not model_str.startswith("gemini/"):
                    model_str = f"gemini/{model_str}"

                response = litellm.completion(
                    model=model_str,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout_seconds,
                    response_format={"type": "json_object"}
                )

                latency_ms = (time.perf_counter() - start_time) * 1000.0
                content_str = response.choices[0].message.content

                # Parse JSON
                parsed_json = json.loads(content_str)

                # Extract usage
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                output_tokens = getattr(usage, "completion_tokens", None) if usage else None
                total_tokens = getattr(usage, "total_tokens", None) if usage else None

                estimated_cost = None
                if input_tokens is not None and output_tokens is not None:
                    estimated_cost = (input_tokens * self.input_cost_per_1k + output_tokens * self.output_cost_per_1k) / 1000.0

                telemetry = {
                    "model_provider": self.provider,
                    "model": self.model,
                    "latency_ms": round(latency_ms, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": round(estimated_cost, 6) if estimated_cost else None,
                    "retry_count": retries_used,
                    "fallback_used": False
                }

                return parsed_json, telemetry

            except (json.JSONDecodeError, Exception) as e:
                retries_used += 1
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    current_user_prompt += "\n\nCRITICAL: Your previous response was invalid. You MUST return ONLY valid JSON matching the exact schema."
                else:
                    raise e

    def _generate_mock_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        start_time: float
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Deterministic mock generator for testing and offline execution.
        """
        # Parse context from prompt text if available
        is_executive = "EXECUTIVE REQUIREMENTS:" in user_prompt
        latency_ms = (time.perf_counter() - start_time) * 1000.0 + 15.0  # simulate ~15ms
        
        if is_executive:
            headline = "Gross Revenue declined by 15.0% due to checkout timeouts and stockout friction."
            summary = "Gross Revenue declined 15.0% (-$15,020.00 USD) across the anomaly period, driven by severe checkout friction and regional stockouts. Payment Operations and Inventory teams should execute immediate mitigation."
            caveats = ["Assessment confidence: HIGH (93.7/100).", "Multi-factor correlation across conversion rate and unit volume."]
        else:
            headline = "Gross Revenue observed negative deviation of -15.02% with statistical significance (|z| = 7.74, p < 0.001)."
            summary = "Quantitative investigation of Gross Revenue reveals a statistically significant drop of -15.02% (-$15,020.00 USD) relative to the 83-day baseline. Multiplicative decomposition confirms conversion_rate (-52.1% contribution) and orders (-47.9% contribution) as primary drivers, corroborated by matching payment gateway timeout and stockout incident logs."
            caveats = ["Statistical significance: STATISTICALLY_SIGNIFICANT (|z| = 7.74).", "Data quality catalog score: 95.0/100.", "Upstream SLA freshness verified."]

        import re
        found_eids = list(dict.fromkeys(re.findall(r"EVID-[A-Za-z0-9\-]+", user_prompt)))
        eid1 = found_eids[0] if len(found_eids) > 0 else "EVID-OPS-001"
        eid2 = found_eids[1] if len(found_eids) > 1 else eid1

        mock_json = {
            "headline": headline,
            "summary": summary,
            "kpi_movement": {
                "baseline_value": 100000.0,
                "current_value": 84980.0,
                "absolute_change": -15020.0,
                "percentage_change": -15.02,
                "unit": "USD"
            },
            "key_drivers": [
                {
                    "driver_name": "conversion_rate",
                    "contribution_value": -7820.0,
                    "contribution_percentage": -52.1,
                    "direction": "NEGATIVE",
                    "explanation": "Conversion rate decline caused by EU checkout payment gateway timeouts."
                },
                {
                    "driver_name": "orders",
                    "contribution_value": -7200.0,
                    "contribution_percentage": -47.9,
                    "direction": "NEGATIVE",
                    "explanation": "Order volume decline caused by high-velocity SKU stockouts."
                }
            ],
            "evidence_citations": [
                {
                    "statement": f"Operational ticket {eid1} reported PAYMENT_GATEWAY_TIMEOUT affecting conversion_rate.",
                    "evidence_ids": [eid1],
                    "driver": "conversion_rate",
                    "snippet_summary": "Payment gateway timeout spikes observed in checkout service."
                },
                {
                    "statement": f"Operational ticket {eid2} reported STOCKOUT affecting product_availability.",
                    "evidence_ids": [eid2],
                    "driver": "product_availability",
                    "snippet_summary": "Inventory stockout reported for top apparel SKU."
                }
            ],
            "caveats": caveats,
            "alternative_hypotheses": [
                "Regional consumer demand deceleration may account for residual unexplained variance."
            ]
        }

        telemetry = {
            "model_provider": "mock",
            "model": "mock-llm-v1",
            "latency_ms": round(latency_ms, 2),
            "input_tokens": 480,
            "output_tokens": 220,
            "total_tokens": 700,
            "estimated_cost": 0.0017,
            "retry_count": 0,
            "fallback_used": False
        }

        return mock_json, telemetry

llm_gateway = LLMGateway()

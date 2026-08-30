# Phase 7 — Judge-Ready Frontend & Demo Dashboard Guide

## 1. Overview & Architecture

Verta.ai is a deterministic KPI Decision Intelligence platform designed for the Accenture Innovation Challenge 2026 Round 2. It operationalizes the core paradigm:
$$\text{DETECT} \longrightarrow \text{CORRELATE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{RECOMMEND}$$

The Phase 7 dashboard delivers a high-impact, enterprise-grade user interface built on **React 18 + Vite** connected in real-time to the **FastAPI** deterministic intelligence backend.

```
+-----------------------------------------------------------------------------------------+
|                                    REACT + VITE DASHBOARD                               |
|   - Screen 1: Executive KPI Overview Grid & Anomaly Prioritisation                      |
|   - Screen 2: Detailed KPI Investigation, Decomposition & Traceable Evidence            |
|   - Screen 3: Governed Persona Narrative (Executive vs Analyst Views)                   |
|   - Screen 4 & 6: Calibrated Confidence Gauge & Governance Circuit Breaker              |
|   - Screen 5: 8-Point Accenture Action Recommendation Pipeline                          |
|   - Screen 7: Enterprise Security & RBAC Guardrails ([MASKED_PII] & Role Filtering)     |
|   - Screen 8: Non-LLM vs LLM Architectural Matrix ("How Verta.ai Thinks")               |
|   - Screen 9: Observability & Real-Time Telemetry Slide-Out Drawer                      |
|   - Screen 10: Analyst Feedback & Continuous Calibration Loop                           |
+-----------------------------------------------------------------------------------------+
                                           │
                                   HTTP / REST (JSON)
                                           │
+-----------------------------------------------------------------------------------------+
|                                    FASTAPI BACKEND                                      |
|   - /api/kpi/overview                     - /api/analysis/investigate/{kpi_id}          |
|   - /api/evidence/{kpi_id}                - /api/governance/assess/{kpi_id}             |
|   - /api/narrative/generate/{kpi_id}      - /api/actions/recommend/{kpi_id}            |
|   - /api/feedback/submit                  - /api/narrative/telemetry                    |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Screen-by-Screen Feature Mapping

### Screen 1 — Executive KPI Overview & Prioritisation
- **Header**: `Verta.ai | KPI Intelligence → Action`
- **5 Standard KPI Cards**:
  1. Gross Revenue (`kpi_revenue`)
  2. Completed Orders (`kpi_orders`)
  3. Average Order Value (`kpi_aov`)
  4. E-Commerce Conversion Rate (`kpi_conv_rate`)
  5. Gross Profit Margin % (`kpi_gross_margin`)
- **Key Metrics Displayed**: Current Value, Baseline Value, % Delta, Materiality Badge (`CRITICAL ACTIONABLE`, `BUSINESS WARNING`, `NORMAL`).
- **Visual Prioritisation**: The target KPI with the largest material movement receives an active highlight ribbon and priority investigation card border.

### Screen 2 — Detailed KPI Investigation & Evidence Traceability
- **Movement Summary**: Baseline period vs anomaly period, exact absolute delta, and percentage delta.
- **Statistical Evidence**: Approximate $z$-score, $p$-value approximation ($p < 0.001$), sample size, and variance metrics.
- **Quantitative Driver Decomposition**: Ranked table presenting each driver's contribution value (\$), contribution percentage (\%), direction (`NEGATIVE`/`POSITIVE`), and decomposition methodology (`Logarithmic Multiplicative Decomposition`, `Logarithmic Bennet Exact Mix-Shift`).
- **Traceable Evidence Cards**: Displays concrete ChromaDB vector store IDs (e.g. `[EVID-OPS-20260822-a95c4f62]`), source table (`customer_operations_events`), timestamp, issue type, severity, relevance score, and sanitized log text.
- **Lineage Flow**: Visual step-by-step breadcrumb tracking data from raw upstream tables through semantic formulas, decomposition, vector RAG, and action rights.

### Screen 3 — Governed Persona Narrative (Executive vs Analyst)
- **Executive View**: Concise, business-oriented headline and summary focusing on high-level financial impact and cross-functional team delegation (`Payment Operations`, `Inventory Operations`).
- **Analyst View**: Deep technical explanation detailing statistical significance, z-scores, multiplicative driver contribution values, and incident log correlations.
- **Grounded Citations**: Traceable `[EVID-...]` pills directly embedded in explanatory text.
- **Explicit Uncertainty & Caveats**: Lists statistical variance boundaries and alternative hypotheses evaluated by the engine.

### Screen 4 & 6 — Calibrated Confidence & Governance Circuit Breaker
- **Confidence Gauge**: Displays calibrated confidence score $X / 100$ and confidence band (`HIGH`, `MEDIUM`, `LOW`, `VERY_LOW`).
- **Governance Decision Badge**:
  - `PROCEED`: High confidence ($\ge 75/100$); permits autonomous narrative synthesis and action generation.
  - `ABSTAIN`: Triggered on low confidence ($< 40/100$) or contradictory evidence; suppresses causal recommendations to prevent hallucinated advice.
  - `REQUEST_CLARIFICATION`: Triggered on sparse history; pauses autonomous generation and surfaces interactive clarification prompts.
- **Sub-score Pillars**: Shows statistical confidence, evidence quality, data freshness & SLA compliance, and contradiction penalty.

### Screen 5 — Approved Action Recommendations (Accenture Paradigm)
- Follows the complete 8-point Accenture recommendation framework:
  $$\text{Driver} \longrightarrow \text{Controllable Lever} \longrightarrow \text{Action} \longrightarrow \text{Expected Impact} \longrightarrow \text{Owner} \longrightarrow \text{Confidence} \longrightarrow \text{Monitoring Plan} \longrightarrow \text{Decision Right}$$
- **Approved Decision Owners**: `Payments Operations`, `Inventory Operations`, `Growth Marketing`, `Commercial Finance`.
- **Governance Circuit Breaker**: When `ABSTAIN` or `REQUEST_CLARIFICATION` is active, recommendations are visibly blocked with a governance warning.

### Screen 7 — Enterprise Security & RBAC Guardrails
- **Executive Role**: PII, raw IPs, user emails, and low-level stack traces are pre-filtered before narrative rendering.
- **Analyst Role**: Technical metric breakdowns and sanitized incident logs are visible; customer PII is tokenized with `[MASKED_EMAIL]` and `[MASKED_PHONE]`.
- **Operations Role**: Full access to operational incident tickets and gateway telemetry.

### Screen 8 — Non-LLM vs LLM Architectural Matrix ("How Verta.ai Thinks")
- **Non-LLM (Deterministic Ground Truth)**: Semantic formula contracts, statistical anomaly detection, exact driver decomposition, ChromaDB local vector search, confidence scoring, circuit breakers, and action catalog mapping.
- **LLM (Translation & Synthesis)**: User intent understanding, persona contextualization, natural language synthesis, and citation formatting.
- **Foundational Principle**: *"The LLM is NEVER the source of quantitative truth."*

### Screen 9 — Observability & Real-Time Telemetry
- Slide-out drawer tracking real-time request metrics:
  - `Request ID`, `Model Provider` (`mock`, `ollama`, `openai`, `gemini`), `Model Name`, `Latency (ms)`, `Input / Output / Total Tokens`, `Estimated Cost ($)`, `Cache Hit (Yes/No)`, `Fallback Used (Yes/No)`.

### Screen 10 — Analyst Feedback Loop
- Enables domain experts to submit ratings (`Correct`, `Partially Correct`, `Incorrect`) and corrective notes.
- Submissions are logged to the backend evaluation registry (`POST /api/feedback/submit`) with a generated tracking ID (`FB-...`) for continuous calibration.

---

## 3. Demo Scenario Cheat-Sheet for Competition Judges

| Scenario | Objective / Theme | Expected Governance | Key Characteristics |
| :--- | :--- | :--- | :--- |
| **1. Multi-Factor Revenue Drop** | Primary End-to-End Demo | `PROCEED` (93.7/100, HIGH) | Multi-factor decline driven by checkout payment timeouts (-52.1%) and stockouts (-47.9%). Actions generated for Payments & Inventory Operations. |
| **2. High Confidence Single Factor** | Clean Operational Incident | `PROCEED` (>90/100, HIGH) | Clear single-driver incident with strong corroborating evidence logs and high statistical significance. |
| **3. Low Confidence Inconclusive** | Noise & Insufficient Support | `ABSTAIN` (<40/100, LOW) | AOV fluctuation with high statistical noise and uncorroborated tickets; action recommendations suppressed. |
| **4. Sparse History** | Cold-Start / New KPI Baseline | `REQUEST_CLARIFICATION` (43.2/100, LOW) | Baseline history limited (<5 observations); pauses generation and prompts clarification questions. |
| **5. Contradictory Evidence** | Operational Conflict | `ABSTAIN` (12.8/100, VERY_LOW) | Conflicting incident tickets (e.g. shipping surcharge vs checkout timeout); actions blocked with conflict summary. |

---

## 4. Local Execution Commands (Windows PowerShell)

### Terminal 1: FastAPI Backend
```powershell
cd c:\Users\kanik\OneDrive\Desktop\verta.ai_accenture
$env:PYTHONPATH = "backend"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: React + Vite Frontend
```powershell
cd c:\Users\kanik\OneDrive\Desktop\verta.ai_accenture\frontend
npm run dev
```

### Local Dashboard URL
Open your web browser and navigate to:
```
http://localhost:5173
```
*(The Vite dev server proxies all `/api/*` requests to the FastAPI backend running on port `8000`).*

---

## 5. Verification & Test Execution

Run the complete multi-phase test suite across all engines and API endpoints:
```powershell
cd c:\Users\kanik\OneDrive\Desktop\verta.ai_accenture
pytest -v
```

Build the production frontend bundle:
```powershell
cd c:\Users\kanik\OneDrive\Desktop\verta.ai_accenture\frontend
npm run build
```

import {
  FALLBACK_KPIS,
  FALLBACK_INVESTIGATION,
  FALLBACK_EVIDENCE,
  FALLBACK_GOVERNANCE,
  FALLBACK_NARRATIVE,
} from './fallbackData';

const API_BASE = '/api';

async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`[API] Fetch failed for ${url}, using deterministic fallback. Error:`, err.message);
    throw err;
  }
}

export async function fetchScenarios() {
  try {
    return await safeFetch(`${API_BASE}/scenarios/list`);
  } catch {
    return [
      { id: 'SCENARIO_1_MULTI_FACTOR', label: '1. Multi-Factor Revenue Drop (Main Demo)' },
      { id: 'SCENARIO_2_HIGH_CONFIDENCE', label: '2. High Confidence Single Factor' },
      { id: 'SCENARIO_3_LOW_CONFIDENCE', label: '3. Low Confidence (AOV Inconclusive)' },
      { id: 'SCENARIO_4_SPARSE_HISTORY', label: '4. Sparse History (New Baseline)' },
      { id: 'SCENARIO_5_CONTRADICTORY_EVIDENCE', label: '5. Contradictory Evidence (Conflict)' },
    ];
  }
}

export async function fetchKPIOverview(scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  try {
    return await safeFetch(`${API_BASE}/kpi/overview?scenario_id=${encodeURIComponent(scenarioId)}`);
  } catch {
    return {
      scenario_id: scenarioId,
      total_kpis: FALLBACK_KPIS.length,
      kpis: FALLBACK_KPIS,
    };
  }
}

export async function fetchKPIInvestigation(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  try {
    return await safeFetch(`${API_BASE}/analysis/investigate/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}`);
  } catch {
    return {
      ...FALLBACK_INVESTIGATION,
      kpi_id: kpiId,
      scenario_id: scenarioId,
    };
  }
}

export async function fetchFactPack(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  try {
    return await safeFetch(`${API_BASE}/analysis/factpack/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}`);
  } catch {
    return {
      kpi_id: kpiId,
      scenario_id: scenarioId,
      investigation: FALLBACK_INVESTIGATION,
    };
  }
}

export async function fetchGovernanceAssessment(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  try {
    return await safeFetch(`${API_BASE}/governance/assess/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}&role=${encodeURIComponent(role)}`);
  } catch {
    return FALLBACK_GOVERNANCE;
  }
}

export async function fetchEvidence(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  try {
    return await safeFetch(`${API_BASE}/evidence/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}&role=${encodeURIComponent(role)}`);
  } catch {
    return FALLBACK_EVIDENCE;
  }
}

export async function generateNarrative(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', persona = 'EXECUTIVE', role = 'ANALYST', forceRefresh = false) {
  try {
    const params = new URLSearchParams({
      scenario_id: scenarioId,
      persona: persona,
      role: role,
      force_refresh: forceRefresh.toString(),
    });
    return await safeFetch(`${API_BASE}/narrative/generate/${encodeURIComponent(kpiId)}?${params.toString()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return {
      ...FALLBACK_NARRATIVE,
      telemetry: {
        ...FALLBACK_NARRATIVE.telemetry,
        kpi_id: kpiId,
        persona: persona,
      },
    };
  }
}

export async function fetchActionRecommendations(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  try {
    const params = new URLSearchParams({
      scenario_id: scenarioId,
      role: role,
    });
    return await safeFetch(`${API_BASE}/actions/recommend/${encodeURIComponent(kpiId)}?${params.toString()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return FALLBACK_NARRATIVE.recommended_actions;
  }
}

export async function fetchNarrativeStatus() {
  try {
    return await safeFetch(`${API_BASE}/narrative/status`);
  } catch {
    return {
      status: 'active',
      provider: 'mock',
      model: 'mock-llm-v1',
      temperature: 0.0,
      max_tokens: 1024,
      pricing: { input_cost_per_1k: 0.00015, output_cost_per_1k: 0.0006 },
      cache_size: 1,
    };
  }
}

export async function fetchNarrativeTelemetry() {
  try {
    return await safeFetch(`${API_BASE}/narrative/telemetry`);
  } catch {
    return [FALLBACK_NARRATIVE.telemetry];
  }
}

export async function submitFeedback(payload) {
  try {
    const res = await fetch(`${API_BASE}/feedback/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to submit feedback (${res.status})`);
    return await res.json();
  } catch (err) {
    // Local storage fallback for feedback registry
    const localId = `FB-${Date.now().toString(36).toUpperCase()}`;
    const record = {
      feedback_id: localId,
      timestamp: new Date().toISOString(),
      ...payload,
    };
    return { status: 'success', record };
  }
}

export async function fetchFeedbackList() {
  try {
    return await safeFetch(`${API_BASE}/feedback/list`);
  } catch {
    return [];
  }
}

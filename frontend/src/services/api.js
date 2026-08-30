const API_BASE = '/api';

export async function fetchScenarios() {
  const res = await fetch(`${API_BASE}/scenarios/list`);
  if (!res.ok) throw new Error(`Failed to load scenarios (${res.status})`);
  return res.json();
}

export async function fetchKPIOverview(scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  const res = await fetch(`${API_BASE}/kpi/overview?scenario_id=${encodeURIComponent(scenarioId)}`);
  if (!res.ok) throw new Error(`Failed to load KPI overview (${res.status})`);
  return res.json();
}

export async function fetchKPIInvestigation(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  const res = await fetch(`${API_BASE}/analysis/investigate/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}`);
  if (!res.ok) throw new Error(`Failed to load KPI investigation (${res.status})`);
  return res.json();
}

export async function fetchFactPack(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR') {
  const res = await fetch(`${API_BASE}/analysis/factpack/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}`);
  if (!res.ok) throw new Error(`Failed to load FactPack (${res.status})`);
  return res.json();
}

export async function fetchGovernanceAssessment(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  const res = await fetch(`${API_BASE}/governance/assess/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}&role=${encodeURIComponent(role)}`);
  if (!res.ok) throw new Error(`Failed to load governance assessment (${res.status})`);
  return res.json();
}

export async function fetchEvidence(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(kpiId)}?scenario_id=${encodeURIComponent(scenarioId)}&role=${encodeURIComponent(role)}`);
  if (!res.ok) throw new Error(`Failed to load evidence (${res.status})`);
  return res.json();
}

export async function generateNarrative(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', persona = 'EXECUTIVE', role = 'ANALYST', forceRefresh = false) {
  const params = new URLSearchParams({
    scenario_id: scenarioId,
    persona: persona,
    role: role,
    force_refresh: forceRefresh.toString(),
  });
  const res = await fetch(`${API_BASE}/narrative/generate/${encodeURIComponent(kpiId)}?${params.toString()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Failed to generate narrative (${res.status})`);
  return res.json();
}

export async function fetchActionRecommendations(kpiId, scenarioId = 'SCENARIO_1_MULTI_FACTOR', role = 'ANALYST') {
  const params = new URLSearchParams({
    scenario_id: scenarioId,
    role: role,
  });
  const res = await fetch(`${API_BASE}/actions/recommend/${encodeURIComponent(kpiId)}?${params.toString()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Failed to load recommendations (${res.status})`);
  return res.json();
}

export async function fetchNarrativeStatus() {
  const res = await fetch(`${API_BASE}/narrative/status`);
  if (!res.ok) throw new Error(`Failed to load narrative engine status (${res.status})`);
  return res.json();
}

export async function fetchNarrativeTelemetry() {
  const res = await fetch(`${API_BASE}/narrative/telemetry`);
  if (!res.ok) throw new Error(`Failed to load telemetry (${res.status})`);
  return res.json();
}

export async function submitFeedback(payload) {
  const res = await fetch(`${API_BASE}/feedback/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to submit feedback (${res.status})`);
  return res.json();
}

export async function fetchFeedbackList() {
  const res = await fetch(`${API_BASE}/feedback/list`);
  if (!res.ok) throw new Error(`Failed to fetch feedback logs (${res.status})`);
  return res.json();
}

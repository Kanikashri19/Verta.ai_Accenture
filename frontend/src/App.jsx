import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import KPIOverviewGrid from './components/KPIOverviewGrid';
import InvestigationView from './components/InvestigationView';
import GovernancePanel from './components/GovernancePanel';
import PersonaNarrativeCard from './components/PersonaNarrativeCard';
import ActionRecommendations from './components/ActionRecommendations';
import SecurityRBACOverlay from './components/SecurityRBACOverlay';
import EngineArchitectureCard from './components/EngineArchitectureCard';
import TelemetryDrawer from './components/TelemetryDrawer';
import AnalystFeedbackModal from './components/AnalystFeedbackModal';

import {
  fetchKPIOverview,
  fetchKPIInvestigation,
  fetchGovernanceAssessment,
  fetchEvidence,
  generateNarrative,
  fetchActionRecommendations,
  fetchNarrativeStatus,
  fetchNarrativeTelemetry,
} from './services/api';

export default function App() {
  const [scenarioId, setScenarioId] = useState('SCENARIO_1_MULTI_FACTOR');
  const [persona, setPersona] = useState('EXECUTIVE');
  const [userRole, setUserRole] = useState('ANALYST');
  const [selectedKpiId, setSelectedKpiId] = useState('kpi_revenue');

  const [kpis, setKpis] = useState([]);
  const [investigation, setInvestigation] = useState(null);
  const [governanceData, setGovernanceData] = useState(null);
  const [evidencePack, setEvidencePack] = useState(null);
  const [narrativeData, setNarrativeData] = useState(null);
  const [actions, setActions] = useState([]);
  const [llmStatus, setLlmStatus] = useState(null);
  const [telemetryHistory, setTelemetryHistory] = useState([]);

  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingInvestigation, setLoadingInvestigation] = useState(false);
  const [isTelemetryOpen, setIsTelemetryOpen] = useState(false);
  const [error, setError] = useState(null);

  // Load KPI overview for scenario
  const loadOverview = useCallback(async (scenId) => {
    setLoadingOverview(true);
    setError(null);
    try {
      const data = await fetchKPIOverview(scenId);
      const list = data.kpis || [];
      setKpis(list);
      // If selected KPI not in list, pick the first one
      if (list.length > 0 && !list.some((k) => k.kpi_id === selectedKpiId)) {
        setSelectedKpiId(list[0].kpi_id);
      }
    } catch (err) {
      console.error('Failed to load KPI overview:', err);
      setError('Could not connect to FastAPI backend at /api/kpi/overview. Ensure the backend server is running on port 8000.');
    } finally {
      setLoadingOverview(false);
    }
  }, [selectedKpiId]);

  // Load deep dive investigation, governance, evidence, narrative & actions
  const loadDeepDive = useCallback(async (kpiId, scenId, pers, role, forceRefresh = false) => {
    setLoadingInvestigation(true);
    setError(null);
    try {
      // Parallel fetch of core deterministic investigation and governance
      const [invRes, govRes, evidRes, narrRes] = await Promise.all([
        fetchKPIInvestigation(kpiId, scenId),
        fetchGovernanceAssessment(kpiId, scenId, role),
        fetchEvidence(kpiId, scenId, role),
        generateNarrative(kpiId, scenId, pers, role, forceRefresh),
      ]);

      setInvestigation(invRes);
      setGovernanceData(govRes);
      setEvidencePack(evidRes);
      setNarrativeData(narrRes);
      setActions(narrRes.recommended_actions || []);

      // Fetch telemetry and status
      const [statusRes, telemRes] = await Promise.all([
        fetchNarrativeStatus().catch(() => null),
        fetchNarrativeTelemetry().catch(() => []),
      ]);
      if (statusRes) setLlmStatus(statusRes);
      if (telemRes) setTelemetryHistory(telemRes);

    } catch (err) {
      console.error('Failed to load deep dive investigation:', err);
      setError(`Investigation error for ${kpiId}: ${err.message}`);
    } finally {
      setLoadingInvestigation(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadOverview(scenarioId);
  }, [scenarioId, loadOverview]);

  // When selected KPI, scenario, persona, or role changes
  useEffect(() => {
    if (selectedKpiId) {
      loadDeepDive(selectedKpiId, scenarioId, persona, userRole);
    }
  }, [selectedKpiId, scenarioId, persona, userRole, loadDeepDive]);

  const handleRefresh = () => {
    loadOverview(scenarioId);
    loadDeepDive(selectedKpiId, scenarioId, persona, userRole, true);
  };

  return (
    <div style={{ minHeight: '100vh', padding: '24px 20px', maxWidth: '1440px', margin: '0 auto' }}>
      
      {/* Global Header & Scenario Controls */}
      <Header
        scenarioId={scenarioId}
        onScenarioChange={setScenarioId}
        persona={persona}
        onPersonaChange={setPersona}
        userRole={userRole}
        onRoleChange={setUserRole}
        onRefresh={handleRefresh}
        loading={loadingOverview || loadingInvestigation}
        onOpenTelemetry={() => setIsTelemetryOpen(true)}
      />

      {/* Security & RBAC Overlay (Screen 7) */}
      <SecurityRBACOverlay userRole={userRole} />

      {/* Global Error Banner */}
      {error && (
        <div style={{ padding: '14px 20px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '10px', color: '#fca5a5', marginBottom: '20px', fontSize: '0.85rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Screen 1: Executive KPI Overview Grid */}
      <KPIOverviewGrid
        kpis={kpis}
        selectedKpiId={selectedKpiId}
        onSelectKpi={setSelectedKpiId}
        loading={loadingOverview}
      />

      {/* Main Investigation & Intelligence Flow */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        
        {/* Screen 4 & 6: Governance & Confidence Panel */}
        <GovernancePanel
          governanceData={governanceData}
          narrativeData={narrativeData}
          loading={loadingInvestigation}
        />

        {/* Screen 3: Persona-Specific Governed Narrative */}
        <PersonaNarrativeCard
          narrativeData={narrativeData}
          persona={persona}
          loading={loadingInvestigation}
        />

        {/* Screen 2: Detailed KPI Investigation, Decomposition & Traceable Evidence */}
        <InvestigationView
          investigation={investigation}
          evidencePack={evidencePack}
          persona={persona}
          userRole={userRole}
          loading={loadingInvestigation}
        />

        {/* Screen 5: Approved Action Recommendations */}
        <ActionRecommendations
          actions={actions}
          governanceDecision={narrativeData?.governance_decision || governanceData?.decision?.decision}
          loading={loadingInvestigation}
        />

        {/* Screen 8: Non-LLM vs Governed LLM Architecture Matrix */}
        <EngineArchitectureCard
          generationMode={narrativeData?.generation_mode}
          llmStatus={llmStatus}
        />

        {/* Screen 10: Analyst Feedback Loop */}
        <AnalystFeedbackModal
          kpiId={selectedKpiId}
          scenarioId={scenarioId}
          persona={persona}
          userRole={userRole}
          requestId={narrativeData?.telemetry?.request_id}
          onFeedbackSubmitted={() => {
            fetchNarrativeTelemetry().then((t) => setTelemetryHistory(t || []));
          }}
        />

      </div>

      {/* Screen 9: Real-Time Telemetry Slide-Out Drawer */}
      <TelemetryDrawer
        isOpen={isTelemetryOpen}
        onClose={() => setIsTelemetryOpen(false)}
        currentTelemetry={narrativeData?.telemetry}
        telemetryHistory={telemetryHistory}
        onRefresh={() => fetchNarrativeTelemetry().then((t) => setTelemetryHistory(t || []))}
      />

      {/* Footer */}
      <footer style={{ marginTop: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
        Verta.ai Decision Intelligence Platform • Accenture Innovation Challenge 2026 Round 2
      </footer>

    </div>
  );
}

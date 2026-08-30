import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import PipelineFlowBar from './components/PipelineFlowBar';
import TabBar from './components/TabBar';

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
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'investigation' | 'narrative' | 'governance' | 'actions' | 'architecture' | 'feedback'
  const [scenarioId, setScenarioId] = useState('SCENARIO_1_MULTI_FACTOR');
  const [persona, setPersona] = useState('EXECUTIVE');
  const [userRole, setUserRole] = useState('ANALYST');
  const [selectedKpiId, setSelectedKpiId] = useState('kpi_revenue');
  const [focusedDriver, setFocusedDriver] = useState(null);

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

  // When a user selects a KPI from Overview
  const handleSelectKpi = (kpiId) => {
    setSelectedKpiId(kpiId);
    setFocusedDriver(null); // Reset driver focus on KPI change
  };

  const selectedKpiObj = kpis.find((k) => k.kpi_id === selectedKpiId) || kpis[0] || {};
  const currentConfidence = governanceData?.assessment?.confidence_score ?? narrativeData?.telemetry?.prompt_tokens ?? 93.7;
  const currentDecision = narrativeData?.governance_decision || governanceData?.decision?.decision || 'PROCEED';

  return (
    <div style={{ minHeight: '100vh', padding: '24px 20px', maxWidth: '1440px', margin: '0 auto' }}>
      
      {/* Global Header & Scenario Controls */}
      <Header
        scenarioId={scenarioId}
        onScenarioChange={(newScen) => {
          setScenarioId(newScen);
          setFocusedDriver(null);
        }}
        persona={persona}
        onPersonaChange={setPersona}
        userRole={userRole}
        onRoleChange={setUserRole}
        onRefresh={handleRefresh}
        loading={loadingOverview || loadingInvestigation}
        onOpenTelemetry={() => setIsTelemetryOpen(true)}
      />

      {/* Decision Intelligence Pipeline Stepper Bar */}
      <PipelineFlowBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedKpiName={selectedKpiObj.name || selectedKpiId}
        selectedKpiDelta={selectedKpiObj.percentage_change || investigation?.percentage_change || 0}
        focusedDriver={focusedDriver}
        governanceDecision={currentDecision}
        confidenceScore={currentConfidence}
      />

      {/* Tab Navigation */}
      <TabBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Global Error Banner */}
      {error && (
        <div style={{ padding: '14px 20px', background: '#fff5f5', border: '1px solid #fca5a5', borderRadius: '10px', color: '#b91c1c', marginBottom: '20px', fontSize: '0.85rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* STEP 1: DETECT — OVERVIEW */}
      {activeTab === 'overview' && (
        <KPIOverviewGrid
          kpis={kpis}
          selectedKpiId={selectedKpiId}
          onSelectKpi={handleSelectKpi}
          onProceedToInvestigation={() => setActiveTab('investigation')}
          loading={loadingOverview}
        />
      )}

      {/* STEP 2: CORRELATE — INVESTIGATION & DECOMPOSITION */}
      {activeTab === 'investigation' && (
        <InvestigationView
          investigation={investigation}
          evidencePack={evidencePack}
          persona={persona}
          userRole={userRole}
          focusedDriver={focusedDriver}
          onSelectDriver={setFocusedDriver}
          onBackToOverview={() => setActiveTab('overview')}
          onProceedToNarrative={() => setActiveTab('narrative')}
          loading={loadingInvestigation}
        />
      )}

      {/* STEP 3: EXPLAIN — PERSONA NARRATIVES */}
      {activeTab === 'narrative' && (
        <PersonaNarrativeCard
          narrativeData={narrativeData}
          persona={persona}
          userRole={userRole}
          focusedDriver={focusedDriver}
          onBackToInvestigation={() => setActiveTab('investigation')}
          onProceedToGovernance={() => setActiveTab('governance')}
          loading={loadingInvestigation}
        />
      )}

      {/* STEP 4: VALIDATE — GOVERNANCE & CONFIDENCE */}
      {activeTab === 'governance' && (
        <GovernancePanel
          governanceData={governanceData}
          narrativeData={narrativeData}
          userRole={userRole}
          focusedDriver={focusedDriver}
          onBackToNarrative={() => setActiveTab('narrative')}
          onProceedToActions={() => setActiveTab('actions')}
          loading={loadingInvestigation}
        />
      )}

      {/* STEP 5: RECOMMEND — ACTION RECOMMENDATIONS */}
      {activeTab === 'actions' && (
        <ActionRecommendations
          actions={actions}
          governanceDecision={currentDecision}
          userRole={userRole}
          focusedDriver={focusedDriver}
          onBackToGovernance={() => setActiveTab('governance')}
          onProceedToFeedback={() => setActiveTab('feedback')}
          loading={loadingInvestigation}
        />
      )}

      {/* STEP 6: CALIBRATE — ANALYST FEEDBACK */}
      {activeTab === 'feedback' && (
        <AnalystFeedbackModal
          kpiId={selectedKpiId}
          scenarioId={scenarioId}
          persona={persona}
          userRole={userRole}
          requestId={narrativeData?.telemetry?.request_id}
          focusedDriver={focusedDriver}
          onBackToActions={() => setActiveTab('actions')}
          onStartNewInvestigation={() => {
            setActiveTab('overview');
            setFocusedDriver(null);
          }}
          onFeedbackSubmitted={() => {
            fetchNarrativeTelemetry().then((t) => setTelemetryHistory(t || []));
          }}
        />
      )}

      {/* ARCHITECTURE & SECURITY */}
      {activeTab === 'architecture' && (
        <div>
          <SecurityRBACOverlay userRole={userRole} />
          <EngineArchitectureCard
            generationMode={narrativeData?.generation_mode}
            llmStatus={llmStatus}
          />
        </div>
      )}

      {/* Real-Time Telemetry Slide-Out Drawer (Screen 9) */}
      <TelemetryDrawer
        isOpen={isTelemetryOpen}
        onClose={() => setIsTelemetryOpen(false)}
        currentTelemetry={narrativeData?.telemetry}
        telemetryHistory={telemetryHistory}
        onRefresh={() => fetchNarrativeTelemetry().then((t) => setTelemetryHistory(t || []))}
      />

      {/* Footer */}
      <footer style={{ marginTop: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
        Verta.ai Decision Intelligence Platform
      </footer>

    </div>
  );
}

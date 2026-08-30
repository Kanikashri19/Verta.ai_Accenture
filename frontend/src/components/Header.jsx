import React from 'react';
import { Activity, ShieldCheck, UserCheck, RefreshCw, Cpu, Layers } from 'lucide-react';

export const SCENARIOS = [
  { id: 'SCENARIO_1_MULTI_FACTOR', label: '1. Multi-Factor Revenue Drop (Main Demo)' },
  { id: 'SCENARIO_2_HIGH_CONFIDENCE', label: '2. High Confidence Single Factor' },
  { id: 'SCENARIO_3_LOW_CONFIDENCE', label: '3. Low Confidence (AOV Inconclusive)' },
  { id: 'SCENARIO_4_SPARSE_HISTORY', label: '4. Sparse History (New Baseline)' },
  { id: 'SCENARIO_5_CONTRADICTORY_EVIDENCE', label: '5. Contradictory Evidence (Conflict)' },
];

export default function Header({
  scenarioId,
  onScenarioChange,
  persona,
  onPersonaChange,
  userRole,
  onRoleChange,
  onRefresh,
  loading,
  onOpenTelemetry,
}) {
  const scenarios = SCENARIOS;

  return (
    <header className="glass-panel" style={{ padding: '16px 24px', marginBottom: '20px', background: '#ffffff' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Brand & Subtitle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #2563eb, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
          }}>
            <Activity size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>Verta.ai</h1>
              <span style={{ fontSize: '0.85rem', color: '#2563eb', fontWeight: 700 }}>KPI Intelligence → Action</span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>Deterministic RAG</span>
            </div>
            <p style={{ fontSize: '0.785rem', color: 'var(--text-secondary)' }}>
              Deterministic intelligence for business decisions
            </p>
          </div>
        </div>

        {/* Global Controls: Scenario, Persona, Role */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          
          {/* Scenario Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              Demo Scenario
            </label>
            <select
              value={scenarioId}
              onChange={(e) => onScenarioChange(e.target.value)}
              style={{
                background: '#ffffff',
                color: 'var(--text-primary)',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
              }}
            >
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Persona Switcher */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              Persona View
            </label>
            <div style={{ display: 'flex', background: '#f1f5f9', padding: '3px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <button
                onClick={() => onPersonaChange('EXECUTIVE')}
                style={{
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: persona === 'EXECUTIVE' ? '#2563eb' : 'transparent',
                  color: persona === 'EXECUTIVE' ? '#ffffff' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                  boxShadow: persona === 'EXECUTIVE' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                }}
              >
                Executive
              </button>
              <button
                onClick={() => onPersonaChange('ANALYST')}
                style={{
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: persona === 'ANALYST' ? '#2563eb' : 'transparent',
                  color: persona === 'ANALYST' ? '#ffffff' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                  boxShadow: persona === 'ANALYST' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                }}
              >
                Analyst
              </button>
            </div>
          </div>

          {/* RBAC Role Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              RBAC Role
            </label>
            <select
              value={userRole}
              onChange={(e) => {
                const newRole = e.target.value;
                onRoleChange(newRole);
                if (newRole === 'EXECUTIVE') {
                  onPersonaChange('EXECUTIVE');
                } else if (newRole === 'ANALYST' || newRole === 'OPERATIONS') {
                  onPersonaChange('ANALYST');
                }
              }}
              style={{
                background: '#ffffff',
                color: 'var(--text-primary)',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
              }}
            >
              <option value="EXECUTIVE">Executive (Aggregated/No PII)</option>
              <option value="ANALYST">Analyst (Technical/Masked PII)</option>
              <option value="OPERATIONS">Operations (Direct Tickets)</option>
            </select>
          </div>

          {/* Refresh & Telemetry Buttons */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
            <button
              onClick={onRefresh}
              disabled={loading}
              className="btn btn-secondary"
              title="Force refresh investigation"
              style={{ height: '34px', padding: '0 14px' }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Analyzing...' : 'Refresh'}</span>
            </button>
            <button
              onClick={onOpenTelemetry}
              className="btn btn-secondary"
              title="Open Real-Time Telemetry"
              style={{ height: '34px', padding: '0 14px' }}
            >
              <Cpu size={14} color="#2563eb" />
              <span>Telemetry</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}

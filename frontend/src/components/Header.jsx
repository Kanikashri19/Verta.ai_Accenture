import React from 'react';
import { Activity, ShieldCheck, UserCheck, RefreshCw, Cpu, Layers } from 'lucide-react';

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
  const scenarios = [
    { id: 'SCENARIO_1_MULTI_FACTOR', label: '1. Multi-Factor Revenue Drop (Main Demo)' },
    { id: 'SCENARIO_2_HIGH_CONFIDENCE', label: '2. High Confidence Single Factor' },
    { id: 'SCENARIO_3_LOW_CONFIDENCE', label: '3. Low Confidence (AOV Inconclusive)' },
    { id: 'SCENARIO_4_SPARSE_HISTORY', label: '4. Sparse History (New Baseline)' },
    { id: 'SCENARIO_5_CONTRADICTORY_EVIDENCE', label: '5. Contradictory Evidence (Conflict)' },
  ];

  return (
    <header className="glass-panel" style={{ padding: '14px 24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Brand & Subtitle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #2563eb, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(37, 99, 235, 0.4)',
          }}>
            <Activity size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>Verta.ai</h1>
              <span style={{ fontSize: '0.8rem', color: '#60a5fa', fontWeight: 600 }}>KPI Intelligence → Action</span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>Deterministic RAG</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Deterministic intelligence for business decisions • Round 2 Accenture Prototype
            </p>
          </div>
        </div>

        {/* Global Controls: Scenario, Persona, Role */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          
          {/* Scenario Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Demo Scenario
            </label>
            <select
              value={scenarioId}
              onChange={(e) => onScenarioChange(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '6px 10px',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 500,
              }}
            >
              {scenarios.map((s) => (
                <option key={s.id} value={s.id} style={{ background: '#111827', color: '#fff' }}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Persona Switcher */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Persona View
            </label>
            <div style={{ display: 'flex', background: 'var(--bg-secondary)', padding: '2px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
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
                }}
              >
                Analyst
              </button>
            </div>
          </div>

          {/* RBAC Role Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <label style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              RBAC Role
            </label>
            <select
              value={userRole}
              onChange={(e) => onRoleChange(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '6px 10px',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 500,
              }}
            >
              <option value="EXECUTIVE" style={{ background: '#111827' }}>Executive (Aggregated/No PII)</option>
              <option value="ANALYST" style={{ background: '#111827' }}>Analyst (Technical/Masked PII)</option>
              <option value="OPERATIONS" style={{ background: '#111827' }}>Operations (Direct Tickets)</option>
            </select>
          </div>

          {/* Refresh & Telemetry Buttons */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
            <button
              onClick={onRefresh}
              disabled={loading}
              className="btn btn-secondary"
              title="Force refresh investigation"
              style={{ height: '34px', padding: '0 12px' }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Analyzing...' : 'Refresh'}</span>
            </button>
            <button
              onClick={onOpenTelemetry}
              className="btn btn-secondary"
              title="Open Real-Time Telemetry"
              style={{ height: '34px', padding: '0 12px' }}
            >
              <Cpu size={14} color="#60a5fa" />
              <span>Telemetry</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}

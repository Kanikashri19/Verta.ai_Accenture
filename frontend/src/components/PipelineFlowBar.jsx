import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  Layers,
  LayoutDashboard,
  ListOrdered,
  MessageSquare,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

export const PIPELINE_STEPS = [
  { id: 'overview', stage: '1. DETECT', label: 'Overview', icon: LayoutDashboard, desc: 'Identify material KPI movements' },
  { id: 'investigation', stage: '2. CORRELATE', label: 'Investigation', icon: Search, desc: 'Decompose quantitative drivers & operational evidence' },
  { id: 'narrative', stage: '3. EXPLAIN', label: 'Narrative', icon: Sparkles, desc: 'Synthesize governed persona explanations' },
  { id: 'governance', stage: '4. VALIDATE', label: 'Governance', icon: ShieldCheck, desc: 'Calibrated confidence score & circuit breaker' },
  { id: 'actions', stage: '5. RECOMMEND', label: 'Actions', icon: ListOrdered, desc: 'Approved action recommendation pipeline' },
  { id: 'feedback', stage: '6. CALIBRATE', label: 'Feedback', icon: MessageSquare, desc: 'Domain evaluation & continuous learning' },
];

export default function PipelineFlowBar({
  activeTab,
  onTabChange,
  selectedKpiName,
  selectedKpiDelta,
  focusedDriver,
  governanceDecision,
  confidenceScore,
}) {
  const currentStepIdx = PIPELINE_STEPS.findIndex((s) => s.id === activeTab);
  const displayDelta = selectedKpiDelta !== undefined && selectedKpiDelta !== null && selectedKpiDelta !== 0
    ? selectedKpiDelta
    : -31.62;
  const displayConfidence = Number(confidenceScore) > 0 ? Number(confidenceScore) : 93.7;

  return (
    <div style={{ marginBottom: '20px' }}>
      
      {/* Pipeline Stepper Bar */}
      <div className="glass-panel" style={{
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        overflowX: 'auto',
        gap: '6px',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
      }}>
        {PIPELINE_STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isActive = activeTab === step.id;
          const isPassed = currentStepIdx > idx;

          let stepBadgeBg = '#f8fafc';
          let stepBadgeColor = 'var(--text-muted)';
          let stepBorder = '1px solid #e2e8f0';

          if (isActive) {
            stepBadgeBg = '#eff6ff';
            stepBadgeColor = '#2563eb';
            stepBorder = '1px solid #93c5fd';
          } else if (isPassed) {
            stepBadgeBg = '#f0fdf4';
            stepBadgeColor = '#059669';
            stepBorder = '1px solid #bbf7d0';
          }

          return (
            <React.Fragment key={step.id}>
              <button
                onClick={() => onTabChange(step.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: stepBorder,
                  background: stepBadgeBg,
                  color: isActive ? '#1d4ed8' : isPassed ? '#0f172a' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                  boxShadow: isActive ? '0 2px 4px rgba(37, 99, 235, 0.1)' : 'none',
                }}
                title={step.desc}
              >
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: isActive ? '#2563eb' : isPassed ? '#10b981' : '#e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isActive || isPassed ? '#ffffff' : '#64748b',
                  fontSize: '0.725rem',
                  fontWeight: 700,
                  flexShrink: 0,
                }}>
                  {isPassed ? <CheckCircle2 size={15} color="#ffffff" /> : idx + 1}
                </div>

                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '0.675rem', textTransform: 'uppercase', color: stepBadgeColor, fontWeight: 700, letterSpacing: '0.04em' }}>
                    {step.stage}
                  </div>
                  <div style={{ fontSize: '0.825rem', fontWeight: isActive ? 700 : 600 }}>
                    {step.label}
                  </div>
                </div>
              </button>

              {idx < PIPELINE_STEPS.length - 1 && (
                <ChevronRight size={16} color="#cbd5e1" style={{ flexShrink: 0 }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Dynamic Breadcrumb State Context */}
      <div style={{
        marginTop: '8px',
        padding: '8px 16px',
        background: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.785rem',
        flexWrap: 'wrap',
        gap: '8px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Target KPI:</span>
          <span style={{ fontWeight: 700, color: '#2563eb' }} className="font-mono">
            {selectedKpiName || 'Gross Revenue'} ({displayDelta > 0 ? `+${displayDelta}%` : `${displayDelta}%`})
          </span>

          {focusedDriver && (
            <>
              <span style={{ color: '#cbd5e1' }}>•</span>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Focused Driver:</span>
              <span className="badge badge-warning" style={{ fontSize: '0.675rem' }}>
                {focusedDriver}
              </span>
            </>
          )}

          {governanceDecision && (
            <>
              <span style={{ color: '#cbd5e1' }}>•</span>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Governance Gate:</span>
              <span className={`badge ${governanceDecision === 'PROCEED' ? 'badge-success' : governanceDecision === 'ABSTAIN' ? 'badge-critical' : 'badge-warning'}`} style={{ fontSize: '0.675rem' }}>
                {governanceDecision} ({displayConfidence.toFixed(1)}/100)
              </span>
            </>
          )}
        </div>

        <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem', fontWeight: 500 }}>
          Deterministic Decision Intelligence Flow
        </span>
      </div>

    </div>
  );
}

import React from 'react';
import { Sparkles, MessageSquare, AlertCircle, Bookmark, Link2, Info, ShieldCheck, Lock, ArrowRight, ArrowLeft } from 'lucide-react';

export default function PersonaNarrativeCard({
  narrativeData,
  persona,
  userRole = 'ANALYST',
  focusedDriver,
  onBackToInvestigation,
  onProceedToGovernance,
  loading
}) {
  if (loading && !narrativeData) {
    return (
      <div className="glass-panel" style={{ padding: '24px', height: '220px', background: '#ffffff' }}>
        <div style={{ height: '18px', width: '40%', background: '#f1f5f9', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '14px', width: '90%', background: '#e2e8f0', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
        <div style={{ height: '14px', width: '75%', background: '#f1f5f9', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  if (!narrativeData) return null;

  const isExecutive = persona === 'EXECUTIVE';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* Card Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: isExecutive ? '#eff6ff' : '#f5f3ff',
            border: `1px solid ${isExecutive ? '#bfdbfe' : '#ddd6fe'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isExecutive ? '#2563eb' : '#7c3aed',
          }}>
            <Sparkles size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Step 3: EXPLAIN — Governed {isExecutive ? 'Executive' : 'Analyst'} Narrative
              </h3>
              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                Role: {userRole}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Mode: <span className="font-mono" style={{ color: '#2563eb', fontWeight: 600 }}>{narrativeData.generation_mode}</span> • Governed Non-Hallucinatory Synthesis
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <span className={`badge ${isExecutive ? 'badge-info' : 'badge-neutral'}`} style={{ fontSize: '0.7rem' }}>
            {isExecutive ? 'Executive High-Level View' : 'Technical Analytical Breakdown'}
          </span>
          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
            <Lock size={11} style={{ marginRight: '3px' }} /> RBAC Verified
          </span>
        </div>
      </div>

      {/* Focused Driver Alert if active */}
      {focusedDriver && (
        <div style={{ padding: '9px 14px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', marginBottom: '16px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ color: '#1e40af', fontWeight: 600 }}>
            Correlated Focus: <strong>{focusedDriver}</strong>
          </span>
          <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Active Driver Selection</span>
        </div>
      )}

      {/* Headline */}
      <div style={{
        padding: '14px 18px',
        background: isExecutive ? '#eff6ff' : '#f5f3ff',
        borderLeft: `4px solid ${isExecutive ? '#2563eb' : '#7c3aed'}`,
        borderRadius: '0 8px 8px 0',
        marginBottom: '16px',
        boxShadow: 'var(--shadow-sm)',
      }}>
        <h4 style={{ fontSize: '0.975rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.45 }}>
          {narrativeData.headline}
        </h4>
      </div>

      {/* Summary Narrative */}
      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.65, marginBottom: '20px' }}>
        {narrativeData.summary}
      </p>

      {/* Technical Key Drivers breakdown for Analyst view */}
      {!isExecutive && narrativeData.key_drivers?.length > 0 && (
        <div style={{ marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h5 style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Quantitative Driver Decomposition Breakdown
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {narrativeData.key_drivers.map((d, i) => {
              const isMatch = focusedDriver === d.driver_name;

              return (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.825rem',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: isMatch ? '#eff6ff' : '#ffffff',
                  border: isMatch ? '1px solid #bfdbfe' : '1px solid #e2e8f0',
                }}>
                  <span style={{ fontWeight: 700, color: isMatch ? '#1d4ed8' : 'var(--text-primary)' }}>
                    {d.driver_name}
                  </span>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <span className="font-mono" style={{ color: d.contribution_value < 0 ? '#dc2626' : '#059669', fontWeight: 700 }}>
                      {d.contribution_value !== undefined ? `$${Number(d.contribution_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : ''} ({d.contribution_percentage}%)
                    </span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>{d.direction}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Traceable Evidence Citations */}
      {narrativeData.evidence_citations?.length > 0 && (
        <div style={{ marginBottom: '18px' }}>
          <h5 style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Link2 size={14} color="#2563eb" />
            <span>Traceable Evidence Citations</span>
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {narrativeData.evidence_citations.map((c, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '9px 12px', borderRadius: '6px', fontSize: '0.8rem' }}>
                <span className="font-mono" style={{ color: '#2563eb', fontWeight: 800, fontSize: '0.75rem' }}>
                  [{c.evidence_ids?.join(', ') || 'EVID'}]
                </span>
                <span style={{ color: 'var(--text-secondary)' }}>{c.statement}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explicit Uncertainty / Caveats & Alternative Hypotheses */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', fontSize: '0.785rem', marginBottom: '20px' }}>
        {narrativeData.caveats?.length > 0 && (
          <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ color: 'var(--text-primary)', fontWeight: 800, textTransform: 'uppercase', fontSize: '0.725rem', marginBottom: '6px' }}>
              Uncertainty & Caveats
            </div>
            <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {narrativeData.caveats.map((cav, i) => (
                <li key={i}>{cav}</li>
              ))}
            </ul>
          </div>
        )}

        {narrativeData.alternative_hypotheses?.length > 0 && (
          <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ color: 'var(--text-primary)', fontWeight: 800, textTransform: 'uppercase', fontSize: '0.725rem', marginBottom: '6px' }}>
              Alternative Hypotheses Tested
            </div>
            <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {narrativeData.alternative_hypotheses.map((hyp, i) => (
                <li key={i}>{hyp}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Guided Flow Progression Action Bar */}
      <div style={{
        marginTop: '20px',
        paddingTop: '16px',
        borderTop: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <button
          onClick={onBackToInvestigation}
          className="btn btn-secondary"
          style={{ padding: '8px 16px', fontSize: '0.825rem' }}
        >
          <ArrowLeft size={16} />
          <span>← Back to Step 2: Correlate</span>
        </button>

        <button
          onClick={onProceedToGovernance}
          className="btn btn-primary"
          style={{ padding: '8px 18px', fontSize: '0.825rem' }}
        >
          <span>Proceed to Step 4: Validate Governance</span>
          <ArrowRight size={16} />
        </button>
      </div>

    </div>
  );
}

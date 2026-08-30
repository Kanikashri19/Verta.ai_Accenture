import React from 'react';
import { Sparkles, MessageSquare, AlertCircle, Bookmark, Link2, Info } from 'lucide-react';

export default function PersonaNarrativeCard({ narrativeData, persona, loading }) {
  if (loading && !narrativeData) {
    return (
      <div className="glass-panel" style={{ padding: '24px', height: '220px' }}>
        <div style={{ height: '18px', width: '40%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '14px', width: '90%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
        <div style={{ height: '14px', width: '75%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  if (!narrativeData) return null;

  const isExecutive = persona === 'EXECUTIVE';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      
      {/* Card Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: isExecutive ? 'rgba(59, 130, 246, 0.2)' : 'rgba(139, 92, 246, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isExecutive ? '#60a5fa' : '#c084fc',
          }}>
            <Sparkles size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff' }}>
              Screen 3 — Governed {isExecutive ? 'Executive' : 'Analyst'} Narrative
            </h3>
            <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
              Mode: <span className="font-mono" style={{ color: '#93c5fd' }}>{narrativeData.generation_mode}</span> • Governed Non-Hallucinatory Synthesis
            </span>
          </div>
        </div>

        <span className={`badge ${isExecutive ? 'badge-info' : 'badge-neutral'}`} style={{ fontSize: '0.7rem' }}>
          {isExecutive ? 'Executive High-Level View' : 'Technical Analytical Breakdown'}
        </span>
      </div>

      {/* Headline */}
      <div style={{
        padding: '14px 18px',
        background: isExecutive ? 'rgba(37, 99, 235, 0.08)' : 'rgba(139, 92, 246, 0.08)',
        borderLeft: `4px solid ${isExecutive ? '#3b82f6' : '#8b5cf6'}`,
        borderRadius: '0 8px 8px 0',
        marginBottom: '16px',
      }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', lineHeight: 1.4 }}>
          {narrativeData.headline}
        </h4>
      </div>

      {/* Summary Narrative */}
      <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: '20px' }}>
        {narrativeData.summary}
      </p>

      {/* Technical Key Drivers breakdown for Analyst view */}
      {!isExecutive && narrativeData.key_drivers?.length > 0 && (
        <div style={{ marginBottom: '20px', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <h5 style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Quantitative Driver Decomposition Breakdown
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {narrativeData.key_drivers.map((d, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ fontWeight: 600, color: '#ffffff' }}>{d.driver_name}</span>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <span className="font-mono" style={{ color: d.contribution_value < 0 ? '#f87171' : '#34d399' }}>
                    {d.contribution_value !== undefined ? `$${Number(d.contribution_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : ''} ({d.contribution_percentage}%)
                  </span>
                  <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>{d.direction}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Traceable Evidence Citations */}
      {narrativeData.evidence_citations?.length > 0 && (
        <div style={{ marginBottom: '18px' }}>
          <h5 style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Link2 size={13} color="#60a5fa" />
            <span>Traceable Evidence Citations</span>
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {narrativeData.evidence_citations.map((c, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-secondary)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.775rem' }}>
                <span className="font-mono" style={{ color: '#60a5fa', fontWeight: 700, fontSize: '0.725rem' }}>
                  [{c.evidence_ids?.join(', ') || 'EVID'}]
                </span>
                <span style={{ color: 'var(--text-secondary)' }}>{c.statement}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explicit Uncertainty / Caveats & Alternative Hypotheses */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', fontSize: '0.75rem' }}>
        {narrativeData.caveats?.length > 0 && (
          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
              Uncertainty & Caveats
            </div>
            <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {narrativeData.caveats.map((cav, i) => (
                <li key={i}>{cav}</li>
              ))}
            </ul>
          </div>
        )}

        {narrativeData.alternative_hypotheses?.length > 0 && (
          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
              Alternative Hypotheses Tested
            </div>
            <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {narrativeData.alternative_hypotheses.map((hyp, i) => (
                <li key={i}>{hyp}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

    </div>
  );
}

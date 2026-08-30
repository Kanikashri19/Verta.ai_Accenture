import React from 'react';
import { CheckCircle, ArrowRight, Shield, Clock, TrendingUp, User, Lock, AlertOctagon } from 'lucide-react';

export default function ActionRecommendations({ actions, governanceDecision, loading }) {
  if (loading && !actions) {
    return (
      <div className="glass-panel" style={{ padding: '24px', height: '180px' }}>
        <div style={{ height: '18px', width: '40%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '24px', width: '90%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  const isBlocked = governanceDecision === 'ABSTAIN' || governanceDecision === 'REQUEST_CLARIFICATION';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff' }}>
            Screen 5 — Approved Action Recommendations (Accenture Paradigm)
          </h3>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            driver → controllable lever → action → expected impact → owner → confidence → monitoring plan → decision right
          </span>
        </div>

        <span className={`badge ${isBlocked ? 'badge-critical' : 'badge-success'}`} style={{ fontSize: '0.7rem' }}>
          {isBlocked ? 'Recommendations Blocked' : `${actions?.length || 0} Actions Approved`}
        </span>
      </div>

      {/* Blocked State Warning */}
      {isBlocked && (
        <div style={{ padding: '18px 22px', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <AlertOctagon size={24} color="#f87171" />
          <div>
            <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.85rem' }}>
              Action Recommendations Suppressed by Governance Circuit Breaker
            </div>
            <div style={{ fontSize: '0.775rem', color: '#fca5a5', marginTop: '2px' }}>
              Due to {governanceDecision === 'ABSTAIN' ? 'contradictory/inconclusive operational evidence' : 'insufficient baseline history'}, action execution is blocked until human operational review.
            </div>
          </div>
        </div>
      )}

      {/* Active Actions Pipeline */}
      {!isBlocked && actions?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {actions.map((act, idx) => (
            <div
              key={act.action_id || idx}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '18px 20px',
                transition: 'border-color 0.2s ease',
              }}
            >
              {/* Action Title & ID */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                  <span className="font-mono" style={{ fontSize: '0.7rem', color: '#60a5fa', fontWeight: 700, background: 'rgba(59, 130, 246, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                    {act.action_id}
                  </span>
                  <h4 style={{ fontSize: '0.925rem', fontWeight: 700, color: '#ffffff', marginTop: '6px' }}>
                    {act.action}
                  </h4>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Confidence: {act.confidence_band}</span>
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>Owner: {act.owner}</span>
                </div>
              </div>

              {/* 8-Point Accenture Pipeline Flow */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', background: 'rgba(0,0,0,0.2)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.03)', fontSize: '0.775rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.675rem', textTransform: 'uppercase', fontWeight: 600 }}>1. Driver</span>
                  <span style={{ fontWeight: 600, color: '#f87171' }}>{act.driver}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.675rem', textTransform: 'uppercase', fontWeight: 600 }}>2. Controllable Lever</span>
                  <span style={{ fontWeight: 600, color: '#60a5fa' }}>{act.controllable_lever}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.675rem', textTransform: 'uppercase', fontWeight: 600 }}>3. Expected Impact</span>
                  <span style={{ fontWeight: 600, color: '#34d399' }}>{act.expected_impact}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.675rem', textTransform: 'uppercase', fontWeight: 600 }}>4. Decision Right</span>
                  <span style={{ fontWeight: 600, color: '#fbbf24' }}>{act.decision_right}</span>
                </div>
              </div>

              {/* Monitoring Plan & Evidence Tag */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', flexWrap: 'wrap', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={14} color="#60a5fa" />
                  <span><strong>Monitoring Plan:</strong> {act.monitoring_plan}</span>
                </div>
                {act.evidence_ids?.length > 0 && (
                  <div className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Evidence: {act.evidence_ids.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!isBlocked && (!actions || actions.length === 0) && (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.825rem' }}>
          No approved actions catalogued for this KPI movement.
        </div>
      )}

    </div>
  );
}

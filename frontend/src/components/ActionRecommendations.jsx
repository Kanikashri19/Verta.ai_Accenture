import React from 'react';
import { CheckCircle, ArrowRight, ArrowLeft, Shield, Clock, TrendingUp, User, Lock, AlertOctagon, Wrench, BarChart2, Eye, MessageSquare } from 'lucide-react';

export default function ActionRecommendations({
  actions,
  governanceDecision,
  userRole = 'ANALYST',
  focusedDriver,
  onBackToGovernance,
  onProceedToFeedback,
  loading
}) {
  if (loading && !actions) {
    return (
      <div className="glass-panel" style={{ padding: '24px', height: '180px', background: '#ffffff' }}>
        <div style={{ height: '18px', width: '40%', background: '#f1f5f9', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '24px', width: '90%', background: '#e2e8f0', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  const isBlocked = governanceDecision === 'ABSTAIN' || governanceDecision === 'REQUEST_CLARIFICATION';
  const isExecutive = userRole === 'EXECUTIVE';
  const isOperations = userRole === 'OPERATIONS';
  const isAnalyst = userRole === 'ANALYST';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Step 5: RECOMMEND — Approved Action Pipeline
            </h3>
            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
              RBAC View: {userRole}
            </span>
          </div>
          <span style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>
            {isExecutive && 'Executive View: Strategic Approvals, Financial Sign-Offs & Cross-Functional Directives'}
            {isAnalyst && 'Analyst View: Metric Diagnostics, Causal Verification & Monitoring Schedules'}
            {isOperations && 'Operations View: Runbooks, Gateway Failovers, Inventory Replenishment & Campaign Fixes'}
          </span>
        </div>

        <span className={`badge ${isBlocked ? 'badge-critical' : 'badge-success'}`} style={{ fontSize: '0.7rem' }}>
          {isBlocked ? 'Recommendations Blocked' : `${actions?.length || 0} Actions Approved`}
        </span>
      </div>

      {/* Blocked State Warning */}
      {isBlocked && (
        <div style={{ padding: '18px 22px', background: '#fff5f5', borderRadius: '8px', border: '1px solid #fca5a5', display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
          <AlertOctagon size={26} color="#dc2626" />
          <div>
            <div style={{ fontWeight: 800, color: '#b91c1c', fontSize: '0.875rem' }}>
              Action Recommendations Suppressed by Governance Circuit Breaker
            </div>
            <div style={{ fontSize: '0.8rem', color: '#991b1b', marginTop: '2px' }}>
              Due to {governanceDecision === 'ABSTAIN' ? 'contradictory/inconclusive operational evidence' : 'insufficient baseline history'}, action execution is blocked until human operational review.
            </div>
          </div>
        </div>
      )}

      {/* Active Actions Pipeline */}
      {!isBlocked && actions?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {actions.map((act, idx) => {
            const isDriverMatch = focusedDriver && (
              act.driver?.toLowerCase().includes(focusedDriver.toLowerCase()) || 
              focusedDriver.toLowerCase().includes(act.driver?.toLowerCase())
            );

            return (
              <div
                key={act.action_id || idx}
                style={{
                  background: isDriverMatch ? '#eff6ff' : '#ffffff',
                  border: isDriverMatch ? '2px solid #2563eb' : '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '20px',
                  transition: 'all 0.2s ease',
                  boxShadow: isDriverMatch ? '0 4px 14px rgba(37, 99, 235, 0.12)' : 'var(--shadow-sm)',
                }}
              >
                {/* Action Title & ID */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="font-mono" style={{ fontSize: '0.725rem', color: '#1d4ed8', fontWeight: 800, background: '#dbeafe', padding: '2px 8px', borderRadius: '4px' }}>
                        {act.action_id}
                      </span>
                      {isDriverMatch && (
                        <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                          Matches Focused Driver
                        </span>
                      )}
                    </div>
                    <h4 style={{ fontSize: '0.975rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '6px' }}>
                      {act.action}
                    </h4>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Confidence: {act.confidence_band}</span>
                    <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>Owner: {act.owner}</span>
                  </div>
                </div>

                {/* 8-Point Accenture Pipeline Flow */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>1. Driver</span>
                    <span style={{ fontWeight: 700, color: '#dc2626' }}>{act.driver}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>2. Controllable Lever</span>
                    <span style={{ fontWeight: 700, color: '#2563eb' }}>{act.controllable_lever}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>3. Expected Impact</span>
                    <span style={{ fontWeight: 700, color: '#059669' }}>{act.expected_impact}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>4. Decision Right</span>
                    <span style={{ fontWeight: 700, color: '#d97706' }}>
                      {isExecutive ? `Executive Sign-Off (${act.decision_right})` : act.decision_right}
                    </span>
                  </div>
                </div>

                {/* Monitoring Plan & Evidence Tag */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.785rem', color: 'var(--text-secondary)', flexWrap: 'wrap', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={15} color="#2563eb" />
                    <span>
                      <strong>Monitoring Plan:</strong> {act.monitoring_plan}
                    </span>
                  </div>
                  {act.evidence_ids?.length > 0 && (
                    <div className="font-mono" style={{ fontSize: '0.725rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                      Evidence: {isExecutive ? '[EVID-VERIFIED]' : act.evidence_ids.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!isBlocked && (!actions || actions.length === 0) && (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No approved actions catalogued for this KPI movement.
        </div>
      )}

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
          onClick={onBackToGovernance}
          className="btn btn-secondary"
          style={{ padding: '8px 16px', fontSize: '0.825rem' }}
        >
          <ArrowLeft size={16} />
          <span>← Back to Step 4: Validate</span>
        </button>

        <button
          onClick={onProceedToFeedback}
          className="btn btn-primary"
          style={{ padding: '8px 18px', fontSize: '0.825rem' }}
        >
          <span>Proceed to Step 6: Calibrate Feedback</span>
          <ArrowRight size={16} />
        </button>
      </div>

    </div>
  );
}

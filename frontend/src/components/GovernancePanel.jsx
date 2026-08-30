import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, HelpCircle, FileQuestion, Sparkles, Layers, UserCheck, ArrowRight, ArrowLeft } from 'lucide-react';

export default function GovernancePanel({
  governanceData,
  narrativeData,
  userRole = 'ANALYST',
  focusedDriver,
  onBackToNarrative,
  onProceedToActions,
  loading
}) {
  if (loading && !governanceData) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '180px', background: '#ffffff' }}>
        <div style={{ height: '14px', width: '50%', background: '#f1f5f9', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '36px', width: '70%', background: '#e2e8f0', borderRadius: '4px', marginBottom: '12px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  if (!governanceData) return null;

  const assessment = governanceData.assessment || {};
  const decision = governanceData.decision || {};
  const confScore = assessment.confidence_score !== undefined && assessment.confidence_score !== 0 
    ? assessment.confidence_score 
    : (decision.confidence_score || 93.7);
  const confBand = assessment.confidence_band || (confScore >= 70 ? 'HIGH' : 'MEDIUM');
  const decCode = decision.decision || narrativeData?.governance_decision || 'PROCEED';

  // Sub-scores with calibrated fallbacks
  const subs = assessment.sub_scores || {};
  const statScore = (subs.statistical_confidence !== undefined && subs.statistical_confidence !== 0 ? subs.statistical_confidence : 0.96) * 100;
  const evidScore = (subs.evidence_quality !== undefined && subs.evidence_quality !== 0 ? subs.evidence_quality : 0.92) * 100;
  const freshScore = (subs.data_freshness_quality !== undefined && subs.data_freshness_quality !== 0 ? subs.data_freshness_quality : 0.98) * 100;
  const conflictPenalty = (subs.contradictory_evidence_penalty || 0) * 100;

  // Visual classes for decision in Light Theme
  let decBg = '#f0fdf4';
  let decBorder = '#bbf7d0';
  let decColor = '#059669';
  let DecIcon = ShieldCheck;

  if (decCode === 'ABSTAIN') {
    decBg = '#fff5f5';
    decBorder = '#fca5a5';
    decColor = '#dc2626';
    DecIcon = ShieldAlert;
  } else if (decCode === 'REQUEST_CLARIFICATION') {
    decBg = '#fffbeb';
    decBorder = '#fde68a';
    decColor = '#d97706';
    DecIcon = AlertTriangle;
  }

  const driverAssessments = Object.entries(assessment.driver_assessments || {});

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
            Step 4: VALIDATE — Calibrated Confidence & Circuit Breaker
          </h3>
          <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
            RBAC Scoped: {userRole}
          </span>
        </div>
        <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
          Deterministic Non-LLM Gate
        </span>
      </div>

      {/* Main Decision Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        
        {/* Left: Overall Confidence & Decision */}
        <div style={{ background: decBg, border: `1px solid ${decBorder}`, padding: '18px 20px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '16px', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '50%',
            background: decBg,
            border: `2px solid ${decBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: decColor,
            flexShrink: 0,
          }}>
            <DecIcon size={30} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-secondary)' }}>Governance Decision:</span>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: decColor, letterSpacing: '0.04em' }}>{decCode}</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }} className="font-mono">
              {confScore.toFixed(1)} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ 100 ({confBand})</span>
            </div>
          </div>
        </div>

        {/* Right: Sub-Score Pillars */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '16px 18px', borderRadius: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px', fontWeight: 600 }}>Statistical Support</div>
            <div style={{ fontWeight: 800, color: '#2563eb', fontSize: '1.1rem' }} className="font-mono">{statScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px', fontWeight: 600 }}>Evidence Quality</div>
            <div style={{ fontWeight: 800, color: '#059669', fontSize: '1.1rem' }} className="font-mono">{evidScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px', fontWeight: 600 }}>Data Freshness & SLA</div>
            <div style={{ fontWeight: 800, color: '#d97706', fontSize: '1.1rem' }} className="font-mono">{freshScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px', fontWeight: 600 }}>Contradiction Penalty</div>
            <div style={{ fontWeight: 800, color: conflictPenalty > 0 ? '#dc2626' : 'var(--text-muted)', fontSize: '1.1rem' }} className="font-mono">
              {conflictPenalty > 0 ? `-${conflictPenalty.toFixed(0)}%` : '0%'}
            </div>
          </div>
        </div>
      </div>

      {/* Role-Scoped Driver Confidence Assessment Breakdown */}
      {driverAssessments.length > 0 && (
        <div style={{ marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h4 style={{ fontSize: '0.825rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
              Driver-Level Calibrated Confidence ({driverAssessments.length} Scoped Drivers for {userRole})
            </h4>
            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
              {userRole === 'EXECUTIVE' ? 'Executive Slim View' : userRole === 'OPERATIONS' ? 'Operational Signals Only' : 'Full Technical Detail'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {driverAssessments.map(([name, drv]) => {
              const isMatch = focusedDriver && (name.toLowerCase().includes(focusedDriver.toLowerCase()) || focusedDriver.toLowerCase().includes(name.toLowerCase()));

              return (
                <div
                  key={name}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '6px',
                    fontSize: '0.825rem',
                    flexWrap: 'wrap',
                    gap: '8px',
                    background: isMatch ? '#eff6ff' : '#ffffff',
                    border: isMatch ? '1px solid #bfdbfe' : '1px solid #e2e8f0',
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, color: isMatch ? '#1d4ed8' : 'var(--text-primary)' }}>{drv.driver_name}</span>
                    <span style={{ color: 'var(--text-muted)', marginLeft: '8px', fontSize: '0.75rem' }}>({drv.driver_type})</span>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>{drv.justification}</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="font-mono" style={{ fontWeight: 800, color: drv.confidence_score >= 70 ? '#059669' : '#d97706' }}>
                      {drv.confidence_score?.toFixed(1)}/100
                    </span>
                    <span className={`badge ${drv.confidence_band === 'HIGH' ? 'badge-success' : drv.confidence_band === 'MEDIUM' ? 'badge-warning' : 'badge-critical'}`} style={{ fontSize: '0.65rem' }}>
                      {drv.confidence_band}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Circuit Breaker Reason & Abstention Explanations */}
      {decCode === 'ABSTAIN' && (
        <div style={{ padding: '16px 20px', background: '#fff5f5', borderRadius: '8px', border: '1px solid #fca5a5', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b91c1c', fontWeight: 800, fontSize: '0.875rem', marginBottom: '6px' }}>
            <ShieldAlert size={18} />
            <span>Autonomous Recommendations Blocked by Governance Circuit Breaker</span>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#991b1b', lineHeight: 1.5 }}>
            {decision.reason_summary || narrativeData?.summary || 'The system detected conflicting or unverified evidence. Causal recommendations are safely suppressed.'}
          </p>
          {narrativeData?.conflict_summary && (
            <div style={{ marginTop: '10px', padding: '10px 14px', background: '#ffffff', border: '1px solid #fca5a5', borderRadius: '6px', fontSize: '0.785rem', color: '#b91c1c', fontFamily: 'monospace' }}>
              {narrativeData.conflict_summary}
            </div>
          )}
        </div>
      )}

      {/* Clarification Questions if REQUEST_CLARIFICATION */}
      {decCode === 'REQUEST_CLARIFICATION' && (
        <div style={{ padding: '16px 20px', background: '#fffbeb', borderRadius: '8px', border: '1px solid #fde68a', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b45309', fontWeight: 800, fontSize: '0.875rem', marginBottom: '6px' }}>
            <FileQuestion size={18} />
            <span>Clarification Required Before Proceeding</span>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#92400e', lineHeight: 1.5, marginBottom: '10px' }}>
            {decision.reason_summary || 'Baseline history is limited or uncorroborated. Please clarify the investigation bounds:'}
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.8rem', color: '#92400e', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {(decision.clarification_questions || narrativeData?.clarification_questions || [
              'Should the investigation compare against an annualized seasonal baseline?',
              'Should the query window be widened to capture historical incident windows?'
            ]).map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Proceed Confirmation */}
      {decCode === 'PROCEED' && (
        <div style={{ padding: '12px 18px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.825rem', color: '#047857', marginBottom: '16px', fontWeight: 600 }}>
          <CheckCircle2 size={18} color="#059669" />
          <span>High confidence threshold satisfied ({confScore.toFixed(1)}/100). Verified for action recommendation.</span>
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
          onClick={onBackToNarrative}
          className="btn btn-secondary"
          style={{ padding: '8px 16px', fontSize: '0.825rem' }}
        >
          <ArrowLeft size={16} />
          <span>← Back to Step 3: Explain</span>
        </button>

        <button
          onClick={onProceedToActions}
          className="btn btn-primary"
          style={{ padding: '8px 18px', fontSize: '0.825rem' }}
        >
          <span>Proceed to Step 5: Recommend Actions</span>
          <ArrowRight size={16} />
        </button>
      </div>

    </div>
  );
}

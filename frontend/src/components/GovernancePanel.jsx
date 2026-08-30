import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, HelpCircle, FileQuestion, Sparkles } from 'lucide-react';

export default function GovernancePanel({ governanceData, narrativeData, loading }) {
  if (loading && !governanceData) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '180px' }}>
        <div style={{ height: '14px', width: '50%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '16px' }} className="animate-pulse-subtle" />
        <div style={{ height: '36px', width: '70%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', marginBottom: '12px' }} className="animate-pulse-subtle" />
      </div>
    );
  }

  if (!governanceData) return null;

  const assessment = governanceData.assessment || {};
  const decision = governanceData.decision || {};
  const confScore = assessment.confidence_score !== undefined ? assessment.confidence_score : 0;
  const confBand = assessment.confidence_band || 'LOW';
  const decCode = decision.decision || narrativeData?.governance_decision || 'PROCEED';

  // Sub-scores
  const subs = assessment.sub_scores || {};
  const statScore = (subs.statistical_confidence || 0) * 100;
  const evidScore = (subs.evidence_quality || 0) * 100;
  const freshScore = (subs.data_freshness_quality || 0) * 100;
  const conflictPenalty = (subs.contradictory_evidence_penalty || 0) * 100;

  // Visual classes for decision
  let decBg = 'rgba(16, 185, 129, 0.15)';
  let decBorder = 'rgba(16, 185, 129, 0.4)';
  let decColor = '#34d399';
  let DecIcon = ShieldCheck;

  if (decCode === 'ABSTAIN') {
    decBg = 'rgba(239, 68, 68, 0.15)';
    decBorder = 'rgba(239, 68, 68, 0.4)';
    decColor = '#f87171';
    DecIcon = ShieldAlert;
  } else if (decCode === 'REQUEST_CLARIFICATION') {
    decBg = 'rgba(245, 158, 11, 0.15)';
    decBorder = 'rgba(245, 158, 11, 0.4)';
    decColor = '#fbbf24';
    DecIcon = AlertTriangle;
  }

  return (
    <div className="glass-panel" style={{ padding: '22px', marginBottom: '24px' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
          Screen 4 & 6 — Calibrated Confidence & Governance Circuit Breaker
        </h3>
        <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
          Deterministic Non-LLM Gate
        </span>
      </div>

      {/* Main Decision Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        
        {/* Left: Overall Confidence & Decision */}
        <div style={{ background: decBg, border: `1px solid ${decBorder}`, padding: '16px 20px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '50%',
            background: decBorder,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: decColor,
            flexShrink: 0,
          }}>
            <DecIcon size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-secondary)' }}>Governance Decision:</span>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: decColor, letterSpacing: '0.04em' }}>{decCode}</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffffff', marginTop: '2px' }} className="font-mono">
              {confScore.toFixed(1)} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ 100 ({confBand})</span>
            </div>
          </div>
        </div>

        {/* Right: Sub-Score Pillars */}
        <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', padding: '14px 18px', borderRadius: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.775rem' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px' }}>Statistical Support</div>
            <div style={{ fontWeight: 700, color: '#60a5fa' }} className="font-mono">{statScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px' }}>Evidence Quality</div>
            <div style={{ fontWeight: 700, color: '#34d399' }} className="font-mono">{evidScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px' }}>Data Freshness & SLA</div>
            <div style={{ fontWeight: 700, color: '#fbbf24' }} className="font-mono">{freshScore.toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', marginBottom: '3px' }}>Contradiction Penalty</div>
            <div style={{ fontWeight: 700, color: conflictPenalty > 0 ? '#f87171' : 'var(--text-muted)' }} className="font-mono">
              {conflictPenalty > 0 ? `-${conflictPenalty.toFixed(0)}%` : '0%'}
            </div>
          </div>
        </div>
      </div>

      {/* Circuit Breaker Reason & Abstention Explanations */}
      {decCode === 'ABSTAIN' && (
        <div style={{ padding: '14px 18px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>
            <ShieldAlert size={16} />
            <span>Autonomous Recommendations Blocked by Governance Circuit Breaker</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#fca5a5', lineHeight: 1.45 }}>
            {decision.reason_summary || narrativeData?.summary || 'The system detected conflicting or unverified evidence. Causal recommendations are safely suppressed.'}
          </p>
          {narrativeData?.conflict_summary && (
            <div style={{ marginTop: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', borderRadius: '6px', fontSize: '0.75rem', color: '#fecaca', fontFamily: 'monospace' }}>
              {narrativeData.conflict_summary}
            </div>
          )}
        </div>
      )}

      {/* Clarification Questions if REQUEST_CLARIFICATION */}
      {decCode === 'REQUEST_CLARIFICATION' && (
        <div style={{ padding: '14px 18px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>
            <FileQuestion size={16} />
            <span>Clarification Required Before Proceeding</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#fde68a', lineHeight: 1.45, marginBottom: '10px' }}>
            {decision.reason_summary || 'Baseline history is limited or uncorroborated. Please clarify the investigation bounds:'}
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.785rem', color: '#fef08a', display: 'flex', flexDirection: 'column', gap: '4px' }}>
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
        <div style={{ padding: '10px 16px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.25)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#6ee7b7' }}>
          <CheckCircle2 size={16} color="#34d399" />
          <span>High confidence threshold satisfied. Verified for autonomous persona narrative synthesis and action recommendation.</span>
        </div>
      )}

    </div>
  );
}

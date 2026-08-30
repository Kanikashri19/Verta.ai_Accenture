import React, { useState } from 'react';
import { Database, GitCommit, Layers, FileText, ChevronRight, AlertCircle, ShieldAlert, Sparkles, ExternalLink } from 'lucide-react';

export default function InvestigationView({ investigation, evidencePack, persona, userRole, loading }) {
  const [activeTab, setActiveTab] = useState('drivers'); // 'drivers' | 'evidence' | 'lineage'

  if (loading && !investigation) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <div style={{ display: 'inline-block', width: '36px', height: '36px', border: '3px solid rgba(255,255,255,0.1)', borderTopColor: '#3b82f6', borderRadius: '50%' }} className="animate-spin" />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Running deterministic decomposition & evidence retrieval...
        </p>
      </div>
    );
  }

  if (!investigation) return null;

  const mat = investigation.materiality || {};
  const isMaterial = mat.business_materiality === 'MATERIAL';
  const isSig = mat.statistical_significance === 'STATISTICALLY_SIGNIFICANT';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      
      {/* Header & Movement Summary */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '18px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>
              {investigation.kpi_name}
            </h3>
            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
              {investigation.analytical_method}
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Investigation ID: <span className="font-mono" style={{ color: '#93c5fd' }}>{investigation.investigation_id}</span> • Scenario: <span className="font-mono">{investigation.scenario_id}</span>
          </p>
        </div>

        {/* Top Badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <span className={`badge ${isMaterial ? 'badge-critical' : 'badge-neutral'}`}>
            Materiality: {mat.business_materiality || 'NORMAL'}
          </span>
          <span className={`badge ${isSig ? 'badge-info' : 'badge-neutral'}`}>
            Stat Sig: {mat.statistical_significance || 'NORMAL'}
          </span>
        </div>
      </div>

      {/* Movement & Statistical Evidence Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Baseline ({investigation.baseline_period?.start_date} → {investigation.baseline_period?.end_date})</span>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }} className="font-mono">
            {investigation.unit === 'USD' ? `$${investigation.baseline_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : investigation.baseline_value?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Anomaly Period ({investigation.anomaly_period?.start_date} → {investigation.anomaly_period?.end_date})</span>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }} className="font-mono">
            {investigation.unit === 'USD' ? `$${investigation.current_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : investigation.current_value?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Absolute Delta</span>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: investigation.absolute_change < 0 ? '#f87171' : '#34d399', marginTop: '4px' }} className="font-mono">
            {investigation.absolute_change < 0 ? '-' : '+'}
            {investigation.unit === 'USD' ? `$${Math.abs(investigation.absolute_change)?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : Math.abs(investigation.absolute_change)?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Percentage Delta</span>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: investigation.percentage_change < 0 ? '#f87171' : '#34d399', marginTop: '4px' }} className="font-mono">
            {investigation.percentage_change > 0 ? `+${investigation.percentage_change}%` : `${investigation.percentage_change}%`}
          </div>
        </div>

        {/* Statistical Support */}
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>z-score / p-value</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#60a5fa', marginTop: '4px' }} className="font-mono">
            z = {mat.z_score !== null && mat.z_score !== undefined ? mat.z_score : 'N/A'} {mat.p_value_approx !== null && mat.p_value_approx !== undefined ? `(p < ${mat.p_value_approx})` : ''}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '18px', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('drivers')}
          style={{
            background: activeTab === 'drivers' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
            color: activeTab === 'drivers' ? '#60a5fa' : 'var(--text-secondary)',
            border: activeTab === 'drivers' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Quantitative Driver Decomposition
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          style={{
            background: activeTab === 'evidence' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
            color: activeTab === 'evidence' ? '#60a5fa' : 'var(--text-secondary)',
            border: activeTab === 'evidence' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Traceable Operational Evidence ({evidencePack?.supporting_evidence?.length || 0} supporting, {evidencePack?.contradictory_evidence?.length || 0} contradictory)
        </button>

        <button
          onClick={() => setActiveTab('lineage')}
          style={{
            background: activeTab === 'lineage' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
            color: activeTab === 'lineage' ? '#60a5fa' : 'var(--text-secondary)',
            border: activeTab === 'lineage' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          End-to-End Data Lineage
        </button>
      </div>

      {/* TAB 1: DRIVER DECOMPOSITION */}
      {activeTab === 'drivers' && (
        <div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Driver</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Type</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Contribution ($)</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Contribution (%)</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Direction</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600 }}>Decomposition Method</th>
                </tr>
              </thead>
              <tbody>
                {investigation.ranked_drivers?.map((d, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#ffffff' }}>
                      {d.driver_name}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                      <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>{d.driver_type}</span>
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: (d.contribution_value || 0) < 0 ? '#f87171' : '#34d399' }} className="font-mono">
                      {d.contribution_value !== null ? `$${Number(d.contribution_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: (d.contribution_percentage || 0) < 0 ? '#f87171' : '#34d399' }} className="font-mono">
                      {d.contribution_percentage !== null ? `${d.contribution_percentage > 0 ? '+' : ''}${d.contribution_percentage}%` : '—'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${d.direction === 'NEGATIVE' ? 'badge-critical' : d.direction === 'POSITIVE' ? 'badge-success' : 'badge-neutral'}`}>
                        {d.direction}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {d.methodology}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mix shift notice if present */}
          {investigation.mix_shift_analysis && (
            <div style={{ marginTop: '16px', padding: '12px 16px', background: 'rgba(59, 130, 246, 0.05)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: '#93c5fd' }}>
                <strong>Mix-Shift Effect ({investigation.mix_shift_analysis.dimension_name}):</strong> Volume: ${investigation.mix_shift_analysis.volume_effect_usd?.toLocaleString()} | Mix-Shift: ${investigation.mix_shift_analysis.mix_shift_effect_usd?.toLocaleString()} | Price/Rate: ${investigation.mix_shift_analysis.price_rate_effect_usd?.toLocaleString()}
              </span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Logarithmic Bennet Exact</span>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EVIDENCE INTELLIGENCE */}
      {activeTab === 'evidence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Contradictory Evidence Alert if present */}
          {evidencePack?.contradictory_evidence?.length > 0 && (
            <div style={{ padding: '14px 18px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.4)', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>
                <ShieldAlert size={18} />
                <span>Contradictory Operational Evidence Detected ({evidencePack.contradictory_evidence.length} conflicts)</span>
              </div>
              <p style={{ fontSize: '0.775rem', color: '#fca5a5' }}>
                Operational event logs contain conflicting signals (e.g. shipping surcharges vs checkout errors). Autonomous causal recommendations are paused to prevent hallucinated advice.
              </p>
            </div>
          )}

          {/* Evidence Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
            {evidencePack?.supporting_evidence?.map((ev, i) => (
              <div key={i} style={{ background: 'var(--bg-secondary)', padding: '14px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span className="font-mono" style={{ fontSize: '0.75rem', color: '#60a5fa', fontWeight: 600 }}>
                    {ev.evidence_id}
                  </span>
                  <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                    Relevance: {(ev.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '6px', marginBottom: '8px', flexWrap: 'wrap' }}>
                  <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>{ev.issue_type}</span>
                  <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>Severity: {ev.severity}</span>
                  {ev.affected_region && <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>Region: {ev.affected_region}</span>}
                </div>
                <p style={{ fontSize: '0.785rem', color: 'var(--text-primary)', lineHeight: 1.45 }}>
                  {ev.sanitized_content}
                </p>
                <div style={{ marginTop: '8px', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Source: {ev.source_table}</span>
                  <span>{ev.timestamp}</span>
                </div>
              </div>
            ))}

            {(!evidencePack?.supporting_evidence || evidencePack?.supporting_evidence.length === 0) && (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', gridColumn: '1 / -1' }}>
                No operational evidence documents indexed for this window.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: DATA LINEAGE */}
      {activeTab === 'lineage' && (
        <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
            Deterministic End-to-End Lineage Flow
          </h4>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontSize: '0.8rem' }}>
            <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={14} color="#60a5fa" />
              <span>orders, order_items, marketing_events</span>
            </div>
            <ChevronRight size={16} color="var(--text-muted)" />
            <div style={{ padding: '8px 12px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '6px', border: '1px solid rgba(59, 130, 246, 0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <GitCommit size={14} color="#60a5fa" />
              <span>Semantic Formula Contract</span>
            </div>
            <ChevronRight size={16} color="var(--text-muted)" />
            <div style={{ padding: '8px 12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} color="#34d399" />
              <span>Logarithmic Multiplicative Decomposition</span>
            </div>
            <ChevronRight size={16} color="var(--text-muted)" />
            <div style={{ padding: '8px 12px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileText size={14} color="#fbbf24" />
              <span>ChromaDB Vector Evidence RAG</span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

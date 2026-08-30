import React, { useState } from 'react';
import { Database, GitCommit, Layers, FileText, ChevronRight, AlertCircle, ShieldAlert, Sparkles, ExternalLink, ShieldCheck, Eye, EyeOff, Wrench, BarChart2, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';

export default function InvestigationView({
  investigation,
  evidencePack,
  persona,
  userRole = 'ANALYST',
  focusedDriver,
  onSelectDriver,
  onBackToOverview,
  onProceedToNarrative,
  loading
}) {
  const [activeTab, setActiveTab] = useState('drivers'); // 'drivers' | 'evidence' | 'lineage'

  if (loading && !investigation) {
    return (
      <div className="glass-panel" style={{ padding: '36px', textAlign: 'center', background: '#ffffff' }}>
        <div style={{ display: 'inline-block', width: '36px', height: '36px', border: '3px solid #e2e8f0', borderTopColor: '#2563eb', borderRadius: '50%' }} className="animate-spin" />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500 }}>
          Running deterministic decomposition & evidence retrieval...
        </p>
      </div>
    );
  }

  if (!investigation) return null;

  const mat = investigation.materiality || {};
  const isMaterial = mat.business_materiality === 'MATERIAL';
  const isSig = mat.statistical_significance === 'STATISTICALLY_SIGNIFICANT';

  const isExecutive = userRole === 'EXECUTIVE';
  const isOperations = userRole === 'OPERATIONS';
  const isAnalyst = userRole === 'ANALYST';

  // Role-filtered drivers
  let displayedDrivers = investigation.ranked_drivers || [];
  if (isOperations) {
    displayedDrivers = displayedDrivers.filter(d => 
      d.driver_type?.toLowerCase().includes('operational') || 
      d.driver_name?.toLowerCase().includes('conversion') || 
      d.driver_name?.toLowerCase().includes('stockout') ||
      d.driver_name?.toLowerCase().includes('payment') ||
      d.driver_name?.toLowerCase().includes('order')
    );
    if (displayedDrivers.length === 0) displayedDrivers = investigation.ranked_drivers || [];
  }

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* RBAC Role Context Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 16px',
        borderRadius: '8px',
        marginBottom: '18px',
        background: isExecutive ? '#eff6ff' : isOperations ? '#fef3c7' : '#f0fdf4',
        border: `1px solid ${isExecutive ? '#bfdbfe' : isOperations ? '#fde68a' : '#bbf7d0'}`,
        flexWrap: 'wrap',
        gap: '8px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.825rem' }}>
          {isExecutive && <Eye size={16} color="#2563eb" />}
          {isAnalyst && <BarChart2 size={16} color="#059669" />}
          {isOperations && <Wrench size={16} color="#d97706" />}
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
            Current RBAC View: <strong style={{ color: isExecutive ? '#1d4ed8' : isOperations ? '#b45309' : '#047857' }}>{userRole}</strong>
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.785rem' }}>
            {isExecutive && '— Aggregated Financial View (Low-level stack traces and customer PII are redacted)'}
            {isAnalyst && '— Technical Analytical View (Full mathematical decomposition, formulas, z-scores & tokenized PII)'}
            {isOperations && '— Operational Incident View (Gateway root-causes, error codes, ticket severities & runbooks)'}
          </span>
        </div>

        <span className={`badge ${isExecutive ? 'badge-info' : isOperations ? 'badge-warning' : 'badge-success'}`} style={{ fontSize: '0.675rem' }}>
          {isExecutive ? 'PII Hidden' : isAnalyst ? 'PII Tokenized' : 'Raw Telemetry'}
        </span>
      </div>

      {/* Header & Movement Summary */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '18px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Step 2: CORRELATE — {investigation.kpi_name}
            </h3>
            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
              {isExecutive ? 'Executive Impact Analysis' : investigation.analytical_method}
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Investigation ID: <span className="font-mono" style={{ color: '#2563eb', fontWeight: 600 }}>{investigation.investigation_id}</span> • Click any driver below to focus downstream narrative & actions
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
        <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Baseline ({investigation.baseline_period?.start_date} → {investigation.baseline_period?.end_date})</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }} className="font-mono">
            {investigation.unit === 'USD' ? `$${investigation.baseline_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : investigation.baseline_value?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Anomaly Period ({investigation.anomaly_period?.start_date} → {investigation.anomaly_period?.end_date})</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }} className="font-mono">
            {investigation.unit === 'USD' ? `$${investigation.current_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : investigation.current_value?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Absolute Delta</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: investigation.absolute_change < 0 ? '#dc2626' : '#059669', marginTop: '4px' }} className="font-mono">
            {investigation.absolute_change < 0 ? '-' : '+'}
            {investigation.unit === 'USD' ? `$${Math.abs(investigation.absolute_change)?.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : Math.abs(investigation.absolute_change)?.toLocaleString()}
          </div>
        </div>

        <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Percentage Delta</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: investigation.percentage_change < 0 ? '#dc2626' : '#059669', marginTop: '4px' }} className="font-mono">
            {investigation.percentage_change > 0 ? `+${investigation.percentage_change}%` : `${investigation.percentage_change}%`}
          </div>
        </div>

        {/* Statistical Support */}
        <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
            {isExecutive ? 'Significance Confidence' : 'z-score / p-value'}
          </span>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2563eb', marginTop: '4px' }} className="font-mono">
            {isExecutive ? (
              isSig ? 'High Confidence (p < 0.001)' : 'Inconclusive Noise'
            ) : (
              `z = ${mat.z_score !== null && mat.z_score !== undefined ? mat.z_score : 'N/A'} ${mat.p_value_approx !== null && mat.p_value_approx !== undefined ? `(p < ${mat.p_value_approx})` : ''}`
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '18px', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('drivers')}
          style={{
            background: activeTab === 'drivers' ? '#eff6ff' : 'transparent',
            color: activeTab === 'drivers' ? '#1d4ed8' : 'var(--text-secondary)',
            border: activeTab === 'drivers' ? '1px solid #93c5fd' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {isExecutive ? 'Executive Driver Impact' : isOperations ? 'Operational Root-Cause Drivers' : 'Quantitative Driver Decomposition'}
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          style={{
            background: activeTab === 'evidence' ? '#eff6ff' : 'transparent',
            color: activeTab === 'evidence' ? '#1d4ed8' : 'var(--text-secondary)',
            border: activeTab === 'evidence' ? '1px solid #93c5fd' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          Traceable Evidence ({evidencePack?.supporting_evidence?.length || 0} supporting, {evidencePack?.contradictory_evidence?.length || 0} contradictory)
        </button>

        <button
          onClick={() => setActiveTab('lineage')}
          style={{
            background: activeTab === 'lineage' ? '#eff6ff' : 'transparent',
            color: activeTab === 'lineage' ? '#1d4ed8' : 'var(--text-secondary)',
            border: activeTab === 'lineage' ? '1px solid #93c5fd' : '1px solid transparent',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {isExecutive ? 'Business Impact Lineage' : isOperations ? 'Operational System Lineage' : 'End-to-End Data Lineage'}
        </button>
      </div>

      {/* TAB 1: DRIVER DECOMPOSITION */}
      {activeTab === 'drivers' && (
        <div>
          <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>Driver (Click to Focus Flow)</th>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>Category</th>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>Financial Contribution ($)</th>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>Contribution (%)</th>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>Direction</th>
                  <th style={{ padding: '10px 14px', fontWeight: 700 }}>{isExecutive ? 'Business Rationale' : isOperations ? 'Operational Runbook' : 'Decomposition Method'}</th>
                </tr>
              </thead>
              <tbody>
                {displayedDrivers.map((d, i) => {
                  const isDriverFocused = focusedDriver === d.driver_name;

                  return (
                    <tr
                      key={i}
                      onClick={() => onSelectDriver && onSelectDriver(isDriverFocused ? null : d.driver_name)}
                      style={{
                        borderBottom: '1px solid #f1f5f9',
                        background: isDriverFocused 
                          ? '#eff6ff' 
                          : i % 2 === 0 ? '#ffffff' : '#fcfcfd',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                      title="Click to focus this driver in Narrative, Governance & Actions"
                    >
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {isDriverFocused && <CheckCircle2 size={15} color="#2563eb" />}
                        <span>{d.driver_name}</span>
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                        <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>{d.driver_type}</span>
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: (d.contribution_value || 0) < 0 ? '#dc2626' : '#059669' }} className="font-mono">
                        {d.contribution_value !== null ? `$${Number(d.contribution_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: (d.contribution_percentage || 0) < 0 ? '#dc2626' : '#059669' }} className="font-mono">
                        {d.contribution_percentage !== null ? `${d.contribution_percentage > 0 ? '+' : ''}${d.contribution_percentage}%` : '—'}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span className={`badge ${d.direction === 'NEGATIVE' ? 'badge-critical' : d.direction === 'POSITIVE' ? 'badge-success' : 'badge-neutral'}`}>
                          {d.direction}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '0.785rem' }}>
                        {isExecutive 
                          ? (d.contribution_value < 0 ? 'Primary factor driving top-line revenue reduction' : 'Mitigating revenue factor')
                          : isOperations 
                          ? (d.driver_name?.toLowerCase().includes('conversion') ? 'Runbook: Payments Gateway Failover' : d.driver_name?.toLowerCase().includes('order') ? 'Runbook: Inventory Rebalancing' : 'Runbook: Campaign Traffic Recovery')
                          : d.methodology}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mix shift notice if present */}
          {investigation.mix_shift_analysis && (
            <div style={{ marginTop: '16px', padding: '12px 16px', background: '#eff6ff', borderRadius: '8px', border: '1px solid #bfdbfe', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.825rem' }}>
              <span style={{ color: '#1e40af', fontWeight: 600 }}>
                <strong>Mix-Shift Effect ({investigation.mix_shift_analysis.dimension_name}):</strong> Volume: ${investigation.mix_shift_analysis.volume_effect_usd?.toLocaleString()} | Mix-Shift: ${investigation.mix_shift_analysis.mix_shift_effect_usd?.toLocaleString()} | Price/Rate: ${investigation.mix_shift_analysis.price_rate_effect_usd?.toLocaleString()}
              </span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                {isExecutive ? 'Mix-Shift Variance' : 'Logarithmic Bennet Exact'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EVIDENCE INTELLIGENCE */}
      {activeTab === 'evidence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Contradictory Evidence Alert if present */}
          {evidencePack?.contradictory_evidence?.length > 0 && (
            <div style={{ padding: '14px 18px', background: '#fff5f5', borderRadius: '8px', border: '1px solid #fca5a5', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b91c1c', fontWeight: 800, fontSize: '0.875rem', marginBottom: '6px' }}>
                <ShieldAlert size={18} />
                <span>Contradictory Operational Evidence Detected ({evidencePack.contradictory_evidence.length} conflicts)</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#991b1b' }}>
                Operational event logs contain conflicting signals (e.g. shipping surcharges vs checkout errors). Autonomous causal recommendations are paused to prevent hallucinated advice.
              </p>
            </div>
          )}

          {/* Evidence Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
            {evidencePack?.supporting_evidence?.map((ev, i) => (
              <div key={i} style={{ background: '#ffffff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: 'var(--shadow-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span className="font-mono" style={{ fontSize: '0.75rem', color: '#2563eb', fontWeight: 700 }}>
                    {isExecutive ? `[EVID-SUMMARY-${i+1}]` : ev.evidence_id}
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
                <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                  {isExecutive ? ev.sanitized_content?.split('.')[0] + '.' : ev.sanitized_content}
                </p>
                <div style={{ marginTop: '10px', fontSize: '0.725rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '6px' }}>
                  <span>Source: {isExecutive ? 'Operational Telemetry' : ev.source_table}</span>
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
        <div style={{ padding: '18px 20px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '14px' }}>
            {isExecutive ? 'Executive Decision Lineage Flow' : isOperations ? 'Operational System Infrastructure Lineage' : 'Deterministic End-to-End Lineage Flow'}
          </h4>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontSize: '0.8rem' }}>
            <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '6px', border: '1px solid #cbd5e1', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <Database size={15} color="#2563eb" />
              <span>{isExecutive ? 'Enterprise Core Data' : isOperations ? 'API Gateways & Incident Logs' : 'orders, order_items, marketing_events'}</span>
            </div>
            <ChevronRight size={16} color="#94a3b8" />
            <div style={{ padding: '8px 12px', background: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <GitCommit size={15} color="#2563eb" />
              <span>{isExecutive ? 'Revenue Model Contract' : isOperations ? 'Telemetry Signal Parser' : 'Semantic Formula Contract'}</span>
            </div>
            <ChevronRight size={16} color="#94a3b8" />
            <div style={{ padding: '8px 12px', background: '#f0fdf4', borderRadius: '6px', border: '1px solid #bbf7d0', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <Layers size={15} color="#059669" />
              <span>{isExecutive ? 'Business Driver Allocation' : isOperations ? 'Failure Incident Attribution' : 'Logarithmic Multiplicative Decomposition'}</span>
            </div>
            <ChevronRight size={16} color="#94a3b8" />
            <div style={{ padding: '8px 12px', background: '#fef3c7', borderRadius: '6px', border: '1px solid #fde68a', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <FileText size={15} color="#d97706" />
              <span>{isExecutive ? 'Executive Sign-Off' : isOperations ? 'Automated Runbook Actions' : 'ChromaDB Vector Evidence RAG'}</span>
            </div>
          </div>
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
          onClick={onBackToOverview}
          className="btn btn-secondary"
          style={{ padding: '8px 16px', fontSize: '0.825rem' }}
        >
          <ArrowLeft size={16} />
          <span>← Back to Step 1: Detect</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {focusedDriver && (
            <span style={{ fontSize: '0.785rem', color: '#2563eb', fontWeight: 600 }}>
              Focused Driver: <strong>{focusedDriver}</strong>
            </span>
          )}
          <button
            onClick={onProceedToNarrative}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.825rem' }}
          >
            <span>Proceed to Step 3: Explain Narrative</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

    </div>
  );
}

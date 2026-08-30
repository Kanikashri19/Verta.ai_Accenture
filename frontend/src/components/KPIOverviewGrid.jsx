import React from 'react';
import { ArrowDownRight, ArrowUpRight, AlertTriangle, CheckCircle2, TrendingDown, TrendingUp } from 'lucide-react';

export default function KPIOverviewGrid({ kpis, selectedKpiId, onSelectKpi, loading }) {
  if (loading && (!kpis || kpis.length === 0)) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="glass-panel" style={{ padding: '20px', height: '140px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ height: '14px', width: '60%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '12px' }} className="animate-pulse-subtle" />
            <div style={{ height: '24px', width: '80%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
            <div style={{ height: '12px', width: '40%', background: 'rgba(255,255,255,0.04)', borderRadius: '4px' }} className="animate-pulse-subtle" />
          </div>
        ))}
      </div>
    );
  }

  const formatValue = (val, unit) => {
    if (val === null || val === undefined) return '—';
    if (unit === 'USD') {
      return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (unit === '%') {
      return `${(Number(val) * (val <= 1 ? 100 : 1)).toFixed(2)}%`;
    }
    return Number(val).toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  return (
    <section style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
          Screen 1 — Executive KPI Overview & Prioritisation
        </h2>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Click any card to trigger deterministic investigation
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {kpis.map((kpi, idx) => {
          const isSelected = kpi.kpi_id === selectedKpiId;
          const isTopPriority = idx === 0 && kpi.is_material;
          const isNegative = kpi.percentage_change < 0;

          let badgeClass = 'badge-neutral';
          let badgeText = 'Normal';
          if (kpi.overall_materiality === 'CRITICAL_ACTIONABLE') {
            badgeClass = 'badge-critical';
            badgeText = 'Critical Actionable';
          } else if (kpi.overall_materiality === 'BUSINESS_WARNING') {
            badgeClass = 'badge-warning';
            badgeText = 'Business Warning';
          } else if (kpi.is_material) {
            badgeClass = 'badge-critical';
            badgeText = 'Material Movement';
          }

          return (
            <div
              key={kpi.kpi_id}
              onClick={() => onSelectKpi(kpi.kpi_id)}
              className="glass-panel"
              style={{
                padding: '18px 20px',
                cursor: 'pointer',
                position: 'relative',
                transition: 'all 0.2s ease',
                border: isSelected
                  ? '2px solid var(--accent-blue)'
                  : isTopPriority
                  ? '1px solid rgba(239, 68, 68, 0.4)'
                  : '1px solid var(--border-subtle)',
                background: isSelected
                  ? 'rgba(37, 99, 235, 0.12)'
                  : isTopPriority
                  ? 'rgba(239, 68, 68, 0.05)'
                  : 'var(--bg-glass)',
                boxShadow: isTopPriority ? '0 0 20px rgba(239, 68, 68, 0.15)' : 'none',
              }}
            >
              {/* Prioritisation Ribbon */}
              {isTopPriority && (
                <div style={{
                  position: 'absolute',
                  top: '-9px',
                  right: '12px',
                  background: '#ef4444',
                  color: '#ffffff',
                  fontSize: '0.625rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  boxShadow: '0 2px 8px rgba(239, 68, 68, 0.4)',
                }}>
                  Top Priority Target
                </div>
              )}

              {/* KPI Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {kpi.name}
                </span>
                <span className={`badge ${badgeClass}`}>
                  {badgeText}
                </span>
              </div>

              {/* Current Value */}
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '6px' }} className="font-mono">
                {formatValue(kpi.current_value, kpi.unit)}
              </div>

              {/* Delta & Baseline Comparison */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.775rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: isNegative ? '#f87171' : '#34d399', fontWeight: 600 }}>
                  {isNegative ? <ArrowDownRight size={16} /> : <ArrowUpRight size={16} />}
                  <span>{kpi.percentage_change > 0 ? `+${kpi.percentage_change}%` : `${kpi.percentage_change}%`}</span>
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Base: <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{formatValue(kpi.baseline_value, kpi.unit)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

import React from 'react';
import { ArrowDownRight, ArrowUpRight, AlertTriangle, CheckCircle2, TrendingDown, TrendingUp, ArrowRight, Search } from 'lucide-react';

export default function KPIOverviewGrid({ kpis, selectedKpiId, onSelectKpi, onProceedToInvestigation, loading }) {
  if (loading && (!kpis || kpis.length === 0)) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="glass-panel" style={{ padding: '20px', height: '140px', display: 'flex', flexDirection: 'column', justifyContent: 'center', background: '#ffffff' }}>
            <div style={{ height: '14px', width: '60%', background: '#f1f5f9', borderRadius: '4px', marginBottom: '12px' }} className="animate-pulse-subtle" />
            <div style={{ height: '24px', width: '80%', background: '#e2e8f0', borderRadius: '4px', marginBottom: '8px' }} className="animate-pulse-subtle" />
            <div style={{ height: '12px', width: '40%', background: '#f1f5f9', borderRadius: '4px' }} className="animate-pulse-subtle" />
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

  const selectedKpi = kpis.find(k => k.kpi_id === selectedKpiId) || kpis[0];

  return (
    <section style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
          Step 1: DETECT — Executive KPI Overview & Prioritisation
        </h2>
        <span style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>
          Click any card to focus investigation across the entire decision pipeline
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
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
                  ? '2px solid #2563eb'
                  : isTopPriority
                  ? '1px solid #fca5a5'
                  : '1px solid #e2e8f0',
                background: isSelected
                  ? '#eff6ff'
                  : isTopPriority
                  ? '#fff5f5'
                  : '#ffffff',
                boxShadow: isSelected 
                  ? '0 4px 14px rgba(37, 99, 235, 0.15)' 
                  : isTopPriority 
                  ? '0 4px 12px rgba(239, 68, 68, 0.1)' 
                  : 'var(--shadow-sm)',
              }}
            >
              {/* Prioritisation Ribbon */}
              {isTopPriority && (
                <div style={{
                  position: 'absolute',
                  top: '-9px',
                  right: '12px',
                  background: '#dc2626',
                  color: '#ffffff',
                  fontSize: '0.625rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  boxShadow: '0 2px 6px rgba(220, 38, 38, 0.3)',
                }}>
                  Top Priority Target
                </div>
              )}

              {/* KPI Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: isSelected ? '#1d4ed8' : 'var(--text-secondary)' }}>
                  {kpi.name}
                </span>
                <span className={`badge ${badgeClass}`}>
                  {badgeText}
                </span>
              </div>

              {/* Current Value */}
              <div style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }} className="font-mono">
                {formatValue(kpi.current_value, kpi.unit)}
              </div>

              {/* Delta & Baseline Comparison */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: isNegative ? '#dc2626' : '#059669', fontWeight: 700 }}>
                  {isNegative ? <ArrowDownRight size={16} /> : <ArrowUpRight size={16} />}
                  <span>{kpi.percentage_change > 0 ? `+${kpi.percentage_change}%` : `${kpi.percentage_change}%`}</span>
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Base: <span className="font-mono" style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{formatValue(kpi.baseline_value, kpi.unit)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Guided Flow Progression Action Bar */}
      {selectedKpi && (
        <div style={{
          padding: '14px 20px',
          background: '#ffffff',
          border: '1px solid #cbd5e1',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <div>
            <div style={{ fontSize: '0.725rem', textTransform: 'uppercase', color: '#2563eb', fontWeight: 800 }}>
              Active Investigation Focus
            </div>
            <div style={{ fontSize: '0.925rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
              {selectedKpi.name} • {selectedKpi.percentage_change > 0 ? `+${selectedKpi.percentage_change}%` : `${selectedKpi.percentage_change}%`} Delta ({selectedKpi.business_materiality || 'MATERIAL'})
            </div>
          </div>

          <button
            onClick={onProceedToInvestigation}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.825rem' }}
          >
            <span>Proceed to Step 2: Correlate Drivers</span>
            <ArrowRight size={16} />
          </button>
        </div>
      )}
    </section>
  );
}

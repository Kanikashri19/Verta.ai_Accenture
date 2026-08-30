import React from 'react';
import { X, Cpu, Clock, DollarSign, Zap, Database, Activity, RefreshCw } from 'lucide-react';

export default function TelemetryDrawer({ isOpen, onClose, currentTelemetry, telemetryHistory, onRefresh }) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '100%',
      maxWidth: '480px',
      background: '#ffffff',
      borderLeft: '1px solid #e2e8f0',
      zIndex: 1000,
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-8px 0 30px rgba(0, 0, 0, 0.12)',
      overflowY: 'auto',
    }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={22} color="#2563eb" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Screen 9 — Real-Time Telemetry & Observability
          </h3>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Current Active Request Metrics */}
      {currentTelemetry && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Latest Investigation Request Telemetry
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8rem' }}>
            
            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>Latency</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#059669', marginTop: '2px' }} className="font-mono">
                {currentTelemetry.latency_ms?.toFixed(1)} ms
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>Estimated Cost</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#2563eb', marginTop: '2px' }} className="font-mono">
                ${currentTelemetry.estimated_cost_usd?.toFixed(5)}
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>Prompt Tokens</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }} className="font-mono">
                {currentTelemetry.prompt_tokens}
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700 }}>Completion Tokens</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }} className="font-mono">
                {currentTelemetry.completion_tokens}
              </div>
            </div>

          </div>

          <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Model: <strong style={{ color: 'var(--text-primary)' }}>{currentTelemetry.model}</strong></span>
            <span>Cache Hit: <strong style={{ color: currentTelemetry.cache_hit ? '#059669' : '#d97706' }}>{currentTelemetry.cache_hit ? 'YES (0ms)' : 'NO'}</strong></span>
          </div>
        </div>
      )}

      {/* Telemetry Log History */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            Recent Requests ({telemetryHistory.length})
          </h4>
          <button
            onClick={onRefresh}
            className="btn btn-secondary"
            style={{ fontSize: '0.725rem', padding: '3px 8px', height: '26px' }}
          >
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {telemetryHistory.slice(-8).reverse().map((t, i) => (
            <div
              key={t.request_id || i}
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '0.775rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="font-mono" style={{ color: '#2563eb', fontWeight: 700 }}>
                  {t.request_id}
                </span>
                <span className="badge badge-info" style={{ fontSize: '0.625rem' }}>
                  {t.latency_ms?.toFixed(0)} ms
                </span>
              </div>
              <div style={{ color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem' }}>
                <span>KPI: {t.kpi_id} • {t.persona}</span>
                <span>${t.estimated_cost_usd?.toFixed(5)}</span>
              </div>
            </div>
          ))}

          {telemetryHistory.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No telemetry requests logged yet.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

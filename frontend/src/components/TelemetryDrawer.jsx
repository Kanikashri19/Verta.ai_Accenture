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
      background: 'rgba(11, 15, 25, 0.95)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderLeft: '1px solid var(--border-subtle)',
      zIndex: 1000,
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-10px 0 30px rgba(0,0,0,0.5)',
      overflowY: 'auto',
    }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={20} color="#60a5fa" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ffffff' }}>
            Screen 9 — Real-Time Telemetry & Observability
          </h3>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Current Active Request Metrics */}
      {currentTelemetry && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Latest Investigation Request Telemetry
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8rem' }}>
            
            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Latency</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399', marginTop: '2px' }} className="font-mono">
                {currentTelemetry.latency_ms?.toFixed(1)} ms
              </div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Estimated Cost</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginTop: '2px' }} className="font-mono">
                ${currentTelemetry.estimated_cost?.toFixed(4) || '0.0000'}
              </div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Total Tokens</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }} className="font-mono">
                {currentTelemetry.total_tokens || 0}
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: '4px' }}>
                  ({currentTelemetry.input_tokens || 0} in / {currentTelemetry.output_tokens || 0} out)
                </span>
              </div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Cache State</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: currentTelemetry.cache_hit ? '#34d399' : 'var(--text-secondary)', marginTop: '4px' }}>
                {currentTelemetry.cache_hit ? '⚡ Cache Hit (0 ms)' : 'Cache Miss (Fresh Run)'}
              </div>
            </div>

          </div>

          <div style={{ marginTop: '10px', padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div>Request ID: <span className="font-mono" style={{ color: '#93c5fd' }}>{currentTelemetry.request_id}</span></div>
            <div>Model Provider: <span className="font-mono">{currentTelemetry.model_provider}</span> ({currentTelemetry.model})</div>
            <div>Fallback Triggered: <span style={{ color: currentTelemetry.fallback_used ? '#f87171' : '#34d399', fontWeight: 600 }}>{currentTelemetry.fallback_used ? 'YES (Rule Fallback)' : 'NO'}</span></div>
          </div>
        </div>
      )}

      {/* Historical Telemetry Logs */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            Recent Requests Log ({telemetryHistory?.length || 0})
          </h4>
          <button
            onClick={onRefresh}
            style={{ background: 'transparent', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {telemetryHistory?.slice(-8).reverse().map((t, idx) => (
            <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.725rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="font-mono" style={{ color: '#60a5fa', fontWeight: 600 }}>{t.request_id}</span>
                <span className="badge badge-info" style={{ fontSize: '0.6rem' }}>{t.latency_ms?.toFixed(0)} ms</span>
              </div>
              <div style={{ color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>{t.persona} • {t.governance_decision}</span>
                <span>{t.total_tokens || 0} tokens • ${t.estimated_cost?.toFixed(4) || '0.00'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

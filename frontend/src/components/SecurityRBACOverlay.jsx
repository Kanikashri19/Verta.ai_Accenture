import React from 'react';
import { Lock, EyeOff, ShieldCheck, UserCheck } from 'lucide-react';

export default function SecurityRBACOverlay({ userRole }) {
  const isExec = userRole === 'EXECUTIVE';
  const isAnalyst = userRole === 'ANALYST';

  return (
    <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#34d399',
        }}>
          <ShieldCheck size={20} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>
              Screen 7 — Enterprise Security & Privacy Guardrails Active
            </span>
            <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>RBAC Enforced</span>
            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>PII Masked</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {isExec && 'Executive Role: Customer identifiers, raw IPs, user emails, and low-level stack traces are pre-filtered before narrative rendering.'}
            {isAnalyst && 'Analyst Role: Technical metric breakdowns and sanitized incident logs are visible; customer PII is tokenized with [MASKED_EMAIL] and [MASKED_PHONE].'}
            {!isExec && !isAnalyst && 'Operations Role: Access to raw incident tickets, gateway logs, and operational telemetry for root-cause recovery.'}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <div style={{ padding: '4px 10px', background: 'var(--bg-secondary)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.725rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Lock size={12} color="#10b981" />
          <span>Active Role: <strong style={{ color: '#ffffff' }}>{userRole}</strong></span>
        </div>
      </div>
    </div>
  );
}

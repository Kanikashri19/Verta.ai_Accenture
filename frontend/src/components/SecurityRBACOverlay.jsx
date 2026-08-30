import React from 'react';
import { Lock, EyeOff, ShieldCheck, UserCheck } from 'lucide-react';

export default function SecurityRBACOverlay({ userRole }) {
  const isExec = userRole === 'EXECUTIVE';
  const isAnalyst = userRole === 'ANALYST';

  return (
    <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', background: '#ffffff' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '8px',
          background: '#d1fae5',
          border: '1px solid #a7f3d0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#047857',
        }}>
          <ShieldCheck size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Screen 7 — Enterprise Security & Privacy Guardrails Active
            </span>
            <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>RBAC Enforced</span>
            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>PII Masked</span>
          </div>
          <p style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {isExec && 'Executive Role: Customer identifiers, raw IPs, user emails, and low-level stack traces are pre-filtered before narrative rendering.'}
            {isAnalyst && 'Analyst Role: Technical metric breakdowns and sanitized incident logs are visible; customer PII is tokenized with [MASKED_EMAIL] and [MASKED_PHONE].'}
            {!isExec && !isAnalyst && 'Operations Role: Access to raw incident tickets, gateway logs, and operational telemetry for root-cause recovery.'}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <div style={{ padding: '6px 12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.785rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Lock size={14} color="#059669" />
          <span>Active Role: <strong style={{ color: 'var(--text-primary)' }}>{userRole}</strong></span>
        </div>
      </div>
    </div>
  );
}

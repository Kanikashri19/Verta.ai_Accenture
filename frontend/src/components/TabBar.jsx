import React from 'react';
import {
  LayoutDashboard,
  Search,
  Sparkles,
  ShieldCheck,
  ListOrdered,
  Cpu,
  MessageSquare,
} from 'lucide-react';

export const TABS = [
  { id: 'overview', label: 'Overview', fullTitle: 'Screen 1 — KPI Overview Grid', icon: LayoutDashboard },
  { id: 'investigation', label: 'Investigation', fullTitle: 'Screen 2 — Decomposition & Evidence', icon: Search },
  { id: 'narrative', label: 'Narrative', fullTitle: 'Screen 3 — Governed Persona Narrative', icon: Sparkles },
  { id: 'governance', label: 'Governance', fullTitle: 'Screen 4 & 6 — Confidence & Circuit Breaker', icon: ShieldCheck },
  { id: 'actions', label: 'Actions', fullTitle: 'Screen 5 — Approved Action Pipeline', icon: ListOrdered },
  { id: 'architecture', label: 'Architecture & Security', fullTitle: 'Screen 7 & 8 — Security & How Verta Thinks', icon: Cpu },
  { id: 'feedback', label: 'Feedback', fullTitle: 'Screen 10 — Analyst Feedback Loop', icon: MessageSquare },
];

export default function TabBar({ activeTab, onTabChange }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: '20px',
      overflowX: 'auto',
      paddingBottom: '4px',
      borderBottom: '2px solid #e2e8f0',
    }}>
      {TABS.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              borderBottom: isActive ? '3px solid #2563eb' : '3px solid transparent',
              background: isActive ? '#eff6ff' : 'transparent',
              color: isActive ? '#1d4ed8' : 'var(--text-secondary)',
              fontWeight: isActive ? 700 : 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap',
            }}
            title={tab.fullTitle}
          >
            <Icon size={17} color={isActive ? '#2563eb' : 'var(--text-muted)'} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}

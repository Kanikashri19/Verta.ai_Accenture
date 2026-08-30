import React from 'react';
import { Cpu, CheckCircle2, ShieldCheck, GitFork, Lock, Sparkles, Terminal } from 'lucide-react';

export default function EngineArchitectureCard({ generationMode, llmStatus }) {
  const isFallback = generationMode === 'DETERMINISTIC_FALLBACK';

  return (
    <div className="glass-panel" style={{ padding: '22px', marginBottom: '24px' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={18} color="#60a5fa" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#ffffff' }}>
            Screen 8 — How Verta.ai Thinks: Architecture & Non-LLM Source of Truth
          </h3>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <span className={`badge ${isFallback ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.675rem' }}>
            Mode: {generationMode || 'MOCK_LLM'}
          </span>
          <span className="badge badge-success" style={{ fontSize: '0.675rem' }}>
            Provider: {llmStatus?.provider || 'mock'} ({llmStatus?.model || 'mock-llm-v1'})
          </span>
        </div>
      </div>

      {/* Core Principle Callout */}
      <div style={{ padding: '10px 16px', background: 'rgba(59, 130, 246, 0.08)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.25)', marginBottom: '16px', fontSize: '0.8rem', color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Sparkles size={16} color="#60a5fa" />
        <span><strong>Foundational Guarantee:</strong> The LLM is <em>never</em> the source of quantitative truth. All numbers, formulas, confidence bands, and action levers are determined deterministically.</span>
      </div>

      {/* 2-Column Split: Non-LLM vs LLM */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
        
        {/* Left: Non-LLM Deterministic Intelligence */}
        <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontWeight: 700, fontSize: '0.825rem', marginBottom: '10px' }}>
            <CheckCircle2 size={16} />
            <span>NON-LLM (Deterministic Ground Truth)</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.775rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Semantic KPI Formula Contracts & SQL Aggregations</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Statistical Anomaly Detection & z-score / p-value Bounds</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Logarithmic Multiplicative Driver & Mix-Shift Decomposition</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• ChromaDB Local Vector Search & PII Token Masking</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Calibrated Confidence Scoring & Circuit Breaker Gate</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Approved Action Catalog Matching & Owner Mapping</li>
          </ul>
        </div>

        {/* Right: Governed LLM Translation Layer */}
        <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#c084fc', fontWeight: 700, fontSize: '0.825rem', marginBottom: '10px' }}>
            <Terminal size={16} />
            <span>LLM (Persona Translation & Narrative Layer)</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.775rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• User Intent Understanding & Persona Contextualization</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Natural Language Narrative Synthesis from FactPack</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Persona-Tailored Formatting (Executive vs Analyst)</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Grounded Invariant Citation Binding ([EVID-...] tags)</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Zero Overrides of Circuit Breaker (Bypassed on ABSTAIN)</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Deterministic Fallback on API Disconnect or Timeouts</li>
          </ul>
        </div>

      </div>

    </div>
  );
}

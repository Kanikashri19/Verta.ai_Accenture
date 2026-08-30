import React from 'react';
import { Cpu, CheckCircle2, ShieldCheck, GitFork, Lock, Sparkles, Terminal } from 'lucide-react';

export default function EngineArchitectureCard({ generationMode, llmStatus }) {
  const isFallback = generationMode === 'DETERMINISTIC_FALLBACK';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={20} color="#2563eb" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
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
      <div style={{ padding: '12px 18px', background: '#eff6ff', borderRadius: '8px', border: '1px solid #bfdbfe', marginBottom: '18px', fontSize: '0.825rem', color: '#1e40af', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Sparkles size={18} color="#2563eb" style={{ flexShrink: 0 }} />
        <span><strong>Foundational Guarantee:</strong> The LLM is <em>never</em> the source of quantitative truth. All numbers, formulas, confidence bands, and action levers are determined deterministically.</span>
      </div>

      {/* 2-Column Split: Non-LLM vs LLM */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        
        {/* Left: Non-LLM Deterministic Intelligence */}
        <div style={{ background: '#f8fafc', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#047857', fontWeight: 800, fontSize: '0.85rem', marginBottom: '12px' }}>
            <CheckCircle2 size={18} />
            <span>NON-LLM (Deterministic Ground Truth)</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Semantic KPI Formula Contracts & SQL Aggregations</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Statistical Anomaly Detection & z-score / p-value Bounds</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Logarithmic Multiplicative Driver & Mix-Shift Decomposition</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• ChromaDB Local Vector Search & PII Token Masking</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Calibrated Confidence Scoring & Circuit Breaker Gate</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Approved Action Catalog Matching & Owner Mapping</li>
          </ul>
        </div>

        {/* Right: Governed LLM Translation Layer */}
        <div style={{ background: '#f8fafc', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#7c3aed', fontWeight: 800, fontSize: '0.85rem', marginBottom: '12px' }}>
            <Terminal size={18} />
            <span>LLM (Persona Translation & Narrative Layer)</span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Executive vs Analyst Tone Formulation</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Grounded In-Text Citations matching [EVID-...]</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Uncertainty Language & Counter-Factual Caveats</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Multi-Provider LLM Gateway (Gemini, Claude, GPT, Fallback)</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Strict Governance Circuit Breaker Guardrails</li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>• Deterministic Output Verification & Hallucination Defense</li>
          </ul>
        </div>

      </div>
    </div>
  );
}

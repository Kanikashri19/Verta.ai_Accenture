import React, { useState } from 'react';
import { ThumbsUp, HelpCircle, ThumbsDown, CheckCircle2, MessageSquare, Send, ArrowLeft, RotateCcw } from 'lucide-react';
import { submitFeedback } from '../services/api';

export default function AnalystFeedbackModal({
  kpiId,
  scenarioId,
  persona,
  userRole,
  requestId,
  focusedDriver,
  onBackToActions,
  onStartNewInvestigation,
  onFeedbackSubmitted
}) {
  const [rating, setRating] = useState('CORRECT'); // 'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT'
  const [feedbackText, setFeedbackText] = useState('');
  const [correctedDriver, setCorrectedDriver] = useState(focusedDriver || '');
  const [submittedRecord, setSubmittedRecord] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await submitFeedback({
        request_id: requestId,
        kpi_id: kpiId,
        scenario_id: scenarioId,
        persona: persona,
        user_role: userRole,
        rating: rating,
        feedback_text: feedbackText,
        corrected_driver: correctedDriver || undefined,
      });
      setSubmittedRecord(res.record);
      if (onFeedbackSubmitted) onFeedbackSubmitted(res.record);
    } catch (err) {
      alert('Feedback submission error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquare size={20} color="#2563eb" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Step 6: CALIBRATE — Analyst Feedback & Evaluation Registry
          </h3>
        </div>
        <span className="badge badge-info" style={{ fontSize: '0.675rem' }}>
          Evaluation Registry Active
        </span>
      </div>

      {submittedRecord ? (
        <div style={{ padding: '18px 20px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <CheckCircle2 size={22} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 800, color: '#047857', fontSize: '0.9rem' }}>
              Feedback Successfully Captured ({submittedRecord.feedback_id})
            </div>
            <p style={{ fontSize: '0.825rem', color: '#065f46', marginTop: '4px', lineHeight: 1.5 }}>
              Rating: <strong>{submittedRecord.rating}</strong> • Stored in deterministic evaluation registry for future formula & catalog calibration reviews.
            </p>
            <button
              onClick={() => {
                setSubmittedRecord(null);
                setFeedbackText('');
                if (onStartNewInvestigation) onStartNewInvestigation();
              }}
              className="btn btn-secondary"
              style={{ marginTop: '12px', fontSize: '0.785rem', padding: '6px 14px' }}
            >
              <RotateCcw size={14} />
              <span>Start New Investigation (Step 1)</span>
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          
          {/* Metadata context header */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', background: '#f8fafc', padding: '12px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '18px', fontSize: '0.8rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Target KPI:</span>
              <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{kpiId}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Focused Driver:</span>
              <div style={{ fontWeight: 800, color: '#2563eb' }}>{focusedDriver || 'All Drivers'}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Scenario:</span>
              <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{scenarioId}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Persona / Role:</span>
              <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{persona} ({userRole})</div>
            </div>
          </div>

          {/* Rating options */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
              How accurate was the deterministic investigation & action recommendations?
            </label>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              
              <button
                type="button"
                onClick={() => setRating('CORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: rating === 'CORRECT' ? '2px solid #059669' : '1px solid #cbd5e1',
                  background: rating === 'CORRECT' ? '#d1fae5' : '#ffffff',
                  color: rating === 'CORRECT' ? '#047857' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <ThumbsUp size={16} />
                <span>Correct</span>
              </button>

              <button
                type="button"
                onClick={() => setRating('PARTIALLY_CORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: rating === 'PARTIALLY_CORRECT' ? '2px solid #d97706' : '1px solid #cbd5e1',
                  background: rating === 'PARTIALLY_CORRECT' ? '#fef3c7' : '#ffffff',
                  color: rating === 'PARTIALLY_CORRECT' ? '#b45309' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <HelpCircle size={16} />
                <span>Partially Correct</span>
              </button>

              <button
                type="button"
                onClick={() => setRating('INCORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: rating === 'INCORRECT' ? '2px solid #dc2626' : '1px solid #cbd5e1',
                  background: rating === 'INCORRECT' ? '#fee2e2' : '#ffffff',
                  color: rating === 'INCORRECT' ? '#b91c1c' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <ThumbsDown size={16} />
                <span>Incorrect</span>
              </button>

            </div>
          </div>

          {/* Corrected Driver (Optional) */}
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.785rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Suggested Primary Driver (Optional Calibration Override)
            </label>
            <input
              type="text"
              value={correctedDriver}
              onChange={(e) => setCorrectedDriver(e.target.value)}
              placeholder="e.g. Regional Marketing Ad Outage or Warehouse Stockout"
              style={{
                width: '100%',
                padding: '10px 14px',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontSize: '0.825rem',
                outline: 'none',
                boxShadow: 'var(--shadow-sm)',
              }}
            />
          </div>

          {/* Feedback notes */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.785rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Analyst Verification Notes & Context
            </label>
            <textarea
              rows={3}
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Provide domain context or reasons for driver calibration..."
              style={{
                width: '100%',
                padding: '10px 14px',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontSize: '0.825rem',
                outline: 'none',
                resize: 'vertical',
                boxShadow: 'var(--shadow-sm)',
              }}
            />
          </div>

          {/* Buttons & Flow Navigation */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', paddingTop: '14px', borderTop: '1px solid #e2e8f0' }}>
            <button
              type="button"
              onClick={onBackToActions}
              className="btn btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.825rem' }}
            >
              <ArrowLeft size={16} />
              <span>← Back to Step 5: Actions</span>
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
              style={{ padding: '9px 22px', fontSize: '0.85rem' }}
            >
              <Send size={15} />
              <span>{submitting ? 'Recording...' : 'Submit Evaluation to Registry'}</span>
            </button>
          </div>

        </form>
      )}

    </div>
  );
}

import React, { useState } from 'react';
import { ThumbsUp, HelpCircle, ThumbsDown, CheckCircle2, MessageSquare, Send } from 'lucide-react';
import { submitFeedback } from '../services/api';

export default function AnalystFeedbackModal({ kpiId, scenarioId, persona, userRole, requestId, onFeedbackSubmitted }) {
  const [rating, setRating] = useState('CORRECT'); // 'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT'
  const [feedbackText, setFeedbackText] = useState('');
  const [correctedDriver, setCorrectedDriver] = useState('');
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
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquare size={18} color="#60a5fa" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff' }}>
            Screen 10 — Analyst Feedback Loop & Continuous Calibration
          </h3>
        </div>
        <span className="badge badge-info" style={{ fontSize: '0.675rem' }}>
          Evaluation Registry Active
        </span>
      </div>

      {submittedRecord ? (
        <div style={{ padding: '18px 20px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <CheckCircle2 size={20} color="#34d399" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, color: '#34d399', fontSize: '0.85rem' }}>
              Feedback Successfully Captured ({submittedRecord.feedback_id})
            </div>
            <p style={{ fontSize: '0.775rem', color: '#a7f3d0', marginTop: '4px', lineHeight: 1.45 }}>
              Rating: <strong>{submittedRecord.rating}</strong> • Stored in deterministic evaluation registry for future formula & catalog calibration reviews.
            </p>
            <button
              onClick={() => setSubmittedRecord(null)}
              className="btn btn-secondary"
              style={{ marginTop: '10px', fontSize: '0.75rem', padding: '4px 10px' }}
            >
              Submit Another Review
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          
          <div>
            <label style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              Was this explanation and driver attribution accurate?
            </label>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => setRating('CORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px',
                  borderRadius: '8px',
                  border: rating === 'CORRECT' ? '2px solid #10b981' : '1px solid var(--border-subtle)',
                  background: rating === 'CORRECT' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-secondary)',
                  color: rating === 'CORRECT' ? '#34d399' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <ThumbsUp size={15} /> Correct
              </button>

              <button
                type="button"
                onClick={() => setRating('PARTIALLY_CORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px',
                  borderRadius: '8px',
                  border: rating === 'PARTIALLY_CORRECT' ? '2px solid #f59e0b' : '1px solid var(--border-subtle)',
                  background: rating === 'PARTIALLY_CORRECT' ? 'rgba(245, 158, 11, 0.15)' : 'var(--bg-secondary)',
                  color: rating === 'PARTIALLY_CORRECT' ? '#fbbf24' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <HelpCircle size={15} /> Partially Correct
              </button>

              <button
                type="button"
                onClick={() => setRating('INCORRECT')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '10px',
                  borderRadius: '8px',
                  border: rating === 'INCORRECT' ? '2px solid #ef4444' : '1px solid var(--border-subtle)',
                  background: rating === 'INCORRECT' ? 'rgba(239, 68, 68, 0.15)' : 'var(--bg-secondary)',
                  color: rating === 'INCORRECT' ? '#f87171' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <ThumbsDown size={15} /> Incorrect
              </button>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              Analyst Correction / Notes (Optional)
            </label>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="e.g. Conversion rate drop aligned with payment timeout, but mix shift contribution should be re-weighted..."
              rows={2}
              style={{
                width: '100%',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '10px 12px',
                fontSize: '0.8rem',
                outline: 'none',
                fontFamily: 'inherit',
                resize: 'vertical',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
              style={{ padding: '8px 18px', fontSize: '0.825rem' }}
            >
              <Send size={14} />
              <span>{submitting ? 'Recording...' : 'Submit Feedback to Registry'}</span>
            </button>
          </div>

        </form>
      )}

    </div>
  );
}

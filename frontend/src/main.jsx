import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[Verta.ai ErrorBoundary]', error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          background: '#f8fafc',
          fontFamily: 'Inter, -apple-system, sans-serif',
          color: '#0f172a',
        }}>
          <div style={{
            maxWidth: '600px',
            width: '100%',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '32px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.08)',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#dc2626', marginBottom: '12px' }}>
              Application Render Warning
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#475569', lineHeight: 1.5, marginBottom: '16px' }}>
              Verta.ai encountered an unexpected render state:
            </p>
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              padding: '12px 16px',
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              color: '#b91c1c',
              marginBottom: '20px',
              overflowX: 'auto',
            }}>
              {this.state.error?.toString() || 'Unknown runtime exception'}
            </div>
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.reload();
              }}
              style={{
                padding: '10px 20px',
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);

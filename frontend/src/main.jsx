import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class GlobalErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null, info: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) { this.setState({ info }); console.error('GLOBAL CRASH', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ position: 'fixed', inset: 0, background: '#1a0000', zIndex: 999999, padding: '40px', overflow: 'auto', fontFamily: 'monospace' }}>
          <div style={{ maxWidth: 900, margin: '0 auto' }}>
            <div style={{ background: '#ff0000', color: '#fff', padding: '16px 24px', borderRadius: 8, marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 900, margin: 0, letterSpacing: 2 }}>💥 CRASH DETECTADO — COPIE O TEXTO ABAIXO PARA O DEV</h1>
            </div>
            <div style={{ background: '#000', color: '#ff6b1a', padding: '16px', borderRadius: 8, marginBottom: 16, fontSize: 16, fontWeight: 700 }}>
              {this.state.error?.toString()}
            </div>
            <pre style={{ background: '#0a0a0a', color: '#aaa', padding: '16px', borderRadius: 8, fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {this.state.info?.componentStack}
            </pre>
            <button
              onClick={() => this.setState({ hasError: false, error: null, info: null })}
              style={{ marginTop: 24, padding: '12px 32px', background: '#ff6b1a', color: '#000', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 900, cursor: 'pointer', letterSpacing: 2 }}>
              ↺ TENTAR NOVAMENTE
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <GlobalErrorBoundary>
    <App />
  </GlobalErrorBoundary>,
)


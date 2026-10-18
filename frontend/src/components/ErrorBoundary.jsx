import React from 'react';

/**
 * React Error Boundary (#24)
 * Catches JavaScript errors anywhere in the component tree and displays
 * a fallback UI instead of crashing the entire application.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ textAlign: 'center', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-panel" style={{ maxWidth: '520px' }}>
            <div className="header-badge" style={{ background: 'rgba(244, 63, 94, 0.12)', borderColor: 'rgba(244, 63, 94, 0.3)', color: '#fb7185' }}>
              <span>Error</span> • Application Error
            </div>
            <h1 style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>Something Went Wrong</h1>
            <p className="subtitle" style={{ marginBottom: '1.5rem' }}>
              An unexpected error occurred in the application. Please try refreshing the page.
            </p>
            {import.meta.env.DEV && this.state.error && (
              <div className="json-box" style={{ textAlign: 'left', marginBottom: '1.5rem', maxHeight: '200px', overflow: 'auto' }}>
                <strong style={{ color: '#fb7185' }}>{this.state.error.toString()}</strong>
                {this.state.errorInfo && (
                  <pre style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#b3b3b3', whiteSpace: 'pre-wrap' }}>
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button
                className="btn-primary"
                onClick={this.handleReset}
                style={{ padding: '0.7rem 1.5rem' }}
              >
                Try Again
              </button>
              <button
                className="btn-primary"
                onClick={() => window.location.reload()}
                style={{ padding: '0.7rem 1.5rem', background: 'var(--bg-elevated)', color: 'var(--text-main)', border: '1px solid var(--border-color)' }}
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

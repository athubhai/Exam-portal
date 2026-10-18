import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Key, Lock, CheckCircle, AlertTriangle, ArrowRight, User } from 'lucide-react';

export default function DashboardPage() {
  const { user, token, logout, authFetch } = useAuth();
  const [apiResult, setApiResult] = useState(null);
  const [loadingEndpoint, setLoadingEndpoint] = useState(null);

  const testEndpoint = async (endpointName, path) => {
    setLoadingEndpoint(endpointName);
    setApiResult(null);

    try {
      const res = await authFetch(path);
      const data = await res.json();
      setApiResult({
        endpoint: path,
        status: res.status,
        statusText: res.statusText,
        ok: res.ok,
        data,
        timestamp: new Date().toLocaleTimeString()
      });
    } catch (err) {
      setApiResult({
        endpoint: path,
        status: 'Error',
        ok: false,
        data: { error: err.message },
        timestamp: new Date().toLocaleTimeString()
      });
    } finally {
      setLoadingEndpoint(null);
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'Admin': return 'badge-error';
      case 'Faculty': return 'badge-warning';
      default: return 'badge-success';
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1080px' }}>
      <div className="fintech-card" style={{ padding: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="header-badge">
              <Shield size={13} />
              <span>RBAC Session Active</span> • Role: {user?.role}
            </div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Welcome, {user?.name}</h1>
            <p className="subtitle" style={{ marginBottom: '1.2rem', marginTop: '0.2rem' }}>
              Authenticated User Email: <span style={{ color: 'var(--ft-primary-light)', fontFamily: 'var(--font-mono)' }}>{user?.email}</span>
            </p>
          </div>
          <button onClick={logout} className="btn-secondary">
            Sign Out
          </button>
        </div>

        {/* User Role Card */}
        <div className="fintech-metric-grid" style={{ marginTop: '1.5rem', marginBottom: '2rem' }}>
          <div className="fintech-stat-card">
            <span className="fintech-stat-label">User Identifier</span>
            <div className="fintech-stat-value">#{user?.id}</div>
          </div>

          <div className="fintech-stat-card">
            <span className="fintech-stat-label">Role Claim</span>
            <div className="fintech-stat-value">
              <span className={`badge ${getRoleBadgeClass(user?.role)}`}>
                <span className="pulse-dot pulse-green"></span>
                {user?.role}
              </span>
            </div>
          </div>

          <div className="fintech-stat-card">
            <span className="fintech-stat-label">2FA Protection</span>
            <div className="fintech-stat-value" style={{ fontSize: '1.2rem', color: user?.mfa_enabled ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)' }}>
              {user?.mfa_enabled ? 'Enabled' : 'Disabled'}
            </div>
          </div>
        </div>

        {/* Interactive RBAC Endpoint Tester */}
        <div style={{ marginTop: '2rem', paddingTop: '1.75rem', borderTop: '1px solid var(--ft-border-subtle)' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Server-Side RBAC Permission Matrix Tester
          </h3>
          <p style={{ color: 'var(--ft-text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Click below to test server-side permission checks. Non-permitted endpoints will strictly return <strong>HTTP 403 Forbidden</strong> from the FastAPI dependency layer.
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <button
              onClick={() => testEndpoint('User Profile', '/api/auth/me')}
              disabled={loadingEndpoint !== null}
              className="btn-secondary"
              style={{ fontSize: '0.85rem' }}
            >
              Test GET /auth/me (All Roles)
            </button>

            <button
              onClick={() => testEndpoint('Faculty Area', '/api/auth/faculty-demo')}
              disabled={loadingEndpoint !== null}
              className="btn-secondary"
              style={{ fontSize: '0.85rem' }}
            >
              Test GET /auth/faculty-demo (Faculty & Admin)
            </button>

            <button
              onClick={() => testEndpoint('Admin Area', '/api/auth/admin-demo')}
              disabled={loadingEndpoint !== null}
              className="btn-secondary"
              style={{ fontSize: '0.85rem' }}
            >
              Test GET /auth/admin-demo (Admin Only)
            </button>
          </div>

          {/* Response Inspector */}
          {apiResult && (
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              border: `1px solid ${apiResult.ok ? 'var(--ft-primary-border)' : 'rgba(244, 63, 94, 0.3)'}`,
              borderRadius: '12px',
              padding: '1.25rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="fintech-stat-label">Endpoint: <code style={{ color: '#ffffff' }}>{apiResult.endpoint}</code></span>
                <span className={`badge ${apiResult.ok ? 'badge-success' : 'badge-error'}`}>
                  {apiResult.status} {apiResult.statusText || (apiResult.ok ? 'OK' : 'Forbidden')}
                </span>
              </div>
              <pre className="json-box">
                {JSON.stringify(apiResult.data, null, 2)}
              </pre>
              <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-dim)', textAlign: 'right', marginTop: '0.4rem' }}>
                Tested at: {apiResult.timestamp}
              </div>
            </div>
          )}
        </div>

        {/* Token Inspection */}
        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--ft-border-subtle)' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--ft-text-secondary)', marginBottom: '0.5rem' }}>
            Active JWT Access Token
          </h4>
          <div className="json-box" style={{ wordBreak: 'break-all', fontSize: '0.75rem', color: '#94a3b8' }}>
            {token}
          </div>
        </div>
      </div>
    </div>
  );
}

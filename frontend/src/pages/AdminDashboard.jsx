import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Users,
  FileText,
  Activity,
  Shield,
  Key,
  Plus,
  RefreshCw,
  CheckCircle,
  AlertOctagon,
  UserCheck,
  Lock,
  X,
  Server
} from 'lucide-react';

export default function AdminDashboard() {
  const { authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({ name: '', email: '', password: '', role: 'Student' });
  const [statusMessage, setStatusMessage] = useState(null);

  useEffect(() => {
    loadStats();
    loadUsers();
    loadAuditLogs();
  }, []);

  const loadStats = async () => {
    try {
      const res = await authFetch('/api/admin/stats');
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/admin/users');
      if (res.ok) setUsers(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const res = await authFetch('/api/admin/audit-logs');
      if (res.ok) setAuditLogs(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const res = await authFetch('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify(newUser)
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create user');
      }
      setShowCreateModal(false);
      setNewUser({ name: '', email: '', password: '', role: 'Student' });
      setStatusMessage('User created successfully with assigned role claim!');
      loadUsers();
      loadStats();
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      const res = await authFetch(`/api/admin/users/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        setStatusMessage(`Role claim updated for user #${userId}`);
        loadUsers();
        loadAuditLogs();
        setTimeout(() => setStatusMessage(null), 3000);
      }
    } catch (err) {
      alert('Failed to update role');
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1180px' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div className="header-badge">
            <Shield size={13} />
            <span>Platform Administration</span>
          </div>
          <h1 style={{ fontSize: '2.1rem', fontWeight: 800 }}>Admin Security & Control Center</h1>
          <p className="subtitle" style={{ marginTop: '0.25rem' }}>
            Manage platform users, inspect immutable security audit trails, and oversee system-wide AI metrics.
          </p>
        </div>

        <button
          onClick={() => {
            loadStats();
            loadUsers();
            loadAuditLogs();
          }}
          className="btn-secondary"
          style={{ fontSize: '0.82rem', padding: '0.55rem 1rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      {statusMessage && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid var(--ft-primary-border)',
          borderRadius: '10px',
          padding: '0.85rem 1.25rem',
          marginBottom: '1.5rem',
          color: 'var(--ft-primary-light)',
          fontSize: '0.88rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <CheckCircle size={16} />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Metrics Overview Grid (Fintech KPI Cards) */}
      <div className="fintech-metric-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Total Users</span>
            <div className="fintech-stat-icon-wrap">
              <Users size={16} color="var(--ft-accent-cyan)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{stats?.total_users || 0}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">Active</span>
              <span>All registered</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Examinations</span>
            <div className="fintech-stat-icon-wrap">
              <FileText size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{stats?.total_exams || 0}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-neutral">Catalog</span>
              <span>Authored tests</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Submissions</span>
            <div className="fintech-stat-icon-wrap">
              <UserCheck size={16} color="#fbbf24" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value">{stats?.total_submissions || 0}</div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">Recorded</span>
              <span>Completed intake</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">Proctoring Flags</span>
            <div className="fintech-stat-icon-wrap">
              <AlertOctagon size={16} color="#fda4af" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value" style={{ color: stats?.total_proctoring_alerts > 0 ? '#fda4af' : 'var(--ft-text-primary)' }}>
              {stats?.total_proctoring_alerts || 0}
            </div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-down">Telemetry</span>
              <span>Suspicious events</span>
            </div>
          </div>
        </div>

        <div className="fintech-stat-card">
          <div className="fintech-stat-header">
            <span className="fintech-stat-label">AI Accuracy</span>
            <div className="fintech-stat-icon-wrap">
              <Server size={16} color="var(--ft-primary-light)" />
            </div>
          </div>
          <div>
            <div className="fintech-stat-value" style={{ color: 'var(--ft-primary-light)' }}>
              {stats?.model_accuracy || 94.5}%
            </div>
            <div className="fintech-stat-subtext">
              <span className="trend-pill trend-pill-up">Optimal</span>
              <span>Multi-modal model</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="fintech-tabs">
        <button
          onClick={() => setActiveTab('users')}
          className={`fintech-tab-item ${activeTab === 'users' ? 'active' : ''}`}
        >
          <Users size={16} />
          <span>User Directory</span>
          <span className="fintech-tab-badge">{users.length}</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`fintech-tab-item ${activeTab === 'audit' ? 'active' : ''}`}
        >
          <Activity size={16} />
          <span>Security Audit Trail</span>
          <span className="fintech-tab-badge">{auditLogs.length}</span>
        </button>
      </div>

      {/* TAB 1: USER MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="fintech-card" style={{ padding: '1rem' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.25rem',
            padding: '0 0.5rem'
          }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>System Users Directory</h3>
              <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
                Inspect registered credentials, role claims, and MFA 2FA activation status.
              </div>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
              style={{ fontSize: '0.85rem', padding: '0.55rem 1.1rem' }}
            >
              <Plus size={15} /> Add New User
            </button>
          </div>

          <div className="fintech-table-wrapper">
            <table className="fintech-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User Identity</th>
                  <th>Role Claim</th>
                  <th>MFA Status</th>
                  <th style={{ textAlign: 'right' }}>Role Assignment</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td style={{ color: 'var(--ft-text-muted)', fontFamily: 'var(--font-mono)' }}>
                      #{u.id}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: '#ffffff' }}>{u.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>{u.email}</div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          u.role === 'Admin'
                            ? 'badge-error'
                            : u.role === 'Faculty'
                            ? 'badge-warning'
                            : 'badge-success'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td>
                      {u.mfa_enabled ? (
                        <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                          <CheckCircle size={11} /> 2FA Active
                        </span>
                      ) : (
                        <span style={{ color: 'var(--ft-text-dim)', fontSize: '0.75rem' }}>
                          Disabled
                        </span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        className="fintech-input"
                        style={{
                          width: 'auto',
                          padding: '0.35rem 0.75rem',
                          fontSize: '0.8rem',
                          display: 'inline-block'
                        }}
                      >
                        <option value="Admin">Admin</option>
                        <option value="Faculty">Faculty</option>
                        <option value="Student">Student</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: AUDIT LOGS */}
      {activeTab === 'audit' && (
        <div className="fintech-card" style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1.25rem', padding: '0 0.5rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Platform Security Audit Trail</h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
              Append-only tamper-evident log of authentication attempts, exam starts, and role changes.
            </div>
          </div>

          <div className="fintech-table-wrapper">
            <table className="fintech-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>User Identity</th>
                  <th>Target Resource</th>
                  <th style={{ textAlign: 'right' }}>IP Address</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ color: 'var(--ft-text-muted)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ color: 'var(--ft-primary-light)', fontWeight: 600 }}>
                      {log.user_email}
                    </td>
                    <td style={{ color: 'var(--ft-text-secondary)', fontSize: '0.82rem' }}>
                      {log.target_resource}
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--ft-text-dim)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fintech-modal-overlay">
          <div className="fintech-modal-content" style={{ maxWidth: '440px' }}>
            <button
              onClick={() => setShowCreateModal(false)}
              className="btn-icon"
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
            >
              <X size={18} />
            </button>

            <div className="header-badge" style={{ marginBottom: '0.5rem' }}>
              IAM Identity Provisioning
            </div>
            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.25rem' }}>
              Create Platform User
            </h3>
            <p className="subtitle" style={{ fontSize: '0.82rem', marginBottom: '1.5rem', marginTop: 0 }}>
              Set up credentials and assign system role claim with RBAC enforcement.
            </p>

            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="fintech-label">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elena Rostova"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  className="fintech-input"
                />
              </div>

              <div>
                <label className="fintech-label">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="elena@examportal.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="fintech-input"
                />
              </div>

              <div>
                <label className="fintech-label">Initial Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="fintech-input"
                />
              </div>

              <div>
                <label className="fintech-label">Assigned Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="fintech-input"
                >
                  <option value="Admin">Admin</option>
                  <option value="Faculty">Faculty</option>
                  <option value="Student">Student</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
                <button type="submit" className="btn-primary" style={{ flex: 1, padding: '0.75rem' }}>
                  Create Account
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

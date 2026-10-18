import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, ArrowRight, UserCheck, KeyRound, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (presetEmail, presetPass) => {
    setEmail(presetEmail);
    setPassword(presetPass);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1.5rem',
      position: 'relative'
    }}>
      {/* Background ambient accents */}
      <div style={{
        position: 'absolute',
        top: '20%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '500px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%)',
        pointerEvents: 'none'
      }} />

      <div className="fintech-card" style={{
        maxWidth: '460px',
        width: '100%',
        padding: '2.5rem',
        borderRadius: '18px',
        border: '1px solid var(--ft-border-base)',
        boxShadow: 'var(--ft-shadow-elevated)',
        backgroundColor: 'rgba(14, 18, 26, 0.88)'
      }}>
        {/* Brand Shield & Security Tag */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#04130d',
            boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)'
          }}>
            <Shield size={22} strokeWidth={2.6} />
          </div>

          <div style={{
            fontSize: '0.72rem',
            padding: '0.25rem 0.65rem',
            borderRadius: '9999px',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            color: 'var(--ft-primary-light)',
            border: '1px solid var(--ft-primary-border)',
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}>
            <span className="pulse-dot pulse-green" style={{ width: '6px', height: '6px' }} />
            Zero-Trust Core
          </div>
        </div>

        {/* Title */}
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, marginBottom: '0.4rem' }}>
          Portal Authentication
        </h1>
        <p className="subtitle" style={{ fontSize: '0.88rem', marginBottom: '1.75rem', marginTop: 0 }}>
          Secure AI Examination Platform with RBAC, dynamic JWT claims, and real-time proctoring.
        </p>

        {/* Error Alert */}
        {error && (
          <div style={{
            backgroundColor: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '10px',
            padding: '0.85rem 1rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.6rem'
          }}>
            <AlertCircle size={18} color="#fda4af" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: '#fda4af', letterSpacing: '0.05em' }}>
                Authentication Error
              </div>
              <div style={{ color: '#fecdd3', fontSize: '0.85rem', marginTop: '0.15rem' }}>
                {error}
              </div>
            </div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label className="fintech-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@examportal.com"
                className="fintech-input"
                style={{ paddingLeft: '2.5rem' }}
              />
              <Mail size={16} color="var(--ft-text-muted)" style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <div>
            <label className="fintech-label">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="fintech-input"
                style={{ paddingLeft: '2.5rem' }}
              />
              <Lock size={16} color="var(--ft-text-muted)" style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '0.85rem', fontSize: '0.95rem', marginTop: '0.4rem' }}
          >
            {loading ? (
              <span>Verifying Credentials...</span>
            ) : (
              <>
                <span>Sign In to Platform</span>
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        {/* Quick Test Accounts (Dev Presets) */}
        {import.meta.env.DEV && (
          <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--ft-border-subtle)' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.75rem'
            }}>
              <span style={{
                fontSize: '0.72rem',
                textTransform: 'uppercase',
                letterSpacing: '0.07em',
                color: 'var(--ft-text-muted)',
                fontWeight: 700
              }}>
                Development Fast Login:
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--ft-primary-light)', fontWeight: 600 }}>Click to Autofill</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {/* Admin Chip */}
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@examportal.com', 'AdminPass123!')}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--ft-border-subtle)',
                  borderRadius: '10px',
                  padding: '0.65rem 0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                  e.currentTarget.style.backgroundColor = 'rgba(244, 63, 94, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--ft-border-subtle)';
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff' }}>System Administrator</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-muted)' }}>admin@examportal.com</div>
                </div>
                <span className="badge badge-error" style={{ fontSize: '0.68rem' }}>ADMIN</span>
              </button>

              {/* Faculty Chip */}
              <button
                type="button"
                onClick={() => handleQuickLogin('faculty@examportal.com', 'FacultyPass123!')}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--ft-border-subtle)',
                  borderRadius: '10px',
                  padding: '0.65rem 0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                  e.currentTarget.style.backgroundColor = 'rgba(245, 158, 11, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--ft-border-subtle)';
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff' }}>Faculty & Proctor</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-muted)' }}>faculty@examportal.com</div>
                </div>
                <span className="badge badge-warning" style={{ fontSize: '0.68rem' }}>FACULTY</span>
              </button>

              {/* Student Chip */}
              <button
                type="button"
                onClick={() => handleQuickLogin('student@examportal.com', 'StudentPass123!')}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--ft-border-subtle)',
                  borderRadius: '10px',
                  padding: '0.65rem 0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                  e.currentTarget.style.backgroundColor = 'rgba(16, 185, 129, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--ft-border-subtle)';
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff' }}>Student Candidate</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--ft-text-muted)' }}>student@examportal.com</div>
                </div>
                <span className="badge badge-success" style={{ fontSize: '0.68rem' }}>STUDENT</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

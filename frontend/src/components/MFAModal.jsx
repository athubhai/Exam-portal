import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, X, Check, Copy, AlertCircle, KeyRound, QrCode } from 'lucide-react';

export default function MFAModal({ isOpen, onClose }) {
  const { user, authFetch } = useAuth();
  const [mfaData, setMfaData] = useState(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && !user?.mfa_enabled) {
      loadMFASetup();
    }
  }, [isOpen, user?.mfa_enabled]);

  const loadMFASetup = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch('/api/mfa/setup');
      if (!res.ok) throw new Error('Failed to generate MFA setup keys.');
      const data = await res.json();
      setMfaData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEnableMFA = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await authFetch('/api/mfa/enable', {
        method: 'POST',
        body: JSON.stringify({ code, secret: mfaData?.secret })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid verification code.');

      setSuccess('Multi-Factor Authentication enabled successfully!');
      user.mfa_enabled = true;
      setTimeout(() => {
        onClose();
        setSuccess(null);
        setCode('');
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisableMFA = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await authFetch('/api/mfa/disable', {
        method: 'POST',
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid verification code to disable MFA.');

      setSuccess('MFA has been disabled on your account.');
      user.mfa_enabled = false;
      setTimeout(() => {
        onClose();
        setSuccess(null);
        setCode('');
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    if (mfaData?.secret) {
      navigator.clipboard.writeText(mfaData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fintech-modal-overlay">
      <div className="fintech-modal-content" style={{ maxWidth: '460px', padding: '2.2rem' }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          className="btn-icon"
          style={{ position: 'absolute', top: '1.25rem', right: '1.25rem' }}
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            backgroundColor: user?.mfa_enabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
            border: `1px solid ${user?.mfa_enabled ? 'var(--ft-primary-border)' : 'var(--ft-border-subtle)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: user?.mfa_enabled ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)'
          }}>
            <Lock size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
              {user?.mfa_enabled ? 'MFA Security Active' : 'Two-Factor Authentication'}
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--ft-text-muted)' }}>
              RFC 6238 Standard TOTP • Google Authenticator / Authy
            </p>
          </div>
        </div>

        {error && (
          <div style={{
            backgroundColor: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '10px',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: '#fda4af',
            fontSize: '0.85rem'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid var(--ft-primary-border)',
            borderRadius: '10px',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: 'var(--ft-primary-light)',
            fontSize: '0.85rem'
          }}>
            <Check size={16} />
            <span>{success}</span>
          </div>
        )}

        {user?.mfa_enabled ? (
          <div>
            <p style={{ color: 'var(--ft-text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
              Your portal identity is securely guarded with TOTP multi-factor verification. To disable 2FA, enter your current 6-digit authenticator code:
            </p>
            <form onSubmit={handleDisableMFA} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input
                type="text"
                maxLength="6"
                placeholder="000000"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                className="fintech-input"
                style={{
                  fontSize: '1.4rem',
                  letterSpacing: '0.3em',
                  textAlign: 'center',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.85rem'
                }}
              />
              <button
                type="submit"
                disabled={loading || code.length < 6}
                className="btn-danger"
                style={{ width: '100%', padding: '0.8rem', justifyContent: 'center' }}
              >
                {loading ? 'Verifying...' : 'Disable Two-Factor Auth'}
              </button>
            </form>
          </div>
        ) : (
          <div>
            <p style={{ color: 'var(--ft-text-secondary)', fontSize: '0.82rem', marginBottom: '1rem' }}>
              1. Scan this QR code using Google Authenticator, Microsoft Authenticator, or 1Password:
            </p>

            {mfaData?.qr_code_image ? (
              <div style={{
                textAlign: 'center',
                marginBottom: '1.25rem',
                padding: '1rem',
                borderRadius: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--ft-border-subtle)',
                display: 'flex',
                justifyContent: 'center'
              }}>
                <img
                  src={mfaData.qr_code_image}
                  alt="MFA QR Code"
                  style={{
                    width: '150px',
                    height: '150px',
                    borderRadius: '10px',
                    backgroundColor: '#ffffff',
                    padding: '8px'
                  }}
                />
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--ft-text-muted)' }}>
                Loading QR Code...
              </div>
            )}

            {mfaData?.secret && (
              <div style={{
                backgroundColor: 'var(--ft-bg-inset)',
                padding: '0.6rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--ft-border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '1.25rem',
                fontSize: '0.78rem'
              }}>
                <span style={{ color: 'var(--ft-text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  Secret: {mfaData.secret}
                </span>
                <button
                  type="button"
                  onClick={copySecret}
                  className="btn-secondary"
                  style={{ padding: '0.25rem 0.55rem', fontSize: '0.72rem', borderRadius: '6px' }}
                >
                  {copied ? <Check size={12} color="var(--ft-primary-light)" /> : <Copy size={12} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            )}

            <form onSubmit={handleEnableMFA} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label className="fintech-label">2. Enter 6-digit confirmation code</label>
                <input
                  type="text"
                  maxLength="6"
                  placeholder="123456"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                  className="fintech-input"
                  style={{
                    fontSize: '1.3rem',
                    letterSpacing: '0.25em',
                    textAlign: 'center',
                    fontFamily: 'var(--font-mono)',
                    padding: '0.75rem'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={loading || code.length < 6}
                className="btn-primary"
                style={{ width: '100%', padding: '0.8rem', justifyContent: 'center' }}
              >
                {loading ? 'Verifying Code...' : 'Activate MFA Protection'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

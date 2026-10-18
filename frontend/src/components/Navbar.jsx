import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, LogOut, CheckCircle, Cpu, Activity, User } from 'lucide-react';

export default function Navbar({ onOpenMFA }) {
  const { user, logout } = useAuth();

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case 'Admin':
        return {
          bg: 'rgba(244, 63, 94, 0.12)',
          color: '#fda4af',
          border: '1px solid rgba(244, 63, 94, 0.28)',
          dot: 'pulse-red'
        };
      case 'Faculty':
        return {
          bg: 'rgba(245, 158, 11, 0.12)',
          color: '#fbbf24',
          border: '1px solid rgba(245, 158, 11, 0.28)',
          dot: 'pulse-yellow'
        };
      default:
        return {
          bg: 'rgba(16, 185, 129, 0.12)',
          color: '#34d399',
          border: '1px solid rgba(16, 185, 129, 0.28)',
          dot: 'pulse-green'
        };
    }
  };

  const badgeStyle = getRoleBadgeStyle(user?.role);

  return (
    <header style={{
      width: '100%',
      backgroundColor: 'rgba(9, 12, 19, 0.85)',
      borderBottom: '1px solid var(--ft-border-subtle)',
      padding: '0.75rem 1.75rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)'
    }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#04130d',
          boxShadow: '0 0 16px rgba(16, 185, 129, 0.35)',
          flexShrink: 0
        }}>
          <Shield size={20} strokeWidth={2.6} />
        </div>
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              fontWeight: 800,
              fontSize: '1.05rem',
              color: '#ffffff',
              letterSpacing: '-0.02em',
              fontFamily: 'var(--font-heading)'
            }}>
              SecureAI
            </span>
            <span style={{
              fontSize: '0.7rem',
              padding: '0.1rem 0.45rem',
              borderRadius: '4px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: 'var(--ft-text-secondary)',
              fontWeight: 600,
              letterSpacing: '0.04em'
            }}>
              PROCTOR
            </span>
          </div>
          <div style={{
            fontSize: '0.7rem',
            color: 'var(--ft-text-muted)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}>
            <span>AES-256 GCM</span>
            <span>•</span>
            <span>YOLOv8 + Resemblyzer</span>
          </div>
        </div>
      </div>

      {/* Middle Status Telemetry */}
      <div style={{
        display: 'none',
        alignItems: 'center',
        gap: '0.6rem',
        padding: '0.35rem 0.85rem',
        borderRadius: '9999px',
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--ft-border-subtle)',
        fontSize: '0.75rem',
        color: 'var(--ft-text-secondary)'
      }} className="nav-telemetry">
        <span className="pulse-dot pulse-green" style={{ width: '6px', height: '6px' }} />
        <span style={{ fontWeight: 600, color: 'var(--ft-text-primary)' }}>System Nominal</span>
        <span style={{ color: 'var(--ft-text-dim)' }}>|</span>
        <span style={{ color: 'var(--ft-primary-light)', fontFamily: 'var(--font-mono)' }}>0.04s latency</span>
      </div>

      {/* User Info & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Role Badge */}
        <div style={{
          padding: '0.25rem 0.75rem',
          borderRadius: '9999px',
          fontSize: '0.72rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          backgroundColor: badgeStyle.bg,
          color: badgeStyle.color,
          border: badgeStyle.border,
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem'
        }}>
          <span className={`pulse-dot ${badgeStyle.dot}`} style={{ width: '6px', height: '6px' }} />
          {user?.role}
        </div>

        {/* User Identity Chip */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.3rem 0.75rem',
          borderRadius: '10px',
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--ft-border-subtle)'
        }}>
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--ft-text-secondary)'
          }}>
            <User size={13} />
          </div>
          <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#ffffff' }}>{user?.name}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--ft-text-muted)' }}>{user?.email}</div>
          </div>
        </div>

        {/* MFA Setup / Status Button */}
        <button
          onClick={onOpenMFA}
          title="Configure Multi-Factor Authentication"
          className="btn-secondary"
          style={{
            padding: '0.45rem 0.8rem',
            fontSize: '0.78rem',
            borderRadius: '8px',
            backgroundColor: user?.mfa_enabled ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.03)',
            color: user?.mfa_enabled ? 'var(--ft-primary-light)' : 'var(--ft-text-secondary)',
            borderColor: user?.mfa_enabled ? 'var(--ft-primary-border)' : 'var(--ft-border-subtle)'
          }}
        >
          <Lock size={14} />
          <span>{user?.mfa_enabled ? '2FA Active' : 'Enable 2FA'}</span>
        </button>

        {/* Sign Out Button */}
        <button
          onClick={logout}
          title="Sign Out of Portal"
          className="btn-danger"
          style={{
            padding: '0.45rem 0.85rem',
            fontSize: '0.78rem',
            borderRadius: '8px'
          }}
        >
          <LogOut size={14} />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
}

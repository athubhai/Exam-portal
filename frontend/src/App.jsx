import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';
import MFAModal from './components/MFAModal';
import LoginPage from './pages/LoginPage';
import AdminDashboard from './pages/AdminDashboard';
import FacultyDashboard from './pages/FacultyDashboard';
import StudentDashboard from './pages/StudentDashboard';

/**
 * Protected route wrapper: redirects to /login if not authenticated.
 */
function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="glass-panel" style={{ maxWidth: '380px' }}>
          <span className="badge badge-warning" style={{ fontSize: '0.9rem' }}>
            <span className="pulse-dot pulse-green"></span>
            Initializing Secure Session...
          </span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

/**
 * Resolves the correct dashboard component based on user role.
 */
function DashboardResolver() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  switch (user.role) {
    case 'Admin':
      return <AdminDashboard />;
    case 'Faculty':
      return <FacultyDashboard />;
    case 'Student':
    default:
      return <StudentDashboard />;
  }
}

function AppContent() {
  const { user } = useAuth();
  const [showMFAModal, setShowMFAModal] = useState(false);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', width: '100%' }}>
      {user && <Navbar onOpenMFA={() => setShowMFAModal(true)} />}
      <main style={{ flex: 1, padding: user ? '1rem 0' : 0 }}>
        <Routes>
          {/* Public route */}
          <Route
            path="/login"
            element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />}
          />

          {/* Protected dashboard route (auto-resolves by role) */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardResolver />
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </main>
      {user && <MFAModal isOpen={showMFAModal} onClose={() => setShowMFAModal(false)} />}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

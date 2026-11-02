import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext();

const API_BASE_URL = typeof window !== 'undefined' && !['8000', '8001'].includes(window.location.port)
  ? ''
  : 'http://localhost:8001';

export const AuthProvider = ({ children }) => {
  // #22: Use sessionStorage instead of localStorage to reduce XSS token theft surface
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(sessionStorage.getItem('access_token') || null);
  const [loading, setLoading] = useState(true);

  // #21: Token refresh helper
  const refreshAccessToken = useCallback(async () => {
    const refreshToken = sessionStorage.getItem('refresh_token');
    if (!refreshToken) return null;

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (res.ok) {
        const data = await res.json();
        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('refresh_token', data.refresh_token);
        setToken(data.access_token);
        return data.access_token;
      }
    } catch (err) {
      console.error('Token refresh failed:', err);
    }
    return null;
  }, []);

  // Helper fetch wrapping Bearer token in headers with automatic token refresh (#21)
  const authFetch = useCallback(async (endpoint, options = {}, _isRetry = false) => {
    const currentToken = sessionStorage.getItem('access_token') || token;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // #21: If 401 and not already retrying, attempt token refresh
    if (response.status === 401 && !_isRetry) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        // Retry the original request with the new token
        return authFetch(endpoint, options, true);
      } else {
        // Refresh failed — log out
        logout();
      }
    }

    return response;
  }, [token, refreshAccessToken]);

  // Restore user session on mount if token exists
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const res = await authFetch('/api/auth/me');
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
        } else {
          // Token expired or invalid
          logout();
        }
      } catch (err) {
        console.error("Failed to restore session:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const login = async (email, password, mfa_code = null) => {
    const body = { email, password };
    if (mfa_code) body.mfa_code = mfa_code;

    let res;
    try {
      res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    } catch (networkErr) {
      throw new Error('Cannot connect to backend server. Please verify FastAPI is running on http://localhost:8001.');
    }

    let data;
    try {
      data = await res.json();
    } catch (parseErr) {
      throw new Error(`Server returned status ${res.status} (${res.statusText || 'No response body'}). Please check backend logs.`);
    }

    if (!res.ok) {
      throw new Error(data?.detail || 'Login failed. Please check credentials.');
    }

    // Handle MFA challenge response
    if (data.mfa_required) {
      return data; // Return MFA challenge for the login page to handle
    }

    sessionStorage.setItem('access_token', data.access_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

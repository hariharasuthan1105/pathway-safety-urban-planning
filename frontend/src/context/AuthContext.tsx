import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type { User, AuthState } from '../types';
import { fetchApi, setSessionToken } from '../lib/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  signup: (full_name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const revision = useRef(0);

  const refreshUser = useCallback(async () => {
    const requestRevision = ++revision.current;
    try {
      const data = await fetchApi<{ authenticated: boolean; user: User }>('/api/auth/me', { retries: 0 });
      if (requestRevision !== revision.current) return;
      if (data.authenticated && data.user) {
        setUser(data.user);
        setAuthenticated(true);
      } else {
        setUser(null);
        setAuthenticated(false);
      }
    } catch {
      if (requestRevision !== revision.current) return;
      setUser(null);
      setAuthenticated(false);
    } finally {
      if (requestRevision === revision.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();

    const handleAuthExpired = () => {
      setSessionToken(null);
      revision.current++;
      setLoading(false);
      setUser(null);
      setAuthenticated(false);
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, [refreshUser]);

  const login = async (email: string, password: string, remember: boolean = false) => {
    revision.current++;
    setLoading(false);
    const data = await fetchApi<{ user: User; token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, remember, session_mode: 'memory' }),
    });
    setSessionToken(data.token);
    setUser(data.user);
    setAuthenticated(true);
    setLoading(false);
  };

  const signup = async (full_name: string, email: string, password: string) => {
    revision.current++;
    setLoading(false);
    const data = await fetchApi<{ user: User; token: string }>('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ full_name, email, password, session_mode: 'memory' }),
    });
    setSessionToken(data.token);
    setUser(data.user);
    setAuthenticated(true);
    setLoading(false);
  };

  const logout = async () => {
    revision.current++;
    try {
      await fetchApi('/api/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors on logout
    } finally {
      setSessionToken(null);
      setUser(null);
      setAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, authenticated, loading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

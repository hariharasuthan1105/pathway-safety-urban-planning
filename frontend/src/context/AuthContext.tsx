import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, AuthState } from '../types';
import { fetchApi } from '../lib/api';

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

  const refreshUser = useCallback(async () => {
    try {
      const data = await fetchApi<{ authenticated: boolean; user: User }>('/api/auth/me', { retries: 0 });
      if (data.authenticated && data.user) {
        setUser(data.user);
        setAuthenticated(true);
      } else {
        setUser(null);
        setAuthenticated(false);
      }
    } catch {
      setUser(null);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();

    const handleAuthExpired = () => {
      setUser(null);
      setAuthenticated(false);
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, [refreshUser]);

  const login = async (email: string, password: string, remember: boolean = false) => {
    const data = await fetchApi<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, remember }),
    });
    setUser(data.user);
    setAuthenticated(true);
  };

  const signup = async (full_name: string, email: string, password: string) => {
    const data = await fetchApi<{ user: User }>('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ full_name, email, password }),
    });
    setUser(data.user);
    setAuthenticated(true);
  };

  const logout = async () => {
    try {
      await fetchApi('/api/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors on logout
    } finally {
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

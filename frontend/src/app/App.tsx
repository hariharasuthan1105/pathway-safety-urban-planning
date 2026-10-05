import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from './ProtectedRoute';
import { Landing } from '../pages/Landing';
import { Login } from '../pages/Login';
import { Signup } from '../pages/Signup';
import { AppShell } from '../layouts/AppShell';
import { Overview } from '../pages/Overview';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected Application Routes */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/app/overview" replace />} />
            <Route path="overview" element={<Overview />} />
            <Route path="cities" element={<Overview />} />
            <Route path="traffic" element={<Overview />} />
            <Route path="risk" element={<Overview />} />
            <Route path="environment" element={<Overview />} />
            <Route path="events" element={<Overview />} />
            <Route path="copilot" element={<Overview />} />
            <Route path="settings" element={<Overview />} />
          </Route>

          {/* Fallback Redirects */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

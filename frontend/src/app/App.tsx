import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from './ProtectedRoute';
import { Landing } from '../pages/Landing';
import { Login } from '../pages/Login';
import { Signup } from '../pages/Signup';
import { AppShell } from '../layouts/AppShell';
import { Overview } from '../pages/Overview';
import { Cities } from '../pages/Cities';
import { Traffic } from '../pages/Traffic';
import { Risk } from '../pages/Risk';
import { Environment } from '../pages/Environment';
import { Events } from '../pages/Events';
import { Copilot } from '../pages/Copilot';
import { Settings } from '../pages/Settings';

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
            <Route path="cities" element={<Cities />} />
            <Route path="traffic" element={<Traffic />} />
            <Route path="risk" element={<Risk />} />
            <Route path="environment" element={<Environment />} />
            <Route path="events" element={<Events />} />
            <Route path="copilot" element={<Copilot />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Fallback Redirects */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

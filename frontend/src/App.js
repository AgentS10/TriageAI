import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeModeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import './animations.css';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PatientIntake from './pages/PatientIntake';
import PatientQueue from './pages/PatientQueue';
import AdminPanel from './pages/AdminPanel';
import TriageResult from './pages/TriageResult';
import PatientDetail from './pages/PatientDetail';
import NotFound from './pages/NotFound';
import ClinicianProfile from './pages/ClinicianProfile';
import ShiftHandover from './pages/ShiftHandover';
import SystemSettings from './pages/SystemSettings';
import SystemAbout from './pages/SystemAbout';

const RoleRedirect = () => {
  const { isAdmin } = useAuth();
  return <Navigate to={isAdmin ? '/dashboard' : '/queue'} replace />;
};

function App() {
  return (
    <ErrorBoundary>
      <ThemeModeProvider>
        <AuthProvider>
          <ToastProvider>
            <Router>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route element={<Layout />}>
                  <Route path="/" element={<RoleRedirect />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/intake" element={<PatientIntake />} />
                  <Route path="/queue" element={<PatientQueue />} />
                  <Route path="/result/:assessmentId" element={<TriageResult />} />
                  <Route path="/patient/:patientId" element={<PatientDetail />} />
                  <Route path="/admin/*" element={<AdminPanel />} />
                  <Route path="/profile" element={<ClinicianProfile />} />
                  <Route path="/shift-handover" element={<ShiftHandover />} />
                  <Route path="/system-settings" element={<SystemSettings />} />
                  <Route path="/about" element={<SystemAbout />} />
                </Route>
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Router>
          </ToastProvider>
        </AuthProvider>
      </ThemeModeProvider>
    </ErrorBoundary>
  );
}

export default App;

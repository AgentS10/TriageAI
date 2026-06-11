import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
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

const theme = createTheme({
  palette: {
    primary: { main: '#0d47a1', light: '#5472d3', dark: '#002171' },
    secondary: { main: '#00838f' },
    error: { main: '#c62828' },
    warning: { main: '#ef6c00' },
    success: { main: '#2e7d32' },
    info: { main: '#0277bd' },
    background: { default: '#f0f2f5', paper: '#ffffff' },
    text: { primary: '#1a1a2e', secondary: '#555770' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h3: { fontWeight: 700, letterSpacing: '-0.5px' },
    h4: { fontWeight: 700, letterSpacing: '-0.3px' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500, color: '#555770' },
    button: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04)',
          borderRadius: 16,
          border: '1px solid rgba(0,0,0,0.06)',
          transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', borderRadius: 10, fontWeight: 600, padding: '8px 20px' },
        contained: { boxShadow: '0 2px 8px rgba(13,71,161,0.25)' },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', size: 'small' },
      styleOverrides: { root: { '& .MuiOutlinedInput-root': { borderRadius: 10 } } },
    },
    MuiChip: {
      styleOverrides: { root: { fontWeight: 600, borderRadius: 8 } },
    },
    MuiAlert: {
      styleOverrides: { root: { borderRadius: 12 } },
    },
    MuiDialog: {
      styleOverrides: { paper: { borderRadius: 16 } },
    },
    MuiTableHead: {
      styleOverrides: { root: { '& .MuiTableCell-head': { fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#555770' } } },
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/intake" element={<PatientIntake />} />
              <Route path="/queue" element={<PatientQueue />} />
              <Route path="/result/:assessmentId" element={<TriageResult />} />
              <Route path="/patient/:patientId" element={<PatientDetail />} />
              <Route path="/admin/*" element={<AdminPanel />} />
              <Route path="/profile" element={<ClinicianProfile />} />
              <Route path="/shift-handover" element={<ShiftHandover />} />
              <Route path="/system-settings" element={<SystemSettings />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;

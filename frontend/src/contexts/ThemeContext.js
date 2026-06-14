import React, { createContext, useContext, useState, useMemo } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const ThemeContext = createContext();

export const useThemeMode = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useThemeMode must be used within ThemeModeProvider');
  return context;
};

const getDesignTokens = (mode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          primary: { main: '#0d47a1', light: '#5472d3', dark: '#002171' },
          secondary: { main: '#00838f' },
          error: { main: '#c62828' },
          warning: { main: '#ef6c00' },
          success: { main: '#2e7d32' },
          info: { main: '#0277bd' },
          background: { default: '#f0f2f5', paper: '#ffffff' },
          text: { primary: '#1a1a2e', secondary: '#555770' },
        }
      : {
          primary: { main: '#5c9ce6', light: '#90caf9', dark: '#1565c0' },
          secondary: { main: '#4dd0e1' },
          error: { main: '#ef5350' },
          warning: { main: '#ffb74d' },
          success: { main: '#66bb6a' },
          info: { main: '#29b6f6' },
          background: { default: '#121212', paper: '#1e1e1e' },
          text: { primary: '#e0e0e0', secondary: '#aaaaaa' },
        }),
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h3: { fontWeight: 700, letterSpacing: '-0.5px' },
    h4: { fontWeight: 700, letterSpacing: '-0.3px' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    button: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: mode === 'light'
            ? '0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04)'
            : '0 1px 3px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.2)',
          borderRadius: 16,
          border: mode === 'light' ? '1px solid rgba(0,0,0,0.06)' : '1px solid rgba(255,255,255,0.08)',
          transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', borderRadius: 10, fontWeight: 600, padding: '8px 20px' },
        contained: { boxShadow: mode === 'light' ? '0 2px 8px rgba(13,71,161,0.25)' : '0 2px 8px rgba(0,0,0,0.4)' },
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
      styleOverrides: { root: { '& .MuiTableCell-head': { fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' } } },
    },
  },
});

export const ThemeModeProvider = ({ children }) => {
  const [mode, setMode] = useState(() => {
    try { return localStorage.getItem('triageai_theme') || 'light'; }
    catch { return 'light'; }
  });

  const toggleTheme = () => {
    setMode((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('triageai_theme', next);
      return next;
    });
  };

  const theme = useMemo(() => createTheme(getDesignTokens(mode)), [mode]);

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

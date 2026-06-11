import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import Navbar from './Navbar';
import { useAuth } from '../contexts/AuthContext';
import useSessionTimeout from '../hooks/useSessionTimeout';

const Layout = () => {
  const { isAuthenticated, loading } = useAuth();
  useSessionTimeout();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <Navbar />
      <Box component="main" sx={{ p: 0 }}>
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;

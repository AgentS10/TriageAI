import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Box, IconButton,
  Menu, MenuItem, Avatar, Tooltip, Divider
} from '@mui/material';
import {
  MedicalServices as MedicalIcon,
  SpaceDashboard as DashboardIcon,
  PersonAdd as IntakeIcon,
  FormatListNumbered as QueueIcon,
  AdminPanelSettings as AdminIcon,
  Logout as LogoutIcon,
  Warning as WarningIcon,
  Person as PersonIcon,
  Assignment as HandoverIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useThemeMode } from '../contexts/ThemeContext';

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [profileAnchor, setProfileAnchor] = useState(null);
  const { mode, toggleTheme } = useThemeMode();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon fontSize="small" /> },
    { label: 'New Assessment', path: '/intake', icon: <IntakeIcon fontSize="small" /> },
    { label: 'Patient Queue', path: '/queue', icon: <QueueIcon fontSize="small" /> },
  ];
  if (isAdmin) {
    navItems.push({ label: 'Admin', path: '/admin', icon: <AdminIcon fontSize="small" /> });
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path || (path !== '/dashboard' && location.pathname.startsWith(path));

  return (
    <>
      <AppBar position="sticky" elevation={0} sx={{
        bgcolor: '#0d47a1',
        background: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #0277bd 100%)',
      }}>
        <Toolbar sx={{ minHeight: 56 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', mr: 4 }} onClick={() => navigate(isAdmin ? '/dashboard' : '/queue')}>
            <Box sx={{
              bgcolor: 'rgba(255,255,255,0.15)', borderRadius: 2, p: 0.7, mr: 1.2,
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <MedicalIcon sx={{ color: 'white', fontSize: 22 }} />
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, color: 'white', lineHeight: 1.1, fontSize: '1rem', letterSpacing: '0.5px' }}>
                TriageAI
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.6rem', letterSpacing: '1px', textTransform: 'uppercase' }}>
                Clinical Decision Support
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 0.5, flexGrow: 1 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                size="small"
                sx={{
                  color: 'white',
                  px: 2, py: 0.8,
                  borderRadius: 2,
                  fontSize: '0.82rem',
                  bgcolor: isActive(item.path) ? 'rgba(255,255,255,0.18)' : 'transparent',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.12)' },
                  ...(isActive(item.path) && { fontWeight: 700 }),
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode (night shift)'}>
              <IconButton size="small" onClick={toggleTheme} sx={{ color: 'rgba(255,255,255,0.8)' }}>
                {mode === 'dark' ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title={`${user?.username} (${user?.role})`}>
              <IconButton size="small" onClick={(e) => setProfileAnchor(e.currentTarget)} sx={{ ml: 0.5 }}>
                <Avatar sx={{
                  bgcolor: 'rgba(255,255,255,0.2)', color: 'white',
                  width: 32, height: 32, fontSize: '0.85rem', fontWeight: 700,
                  border: '2px solid rgba(255,255,255,0.4)'
                }}>
                  {user?.username?.[0]?.toUpperCase()}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu anchorEl={profileAnchor} open={Boolean(profileAnchor)} onClose={() => setProfileAnchor(null)}>
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle2" fontWeight={700}>{user?.username}</Typography>
                <Typography variant="caption" color="text.secondary">{user?.role?.toUpperCase()}</Typography>
              </Box>
              <Divider />
              <MenuItem onClick={() => { setProfileAnchor(null); navigate('/profile'); }} dense>
                <PersonIcon fontSize="small" sx={{ mr: 1 }} /> My Profile
              </MenuItem>
              <MenuItem onClick={() => { setProfileAnchor(null); navigate('/shift-handover'); }} dense>
                <HandoverIcon fontSize="small" sx={{ mr: 1 }} /> Shift Handover
              </MenuItem>
              {isAdmin && (
                <MenuItem onClick={() => { setProfileAnchor(null); navigate('/system-settings'); }} dense>
                  <AdminIcon fontSize="small" sx={{ mr: 1 }} /> System Settings
                </MenuItem>
              )}
              <Divider />
              <MenuItem onClick={() => { setProfileAnchor(null); navigate('/about'); }} dense>
                <InfoIcon fontSize="small" sx={{ mr: 1 }} /> About TriageAI
              </MenuItem>
              <MenuItem onClick={handleLogout} dense sx={{ color: 'error.main' }}>
                <LogoutIcon fontSize="small" sx={{ mr: 1 }} /> Sign Out
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{
        bgcolor: mode === 'dark' ? 'rgba(255,248,225,0.08)' : '#fff8e1',
        px: 2.5, py: 0.6,
        display: 'flex', alignItems: 'center', gap: 1,
        borderBottom: mode === 'dark' ? '1px solid rgba(255,224,130,0.15)' : '1px solid #ffe082'
      }}>
        <WarningIcon sx={{ color: '#f57f17', fontSize: 16 }} />
        <Typography variant="caption" sx={{ color: mode === 'dark' ? '#ffcc80' : '#e65100', fontWeight: 500 }}>
          Advisory Only — All AI recommendations require clinician confirmation before clinical action. This is a research prototype.
        </Typography>
      </Box>
    </>
  );
};

export default Navbar;

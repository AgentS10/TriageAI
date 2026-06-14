import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Button,
  TextField, Alert, CircularProgress, Divider
} from '@mui/material';
import {
  ArrowBack as BackIcon, Save as SaveIcon, Timer as TimerIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const SystemSettings = () => {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    session_timeout_minutes: 15,
    rate_limit_attempts: 5,
    rate_limit_window_minutes: 15,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    try {
      const r = await axios.get('/api/admin/settings');
      setSettings(r.data.settings);
    } catch (e) { setError(e.response?.data?.error || 'Failed to load settings'); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true); setSuccess(null); setError(null);
    try {
      const r = await axios.put('/api/admin/settings', settings);
      setSettings(r.data.settings);
      setSuccess('Settings updated successfully');
    } catch (e) { setError(e.response?.data?.error || 'Failed to save settings'); }
    finally { setSaving(false); }
  };

  if (!isAdmin) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Access denied. Admin role required.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }} className="fade-slide-up">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/admin')} variant="outlined">
          Back
        </Button>
        <Typography variant="h4" fontWeight={700}>System Settings</Typography>
      </Box>

      {loading ? <CircularProgress /> : (
        <>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

          <Card>
            <CardContent sx={{ p: 4 }}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TimerIcon color="primary" />
                    <Typography variant="h6">Session & Security</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField fullWidth type="number" label="Session Timeout (minutes)"
                    value={settings.session_timeout_minutes}
                    onChange={(e) => setSettings({ ...settings, session_timeout_minutes: parseInt(e.target.value) || 15 })}
                    helperText="Auto-logout after inactivity" />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField fullWidth type="number" label="Rate Limit Attempts"
                    value={settings.rate_limit_attempts}
                    onChange={(e) => setSettings({ ...settings, rate_limit_attempts: parseInt(e.target.value) || 5 })}
                    helperText="Max login attempts per IP" />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField fullWidth type="number" label="Rate Limit Window (minutes)"
                    value={settings.rate_limit_window_minutes}
                    onChange={(e) => setSettings({ ...settings, rate_limit_window_minutes: parseInt(e.target.value) || 15 })}
                    helperText="Time window for rate limiting" />
                </Grid>
              </Grid>

              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                <Button variant="contained" startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={handleSave} disabled={saving}>
                  Save Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </>
      )}
    </Container>
  );
};

export default SystemSettings;

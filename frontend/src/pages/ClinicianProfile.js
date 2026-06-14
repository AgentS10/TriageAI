import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Button,
  TextField, Alert, CircularProgress, Chip, Divider, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Skeleton
} from '@mui/material';
import {
  Person as PersonIcon, Lock as LockIcon, Assessment as AssessmentIcon,
  CheckCircle as ConfirmIcon, SwapHoriz as OverrideIcon, Schedule as PendingIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ClinicianProfile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pwForm, setPwForm] = useState({ current: '', new: '', confirm: '' });
  const [pwError, setPwError] = useState(null);
  const [pwSuccess, setPwSuccess] = useState(null);
  const [pwLoading, setPwLoading] = useState(false);

  useEffect(() => { fetchActivity(); }, []);

  const fetchActivity = async () => {
    try {
      const r = await axios.get('/api/auth/profile/activity');
      setActivity(r.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwError(null); setPwSuccess(null);
    if (pwForm.new !== pwForm.confirm) {
      setPwError('New passwords do not match'); return;
    }
    setPwLoading(true);
    try {
      await axios.post('/api/auth/change-password', {
        current_password: pwForm.current,
        new_password: pwForm.new
      });
      setPwSuccess('Password changed successfully');
      setPwForm({ current: '', new: '', confirm: '' });
    } catch (e) {
      setPwError(e.response?.data?.error || 'Password change failed');
    } finally { setPwLoading(false); }
  };

  const statCards = activity ? [
    { label: 'Total Assessments', value: activity.stats.total_assessments, icon: <AssessmentIcon />, color: 'primary.main' },
    { label: 'Confirmed', value: activity.stats.confirmed, icon: <ConfirmIcon />, color: 'success.main' },
    { label: 'Overridden', value: activity.stats.overridden, icon: <OverrideIcon />, color: 'warning.main' },
    { label: 'Pending', value: activity.stats.pending, icon: <PendingIcon />, color: 'error.main' },
  ] : [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }} className="fade-slide-up">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/')} variant="outlined">
          Back
        </Button>
        <Typography variant="h4" fontWeight={700}>My Profile</Typography>
      </Box>

      {loading && !activity && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}><Skeleton variant="rounded" height={200} /></Grid>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              {[0,1,2,3].map(i => (<Grid item xs={6} sm={3} key={i}><Skeleton variant="rounded" height={100} /></Grid>))}
            </Grid>
            <Skeleton variant="rounded" height={180} sx={{ mt: 2 }} />
          </Grid>
          <Grid item xs={12}><Skeleton variant="rounded" height={200} /></Grid>
        </Grid>
      )}

      <Grid container spacing={3} sx={{ display: loading && !activity ? 'none' : undefined }}>
        {/* User Info */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Box sx={{ bgcolor: 'primary.main', color: 'white', borderRadius: '50%', p: 1.5 }}>
                  <PersonIcon sx={{ fontSize: 32 }} />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={700}>{user?.username}</Typography>
                  <Chip label={user?.role} size="small" color={user?.role === 'admin' ? 'secondary' : 'primary'} />
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary">
                <strong>User ID:</strong> {activity?.user?.user_id}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                <strong>Joined:</strong> {activity?.user?.created_at ? new Date(activity.user.created_at).toLocaleDateString() : '—'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                <strong>Status:</strong> {activity?.user?.is_active ? 'Active' : 'Inactive'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Stats */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            {statCards.map((s, i) => (
              <Grid item xs={6} sm={3} key={i}>
                <Card sx={{ textAlign: 'center', py: 2 }}>
                  <CardContent>
                    <Box sx={{ color: s.color, mb: 1 }}>{React.cloneElement(s.icon, { sx: { fontSize: 28 } })}</Box>
                    <Typography variant="h4" sx={{ color: s.color, fontWeight: 800 }}>{s.value}</Typography>
                    <Typography variant="caption" color="text.secondary">{s.label}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Change Password */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <LockIcon color="primary" />
                <Typography variant="h6">Change Password</Typography>
              </Box>
              {pwError && <Alert severity="error" sx={{ mb: 2 }}>{pwError}</Alert>}
              {pwSuccess && <Alert severity="success" sx={{ mb: 2 }}>{pwSuccess}</Alert>}
              <Box component="form" onSubmit={handleChangePassword}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <TextField fullWidth type="password" label="Current Password" value={pwForm.current}
                      onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })} required />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField fullWidth type="password" label="New Password" value={pwForm.new}
                      onChange={(e) => setPwForm({ ...pwForm, new: e.target.value })} required
                      helperText="Min 8 chars, upper, lower, digit" />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField fullWidth type="password" label="Confirm Password" value={pwForm.confirm}
                      onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })} required />
                  </Grid>
                </Grid>
                <Button type="submit" variant="contained" sx={{ mt: 2 }}
                  disabled={pwLoading || !pwForm.current || !pwForm.new || !pwForm.confirm}>
                  {pwLoading ? <CircularProgress size={20} /> : 'Update Password'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Activity</Typography>
              {loading ? <Skeleton variant="rounded" height={120} /> : activity?.recent_activity?.length > 0 ? (
                <TableContainer component={Paper} elevation={0}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Assessment ID</TableCell>
                        <TableCell>AI Priority</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Time</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {activity.recent_activity.map((a) => (
                        <TableRow key={a.assessment_id} hover>
                          <TableCell><Typography variant="caption">{a.assessment_id.slice(0, 8)}...</Typography></TableCell>
                          <TableCell><Chip label={`L${a.ai_priority}`} size="small" sx={{ fontWeight: 700 }} /></TableCell>
                          <TableCell>
                            <Chip label={a.status} size="small" color={a.status === 'resolved' ? 'success' : 'warning'} variant="outlined" />
                          </TableCell>
                          <TableCell><Typography variant="caption">{new Date(a.assessed_at).toLocaleString()}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="text.secondary">No recent activity.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ClinicianProfile;

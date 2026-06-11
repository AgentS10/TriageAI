import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Grid, Card, CardContent, Typography, Box, Button,
  CircularProgress, Chip, LinearProgress, Skeleton
} from '@mui/material';
import {
  PersonAdd as IntakeIcon,
  FormatListNumbered as QueueIcon,
  Assessment as AssessmentIcon,
  ArrowForward as ArrowIcon,
  Favorite as HeartIcon,
  TrendingUp as TrendingIcon,
  CheckCircle as CheckIcon,
  SwapHoriz as OverrideIcon,
  Speed as SpeedIcon,
  AccessTime as TimeIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const StatCard = ({ value, label, color, icon, suffix = '' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent sx={{ p: 2.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
            {label}
          </Typography>
          <Typography variant="h4" sx={{ color, fontWeight: 800, mt: 0.5 }}>
            {value}{suffix}
          </Typography>
        </Box>
        <Box sx={{ bgcolor: `${color}15`, borderRadius: 2, p: 1, display: 'flex' }}>
          {React.cloneElement(icon, { sx: { color, fontSize: 22 } })}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const ActionCard = ({ title, description, icon, onClick, gradient }) => (
  <Card sx={{
    cursor: 'pointer', height: '100%',
    transition: 'all 0.25s ease',
    '&:hover': { transform: 'translateY(-6px)', boxShadow: '0 12px 24px rgba(0,0,0,0.12)' },
  }} onClick={onClick}>
    <CardContent sx={{ p: 3 }}>
      <Box sx={{
        background: gradient, borderRadius: 3, p: 2, mb: 2,
        display: 'flex', alignItems: 'center', justifyContent: 'center', width: 56, height: 56,
      }}>
        {React.cloneElement(icon, { sx: { color: 'white', fontSize: 28 } })}
      </Box>
      <Typography variant="h6" sx={{ mb: 0.5 }}>{title}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.5 }}>
        {description}
      </Typography>
      <Button size="small" endIcon={<ArrowIcon />} sx={{ fontWeight: 600 }}>
        Open
      </Button>
    </CardContent>
  </Card>
);

const Dashboard = () => {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [queueStats, setQueueStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchStats(); fetchQueueStats(); }, []);

  const fetchStats = async () => {
    try {
      if (isAdmin) {
        const r = await axios.get('/api/admin/analytics?days=7');
        setStats(r.data);
      }
    } catch (e) { console.error('Stats fetch failed:', e); }
    finally { setLoading(false); }
  };

  const fetchQueueStats = async () => {
    try {
      const r = await axios.get('/api/queue/stats');
      setQueueStats(r.data);
    } catch (e) { console.error('Queue stats failed:', e); }
  };

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Good Morning' : now.getHours() < 18 ? 'Good Afternoon' : 'Good Evening';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          {greeting}, <Box component="span" sx={{ color: 'primary.main' }}>{user?.username}</Box>
        </Typography>
        <Typography variant="subtitle1">
          TriageAI Clinical Decision Support — {now.toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </Typography>
      </Box>

      {/* Live Queue Stats */}
      {queueStats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: queueStats.critical_count > 0 ? '#ffebee' : 'white' }}
              className={queueStats.critical_count > 0 ? 'pulse-critical' : ''}>
              <CardContent sx={{ py: 2, textAlign: 'center' }}>
                <Typography variant="h3" sx={{ color: '#c62828', fontWeight: 800 }} className="count-up">
                  {queueStats.critical_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">Critical Waiting (L1-2)</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ py: 2, textAlign: 'center' }}>
                <Typography variant="h3" sx={{ color: '#ef6c00', fontWeight: 800 }} className="count-up">
                  {queueStats.pending_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">Total Pending</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ py: 2, textAlign: 'center' }}>
                <Typography variant="h3" sx={{ color: '#0d47a1', fontWeight: 800 }} className="count-up">
                  {queueStats.today_total}
                </Typography>
                <Typography variant="caption" color="text.secondary">Today's Assessments</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ py: 2, textAlign: 'center' }}>
                <Typography variant="h3" sx={{ color: '#2e7d32', fontWeight: 800 }} className="count-up">
                  {queueStats.today_confirmed}
                </Typography>
                <Typography variant="caption" color="text.secondary">Today Confirmed</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Quick Actions */}
      <Typography variant="h6" sx={{ mb: 2 }}>Quick Actions</Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <ActionCard title="New Triage Assessment" description="Enter patient vitals and chief complaint to generate an AI-powered ESI priority recommendation."
            icon={<IntakeIcon />} gradient="linear-gradient(135deg, #0d47a1, #1565c0)" onClick={() => navigate('/intake')} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <ActionCard title="Patient Queue" description="View all patients awaiting triage decisions, sorted by AI-predicted urgency level."
            icon={<QueueIcon />} gradient="linear-gradient(135deg, #ef6c00, #ff9800)" onClick={() => navigate('/queue')} />
        </Grid>
        {isAdmin && (
          <Grid item xs={12} sm={6} md={4}>
            <ActionCard title="Administration" description="Access audit logs, manage user accounts, and review system-wide analytics."
              icon={<AssessmentIcon />} gradient="linear-gradient(135deg, #00838f, #00acc1)" onClick={() => navigate('/admin')} />
          </Grid>
        )}
      </Grid>

      {/* Admin Stats */}
      {isAdmin && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>Last 7 Days</Typography>
          {loading ? (
            <Grid container spacing={3}>
              {[1,2,3,4].map(i => <Grid item xs={6} sm={3} key={i}><Skeleton variant="rounded" height={100} sx={{ borderRadius: 4 }} /></Grid>)}
            </Grid>
          ) : stats ? (
            <Grid container spacing={3}>
              <Grid item xs={6} sm={3}>
                <StatCard value={stats.overview?.total_assessments || 0} label="Total Assessments" color="#0d47a1" icon={<HeartIcon />} />
              </Grid>
              <Grid item xs={6} sm={3}>
                <StatCard value={stats.overview?.ai_clinician_agreement_rate || 0} label="AI Agreement" color="#2e7d32" icon={<CheckIcon />} suffix="%" />
              </Grid>
              <Grid item xs={6} sm={3}>
                <StatCard value={stats.overview?.overridden_assessments || 0} label="Overrides" color="#ef6c00" icon={<OverrideIcon />} />
              </Grid>
              <Grid item xs={6} sm={3}>
                <StatCard value={Math.round(stats.overview?.override_rate || 0)} label="Override Rate" color="#c62828" icon={<TrendingIcon />} suffix="%" />
              </Grid>
            </Grid>
          ) : (
            <Card sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">No data available for this period.</Typography>
            </Card>
          )}
        </>
      )}

      {/* System Info */}
      <Card sx={{ mt: 4, bgcolor: '#f8f9fa' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>System Status</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#2e7d32' }} />
                <Typography variant="body2">ML Model Active</Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#2e7d32' }} />
                <Typography variant="body2">API Healthy</Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#2e7d32' }} />
                <Typography variant="body2">Audit Logging Active</Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Dashboard;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Button,
  Chip, CircularProgress, Alert, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Divider
} from '@mui/material';
import {
  Assignment as AssignmentIcon, CheckCircle as ConfirmIcon,
  SwapHoriz as OverrideIcon, Schedule as PendingIcon,
  ArrowBack as BackIcon, TrendingUp as TrendIcon
} from '@mui/icons-material';
import axios from 'axios';

const ESI_COLORS = { 1: '#c62828', 2: '#ef6c00', 3: '#f9a825', 4: '#2e7d32', 5: '#0277bd' };

const ShiftHandover = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchHandover(); }, []);

  const fetchHandover = async () => {
    try {
      const r = await axios.get('/api/shift-handover');
      setData(r.data);
    } catch (e) { setError(e.response?.data?.error || 'Failed to load handover'); }
    finally { setLoading(false); }
  };

  if (loading) return (
    <Container sx={{ py: 8, textAlign: 'center' }}>
      <CircularProgress />
    </Container>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Shift Handover</Typography>
          <Typography variant="subtitle2" color="text.secondary">
            {data?.date ? new Date(data.date).toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : ''}
          </Typography>
        </Box>
        <Button startIcon={<BackIcon />} variant="outlined" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={6} sm={3}>
          <Card><CardContent sx={{ textAlign: 'center', py: 3 }}>
            <AssignmentIcon sx={{ fontSize: 28, color: '#0d47a1', mb: 1 }} />
            <Typography variant="h4" sx={{ color: '#0d47a1', fontWeight: 800 }}>{data?.summary?.total || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Total Assessments</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card><CardContent sx={{ textAlign: 'center', py: 3 }}>
            <ConfirmIcon sx={{ fontSize: 28, color: '#2e7d32', mb: 1 }} />
            <Typography variant="h4" sx={{ color: '#2e7d32', fontWeight: 800 }}>{data?.summary?.confirmed || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Confirmed</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card><CardContent sx={{ textAlign: 'center', py: 3 }}>
            <OverrideIcon sx={{ fontSize: 28, color: '#ef6c00', mb: 1 }} />
            <Typography variant="h4" sx={{ color: '#ef6c00', fontWeight: 800 }}>{data?.summary?.overridden || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Overrides</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card><CardContent sx={{ textAlign: 'center', py: 3 }}>
            <PendingIcon sx={{ fontSize: 28, color: '#c62828', mb: 1 }} />
            <Typography variant="h4" sx={{ color: '#c62828', fontWeight: 800 }}>{data?.summary?.pending || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Pending</Typography>
          </CardContent></Card>
        </Grid>

        {/* Priority Distribution */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Priority Distribution</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(data?.summary?.by_priority || {}).sort((a, b) => a[0] - b[0]).map(([level, count]) => (
                  <Chip key={level} label={`Level ${level}: ${count}`}
                    sx={{ bgcolor: ESI_COLORS[level] || '#999', color: 'white', fontWeight: 700 }} />
                ))}
              </Box>
              {!data?.summary?.by_priority || Object.keys(data.summary.by_priority).length === 0 && (
                <Typography color="text.secondary" sx={{ mt: 2 }}>No assessments today.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Override Rate */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Override Rate</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendIcon sx={{ fontSize: 40, color: '#ef6c00' }} />
                <Box>
                  <Typography variant="h3" fontWeight={800}>
                    {data?.summary?.total > 0 ? Math.round((data.summary.overridden / data.summary.total) * 100) : 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {data?.summary?.overridden || 0} of {data?.summary?.total || 0} assessments overridden
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Assessments Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Today's Assessments</Typography>
              {data?.assessments?.length > 0 ? (
                <TableContainer component={Paper} elevation={0}>
                  <Table size="small">
                    <TableHead><TableRow>
                      <TableCell>ID</TableCell><TableCell>AI Priority</TableCell>
                      <TableCell>Clinician Priority</TableCell><TableCell>Status</TableCell><TableCell>Time</TableCell>
                    </TableRow></TableHead>
                    <TableBody>
                      {data.assessments.map((a) => (
                        <TableRow key={a.assessment_id} hover>
                          <TableCell><Typography variant="caption">{a.assessment_id.slice(0, 8)}...</Typography></TableCell>
                          <TableCell><Chip label={`L${a.ai_priority}`} size="small"
                            sx={{ bgcolor: ESI_COLORS[a.ai_priority], color: 'white', fontWeight: 700 }} /></TableCell>
                          <TableCell>{a.clinician_priority ? <Chip label={`L${a.clinician_priority}`} size="small" variant="outlined" /> : '—'}</TableCell>
                          <TableCell><Chip label={a.status} size="small" color={a.status === 'resolved' ? 'success' : 'warning'} variant="outlined" /></TableCell>
                          <TableCell><Typography variant="caption">{new Date(a.assessed_at).toLocaleTimeString()}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="text.secondary">No assessments recorded today.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ShiftHandover;

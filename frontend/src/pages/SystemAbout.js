import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Chip, Alert,
  Button, Divider, Table, TableBody, TableCell,
  TableContainer, TableRow, Paper, Skeleton
} from '@mui/material';
import {
  ArrowBack as BackIcon, Info as InfoIcon, Security as SecurityIcon,
  Memory as ModelIcon, Storage as DbIcon, CheckCircle as OkIcon,
  Warning as WarnIcon
} from '@mui/icons-material';
import axios from 'axios';

const SystemAbout = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const r = await axios.get('/api/health/detailed');
        setHealth(r.data);
      } catch (e) {
        try {
          const r = await axios.get('/api/health');
          setHealth(r.data);
        } catch (e2) { console.error(e2); }
      } finally { setLoading(false); }
    };
    fetchHealth();
  }, []);

  const StatusChip = ({ ok, label }) => (
    <Chip
      icon={ok ? <OkIcon /> : <WarnIcon />}
      label={label || (ok ? 'Healthy' : 'Unhealthy')}
      color={ok ? 'success' : 'warning'}
      size="small"
      variant="outlined"
    />
  );

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Skeleton variant="text" width={120} height={36} sx={{ mb: 1 }} />
        <Skeleton variant="text" width={260} height={40} sx={{ mb: 3 }} />
        <Skeleton variant="rounded" height={50} sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}><Skeleton variant="rounded" height={220} /></Grid>
          <Grid item xs={12} md={6}><Skeleton variant="rounded" height={220} /></Grid>
          <Grid item xs={12}><Skeleton variant="rounded" height={160} /></Grid>
        </Grid>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }} className="fade-slide-up">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate(-1)} variant="outlined">Back</Button>
        <Typography variant="h4" fontWeight={700}>About TriageAI</Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }} icon={<InfoIcon />}>
        <strong>Advisory Only</strong> — All AI recommendations require clinician confirmation before clinical action. This is a research prototype, not a certified medical device.
      </Alert>

      <Grid container spacing={3}>
        {/* System Overview */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <InfoIcon color="primary" />
                <Typography variant="h6">System Information</Typography>
              </Box>
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableBody>
                    <TableRow><TableCell><strong>Application</strong></TableCell><TableCell>TriageAI Clinical Decision Support System</TableCell></TableRow>
                    <TableRow><TableCell><strong>Version</strong></TableCell><TableCell>1.0.0</TableCell></TableRow>
                    <TableRow><TableCell><strong>Author</strong></TableCell><TableCell>M.S.M. Sajidh (CL/BSCSD/34/01)</TableCell></TableRow>
                    <TableRow><TableCell><strong>Institution</strong></TableCell><TableCell>Cardiff Metropolitan University</TableCell></TableRow>
                    <TableRow><TableCell><strong>Framework</strong></TableCell><TableCell>React 18 + Flask + PostgreSQL</TableCell></TableRow>
                    <TableRow><TableCell><strong>ML Engine</strong></TableCell><TableCell>XGBoost + SHAP Explainability</TableCell></TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Health Status */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <ModelIcon color="primary" />
                <Typography variant="h6">System Health</Typography>
              </Box>
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell><strong>Overall</strong></TableCell>
                      <TableCell><StatusChip ok={health?.status === 'healthy'} /></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>ML Model</strong></TableCell>
                      <TableCell><StatusChip ok={health?.components?.model === 'loaded'} label={health?.components?.model === 'loaded' ? 'Loaded' : 'Not loaded'} /></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Database</strong></TableCell>
                      <TableCell><StatusChip ok={health?.components?.database === 'connected'} label={health?.components?.database === 'connected' ? 'Connected' : 'Disconnected'} /></TableCell>
                    </TableRow>
                    {health?.model_contract_hash && (
                      <TableRow>
                        <TableCell><strong>Contract Hash</strong></TableCell>
                        <TableCell><Typography variant="caption" fontFamily="monospace">{health.model_contract_hash}</Typography></TableCell>
                      </TableRow>
                    )}
                    {health?.uptime_seconds != null && (
                      <TableRow>
                        <TableCell><strong>Uptime</strong></TableCell>
                        <TableCell>{Math.floor(health.uptime_seconds / 3600)}h {Math.floor((health.uptime_seconds % 3600) / 60)}m</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Compliance */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <SecurityIcon color="primary" />
                <Typography variant="h6">Compliance & Security</Typography>
              </Box>
              <Grid container spacing={2}>
                {[
                  'HIPAA — Protected Health Information safeguards',
                  'GDPR Art. 17 — Right to Erasure (pseudonymisation)',
                  'RBAC — Role-Based Access Control (admin/clinician)',
                  'JWT — Token-based authentication with refresh rotation',
                  'Fernet — AES-128 encryption with key rotation for PII',
                  'Immutable Audit Trail — ON DELETE RESTRICT integrity',
                  'OWASP — Security headers (CSP, HSTS, X-Frame-Options)',
                  'Rate Limiting — API throttling on sensitive endpoints',
                  'CITI Training — IRB human subjects research certification',
                ].map((item, i) => (
                  <Grid item xs={12} sm={6} key={i}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                      <OkIcon sx={{ color: 'success.main', fontSize: 18, mt: 0.3 }} />
                      <Typography variant="body2">{item}</Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Disclaimer */}
        <Grid item xs={12}>
          <Alert severity="warning">
            <strong>Clinical Disclaimer:</strong> TriageAI is a research prototype developed as part of a Software Engineering dissertation project.
            It is NOT a certified medical device and must NOT be used for actual clinical decision-making.
            All AI predictions are advisory only and require clinician review before any clinical action.
            The ESI predictions are based on an XGBoost model trained on publicly available datasets and may not reflect real-world clinical accuracy.
          </Alert>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SystemAbout;

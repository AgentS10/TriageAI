import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Card, CardContent, Typography, Box, Grid, Button,
  Chip, Alert, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem,
  Snackbar
} from '@mui/material';
import {
  CheckCircle as ConfirmIcon,
  SwapHoriz as OverrideIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import axios from 'axios';

const ESI_COLORS = {
  1: { bg: '#ffebee', color: '#d32f2f', label: 'IMMEDIATE' },
  2: { bg: '#fff3e0', color: '#f57c00', label: 'EMERGENT' },
  3: { bg: '#fffde7', color: '#f9a825', label: 'URGENT' },
  4: { bg: '#e8f5e9', color: '#388e3c', label: 'LESS URGENT' },
  5: { bg: '#e3f2fd', color: '#1976d2', label: 'NON-URGENT' },
};

const OVERRIDE_REASONS = {
  'OVR-01': 'Clinical instinct based on patient presentation',
  'OVR-02': 'Additional history not captured in vitals',
  'OVR-03': 'Known patient with relevant medical history',
  'OVR-04': 'Patient showing signs of rapid deterioration',
  'OVR-05': 'Communication barrier affecting assessment',
  'OVR-06': 'Concern about vital sign measurement accuracy',
  'OVR-07': 'Other (documented in notes)',
};

const TriageResult = () => {
  const { assessmentId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [overrideLevel, setOverrideLevel] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [resolved, setResolved] = useState(false);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    if (assessmentId) {
      const cached = sessionStorage.getItem(`result_${assessmentId}`);
      if (cached) {
        setResult(JSON.parse(cached));
        setLoading(false);
      } else {
        axios.get(`/api/assessment/${assessmentId}`)
          .then(r => { setResult(r.data); setLoading(false); })
          .catch(() => setLoading(false));
      }
    }
  }, [assessmentId]);

  const handleConfirm = async () => {
    setActionLoading(true);
    try {
      await axios.post(`/api/confirm/${assessmentId}`);
      setResolved(true);
      setToast({ open: true, message: 'Assessment confirmed and logged', severity: 'success' });
    } catch (error) {
      setToast({ open: true, message: error.response?.data?.error || 'Confirmation failed', severity: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOverride = async () => {
    if (!overrideLevel || !overrideReason) return;
    setActionLoading(true);
    try {
      await axios.post(`/api/override/${assessmentId}`, {
        new_level: parseInt(overrideLevel),
        reason_code: overrideReason
      });
      setOverrideOpen(false);
      setResolved(true);
      setToast({ open: true, message: 'Override logged to audit trail', severity: 'success' });
    } catch (error) {
      setToast({ open: true, message: error.response?.data?.error || 'Override failed', severity: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!result) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="info">No result data found. Please start a new assessment.</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/intake')} sx={{ mt: 2 }}>
          New Assessment
        </Button>
      </Container>
    );
  }

  const esi = result.ai_prediction?.esi_level || 3;
  const esiStyle = ESI_COLORS[esi] || ESI_COLORS[3];

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      {resolved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Assessment resolved successfully. Logged to audit trail.
        </Alert>
      )}

      {/* Main Result Card */}
      <Card className="fade-slide-up" sx={{ mb: 3, border: `3px solid ${esiStyle.color}`, bgcolor: esiStyle.bg }}>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="overline" color="text.secondary">
            AI Triage Recommendation
          </Typography>
          <Box className={esi <= 1 ? 'pulse-critical' : esi <= 2 ? 'pulse-emergent' : ''} sx={{
            display: 'inline-block', px: 4, py: 2, borderRadius: 2, mt: 2,
            bgcolor: esiStyle.color, color: 'white'
          }}>
            <Typography variant="h2" fontWeight="bold">
              ESI Level {esi}
            </Typography>
            <Typography variant="h5">
              {esiStyle.label}
            </Typography>
          </Box>
          <Typography variant="h6" sx={{ mt: 2 }}>
            Confidence: {(result.ai_prediction?.confidence * 100).toFixed(1)}%
          </Typography>
        </CardContent>
      </Card>

      {/* SHAP Explanation */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Top Contributing Factors (SHAP)
          </Typography>
          {result.shap_explanation?.map((item, idx) => (
            <Box key={idx} sx={{ display: 'flex', alignItems: 'center', mb: 1.5, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Chip label={`#${idx + 1}`} size="small" color="primary" sx={{ mr: 2 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="subtitle2">
                  {item.feature.replace(/_/g, ' ').toUpperCase()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Value: {item.value} | Impact: {item.impact > 0 ? '+' : ''}{item.impact.toFixed(4)}
                </Typography>
              </Box>
              <Chip
                label={item.impact > 0 ? 'Increases urgency' : 'Decreases urgency'}
                color={item.impact > 0 ? 'error' : 'success'}
                size="small"
                variant="outlined"
              />
            </Box>
          ))}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      {!resolved && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Clinical Decision
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Review the AI recommendation and either confirm or override with clinical justification.
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Button
                  fullWidth variant="contained" color="success" size="large"
                  startIcon={<ConfirmIcon />}
                  onClick={handleConfirm}
                  disabled={actionLoading}
                >
                  Confirm AI Recommendation
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth variant="outlined" color="warning" size="large"
                  startIcon={<OverrideIcon />}
                  onClick={() => setOverrideOpen(true)}
                  disabled={actionLoading}
                >
                  Override
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/queue')}>
          Back to Queue
        </Button>
        {result?.patient_id && (
          <Button variant="outlined" onClick={() => navigate(`/patient/${result.patient_id}`)}>
            View Patient Record
          </Button>
        )}
        <Button variant="outlined" onClick={() => window.print()}>
          Print Result
        </Button>
        <Button variant="contained" onClick={() => navigate('/intake')}>
          New Assessment
        </Button>
      </Box>

      {/* Override Dialog */}
      <Dialog open={overrideOpen} onClose={() => setOverrideOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Override AI Recommendation</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select the correct ESI level and provide a coded reason for the override.
            This will be logged to the audit trail.
          </Typography>
          <FormControl fullWidth sx={{ mb: 2, mt: 1 }}>
            <InputLabel>New ESI Level</InputLabel>
            <Select value={overrideLevel} onChange={(e) => setOverrideLevel(e.target.value)}>
              {[1, 2, 3, 4, 5].map((level) => (
                <MenuItem key={level} value={level}>
                  Level {level} — {ESI_COLORS[level].label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Override Reason</InputLabel>
            <Select value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)}>
              {Object.entries(OVERRIDE_REASONS).map(([code, text]) => (
                <MenuItem key={code} value={code}>
                  [{code}] {text}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOverrideOpen(false)}>Cancel</Button>
          <Button
            onClick={handleOverride} variant="contained" color="warning"
            disabled={!overrideLevel || !overrideReason || actionLoading}
          >
            Submit Override
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notification */}
      <Snackbar open={toast.open} autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={toast.severity} onClose={() => setToast({ ...toast, open: false })} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default TriageResult;

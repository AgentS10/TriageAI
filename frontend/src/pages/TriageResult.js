import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Card, CardContent, Typography, Box, Grid, Button,
  Chip, Alert, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem,
  Checkbox, FormControlLabel
} from '@mui/material';
import {
  CheckCircle as ConfirmIcon,
  SwapHoriz as OverrideIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import axios from 'axios';
import { useToast } from '../contexts/ToastContext';

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

// Clinical feature metadata for natural-language SHAP explanations
const CLINICAL_FEATURES = {
  heart_rate: { label: 'Heart Rate', unit: 'bpm', normal: [60, 100] },
  sbp: { label: 'Systolic Blood Pressure', unit: 'mmHg', normal: [90, 140] },
  dbp: { label: 'Diastolic Blood Pressure', unit: 'mmHg', normal: [60, 90] },
  respiratory_rate: { label: 'Respiratory Rate', unit: 'br/min', normal: [12, 20] },
  spo2: { label: 'Oxygen Saturation (SpO\u2082)', unit: '%', normal: [95, 100] },
  temperature: { label: 'Body Temperature', unit: '\u00B0C', normal: [36.1, 37.2] },
  gcs: { label: 'Glasgow Coma Scale', unit: '', normal: [14, 15] },
  pain_score: { label: 'Pain Score', unit: '/10', normal: [0, 3] },
  age: { label: 'Patient Age', unit: 'years', normal: [18, 65] },
  sex_encoded: { label: 'Biological Sex', unit: '' },
};

const getNormalStatus = (featureKey, value) => {
  const meta = CLINICAL_FEATURES[featureKey];
  if (!meta?.normal) return '';
  const [low, high] = meta.normal;
  const v = parseFloat(value);
  if (featureKey === 'gcs') {
    if (v >= 14) return 'normal';
    if (v >= 9) return 'moderate impairment';
    return 'severe impairment';
  }
  if (v < low) return 'below normal';
  if (v > high) return 'above normal';
  return 'normal';
};

const translateSHAP = (item) => {
  const meta = CLINICAL_FEATURES[item.feature];
  const direction = item.impact > 0 ? 'increased' : 'decreased';
  const absImpact = Math.abs(item.impact);
  const magnitude = absImpact > 0.1 ? 'significantly' : absImpact > 0.03 ? 'moderately' : 'slightly';

  if (!meta) {
    const name = item.feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    return `${name} (${item.value}) ${magnitude} ${direction} urgency`;
  }

  const status = getNormalStatus(item.feature, item.value);
  const statusStr = status ? ` (${status})` : '';
  const unitStr = meta.unit ? ` ${meta.unit}` : '';
  return `${meta.label} of ${item.value}${unitStr}${statusStr} ${magnitude} ${direction} urgency score`;
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
  const { showToast } = useToast();
  const [reviewed, setReviewed] = useState(false);

  useEffect(() => {
    if (assessmentId) {
      const cached = sessionStorage.getItem(`result_${assessmentId}`);
      if (cached) {
        const cachedData = JSON.parse(cached);
        setResult(cachedData);
        setLoading(false);
        // Fetch full detail (with vitals) if not present in cache
        if (!cachedData.vitals) {
          axios.get(`/api/assessment/${assessmentId}`)
            .then(r => { setResult(r.data); })
            .catch(() => {});
        }
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
      showToast('Assessment confirmed and logged', 'success');
    } catch (error) {
      showToast(error.response?.data?.error || 'Confirmation failed', 'error');
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
      showToast('Override logged to audit trail', 'success');
    } catch (error) {
      showToast(error.response?.data?.error || 'Override failed', 'error');
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

      {/* Derived Clinical Indicators */}
      {result.vitals && (() => {
        const v = result.vitals;
        const shockIndex = v.sbp > 0 ? (v.heart_rate / v.sbp).toFixed(2) : null;
        const map = ((v.sbp + 2 * v.dbp) / 3).toFixed(0);
        const pulsePressure = v.sbp - v.dbp;
        return (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Derived Clinical Indicators</Typography>
              <Grid container spacing={2}>
                {shockIndex && (
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: parseFloat(shockIndex) > 0.9 ? 'rgba(198,40,40,0.06)' : 'action.hover', borderRadius: 2, border: '1px solid', borderColor: parseFloat(shockIndex) > 0.9 ? 'error.light' : 'divider' }}>
                      <Typography variant="h5" fontWeight={700} color={parseFloat(shockIndex) > 0.9 ? 'error.main' : parseFloat(shockIndex) > 0.7 ? 'warning.main' : 'success.main'}>
                        {shockIndex}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">Shock Index (HR/SBP)</Typography>
                      <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                        Normal &lt; 0.7 | Concern &gt; 0.9
                      </Typography>
                    </Box>
                  </Grid>
                )}
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: parseInt(map) < 65 ? 'rgba(198,40,40,0.06)' : 'action.hover', borderRadius: 2, border: '1px solid', borderColor: parseInt(map) < 65 ? 'error.light' : 'divider' }}>
                    <Typography variant="h5" fontWeight={700} color={parseInt(map) < 65 ? 'error.main' : parseInt(map) > 105 ? 'warning.main' : 'success.main'}>
                      {map} <Typography component="span" variant="caption">mmHg</Typography>
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Mean Arterial Pressure</Typography>
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                      Normal: 70–105 mmHg
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: pulsePressure > 60 || pulsePressure < 25 ? 'rgba(239,108,0,0.06)' : 'action.hover', borderRadius: 2, border: '1px solid', borderColor: pulsePressure > 60 || pulsePressure < 25 ? 'warning.light' : 'divider' }}>
                    <Typography variant="h5" fontWeight={700} color={pulsePressure > 60 || pulsePressure < 25 ? 'warning.main' : 'success.main'}>
                      {pulsePressure} <Typography component="span" variant="caption">mmHg</Typography>
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Pulse Pressure</Typography>
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                      Normal: 30–50 mmHg
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        );
      })()}

      {/* SHAP Explanation — Natural Language */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI Explanation — Key Contributing Factors
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            The following factors had the greatest influence on the AI's triage recommendation (SHAP analysis):
          </Typography>
          {result.shap_explanation?.length > 0 ? result.shap_explanation.map((item, idx) => (
            <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', mb: 1.5, p: 2, bgcolor: item.impact > 0 ? 'rgba(198,40,40,0.04)' : 'rgba(46,125,50,0.04)', borderRadius: 2, border: '1px solid', borderColor: item.impact > 0 ? 'rgba(198,40,40,0.12)' : 'rgba(46,125,50,0.12)' }}>
              <Chip label={`#${idx + 1}`} size="small" color={item.impact > 0 ? 'error' : 'success'} sx={{ mr: 2, mt: 0.3 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                  {translateSHAP(item)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Raw: {(CLINICAL_FEATURES[item.feature]?.label || item.feature.replace(/_/g, ' '))} = {item.value} | SHAP impact: {item.impact > 0 ? '+' : ''}{item.impact.toFixed(4)}
                </Typography>
              </Box>
              <Chip
                label={item.impact > 0 ? '\u2191 Urgency' : '\u2193 Urgency'}
                color={item.impact > 0 ? 'error' : 'success'}
                size="small"
                variant="outlined"
                sx={{ minWidth: 90 }}
              />
            </Box>
          )) : (
            <Alert severity="info" variant="outlined">
              No SHAP explanation available for this assessment. This may occur if the model was unable to generate feature attributions.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons — Automation bias mitigation: require review checkbox */}
      {!resolved && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Clinical Decision
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Review the AI recommendation and either confirm or override with clinical justification.
            </Typography>
            <FormControlLabel
              control={<Checkbox checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} color="primary" />}
              label={
                <Typography variant="body2" fontWeight={600}>
                  I have reviewed the vitals and SHAP explanation factors above
                </Typography>
              }
              sx={{ mb: 2, ml: 0, p: 1.5, bgcolor: reviewed ? 'rgba(46,125,50,0.06)' : 'rgba(0,0,0,0.03)', borderRadius: 2, border: '1px solid', borderColor: reviewed ? 'success.light' : 'divider', width: '100%' }}
            />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Button
                  fullWidth variant="contained" color="success" size="large"
                  startIcon={<ConfirmIcon />}
                  onClick={handleConfirm}
                  disabled={actionLoading || !reviewed}
                >
                  Confirm AI Recommendation
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth variant="outlined" color="warning" size="large"
                  startIcon={<OverrideIcon />}
                  onClick={() => setOverrideOpen(true)}
                  disabled={actionLoading || !reviewed}
                >
                  Override
                </Button>
              </Grid>
            </Grid>
            {!reviewed && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                You must review the SHAP factors before making a clinical decision
              </Typography>
            )}
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

    </Container>
  );
};

export default TriageResult;

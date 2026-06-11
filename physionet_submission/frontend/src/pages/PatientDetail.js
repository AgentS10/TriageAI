import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Chip, Button,
  CircularProgress, Alert, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Divider
} from '@mui/material';
import {
  ArrowBack as BackIcon, Print as PrintIcon,
  Person as PersonIcon, MonitorHeart as VitalsIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import axios from 'axios';

const ESI_COLORS = {
  1: { bg: '#c62828', label: 'IMMEDIATE' },
  2: { bg: '#ef6c00', label: 'EMERGENT' },
  3: { bg: '#f9a825', label: 'URGENT' },
  4: { bg: '#2e7d32', label: 'LESS URGENT' },
  5: { bg: '#0277bd', label: 'NON-URGENT' },
};

const PatientDetail = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, [patientId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`/api/patient/${patientId}/history`);
      setData(r.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load patient');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => window.print();

  if (loading) return <Box display="flex" justifyContent="center" py={8}><CircularProgress /></Box>;
  if (error) return <Container sx={{ py: 4 }}><Alert severity="error">{error}</Alert></Container>;
  if (!data) return null;

  const { patient, vitals, assessments } = data;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }} className="fade-slide-up">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Button startIcon={<BackIcon />} onClick={() => navigate(-1)} sx={{ mb: 1 }}>Back</Button>
          <Typography variant="h4">Patient Record</Typography>
          <Typography variant="subtitle1">ID: {patient.patient_id?.slice(0, 8)}...</Typography>
        </Box>
        <Button startIcon={<PrintIcon />} variant="outlined" onClick={handlePrint}>Print</Button>
      </Box>

      <Grid container spacing={3}>
        {/* Patient Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <PersonIcon color="primary" />
                <Typography variant="h6">Patient Information</Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Age</Typography>
                  <Typography variant="h6">{patient.age} years</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Sex</Typography>
                  <Typography variant="h6">{patient.sex === 'M' ? 'Male' : patient.sex === 'F' ? 'Female' : 'Other'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Chief Complaint</Typography>
                  <Typography variant="body1" fontWeight={600}>{patient.chief_complaint?.replace(/_/g, ' ')}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Pain Score</Typography>
                  <Typography variant="h6">{patient.pain_score}/10</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Vitals */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <VitalsIcon color="error" />
                <Typography variant="h6">Vital Signs</Typography>
              </Box>
              {vitals ? (
                <Grid container spacing={2}>
                  {[
                    { label: 'Heart Rate', value: `${vitals.heart_rate} bpm`, key: 'hr' },
                    { label: 'Blood Pressure', value: `${vitals.sbp}/${vitals.dbp} mmHg`, key: 'bp' },
                    { label: 'Resp Rate', value: `${vitals.respiratory_rate} br/min`, key: 'rr' },
                    { label: 'SpO2', value: `${vitals.spo2}%`, key: 'spo2' },
                    { label: 'Temperature', value: `${vitals.temperature}°C`, key: 'temp' },
                    { label: 'GCS', value: vitals.gcs, key: 'gcs' },
                  ].map(v => (
                    <Grid item xs={4} key={v.key}>
                      <Typography variant="caption" color="text.secondary">{v.label}</Typography>
                      <Typography variant="body1" fontWeight={600}>{v.value}</Typography>
                    </Grid>
                  ))}
                </Grid>
              ) : <Typography color="text.secondary">No vitals recorded</Typography>}
            </CardContent>
          </Card>
        </Grid>

        {/* Assessment History */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <HistoryIcon color="info" />
                <Typography variant="h6">Triage History ({assessments.length} assessment{assessments.length !== 1 ? 's' : ''})</Typography>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>AI Priority</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Clinician Decision</TableCell>
                      <TableCell>Override</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Top SHAP Factors</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {assessments.map((a) => {
                      const esi = ESI_COLORS[a.ai_priority] || ESI_COLORS[3];
                      return (
                        <TableRow key={a.assessment_id} hover
                          onClick={() => navigate(`/result/${a.assessment_id}`)}
                          sx={{ cursor: 'pointer' }}>
                          <TableCell>
                            <Typography variant="caption">{new Date(a.assessed_at).toLocaleString()}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={`L${a.ai_priority} ${esi.label}`} size="small"
                              className={a.ai_priority <= 1 ? 'pulse-critical' : ''}
                              sx={{ bgcolor: esi.bg, color: 'white', fontWeight: 700 }} />
                          </TableCell>
                          <TableCell>{(a.ai_confidence * 100).toFixed(0)}%</TableCell>
                          <TableCell>
                            {a.clinician_priority ? (
                              <Chip label={`L${a.clinician_priority}`} size="small" variant="outlined" />
                            ) : '—'}
                          </TableCell>
                          <TableCell>
                            {a.is_override ? (
                              <Chip label={a.override_reason || 'Yes'} size="small" color="warning" variant="outlined" />
                            ) : a.clinician_priority ? 'No' : '—'}
                          </TableCell>
                          <TableCell>
                            <Chip label={a.status} size="small"
                              color={a.status === 'resolved' ? 'success' : 'warning'} variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {a.shap_explanation?.slice(0, 2).map(s => s.feature.replace(/_/g, ' ')).join(', ') || '—'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default PatientDetail;

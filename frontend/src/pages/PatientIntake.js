import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Grid, TextField, Button, FormControl, InputLabel,
  Select, MenuItem, Slider, Alert, CircularProgress, Card, CardContent, Chip,
  Stepper, Step, StepLabel, Snackbar
} from '@mui/material';
import {
  Person as PersonIcon,
  MonitorHeart as VitalsIcon,
  Medication as MedIcon,
  Send as SendIcon,
  ArrowBack as BackIcon,
  ArrowForward as NextIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const PatientIntake = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });
  const [activeStep, setActiveStep] = useState(0);

  const steps = ['Patient Information', 'Vital Signs', 'Medications & Submit'];

  const [patientData, setPatientData] = useState({
    age: '',
    sex: '',
    chief_complaint: '',
    pain_score: 5,
    medication_flags: {
      anticoagulant: false,
      diabetic: false,
      cardiac: false,
      respiratory: false,
    },
  });

  const [vitalsData, setVitalsData] = useState({
    heart_rate: '',
    sbp: '',
    dbp: '',
    respiratory_rate: '',
    spo2: '',
    temperature: '',
    gcs: '',
  });

  const chiefComplaintOptions = [
    { code: 'chest_pain', label: 'Chest Pain' },
    { code: 'shortness_of_breath', label: 'Shortness of Breath' },
    { code: 'abdominal_pain', label: 'Abdominal Pain' },
    { code: 'headache', label: 'Headache' },
    { code: 'fever', label: 'Fever' },
    { code: 'trauma_injury', label: 'Trauma / Injury' },
    { code: 'dizziness_syncope', label: 'Dizziness / Syncope' },
    { code: 'weakness_numbness', label: 'Weakness / Numbness' },
    { code: 'back_pain', label: 'Back Pain' },
    { code: 'altered_mental_status', label: 'Altered Mental Status' },
    { code: 'seizure', label: 'Seizure' },
    { code: 'allergic_reaction', label: 'Allergic Reaction' },
    { code: 'other', label: 'Other' },
  ];

  const handlePatientDataChange = (field, value) => {
    setPatientData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Auto-save draft to localStorage
  useEffect(() => {
    const draft = { patientData, vitalsData };
    localStorage.setItem('intake_draft', JSON.stringify(draft));
  }, [patientData, vitalsData]);

  // Restore draft on mount
  useEffect(() => {
    const saved = localStorage.getItem('intake_draft');
    if (saved) {
      try {
        const draft = JSON.parse(saved);
        if (draft.patientData) setPatientData(draft.patientData);
        if (draft.vitalsData) setVitalsData(draft.vitalsData);
        setToast({ open: true, message: 'Draft restored from auto-save', severity: 'info' });
      } catch (e) { /* ignore corrupt draft */ }
    }
  }, []);

  // Keyboard shortcut: Ctrl+Enter to submit
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 'Enter' && !loading) {
        e.preventDefault();
        const fakeEvent = { preventDefault: () => {} };
        handleSubmit(fakeEvent);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [loading, patientData, vitalsData]);

  const handleVitalsChange = (field, value) => {
    setVitalsData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleMedicationFlagChange = (medication) => {
    setPatientData(prev => ({
      ...prev,
      medication_flags: {
        ...prev.medication_flags,
        [medication]: !prev.medication_flags[medication],
      },
    }));
  };

  const validateForm = () => {
    const required = ['age', 'sex', 'chief_complaint'];
    const vitalsRequired = ['heart_rate', 'sbp', 'dbp', 'respiratory_rate', 'spo2', 'temperature', 'gcs'];
    
    for (const field of required) {
      if (!patientData[field]) {
        return `${field} is required`;
      }
    }
    
    for (const field of vitalsRequired) {
      if (!vitalsData[field]) {
        return `${field} is required`;
      }
    }
    
    const age = parseInt(patientData.age);
    if (age < 0 || age > 150) {
      return 'Please enter a valid age';
    }
    
    // Validate vitals ranges
    const vitalsValidation = {
      heart_rate: { min: 0, max: 300, name: 'Heart Rate' },
      sbp: { min: 0, max: 300, name: 'Systolic BP' },
      dbp: { min: 0, max: 200, name: 'Diastolic BP' },
      respiratory_rate: { min: 0, max: 60, name: 'Respiratory Rate' },
      spo2: { min: 0, max: 100, name: 'SpO2' },
      temperature: { min: 20, max: 45, name: 'Temperature' },
      gcs: { min: 3, max: 15, name: 'GCS' },
    };
    
    for (const [field, validation] of Object.entries(vitalsValidation)) {
      const value = parseFloat(vitalsData[field]);
      if (value < validation.min || value > validation.max) {
        return `${validation.name} must be between ${validation.min} and ${validation.max}`;
      }
    }
    
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post('/api/predict', {
        patient_data: {
          age: parseInt(patientData.age),
          sex: patientData.sex,
          chief_complaint: patientData.chief_complaint,
          pain_score: patientData.pain_score,
          medication_flags: patientData.medication_flags,
        },
        vitals: {
          heart_rate: parseInt(vitalsData.heart_rate),
          sbp: parseInt(vitalsData.sbp),
          dbp: parseInt(vitalsData.dbp),
          respiratory_rate: parseInt(vitalsData.respiratory_rate),
          spo2: parseFloat(vitalsData.spo2),
          temperature: parseFloat(vitalsData.temperature),
          gcs: parseInt(vitalsData.gcs),
        },
      });
      
      setSuccess('Triage assessment completed successfully!');
      setToast({ open: true, message: 'Assessment submitted successfully', severity: 'success' });
      localStorage.removeItem('intake_draft');
      sessionStorage.setItem(`result_${response.data.assessment_id}`, JSON.stringify(response.data));
      setTimeout(() => {
        navigate(`/result/${response.data.assessment_id}`);
      }, 1500);

    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Assessment failed';
      setError(errorMessage);
      setToast({ open: true, message: errorMessage, severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const painColor = patientData.pain_score <= 3 ? '#2e7d32' : patientData.pain_score <= 6 ? '#ef6c00' : '#c62828';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4">New Triage Assessment</Typography>
        <Typography variant="subtitle1">
          Complete all fields to generate an AI-powered ESI priority recommendation
        </Typography>
      </Box>

      {/* Progress Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label, index) => (
          <Step key={label}>
            <StepLabel onClick={() => setActiveStep(index)} sx={{ cursor: 'pointer' }}>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <form onSubmit={handleSubmit} onFocus={() => setActiveStep(0)}>
        <Grid container spacing={3}>
          {/* Patient Information */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <PersonIcon color="primary" />
                  <Typography variant="h6">Patient Information</Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Age"
                      type="number"
                      value={patientData.age}
                      onChange={(e) => handlePatientDataChange('age', e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth required>
                      <InputLabel>Sex</InputLabel>
                      <Select
                        value={patientData.sex}
                        onChange={(e) => handlePatientDataChange('sex', e.target.value)}
                      >
                        <MenuItem value="M">Male</MenuItem>
                        <MenuItem value="F">Female</MenuItem>
                        <MenuItem value="O">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControl fullWidth required>
                      <InputLabel>Chief Complaint</InputLabel>
                      <Select
                        value={patientData.chief_complaint}
                        onChange={(e) => handlePatientDataChange('chief_complaint', e.target.value)}
                      >
                        {chiefComplaintOptions.map(option => (
                          <MenuItem key={option.code} value={option.code}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="subtitle2">Pain Score</Typography>
                      <Chip label={`${patientData.pain_score}/10`} size="small"
                        sx={{ bgcolor: painColor, color: 'white', fontWeight: 700, minWidth: 50 }} />
                    </Box>
                    <Slider
                      value={patientData.pain_score}
                      onChange={(e, value) => handlePatientDataChange('pain_score', value)}
                      min={0}
                      max={10}
                      marks={[
                        { value: 0, label: '0' },
                        { value: 3, label: '3' },
                        { value: 5, label: '5' },
                        { value: 7, label: '7' },
                        { value: 10, label: '10' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Vitals */}
          <Grid item xs={12} md={6} onFocus={() => setActiveStep(1)}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <VitalsIcon color="error" />
                  <Typography variant="h6">Vital Signs</Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Heart Rate (bpm)"
                      type="number"
                      value={vitalsData.heart_rate}
                      onChange={(e) => handleVitalsChange('heart_rate', e.target.value)}
                      required
                      helperText="Normal: 60–100 bpm"
                      error={vitalsData.heart_rate && (vitalsData.heart_rate < 40 || vitalsData.heart_rate > 180)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Systolic BP (mmHg)"
                      type="number"
                      value={vitalsData.sbp}
                      onChange={(e) => handleVitalsChange('sbp', e.target.value)}
                      required
                      helperText="Normal: 90–140 mmHg"
                      error={vitalsData.sbp && (vitalsData.sbp < 60 || vitalsData.sbp > 220)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Diastolic BP (mmHg)"
                      type="number"
                      value={vitalsData.dbp}
                      onChange={(e) => handleVitalsChange('dbp', e.target.value)}
                      required
                      helperText="Normal: 60–90 mmHg"
                      error={vitalsData.dbp && (vitalsData.dbp < 30 || vitalsData.dbp > 130)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Respiratory Rate (br/min)"
                      type="number"
                      value={vitalsData.respiratory_rate}
                      onChange={(e) => handleVitalsChange('respiratory_rate', e.target.value)}
                      required
                      helperText="Normal: 12–20 br/min"
                      error={vitalsData.respiratory_rate && (vitalsData.respiratory_rate < 8 || vitalsData.respiratory_rate > 40)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="SpO2 (%)"
                      type="number"
                      value={vitalsData.spo2}
                      onChange={(e) => handleVitalsChange('spo2', e.target.value)}
                      required
                      helperText="Normal: 95–100%"
                      error={vitalsData.spo2 && (vitalsData.spo2 < 70 || vitalsData.spo2 > 100)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Temperature (°C)"
                      type="number"
                      step="0.1"
                      value={vitalsData.temperature}
                      onChange={(e) => handleVitalsChange('temperature', e.target.value)}
                      required
                      helperText="Normal: 36.1–37.2°C"
                      error={vitalsData.temperature && (vitalsData.temperature < 34 || vitalsData.temperature > 41)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Glasgow Coma Scale (3-15)"
                      type="number"
                      value={vitalsData.gcs}
                      onChange={(e) => handleVitalsChange('gcs', e.target.value)}
                      required
                      helperText="Normal: 15 (fully alert)"
                      error={vitalsData.gcs && (vitalsData.gcs < 3 || vitalsData.gcs > 15)}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Medication Flags */}
          <Grid item xs={12} onFocus={() => setActiveStep(2)}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <MedIcon color="secondary" />
                  <Typography variant="h6">Current Medications</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(patientData.medication_flags).map(([medication, isTaking]) => (
                    <Chip
                      key={medication}
                      label={medication.charAt(0).toUpperCase() + medication.slice(1)}
                      color={isTaking ? 'primary' : 'default'}
                      onClick={() => handleMedicationFlagChange(medication)}
                      clickable
                    />
                  ))}
                </Box>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Click to select current medications
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Submit Button */}
          <Grid item xs={12}>
            <Card sx={{ background: 'linear-gradient(135deg, #0d47a1, #1565c0)', color: 'white' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Typography variant="body2" sx={{ opacity: 0.8, mb: 2 }}>
                  Submitting will run ML inference and generate an ESI priority with SHAP explanation
                </Typography>
                <Button
                  type="submit" variant="contained" size="large" startIcon={loading ? null : <SendIcon />}
                  disabled={loading}
                  sx={{
                    px: 6, py: 1.5, bgcolor: 'white', color: '#0d47a1', fontWeight: 700,
                    '&:hover': { bgcolor: '#e3f2fd' },
                    '&.Mui-disabled': { bgcolor: 'rgba(255,255,255,0.3)' }
                  }}
                >
                  {loading ? <CircularProgress size={22} /> : 'Generate Triage Assessment'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </form>

      {/* Toast */}
      <Snackbar open={toast.open} autoHideDuration={3000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={toast.severity} onClose={() => setToast({ ...toast, open: false })} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default PatientIntake;

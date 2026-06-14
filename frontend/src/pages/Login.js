import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, TextField, Button, Typography, Box, Alert, CircularProgress,
  Card, CardContent, InputAdornment, IconButton
} from '@mui/material';
import {
  MedicalServices as MedicalIcon,
  Person as PersonIcon,
  Lock as LockIcon,
  Visibility, VisibilityOff,
  Shield as ShieldIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  VerifiedUser as VerifiedIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, error } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await login(formData.username, formData.password);
    if (result.success) navigate('/');
    setLoading(false);
  };

  const features = [
    { icon: <PsychologyIcon />, title: 'AI-Powered Triage', desc: 'XGBoost ML model with SHAP explainability for transparent clinical decisions' },
    { icon: <SpeedIcon />, title: 'Real-Time Analysis', desc: 'Sub-500ms inference with five-level ESI priority classification' },
    { icon: <ShieldIcon />, title: 'Clinical Safety', desc: 'All AI outputs require clinician confirmation — advisory only, never autonomous' },
    { icon: <VerifiedIcon />, title: 'Audit Compliance', desc: 'Immutable audit trail with ICD-10 coded terms and OWASP security headers' },
  ];

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 40%, #0277bd 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4
    }}>
      <Container maxWidth="lg">
        <Card sx={{ overflow: 'hidden', borderRadius: 4, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
          <Box sx={{ display: 'flex', minHeight: 560 }}>

            {/* Left — Login Form */}
            <Box sx={{ flex: 1, p: 5, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ bgcolor: '#0d47a1', borderRadius: 2, p: 1, mr: 1.5, display: 'flex' }}>
                  <MedicalIcon sx={{ color: 'white', fontSize: 28 }} />
                </Box>
                <Box>
                  <Typography variant="h4" sx={{ color: '#0d47a1', lineHeight: 1.1 }}>TriageAI</Typography>
                  <Typography variant="caption" sx={{ color: '#555', letterSpacing: 1, textTransform: 'uppercase', fontSize: '0.6rem' }}>
                    Clinical Decision Support System
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 4, mt: 1 }}>
                Emergency Department Patient Triage
              </Typography>

              <Box component="form" onSubmit={handleSubmit} className={error ? 'shake' : ''}>
                <TextField
                  fullWidth required name="username" label="Username" autoComplete="username" autoFocus
                  value={formData.username} onChange={handleChange} sx={{ mb: 2 }}
                  InputProps={{ startAdornment: <InputAdornment position="start"><PersonIcon color="action" /></InputAdornment> }}
                />
                <TextField
                  fullWidth required name="password" label="Password"
                  type={showPassword ? 'text' : 'password'} autoComplete="current-password"
                  value={formData.password} onChange={handleChange} sx={{ mb: 1 }}
                  InputProps={{
                    startAdornment: <InputAdornment position="start"><LockIcon color="action" /></InputAdornment>,
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton size="small" onClick={() => setShowPassword(!showPassword)} edge="end">
                          {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />

                {error && <Alert severity="error" sx={{ mt: 2, mb: 1 }}>{error}</Alert>}

                <Button type="submit" fullWidth variant="contained" size="large"
                  disabled={loading || !formData.username || !formData.password}
                  sx={{ mt: 3, py: 1.4, fontSize: '0.95rem',
                    background: 'linear-gradient(135deg, #0d47a1, #1565c0)',
                    '&:hover': { background: 'linear-gradient(135deg, #002171, #0d47a1)' }
                  }}
                >
                  {loading ? <CircularProgress size={22} color="inherit" /> : 'Sign In'}
                </Button>
              </Box>

              <Box sx={{ mt: 3, p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1.6 }}>
                  <strong>Research Prototype</strong> — Not for real clinical use.
                  All AI recommendations require clinician confirmation.
                </Typography>
              </Box>
            </Box>

            {/* Right — Features */}
            <Box sx={{
              flex: 1, p: 5,
              background: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #0277bd 100%)',
              color: 'white', display: 'flex', flexDirection: 'column', justifyContent: 'center'
            }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                Intelligent Emergency Triage
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8, mb: 4 }}>
                ML-powered clinical decision support with explainable AI and full audit compliance
              </Typography>

              {features.map((f, i) => (
                <Box key={i} sx={{ display: 'flex', mb: 2.5, alignItems: 'flex-start' }}>
                  <Box sx={{ bgcolor: 'rgba(255,255,255,0.15)', borderRadius: 2, p: 1, mr: 2, mt: 0.3 }}>
                    {React.cloneElement(f.icon, { sx: { fontSize: 20 } })}
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.3 }}>{f.title}</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.75, lineHeight: 1.4, display: 'block' }}>{f.desc}</Typography>
                  </Box>
                </Box>
              ))}

              <Box sx={{ mt: 'auto', pt: 3, borderTop: '1px solid rgba(255,255,255,0.15)' }}>
                <Typography variant="caption" sx={{ opacity: 0.5 }}>
                  Cardiff Metropolitan University | BSc Software Development | 2025-2026
                </Typography>
              </Box>
            </Box>

          </Box>
        </Card>
      </Container>
    </Box>
  );
};

export default Login;

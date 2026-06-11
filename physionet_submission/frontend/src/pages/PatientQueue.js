import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid,
  Chip, Button, CircularProgress, Alert, TextField, FormControl,
  InputLabel, Select, MenuItem, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, IconButton
} from '@mui/material';
import { Refresh as RefreshIcon, Visibility as ViewIcon } from '@mui/icons-material';
import axios from 'axios';

const ESI_COLORS = {
  1: { bg: '#d32f2f', label: 'IMMEDIATE' },
  2: { bg: '#f57c00', label: 'EMERGENT' },
  3: { bg: '#fbc02d', label: 'URGENT' },
  4: { bg: '#388e3c', label: 'LESS URGENT' },
  5: { bg: '#1976d2', label: 'NON-URGENT' },
};

const SORT_OPTIONS = [
  { value: 'priority', label: 'Priority' },
  { value: 'arrival', label: 'Arrival Time' },
  { value: 'wait', label: 'Wait Time' },
];

const PatientQueue = () => {
  const navigate = useNavigate();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterLevel, setFilterLevel] = useState('');
  const [sortBy, setSortBy] = useState('priority');

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/queue');
      setQueue(response.data.queue || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  };

  const getWaitTime = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '< 1 min';
    if (mins < 60) return `${mins} min`;
    const hours = Math.floor(mins / 60);
    return `${hours}h ${mins % 60}m`;
  };

  let filteredQueue = filterLevel
    ? queue.filter(p => p.ai_priority === parseInt(filterLevel))
    : queue;

  // Sort queue
  filteredQueue = [...filteredQueue].sort((a, b) => {
    if (sortBy === 'priority') return a.ai_priority - b.ai_priority;
    if (sortBy === 'arrival') return new Date(b.timestamp) - new Date(a.timestamp);
    if (sortBy === 'wait') return new Date(b.timestamp) - new Date(a.timestamp);
    return 0;
  });

  const getPriorityChip = (level) => {
    const esi = ESI_COLORS[level] || ESI_COLORS[3];
    return (
      <Chip
        label={`L${level} ${esi.label}`}
        size="small"
        sx={{ bgcolor: esi.bg, color: 'white', fontWeight: 'bold' }}
      />
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Active Patient Queue
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {filteredQueue.length} patient(s) awaiting triage decision
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Sort by</InputLabel>
            <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} label="Sort by">
              {SORT_OPTIONS.map(o => (
                <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Filter by Level</InputLabel>
            <Select value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)} label="Filter by Level">
              <MenuItem value="">All Levels</MenuItem>
              {[1, 2, 3, 4, 5].map(l => (
                <MenuItem key={l} value={l}>Level {l}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button startIcon={<RefreshIcon />} variant="outlined" onClick={fetchQueue}>
            Refresh
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {filteredQueue.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No patients in queue
          </Typography>
          <Button variant="contained" sx={{ mt: 2 }} onClick={() => navigate('/intake')}>
            Start New Assessment
          </Button>
        </Card>
      ) : (
        <TableContainer component={Paper} elevation={2}>
          <Table>
            <TableHead sx={{ bgcolor: 'grey.100' }}>
              <TableRow>
                <TableCell><strong>Priority</strong></TableCell>
                <TableCell><strong>Patient</strong></TableCell>
                <TableCell><strong>Chief Complaint</strong></TableCell>
                <TableCell><strong>Key Vitals</strong></TableCell>
                <TableCell><strong>Confidence</strong></TableCell>
                <TableCell><strong>Wait Time</strong></TableCell>
                <TableCell><strong>Action</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredQueue.map((patient) => (
                <TableRow
                  key={patient.assessment_id}
                  hover
                  sx={{
                    borderLeft: `4px solid ${ESI_COLORS[patient.ai_priority]?.bg || '#999'}`,
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <TableCell>{getPriorityChip(patient.ai_priority)}</TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {patient.sex === 'M' ? 'Male' : patient.sex === 'F' ? 'Female' : 'Other'}, {patient.age}y
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Pain: {patient.pain_score}/10
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {patient.chief_complaint?.replace(/_/g, ' ')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" component="div">
                      HR: {patient.vitals?.heart_rate} | BP: {patient.vitals?.sbp}/{patient.vitals?.dbp}
                    </Typography>
                    <Typography variant="caption" component="div">
                      SpO2: {patient.vitals?.spo2}% | T: {patient.vitals?.temperature}°C
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {(patient.confidence * 100).toFixed(0)}%
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600} color={patient.ai_priority <= 2 ? 'error' : 'text.primary'}>
                      {getWaitTime(patient.timestamp)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      color="primary"
                      onClick={() => navigate(`/result/${patient.assessment_id}`)}
                      title="View & Decide"
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
};

export default PatientQueue;

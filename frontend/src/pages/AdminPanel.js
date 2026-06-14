import React, { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container, Typography, Box, Card, CardContent, Grid, Tabs, Tab,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, Chip, Alert, TextField, IconButton,
  Pagination, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Tooltip, Skeleton
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  Download as DownloadIcon, PersonOff as DeactivateIcon, Person as ActivateIcon,
  Refresh as RefreshIcon, Add as AddIcon, Edit as EditIcon, Key as KeyIcon,
  Delete as DeleteIcon, Search as SearchIcon, History as HistoryIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';

const ESI_COLORS = { 1: '#c62828', 2: '#ef6c00', 3: '#f9a825', 4: '#2e7d32', 5: '#0277bd' };

const TAB_PATHS = ['audit', 'users', 'analytics', 'search'];

const AdminPanel = () => {
  const { isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();

  const tab = useMemo(() => {
    const segment = location.pathname.split('/admin/')[1]?.split('/')[0];
    const idx = TAB_PATHS.indexOf(segment);
    return idx >= 0 ? idx : 0;
  }, [location.pathname]);

  const setTab = (index) => {
    navigate(`/admin/${TAB_PATHS[index]}`, { replace: true });
  };
  const [auditLogs, setAuditLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { showToast } = useToast();

  // Dialogs
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [resetPwOpen, setResetPwOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Form data
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'clinician' });
  const [editData, setEditData] = useState({ username: '', role: '' });
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    if (tab === 0) fetchAuditLogs();
    else if (tab === 1) fetchUsers();
    else if (tab === 2) fetchAnalytics();
    else if (tab === 3) fetchSearch();
  }, [tab, page]);

  const show = (msg, severity = 'success') => showToast(msg, severity);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`/api/admin/audit-log?page=${page}&per_page=20`);
      setAuditLogs(r.data.audit_log || []);
      setTotalPages(r.data.pagination?.pages || 1);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try { const r = await axios.get('/api/admin/users'); setUsers(r.data.users || []); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    try { const r = await axios.get('/api/admin/analytics?days=30'); setAnalytics(r.data); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults([]); setLoading(false); return; }
    setLoading(true);
    try {
      const r = await axios.get(`/api/admin/patients/search?q=${encodeURIComponent(searchQuery)}&page=${page}`);
      setSearchResults(r.data.results || []);
      setTotalPages(r.data.pagination?.pages || 1);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  // User actions
  const handleCreateUser = async () => {
    try {
      await axios.post('/api/auth/register', newUser);
      show(`User ${newUser.username} created`);
      setCreateOpen(false); setNewUser({ username: '', password: '', role: 'clinician' }); fetchUsers();
    } catch (e) { show(e.response?.data?.error || 'Failed', 'error'); }
  };

  const handleEditUser = async () => {
    try {
      await axios.put(`/api/admin/users/${selectedUser.user_id}/update`, editData);
      show('User updated'); setEditOpen(false); fetchUsers();
    } catch (e) { show(e.response?.data?.error || 'Failed', 'error'); }
  };

  const handleResetPassword = async () => {
    try {
      await axios.post(`/api/admin/users/${selectedUser.user_id}/reset-password`, { new_password: newPassword });
      show(`Password reset for ${selectedUser.username}`); setResetPwOpen(false); setNewPassword('');
    } catch (e) { show(e.response?.data?.error || 'Failed', 'error'); }
  };

  const handleToggle = async (userId) => {
    try { await axios.post(`/api/admin/users/${userId}/toggle`); fetchUsers(); }
    catch (e) { show('Toggle failed', 'error'); }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`/api/admin/users/${selectedUser.user_id}`);
      show(`User ${selectedUser.username} deleted`); setDeleteOpen(false); fetchUsers();
    } catch (e) { show(e.response?.data?.error || 'Cannot delete', 'error'); setDeleteOpen(false); }
  };

  const exportAuditLog = async () => {
    try {
      const r = await axios.get('/api/admin/export/audit-log', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url;
      a.setAttribute('download', `audit_log_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(a); a.click(); a.remove();
      show('Audit log exported');
    } catch (e) { show('Export failed', 'error'); }
  };

  if (!isAdmin) return <Container sx={{ py: 4 }}><Alert severity="error">Access denied. Admin role required.</Alert></Container>;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }} className="fade-slide-up">
      <Typography variant="h4" sx={{ mb: 3 }}>Administration</Typography>

      <Tabs value={tab} onChange={(_, v) => { setTab(v); setPage(1); }} sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
        aria-label="Admin panel tabs">
        <Tab label="Audit Log" />
        <Tab label="User Management" />
        <Tab label="Analytics" />
        <Tab label="Patient History" />
      </Tabs>

      {loading ? (
        <Box py={2}>
          {(tab === 0 || tab === 1 || tab === 3) && (
            <>{[0,1,2,3,4,5].map(i => <Skeleton key={i} variant="rounded" height={40} sx={{ mb: 1 }} />)}</>
          )}
          {tab === 2 && (
            <Grid container spacing={3}>
              {[0,1,2,3].map(i => <Grid item xs={6} sm={3} key={i}><Skeleton variant="rounded" height={90} /></Grid>)}
              <Grid item xs={12} md={6}><Skeleton variant="rounded" height={300} /></Grid>
              <Grid item xs={12} md={6}><Skeleton variant="rounded" height={300} /></Grid>
            </Grid>
          )}
        </Box>
      ) : (
        <>
          {/* ─── AUDIT LOG ─── */}
          {tab === 0 && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2, gap: 1 }}>
                <Button startIcon={<RefreshIcon />} variant="text" onClick={fetchAuditLogs}>Refresh</Button>
                <Button startIcon={<DownloadIcon />} variant="outlined" onClick={exportAuditLog}>Export CSV</Button>
              </Box>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead><TableRow>
                    <TableCell>Timestamp</TableCell><TableCell>Clinician</TableCell>
                    <TableCell>Event</TableCell><TableCell>Detail</TableCell><TableCell>IP</TableCell>
                  </TableRow></TableHead>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.log_id} hover sx={{ cursor: log.assessment_id ? 'pointer' : 'default' }}
                        onClick={() => log.assessment_id && navigate(`/result/${log.assessment_id}`)}>
                        <TableCell><Typography variant="caption">{new Date(log.timestamp).toLocaleString()}</Typography></TableCell>
                        <TableCell><Typography variant="body2">{log.clinician_name}</Typography></TableCell>
                        <TableCell>
                          <Chip label={log.event_type.replace(/_/g, ' ')} size="small" variant="outlined"
                            color={log.event_type === 'clinician_override' ? 'warning' : log.event_type === 'clinician_confirm' ? 'success' : 'primary'} />
                        </TableCell>
                        <TableCell><Typography variant="caption" sx={{ maxWidth: 300, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.event_detail}</Typography></TableCell>
                        <TableCell><Typography variant="caption" color="text.secondary">{log.ip_address}</Typography></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Pagination count={totalPages} page={page} onChange={(_, v) => setPage(v)} />
              </Box>
            </Box>
          )}

          {/* ─── USER MANAGEMENT ─── */}
          {tab === 1 && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2, gap: 1 }}>
                <Button startIcon={<RefreshIcon />} variant="text" onClick={fetchUsers}>Refresh</Button>
                <Button startIcon={<AddIcon />} variant="contained" onClick={() => setCreateOpen(true)}>Add User</Button>
              </Box>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead><TableRow>
                    <TableCell>Username</TableCell><TableCell>Role</TableCell>
                    <TableCell>Status</TableCell><TableCell>Created</TableCell><TableCell align="right">Actions</TableCell>
                  </TableRow></TableHead>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.user_id} hover>
                        <TableCell><Typography variant="body2" fontWeight={600}>{u.username}</Typography></TableCell>
                        <TableCell><Chip label={u.role} size="small" color={u.role === 'admin' ? 'secondary' : 'primary'} /></TableCell>
                        <TableCell><Chip label={u.is_active ? 'Active' : 'Inactive'} size="small" color={u.is_active ? 'success' : 'default'} variant={u.is_active ? 'filled' : 'outlined'} /></TableCell>
                        <TableCell><Typography variant="caption">{new Date(u.created_at).toLocaleDateString()}</Typography></TableCell>
                        <TableCell align="right">
                          <Tooltip title="Edit"><IconButton size="small" onClick={() => { setSelectedUser(u); setEditData({ username: u.username, role: u.role }); setEditOpen(true); }}><EditIcon fontSize="small" /></IconButton></Tooltip>
                          <Tooltip title="Reset Password"><IconButton size="small" onClick={() => { setSelectedUser(u); setResetPwOpen(true); }}><KeyIcon fontSize="small" /></IconButton></Tooltip>
                          <Tooltip title={u.is_active ? 'Deactivate' : 'Activate'}><IconButton size="small" color={u.is_active ? 'warning' : 'success'} onClick={() => handleToggle(u.user_id)}>{u.is_active ? <DeactivateIcon fontSize="small" /> : <ActivateIcon fontSize="small" />}</IconButton></Tooltip>
                          <Tooltip title="Delete"><IconButton size="small" color="error" onClick={() => { setSelectedUser(u); setDeleteOpen(true); }}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* ─── ANALYTICS ─── */}
          {tab === 2 && analytics && (
            <Grid container spacing={3}>
              <Grid item xs={12}><Typography variant="subtitle1" color="text.secondary">Last {analytics.period?.days} days</Typography></Grid>
              {[
                { v: analytics.overview?.total_assessments, l: 'Total Assessments', c: '#0d47a1' },
                { v: analytics.overview?.confirmed_assessments, l: 'Confirmed', c: '#2e7d32' },
                { v: analytics.overview?.overridden_assessments, l: 'Overrides', c: '#ef6c00' },
                { v: `${analytics.overview?.ai_clinician_agreement_rate || 0}%`, l: 'AI Agreement', c: '#0277bd' },
              ].map((s, i) => (
                <Grid item xs={6} sm={3} key={i}>
                  <Card><CardContent sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="h4" sx={{ color: s.c, fontWeight: 800 }}>{s.v}</Typography>
                    <Typography variant="caption" color="text.secondary">{s.l}</Typography>
                  </CardContent></Card>
                </Grid>
              ))}

              {/* ESI Bar Chart */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: 350 }}>
                  <CardContent sx={{ height: '100%' }}>
                    <Typography variant="h6" gutterBottom>ESI Level Distribution</Typography>
                    <ResponsiveContainer width="100%" height="85%">
                      <BarChart data={analytics.esi_distribution?.map(d => ({ name: `L${d.level}`, count: d.count })) || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                        <XAxis dataKey="name" tick={{ fill: theme.palette.text.secondary }} />
                        <YAxis tick={{ fill: theme.palette.text.secondary }} />
                        <RechartsTooltip />
                        <Bar dataKey="count" fill="#0d47a1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Daily Volume Line Chart */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: 350 }}>
                  <CardContent sx={{ height: '100%' }}>
                    <Typography variant="h6" gutterBottom>Daily Assessment Volume</Typography>
                    <ResponsiveContainer width="100%" height="85%">
                      <LineChart data={analytics.daily_volume?.map(d => ({ date: d.date.slice(5), count: d.count })) || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                        <XAxis dataKey="date" tick={{ fontSize: 12, fill: theme.palette.text.secondary }} />
                        <YAxis tick={{ fill: theme.palette.text.secondary }} />
                        <RechartsTooltip />
                        <Line type="monotone" dataKey="count" stroke="#1565c0" strokeWidth={2} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Override Reasons Pie Chart */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: 350 }}>
                  <CardContent sx={{ height: '100%' }}>
                    <Typography variant="h6" gutterBottom>Override Reasons</Typography>
                    <ResponsiveContainer width="100%" height="85%">
                      <PieChart>
                        <Pie data={analytics.override_reasons?.map((d, i) => ({
                          name: d.reason || 'Unknown',
                          value: d.count
                        })) || []} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value">
                          {(analytics.override_reasons || []).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={['#c62828', '#ef6c00', '#f9a825', '#2e7d32', '#0277bd', '#1565c0'][index % 6]} />
                          ))}
                        </Pie>
                        <RechartsTooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Clinician Performance Table */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: 350, overflow: 'auto' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Clinician Performance</Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead><TableRow>
                          <TableCell>Clinician</TableCell><TableCell>Total</TableCell>
                          <TableCell>Overrides</TableCell><TableCell>Agreement</TableCell>
                        </TableRow></TableHead>
                        <TableBody>
                          {analytics.clinician_performance?.map((c, i) => (
                            <TableRow key={i} hover>
                              <TableCell><Typography variant="body2" fontWeight={600}>{c.username}</Typography></TableCell>
                              <TableCell>{c.total_assessments}</TableCell>
                              <TableCell>{c.overrides}</TableCell>
                              <TableCell><Typography variant="body2" color={c.agreement_rate >= 80 ? 'success.main' : 'warning.main'}>{c.agreement_rate}%</Typography></TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* ─── PATIENT HISTORY ─── */}
          {tab === 3 && (
            <Box>
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <TextField fullWidth placeholder="Search by chief complaint or patient ID..." value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchSearch()}
                  InputProps={{ startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} /> }} />
                <Button variant="contained" onClick={fetchSearch} sx={{ minWidth: 100 }}>Search</Button>
              </Box>
              {searchResults.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead><TableRow>
                      <TableCell>Date</TableCell><TableCell>Patient</TableCell><TableCell>Complaint</TableCell>
                      <TableCell>AI Priority</TableCell><TableCell>Clinician</TableCell><TableCell>Status</TableCell>
                    </TableRow></TableHead>
                    <TableBody>
                      {searchResults.map((r) => (
                        <TableRow key={r.assessment_id} hover sx={{ cursor: 'pointer' }}
                          onClick={() => navigate(`/result/${r.assessment_id}`)}>
                          <TableCell><Typography variant="caption">{new Date(r.assessed_at).toLocaleString()}</Typography></TableCell>
                          <TableCell>{r.sex === 'M' ? 'Male' : 'Female'}, {r.age}y</TableCell>
                          <TableCell>{r.chief_complaint?.replace(/_/g, ' ')}</TableCell>
                          <TableCell><Chip label={`L${r.ai_priority}`} size="small" sx={{ bgcolor: ESI_COLORS[r.ai_priority], color: 'white', fontWeight: 700 }} /></TableCell>
                          <TableCell>{r.clinician_priority ? <Chip label={`L${r.clinician_priority}`} size="small" variant="outlined" /> : '—'}</TableCell>
                          <TableCell><Chip label={r.status} size="small" color={r.status === 'resolved' ? 'success' : 'warning'} variant="outlined" /></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : <Card sx={{ p: 4, textAlign: 'center' }}><HistoryIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} /><Typography color="text.secondary">Enter a search query to find patient assessments</Typography></Card>}
            </Box>
          )}
        </>
      )}

      {/* ─── CREATE USER DIALOG ─── */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Username" value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} sx={{ mt: 1, mb: 2 }} />
          <TextField fullWidth label="Password" type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} sx={{ mb: 2 }}
            helperText="Min 8 chars, uppercase, lowercase, digit" />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}>
              <MenuItem value="clinician">Clinician</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateUser} disabled={!newUser.username || !newUser.password}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* ─── EDIT USER DIALOG ─── */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User: {selectedUser?.username}</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Username" value={editData.username} onChange={(e) => setEditData({ ...editData, username: e.target.value })} sx={{ mt: 1, mb: 2 }} />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select value={editData.role} onChange={(e) => setEditData({ ...editData, role: e.target.value })}>
              <MenuItem value="clinician">Clinician</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleEditUser}>Save Changes</Button>
        </DialogActions>
      </Dialog>

      {/* ─── RESET PASSWORD DIALOG ─── */}
      <Dialog open={resetPwOpen} onClose={() => setResetPwOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reset Password: {selectedUser?.username}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>Enter a new password for this user. They will need to use this password on their next login.</Typography>
          <TextField fullWidth label="New Password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
            helperText="Min 8 chars, uppercase, lowercase, digit" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setResetPwOpen(false); setNewPassword(''); }}>Cancel</Button>
          <Button variant="contained" color="warning" onClick={handleResetPassword} disabled={!newPassword}>Reset Password</Button>
        </DialogActions>
      </Dialog>

      {/* ─── DELETE CONFIRMATION ─── */}
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete User?</DialogTitle>
        <DialogContent>
          <Typography>Are you sure you want to delete <strong>{selectedUser?.username}</strong>? This action cannot be undone.</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>Note: Users with existing assessments cannot be deleted — deactivate them instead.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>Delete</Button>
        </DialogActions>
      </Dialog>

    </Container>
  );
};

export default AdminPanel;

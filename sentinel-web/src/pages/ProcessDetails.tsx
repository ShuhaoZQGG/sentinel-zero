import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  Container,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  TextField,
  IconButton,
  CircularProgress,
  Alert,
  FormControlLabel,
  Checkbox,
  ToggleButton,
  ToggleButtonGroup,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Edit,
  Save,
  Cancel,
  Memory,
  Speed,
  Schedule,
  Folder,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { RootState, AppDispatch } from '../store/store';
import { startProcess, stopProcess, restartProcess } from '../store/slices/processesSlice';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`process-tabpanel-${index}`}
      aria-labelledby={`process-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProcessDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  
  // Redux state
  const process = useSelector((state: RootState) => 
    state.processes.processes.find(p => p.id === id)
  );
  const loading = useSelector((state: RootState) => state.processes.loading);
  const logs = useSelector((state: RootState) => state.logs?.logs || []);
  const metrics = useSelector((state: RootState) => state.metrics?.data || { cpu: [], memory: [] });
  
  // Local state
  const [tabValue, setTabValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [editedConfig, setEditedConfig] = useState({
    command: '',
    working_directory: '',
    environment: {},
    restart_policy: '',
  });
  const [logFilter, setLogFilter] = useState<string[]>(['info', 'warning', 'error']);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (process) {
      setEditedConfig({
        command: process.command,
        working_directory: process.working_directory || '',
        environment: process.environment || {},
        restart_policy: process.restart_policy || '',
      });
    }
  }, [process]);

  useEffect(() => {
    if (autoScroll && tabValue === 2) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, tabValue]);

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!process) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">Process not found</Alert>
        <Button sx={{ mt: 2 }} onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleStart = () => {
    dispatch(startProcess(process.id));
  };

  const handleStop = () => {
    dispatch(stopProcess(process.id));
  };

  const handleRestart = () => {
    dispatch(restartProcess(process.id));
  };

  const handleSaveConfig = () => {
    // TODO: Implement config save
    setEditMode(false);
  };

  const handleCancelEdit = () => {
    setEditedConfig({
      command: process.command,
      working_directory: process.working_directory || '',
      environment: process.environment || {},
      restart_policy: process.restart_policy || '',
    });
    setEditMode(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'default';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const filteredLogs = logs.filter(log => logFilter.includes(log.level));

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {process.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Chip 
                label={process.status.charAt(0).toUpperCase() + process.status.slice(1)}
                color={getStatusColor(process.status) as any}
              />
              {process.pid && (
                <Typography variant="body2" color="text.secondary">
                  PID: {process.pid}
                </Typography>
              )}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {process.status === 'stopped' ? (
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
                onClick={handleStart}
              >
                Start
              </Button>
            ) : (
              <Button
                variant="contained"
                color="error"
                startIcon={<Stop />}
                onClick={handleStop}
                disabled={process.status === 'stopped'}
              >
                Stop
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={handleRestart}
            >
              Restart
            </Button>
          </Box>
        </Box>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Information" />
            <Tab label="Metrics" />
            <Tab label="Logs" />
            <Tab label="Configuration" />
          </Tabs>
        </Box>

        {/* Information Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Command
                      </Typography>
                      <Typography variant="body1">{process.command}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Working Directory
                      </Typography>
                      <Typography variant="body1">
                        {process.working_directory || 'Not specified'}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Started At
                      </Typography>
                      <Typography variant="body1">
                        {process.started_at ? new Date(process.started_at).toLocaleString() : 'Never'}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Restart Policy
                  </Typography>
                  <Typography variant="body1">
                    {process.restart_policy || 'No restart policy'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Environment Variables
                  </Typography>
                  {process.environment && Object.keys(process.environment).length > 0 ? (
                    <List dense>
                      {Object.entries(process.environment).map(([key, value]) => (
                        <ListItem key={key}>
                          <ListItemText
                            primary={key}
                            secondary={value}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No environment variables
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Metrics Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">CPU Usage (%)</Typography>
                    <Chip 
                      icon={<Speed />}
                      label={`${process.cpu_percent || 0}%`}
                      color="primary"
                    />
                  </Box>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={metrics.cpu}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke="#8884d8" name="CPU %" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Memory Usage (MB)</Typography>
                    <Chip 
                      icon={<Memory />}
                      label={`${process.memory_percent || 0}%`}
                      color="secondary"
                    />
                  </Box>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={metrics.memory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke="#82ca9d" name="Memory MB" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Logs Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <ToggleButtonGroup
              value={logFilter}
              onChange={(e, newFilters) => setLogFilter(newFilters)}
              aria-label="log level filter"
            >
              <ToggleButton value="info" aria-label="info">
                Info
              </ToggleButton>
              <ToggleButton value="warning" aria-label="warning">
                Warning
              </ToggleButton>
              <ToggleButton value="error" aria-label="error">
                Error
              </ToggleButton>
            </ToggleButtonGroup>
            <FormControlLabel
              control={
                <Checkbox
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  name="auto-scroll"
                />
              }
              label="Auto-scroll"
            />
          </Box>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 2, 
              maxHeight: 500, 
              overflow: 'auto',
              backgroundColor: '#f5f5f5',
              fontFamily: 'monospace',
            }}
          >
            {filteredLogs.map((log, index) => (
              <Box key={index} sx={{ mb: 1 }}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: log.level === 'error' ? 'error.main' : 
                           log.level === 'warning' ? 'warning.main' : 
                           'text.primary'
                  }}
                >
                  [{new Date(log.timestamp).toLocaleTimeString()}] [{log.level.toUpperCase()}] {log.message}
                </Typography>
              </Box>
            ))}
            <div ref={logsEndRef} />
          </Paper>
        </TabPanel>

        {/* Configuration Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            {!editMode ? (
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={() => setEditMode(true)}
              >
                Edit
              </Button>
            ) : (
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleSaveConfig}
                >
                  Save
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Cancel />}
                  onClick={handleCancelEdit}
                >
                  Cancel
                </Button>
              </Box>
            )}
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Command"
                value={editedConfig.command}
                onChange={(e) => setEditedConfig({ ...editedConfig, command: e.target.value })}
                disabled={!editMode}
                variant={editMode ? 'outlined' : 'filled'}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Working Directory"
                value={editedConfig.working_directory}
                onChange={(e) => setEditedConfig({ ...editedConfig, working_directory: e.target.value })}
                disabled={!editMode}
                variant={editMode ? 'outlined' : 'filled'}
                InputProps={{
                  startAdornment: <Folder sx={{ mr: 1, color: 'action.active' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Restart Policy"
                value={editedConfig.restart_policy}
                onChange={(e) => setEditedConfig({ ...editedConfig, restart_policy: e.target.value })}
                disabled={!editMode}
                variant={editMode ? 'outlined' : 'filled'}
                helperText="e.g., on-failure:3, always, unless-stopped"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Environment Variables
              </Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={Object.entries(editedConfig.environment)
                    .map(([k, v]) => `${k}=${v}`)
                    .join('\n')}
                  onChange={(e) => {
                    const env: Record<string, string> = {};
                    e.target.value.split('\n').forEach(line => {
                      const [key, ...valueParts] = line.split('=');
                      if (key) {
                        env[key] = valueParts.join('=');
                      }
                    });
                    setEditedConfig({ ...editedConfig, environment: env });
                  }}
                  placeholder="KEY=value (one per line)"
                  variant="outlined"
                />
              ) : (
                <Paper variant="outlined" sx={{ p: 2 }}>
                  {Object.entries(editedConfig.environment).length > 0 ? (
                    Object.entries(editedConfig.environment).map(([key, value]) => (
                      <Typography key={key} variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {key}={value}
                      </Typography>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No environment variables configured
                    </Typography>
                  )}
                </Paper>
              )}
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default ProcessDetails;
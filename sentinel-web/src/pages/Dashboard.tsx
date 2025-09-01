import React, { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  Memory,
  Speed,
  Schedule,
  CheckCircle,
  Error,
  Warning,
  Pending,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../store/store';
import { fetchProcesses, startProcess, stopProcess } from '../store/slices/processesSlice';
import { fetchMetrics } from '../store/slices/metricsSlice';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { processes, loading } = useSelector((state: RootState) => state.processes);
  const { systemMetrics } = useSelector((state: RootState) => state.metrics);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timer | null>(null);

  useEffect(() => {
    // Initial fetch
    dispatch(fetchProcesses() as any);
    dispatch(fetchMetrics() as any);

    // Set up auto-refresh every 5 seconds
    const interval = setInterval(() => {
      dispatch(fetchProcesses() as any);
      dispatch(fetchMetrics() as any);
    }, 5000);

    setRefreshInterval(interval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [dispatch]);

  const handleStartProcess = async (processId: string) => {
    await dispatch(startProcess(processId) as any);
    dispatch(fetchProcesses() as any);
  };

  const handleStopProcess = async (processId: string) => {
    await dispatch(stopProcess(processId) as any);
    dispatch(fetchProcesses() as any);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle color="success" />;
      case 'stopped':
        return <Stop color="disabled" />;
      case 'failed':
        return <Error color="error" />;
      case 'pending':
        return <Pending color="warning" />;
      default:
        return <Warning color="warning" />;
    }
  };

  const getStatusChip = (status: string) => {
    const statusColors: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
      running: 'success',
      stopped: 'default',
      failed: 'error',
      pending: 'warning',
    };

    return (
      <Chip
        label={status.toUpperCase()}
        color={statusColors[status] || 'default'}
        size="small"
        icon={getStatusIcon(status)}
      />
    );
  };

  const formatUptime = (startTime: string | null) => {
    if (!startTime) return '-';
    const start = new Date(startTime).getTime();
    const now = Date.now();
    const diff = now - start;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Header */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h4" gutterBottom>
              Process Monitor Dashboard
            </Typography>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={() => {
                dispatch(fetchProcesses() as any);
                dispatch(fetchMetrics() as any);
              }}
            >
              Refresh
            </Button>
          </Box>
        </Grid>

        {/* System Metrics Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Speed color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    CPU Usage
                  </Typography>
                  <Typography variant="h5">
                    {systemMetrics?.cpu_percent || 0}%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemMetrics?.cpu_percent || 0}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Memory color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Memory Usage
                  </Typography>
                  <Typography variant="h5">
                    {systemMetrics?.memory_percent || 0}%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemMetrics?.memory_percent || 0}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CheckCircle color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Running Processes
                  </Typography>
                  <Typography variant="h5">
                    {processes.filter(p => p.status === 'running').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Schedule color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Scheduled Tasks
                  </Typography>
                  <Typography variant="h5">
                    {processes.filter(p => p.schedule).length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Process List Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Active Processes
            </Typography>
            {loading ? (
              <LinearProgress />
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>PID</TableCell>
                      <TableCell>CPU %</TableCell>
                      <TableCell>Memory %</TableCell>
                      <TableCell>Uptime</TableCell>
                      <TableCell>Command</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {processes.map((process) => (
                      <TableRow
                        key={process.id}
                        hover
                        onClick={() => navigate(`/process/${process.id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>
                          <Typography variant="subtitle2">{process.name}</Typography>
                        </TableCell>
                        <TableCell>{getStatusChip(process.status)}</TableCell>
                        <TableCell>{process.pid || '-'}</TableCell>
                        <TableCell>{process.cpu_percent?.toFixed(1) || '0'}%</TableCell>
                        <TableCell>{process.memory_percent?.toFixed(1) || '0'}%</TableCell>
                        <TableCell>{formatUptime(process.started_at)}</TableCell>
                        <TableCell>
                          <Tooltip title={process.command}>
                            <Typography noWrap sx={{ maxWidth: 200 }}>
                              {process.command}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">
                          <Box onClick={(e) => e.stopPropagation()}>
                            {process.status === 'running' ? (
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleStopProcess(process.id)}
                              >
                                <Stop />
                              </IconButton>
                            ) : (
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleStartProcess(process.id)}
                              >
                                <PlayArrow />
                              </IconButton>
                            )}
                            <IconButton size="small" color="primary">
                              <Refresh />
                            </IconButton>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                    {processes.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8} align="center">
                          <Typography color="textSecondary">
                            No processes configured. Add a process to get started.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
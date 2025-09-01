import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Switch,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ToggleButton,
  ToggleButtonGroup,
  InputAdornment,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  PlayArrow,
  Schedule,
  CalendarMonth,
  ViewList,
  Search,
  FilterList,
  AccessTime,
  Event,
} from '@mui/icons-material';
import { RootState, AppDispatch } from '../store/store';

interface Schedule {
  id: string;
  name: string;
  process_id: string;
  process_name: string;
  schedule_type: 'cron' | 'interval' | 'one-time';
  cron_expression?: string;
  interval?: number;
  interval_unit?: string;
  next_run: string;
  last_run?: string;
  enabled: boolean;
  status: 'active' | 'inactive' | 'running';
}

const Schedules: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  
  // Redux state
  const schedules = useSelector((state: RootState) => state.schedules?.schedules || []) as Schedule[];
  const processes = useSelector((state: RootState) => state.processes?.processes || []);
  const loading = useSelector((state: RootState) => state.schedules?.loading || false);
  const error = useSelector((state: RootState) => state.schedules?.error || null);
  
  // Local state
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
  const [searchTerm, setSearchTerm] = useState('');
  const [showDisabled, setShowDisabled] = useState(true);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    process_id: '',
    schedule_type: 'cron' as const,
    cron_expression: '0 * * * *',
    interval: 60,
    interval_unit: 'minutes',
    enabled: true,
  });

  // Filter schedules based on search and filters
  const filteredSchedules = schedules.filter(schedule => {
    const matchesSearch = schedule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         schedule.process_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = showDisabled || schedule.enabled;
    return matchesSearch && matchesFilter;
  });

  // Sort schedules by next run time for upcoming runs widget
  const upcomingRuns = [...schedules]
    .filter(s => s.enabled)
    .sort((a, b) => new Date(a.next_run).getTime() - new Date(b.next_run).getTime())
    .slice(0, 5);

  const handleViewModeChange = (event: React.MouseEvent<HTMLElement>, newMode: 'list' | 'calendar' | null) => {
    if (newMode) {
      setViewMode(newMode);
    }
  };

  const handleCreateSchedule = () => {
    setEditingSchedule(null);
    setFormData({
      name: '',
      process_id: '',
      schedule_type: 'cron',
      cron_expression: '0 * * * *',
      interval: 60,
      interval_unit: 'minutes',
      enabled: true,
    });
    setDialogOpen(true);
  };

  const handleEditSchedule = (schedule: Schedule) => {
    setEditingSchedule(schedule);
    setFormData({
      name: schedule.name,
      process_id: schedule.process_id,
      schedule_type: schedule.schedule_type,
      cron_expression: schedule.cron_expression || '0 * * * *',
      interval: schedule.interval || 60,
      interval_unit: schedule.interval_unit || 'minutes',
      enabled: schedule.enabled,
    });
    setDialogOpen(true);
  };

  const handleDeleteSchedule = (scheduleId: string) => {
    // TODO: Implement delete
    console.log('Delete schedule:', scheduleId);
  };

  const handleRunNow = (scheduleId: string) => {
    // TODO: Implement run now
    console.log('Run schedule now:', scheduleId);
  };

  const handleToggleEnabled = (scheduleId: string, enabled: boolean) => {
    // TODO: Implement toggle
    console.log('Toggle schedule:', scheduleId, enabled);
  };

  const handleSaveSchedule = () => {
    // TODO: Implement save
    setDialogOpen(false);
  };

  const getTimeUntilNextRun = (nextRun: string) => {
    const now = new Date();
    const next = new Date(nextRun);
    const diff = next.getTime() - now.getTime();
    
    if (diff < 0) return 'Overdue';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `in ${days} day${days > 1 ? 's' : ''}`;
    }
    if (hours > 0) {
      return `in ${hours} hour${hours > 1 ? 's' : ''}`;
    }
    return `in ${minutes} minute${minutes !== 1 ? 's' : ''}`;
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Schedules</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreateSchedule}
        >
          Add Schedule
        </Button>
      </Box>

      {/* Controls Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search schedules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ flex: 1, maxWidth: 400 }}
          />
          
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={handleViewModeChange}
            size="small"
          >
            <ToggleButton value="list" aria-label="list view">
              <ViewList />
            </ToggleButton>
            <ToggleButton value="calendar" aria-label="calendar view">
              <CalendarMonth />
            </ToggleButton>
          </ToggleButtonGroup>

          <Button
            startIcon={<FilterList />}
            onClick={() => setFilterMenuOpen(!filterMenuOpen)}
          >
            Filter
          </Button>
        </Box>

        {filterMenuOpen && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={!showDisabled}
                  onChange={(e) => setShowDisabled(!e.target.checked)}
                  name="show-disabled"
                />
              }
              label="Show Disabled Only"
            />
          </Box>
        )}
      </Paper>

      <Grid container spacing={3}>
        {/* Main Content Area */}
        <Grid item xs={12} md={9}>
          {viewMode === 'list' ? (
            /* List View */
            <TableContainer component={Paper}>
              {filteredSchedules.length === 0 ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Schedule sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No schedules found
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Create your first schedule to automate process execution
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleCreateSchedule}
                    sx={{ mt: 2 }}
                  >
                    Create Schedule
                  </Button>
                </Box>
              ) : (
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Process</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Schedule</TableCell>
                      <TableCell>Next Run</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Enabled</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredSchedules.map((schedule) => (
                      <TableRow key={schedule.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {schedule.name}
                          </Typography>
                        </TableCell>
                        <TableCell>{schedule.process_name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={schedule.schedule_type === 'cron' ? 'Cron' : 
                                   schedule.schedule_type === 'interval' ? 'Interval' : 'One-time'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {schedule.schedule_type === 'cron' ? schedule.cron_expression :
                           schedule.schedule_type === 'interval' ? `Every ${schedule.interval} ${schedule.interval_unit}` :
                           'Once'}
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2">
                              {new Date(schedule.next_run).toLocaleString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {getTimeUntilNextRun(schedule.next_run)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={schedule.status}
                            color={schedule.status === 'active' ? 'success' : 
                                   schedule.status === 'running' ? 'primary' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={schedule.enabled}
                            onChange={(e) => handleToggleEnabled(schedule.id, e.target.checked)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Run Now">
                              <IconButton
                                size="small"
                                onClick={() => handleRunNow(schedule.id)}
                              >
                                <PlayArrow />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton
                                size="small"
                                onClick={() => handleEditSchedule(schedule)}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteSchedule(schedule.id)}
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TableContainer>
          ) : (
            /* Calendar View */
            <Paper sx={{ p: 3 }} data-testid="calendar-view">
              <Typography variant="h6" gutterBottom>
                Calendar View
              </Typography>
              {/* Simplified calendar representation */}
              <Box sx={{ mt: 2 }}>
                {filteredSchedules.map((schedule) => (
                  <Box key={schedule.id} sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="subtitle1">{schedule.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Next: {new Date(schedule.next_run).toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {schedule.schedule_type === 'cron' && `${schedule.cron_expression}`}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          )}
        </Grid>

        {/* Sidebar - Upcoming Runs */}
        <Grid item xs={12} md={3}>
          <Card data-testid="upcoming-runs">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccessTime sx={{ mr: 1 }} />
                <Typography variant="h6">Upcoming Runs</Typography>
              </Box>
              <List dense>
                {upcomingRuns.map((schedule) => (
                  <ListItem key={schedule.id}>
                    <ListItemIcon>
                      <Event fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={schedule.name}
                      secondary={getTimeUntilNextRun(schedule.next_run)}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create/Edit Schedule Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingSchedule ? 'Edit Schedule' : 'Create New Schedule'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              fullWidth
              label="Schedule Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            
            <FormControl fullWidth>
              <InputLabel>Select Process</InputLabel>
              <Select
                value={formData.process_id}
                onChange={(e) => setFormData({ ...formData, process_id: e.target.value })}
                label="Select Process"
              >
                {processes.map((process) => (
                  <MenuItem key={process.id} value={process.id}>
                    {process.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Schedule Type</InputLabel>
              <Select
                value={formData.schedule_type}
                onChange={(e) => setFormData({ ...formData, schedule_type: e.target.value as any })}
                label="Schedule Type"
              >
                <MenuItem value="cron">Cron</MenuItem>
                <MenuItem value="interval">Interval</MenuItem>
                <MenuItem value="one-time">One-time</MenuItem>
              </Select>
            </FormControl>

            {formData.schedule_type === 'cron' && (
              <>
                <TextField
                  fullWidth
                  label="Cron Expression"
                  value={formData.cron_expression}
                  onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })}
                  helperText="e.g., 0 2 * * * (daily at 2 AM)"
                />
                <Typography variant="caption" color="text.secondary">
                  Cron Helper: Use standard cron syntax
                </Typography>
              </>
            )}

            {formData.schedule_type === 'interval' && (
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="number"
                  label="Interval Value"
                  value={formData.interval}
                  onChange={(e) => setFormData({ ...formData, interval: parseInt(e.target.value) })}
                />
                <FormControl sx={{ minWidth: 120 }}>
                  <InputLabel>Interval Unit</InputLabel>
                  <Select
                    value={formData.interval_unit}
                    onChange={(e) => setFormData({ ...formData, interval_unit: e.target.value })}
                    label="Interval Unit"
                  >
                    <MenuItem value="seconds">Seconds</MenuItem>
                    <MenuItem value="minutes">Minutes</MenuItem>
                    <MenuItem value="hours">Hours</MenuItem>
                    <MenuItem value="days">Days</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
              }
              label="Enable Schedule"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveSchedule} variant="contained">
            {editingSchedule ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Schedules;
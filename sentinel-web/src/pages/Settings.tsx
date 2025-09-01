import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import {
  Container,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Snackbar,
} from '@mui/material';
import {
  Save,
  Refresh,
  Download,
  Upload,
  ContentCopy,
  Delete,
  Add,
  Visibility,
  VisibilityOff,
  Security,
  Notifications,
  Storage,
  Api,
  Settings as SettingsIcon,
  Backup,
} from '@mui/icons-material';
import { RootState } from '../store/store';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const user = useSelector((state: RootState) => state.auth?.user);
  
  // Tab state
  const [tabValue, setTabValue] = useState(0);
  
  // Settings state
  const [settings, setSettings] = useState({
    general: {
      systemName: 'SentinelZero',
      timezone: 'America/New_York',
      language: 'en',
      dateFormat: 'MM/DD/YYYY',
      timeFormat: '12h',
    },
    monitoring: {
      metricsInterval: 30,
      logRetention: 7,
      alertThreshold: 80,
      autoRestartDelay: 5,
    },
    notifications: {
      emailEnabled: true,
      slackEnabled: false,
      webhookEnabled: false,
      smtpServer: '',
      smtpPort: 587,
      senderEmail: '',
      slackWebhookUrl: '',
      slackChannel: '#alerts',
    },
    security: {
      sessionTimeout: 30,
      passwordExpiry: 90,
      twoFactorEnabled: false,
      apiTokenExpiry: 365,
    },
    backup: {
      autoBackupEnabled: false,
      backupFrequency: 'daily',
      backupRetention: 30,
    },
  });

  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState(false);

  // API tokens state
  const [apiTokens] = useState([
    { id: '1', name: 'Production API', created: '2025-08-01', expires: '2026-08-01', status: 'active' },
    { id: '2', name: 'Development API', created: '2025-07-15', expires: '2026-07-15', status: 'active' },
  ]);

  // Backup history state
  const [backupHistory] = useState([
    { id: '1', date: '2025-09-01 02:00', size: '45 MB', status: 'success' },
    { id: '2', date: '2025-08-31 02:00', size: '44 MB', status: 'success' },
    { id: '3', date: '2025-08-30 02:00', size: '43 MB', status: 'success' },
  ]);

  // UI state
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSettingChange = (category: string, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [field]: value,
      },
    }));

    // Clear validation error for this field
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[`${category}.${field}`];
      return newErrors;
    });
  };

  const validateSettings = () => {
    const errors: Record<string, string> = {};

    // Validate monitoring settings
    if (settings.monitoring.metricsInterval <= 0) {
      errors['monitoring.metricsInterval'] = 'Must be positive';
    }
    if (settings.monitoring.logRetention <= 0) {
      errors['monitoring.logRetention'] = 'Must be positive';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveSettings = () => {
    if (!validateSettings()) {
      setSnackbarMessage('Please fix validation errors');
      setSnackbarOpen(true);
      return;
    }
    setSaveDialogOpen(true);
  };

  const confirmSaveSettings = () => {
    // TODO: Implement save to backend
    setSaveDialogOpen(false);
    setSnackbarMessage('Settings saved successfully');
    setSnackbarOpen(true);
  };

  const handleResetSettings = () => {
    setSettings({
      general: {
        systemName: 'SentinelZero',
        timezone: 'America/New_York',
        language: 'en',
        dateFormat: 'MM/DD/YYYY',
        timeFormat: '12h',
      },
      monitoring: {
        metricsInterval: 30,
        logRetention: 7,
        alertThreshold: 80,
        autoRestartDelay: 5,
      },
      notifications: {
        emailEnabled: true,
        slackEnabled: false,
        webhookEnabled: false,
        smtpServer: '',
        smtpPort: 587,
        senderEmail: '',
        slackWebhookUrl: '',
        slackChannel: '#alerts',
      },
      security: {
        sessionTimeout: 30,
        passwordExpiry: 90,
        twoFactorEnabled: false,
        apiTokenExpiry: 365,
      },
      backup: {
        autoBackupEnabled: false,
        backupFrequency: 'daily',
        backupRetention: 30,
      },
    });
    setValidationErrors({});
  };

  const handleExportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `settings-${new Date().toISOString()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImportSettings = () => {
    // TODO: Implement import functionality
    console.log('Import settings');
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Settings</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExportSettings}
            >
              Export Settings
            </Button>
            <Button
              variant="outlined"
              startIcon={<Upload />}
              onClick={handleImportSettings}
            >
              Import Settings
            </Button>
          </Box>
        </Box>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab icon={<SettingsIcon />} label="General" iconPosition="start" />
            <Tab icon={<Storage />} label="Monitoring" iconPosition="start" />
            <Tab icon={<Notifications />} label="Notifications" iconPosition="start" />
            <Tab icon={<Security />} label="Security" iconPosition="start" />
            <Tab icon={<Api />} label="API" iconPosition="start" />
            <Tab icon={<Backup />} label="Backup" iconPosition="start" />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="System Name"
                value={settings.general.systemName}
                onChange={(e) => handleSettingChange('general', 'systemName', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={settings.general.timezone}
                  onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
                  label="Timezone"
                >
                  <MenuItem value="America/New_York">Eastern Time</MenuItem>
                  <MenuItem value="America/Chicago">Central Time</MenuItem>
                  <MenuItem value="America/Denver">Mountain Time</MenuItem>
                  <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                  <MenuItem value="UTC">UTC</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.general.language}
                  onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
                  label="Language"
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Date Format</InputLabel>
                <Select
                  value={settings.general.dateFormat}
                  onChange={(e) => handleSettingChange('general', 'dateFormat', e.target.value)}
                  label="Date Format"
                >
                  <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                  <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                  <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Time Format</InputLabel>
                <Select
                  value={settings.general.timeFormat}
                  onChange={(e) => handleSettingChange('general', 'timeFormat', e.target.value)}
                  label="Time Format"
                >
                  <MenuItem value="12h">12 Hour</MenuItem>
                  <MenuItem value="24h">24 Hour</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Monitoring Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Metrics Collection Interval (seconds)"
                value={settings.monitoring.metricsInterval}
                onChange={(e) => handleSettingChange('monitoring', 'metricsInterval', parseInt(e.target.value))}
                error={!!validationErrors['monitoring.metricsInterval']}
                helperText={validationErrors['monitoring.metricsInterval']}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Log Retention Days"
                value={settings.monitoring.logRetention}
                onChange={(e) => handleSettingChange('monitoring', 'logRetention', parseInt(e.target.value))}
                error={!!validationErrors['monitoring.logRetention']}
                helperText={validationErrors['monitoring.logRetention']}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Alert Threshold (%)"
                value={settings.monitoring.alertThreshold}
                onChange={(e) => handleSettingChange('monitoring', 'alertThreshold', parseInt(e.target.value))}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Auto-Restart Delay (seconds)"
                value={settings.monitoring.autoRestartDelay}
                onChange={(e) => handleSettingChange('monitoring', 'autoRestartDelay', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notifications Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Notification Channels
              </Typography>
            </Grid>
            
            {/* Email Settings */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.emailEnabled}
                    onChange={(e) => handleSettingChange('notifications', 'emailEnabled', e.target.checked)}
                  />
                }
                label="Enable Email Notifications"
              />
            </Grid>
            {settings.notifications.emailEnabled && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="SMTP Server"
                    value={settings.notifications.smtpServer}
                    onChange={(e) => handleSettingChange('notifications', 'smtpServer', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="SMTP Port"
                    value={settings.notifications.smtpPort}
                    onChange={(e) => handleSettingChange('notifications', 'smtpPort', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Sender Email"
                    type="email"
                    value={settings.notifications.senderEmail}
                    onChange={(e) => handleSettingChange('notifications', 'senderEmail', e.target.value)}
                  />
                </Grid>
              </>
            )}

            {/* Slack Settings */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.slackEnabled}
                    onChange={(e) => handleSettingChange('notifications', 'slackEnabled', e.target.checked)}
                  />
                }
                label="Enable Slack Notifications"
              />
            </Grid>
            {settings.notifications.slackEnabled && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Slack Webhook URL"
                    value={settings.notifications.slackWebhookUrl}
                    onChange={(e) => handleSettingChange('notifications', 'slackWebhookUrl', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Slack Channel"
                    value={settings.notifications.slackChannel}
                    onChange={(e) => handleSettingChange('notifications', 'slackChannel', e.target.value)}
                  />
                </Grid>
              </>
            )}

            {/* Webhook Settings */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.webhookEnabled}
                    onChange={(e) => handleSettingChange('notifications', 'webhookEnabled', e.target.checked)}
                  />
                }
                label="Enable Webhook Notifications"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Session Timeout (minutes)"
                value={settings.security.sessionTimeout}
                onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Password Expiry (days)"
                value={settings.security.passwordExpiry}
                onChange={(e) => handleSettingChange('security', 'passwordExpiry', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.twoFactorEnabled}
                    onChange={(e) => handleSettingChange('security', 'twoFactorEnabled', e.target.checked)}
                  />
                }
                label="Enable Two-Factor Authentication"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Change Password
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Current Password"
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPasswords(!showPasswords)}
                        edge="end"
                      >
                        {showPasswords ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="New Password"
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="outlined" color="primary">
                Update Password
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        {/* API Settings */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                API Configuration
              </Typography>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    API Endpoint
                  </Typography>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                    http://localhost:8000/api
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">API Tokens</Typography>
                <Button variant="contained" startIcon={<Add />}>
                  Generate New Token
                </Button>
              </Box>
              
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Active Tokens
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Expires</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {apiTokens.map((token) => (
                      <TableRow key={token.id}>
                        <TableCell>{token.name}</TableCell>
                        <TableCell>{token.created}</TableCell>
                        <TableCell>{token.expires}</TableCell>
                        <TableCell>
                          <Chip
                            label={token.status}
                            color={token.status === 'active' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <ContentCopy />
                          </IconButton>
                          <IconButton size="small" color="error">
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Backup Settings */}
        <TabPanel value={tabValue} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Backup Configuration
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.backup.autoBackupEnabled}
                    onChange={(e) => handleSettingChange('backup', 'autoBackupEnabled', e.target.checked)}
                  />
                }
                label="Enable Automatic Backups"
              />
            </Grid>

            {settings.backup.autoBackupEnabled && (
              <>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Backup Frequency</InputLabel>
                    <Select
                      value={settings.backup.backupFrequency}
                      onChange={(e) => handleSettingChange('backup', 'backupFrequency', e.target.value)}
                      label="Backup Frequency"
                    >
                      <MenuItem value="hourly">Hourly</MenuItem>
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="weekly">Weekly</MenuItem>
                      <MenuItem value="monthly">Monthly</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Backup Retention (days)"
                    value={settings.backup.backupRetention}
                    onChange={(e) => handleSettingChange('backup', 'backupRetention', parseInt(e.target.value))}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12}>
              <Button variant="contained" color="primary">
                Backup Now
              </Button>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Backup History
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Size</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {backupHistory.map((backup) => (
                      <TableRow key={backup.id}>
                        <TableCell>{backup.date}</TableCell>
                        <TableCell>{backup.size}</TableCell>
                        <TableCell>
                          <Chip
                            label={backup.status}
                            color={backup.status === 'success' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <Download />
                          </IconButton>
                          <IconButton size="small" color="error">
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleResetSettings}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSaveSettings}
          >
            Save Changes
          </Button>
        </Box>
      </Paper>

      {/* Save Confirmation Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
        <DialogTitle>Confirm Save</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to save these settings? Some changes may require a system restart.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmSaveSettings} variant="contained">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Container>
  );
};

export default Settings;
'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Alert,
  Snackbar,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Palette as PaletteIcon,
  Storage as StorageIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useJiveApi } from '../../hooks/useJiveApi';

interface AppSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    enabled: boolean;
    email: boolean;
    desktop: boolean;
    workItemUpdates: boolean;
    executionComplete: boolean;
  };
  defaultWorkItemType: string;
  autoSave: boolean;
  refreshInterval: number;
  maxRecentItems: number;
  apiTimeout: number;
}

const defaultSettings: AppSettings = {
  theme: 'auto',
  notifications: {
    enabled: true,
    email: true,
    desktop: false,
    workItemUpdates: true,
    executionComplete: true,
  },
  defaultWorkItemType: 'task',
  autoSave: true,
  refreshInterval: 30,
  maxRecentItems: 10,
  apiTimeout: 5000,
};

export function SettingsTab() {
  const theme = useTheme();
  const { connectionStatus } = useJiveApi();
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      const savedSettings = localStorage.getItem('jive-app-settings');
      if (savedSettings) {
        setSettings({ ...defaultSettings, ...JSON.parse(savedSettings) });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      localStorage.setItem('jive-app-settings', JSON.stringify(settings));
      setHasChanges(false);
      setSaveSuccess(true);
      
      // Apply theme changes immediately
      if (settings.theme !== 'auto') {
        document.documentElement.setAttribute('data-theme', settings.theme);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  const updateSetting = (path: string, value: any) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const keys = path.split('.');
      let current: any = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
    setHasChanges(true);
  };

  const clearCache = () => {
    try {
      localStorage.removeItem('jive-work-items-cache');
      localStorage.removeItem('jive-analytics-cache');
      sessionStorage.clear();
      setSaveSuccess(true);
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure your application preferences and behavior
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Appearance Settings */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <PaletteIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Appearance
                </Typography>
              </Box>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.theme}
                  label="Theme"
                  onChange={(e) => updateSetting('theme', e.target.value)}
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto (System)</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Default Work Item Type</InputLabel>
                <Select
                  value={settings.defaultWorkItemType}
                  label="Default Work Item Type"
                  onChange={(e) => updateSetting('defaultWorkItemType', e.target.value)}
                >
                  <MenuItem value="initiative">Initiative</MenuItem>
                  <MenuItem value="epic">Epic</MenuItem>
                  <MenuItem value="feature">Feature</MenuItem>
                  <MenuItem value="story">Story</MenuItem>
                  <MenuItem value="task">Task</MenuItem>
                </Select>
              </FormControl>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoSave}
                    onChange={(e) => updateSetting('autoSave', e.target.checked)}
                  />
                }
                label="Auto-save changes"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <NotificationsIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Notifications
                </Typography>
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.enabled}
                    onChange={(e) => updateSetting('notifications.enabled', e.target.checked)}
                  />
                }
                label="Enable notifications"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <Box sx={{ ml: 4, opacity: settings.notifications.enabled ? 1 : 0.5 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.email}
                      onChange={(e) => updateSetting('notifications.email', e.target.checked)}
                      disabled={!settings.notifications.enabled}
                    />
                  }
                  label="Email notifications"
                  sx={{ mb: 1, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.desktop}
                      onChange={(e) => updateSetting('notifications.desktop', e.target.checked)}
                      disabled={!settings.notifications.enabled}
                    />
                  }
                  label="Desktop notifications"
                  sx={{ mb: 1, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.workItemUpdates}
                      onChange={(e) => updateSetting('notifications.workItemUpdates', e.target.checked)}
                      disabled={!settings.notifications.enabled}
                    />
                  }
                  label="Work item updates"
                  sx={{ mb: 1, display: 'block' }}
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.executionComplete}
                      onChange={(e) => updateSetting('notifications.executionComplete', e.target.checked)}
                      disabled={!settings.notifications.enabled}
                    />
                  }
                  label="Execution completion"
                  sx={{ display: 'block' }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Settings */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <SettingsIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Performance
                </Typography>
              </Box>
              
              <TextField
                fullWidth
                label="Refresh Interval (seconds)"
                type="number"
                value={settings.refreshInterval}
                onChange={(e) => updateSetting('refreshInterval', parseInt(e.target.value) || 30)}
                inputProps={{ min: 5, max: 300 }}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label="Max Recent Items"
                type="number"
                value={settings.maxRecentItems}
                onChange={(e) => updateSetting('maxRecentItems', parseInt(e.target.value) || 10)}
                inputProps={{ min: 5, max: 50 }}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label="API Timeout (ms)"
                type="number"
                value={settings.apiTimeout}
                onChange={(e) => updateSetting('apiTimeout', parseInt(e.target.value) || 5000)}
                inputProps={{ min: 1000, max: 30000 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* System Information */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <SecurityIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  System Information
                </Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Connection Status
                </Typography>
                <Chip
                  label={connectionStatus ? 'Connected' : 'Disconnected'}
                  color={connectionStatus ? 'success' : 'error'}
                  size="small"
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Application Version
                </Typography>
                <Typography variant="body1">v1.0.0</Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Last Settings Update
                </Typography>
                <Typography variant="body1">
                  {new Date().toLocaleDateString()}
                </Typography>
              </Box>
              
              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={clearCache}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                Clear Cache
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Data Management */}
        <Grid item xs={12}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <StorageIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Data Management
                </Typography>
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Manage your application data and preferences. Changes are saved locally in your browser.
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={saveSettings}
                  disabled={!hasChanges || loading}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={resetSettings}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Reset to Defaults
                </Button>
              </Box>
              
              {hasChanges && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  You have unsaved changes. Click "Save Changes" to apply them.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={saveSuccess}
        autoHideDuration={3000}
        onClose={() => setSaveSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSaveSuccess(false)} severity="success">
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
}
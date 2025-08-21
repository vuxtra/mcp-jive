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
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { useTheme as useAppTheme } from '../../contexts/ThemeContext';

interface AppSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    enabled: boolean;
    workItemUpdates: boolean;
  };
  defaultWorkItemType: string;
  autoSave: boolean;
  autoSaveDelay: number; // in seconds
  refreshInterval: number;
  apiTimeout: number;
}

const defaultSettings: AppSettings = {
  theme: 'auto',
  notifications: {
    enabled: true,
    workItemUpdates: true,
  },
  defaultWorkItemType: 'task',
  autoSave: true,
  autoSaveDelay: 3, // 3 seconds
  refreshInterval: 30,
  apiTimeout: 5000,
};

export function SettingsTab() {
  const theme = useTheme();
  const { connectionState } = useJiveApiContext();
  const { mode: currentTheme, setMode: setThemeMode } = useAppTheme();
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      // Check if we're in a browser environment
      if (typeof window !== 'undefined' && window.localStorage) {
        const savedSettings = localStorage.getItem('jive-app-settings');
        if (savedSettings) {
          const parsed = JSON.parse(savedSettings);
          const loadedSettings = { ...defaultSettings, ...parsed };
          setSettings(loadedSettings);
          // Sync theme with context if different
          if (loadedSettings.theme !== currentTheme) {
            setThemeMode(loadedSettings.theme);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      // Check if we're in a browser environment
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('jive-app-settings', JSON.stringify(settings));
        setHasChanges(false);
        setSaveSuccess(true);
        
        // Apply theme changes through context
        setThemeMode(settings.theme);
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
      // Check if we're in a browser environment
      if (typeof window !== 'undefined' && window.localStorage && window.sessionStorage) {
        localStorage.removeItem('jive-work-items-cache');
        localStorage.removeItem('jive-analytics-cache');
        sessionStorage.clear();
        setSaveSuccess(true);
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  return (
    <Box sx={{ p: 4, minHeight: '100%' }}>
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

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* Appearance Settings */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
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
                  onChange={(e) => {
                    const newTheme = e.target.value as 'light' | 'dark' | 'auto';
                    updateSetting('theme', newTheme);
                    // Apply theme immediately for better UX
                    setThemeMode(newTheme);
                  }}
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
                sx={{ mb: 2, display: 'block' }}
              />
              
              {settings.autoSave && (
                <Box sx={{ ml: 4 }}>
                  <TextField
                    label="Auto-save delay (seconds)"
                    type="number"
                    size="small"
                    value={settings.autoSaveDelay}
                    onChange={(e) => updateSetting('autoSaveDelay', Math.max(1, Math.min(30, parseInt(e.target.value) || 3)))}
                    inputProps={{ min: 1, max: 30, step: 1 }}
                    helperText="Delay before auto-saving changes (1-30 seconds)"
                    sx={{ width: 200 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Notification Settings */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
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
                      checked={settings.notifications.workItemUpdates}
                      onChange={(e) => updateSetting('notifications.workItemUpdates', e.target.checked)}
                      disabled={!settings.notifications.enabled}
                    />
                  }
                  label="Work item updates (Snackbar notifications)"
                  sx={{ display: 'block' }}
                />
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Performance Settings */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
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
                label="API Timeout (ms)"
                type="number"
                value={settings.apiTimeout}
                onChange={(e) => updateSetting('apiTimeout', parseInt(e.target.value) || 5000)}
                inputProps={{ min: 1000, max: 30000 }}
              />
            </CardContent>
          </Card>
        </Box>

        {/* System Information */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
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
                  label={connectionState.isConnected ? 'Connected' : 'Disconnected'}
                  color={connectionState.isConnected ? 'success' : 'error'}
                  size="small"
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Application Version
                </Typography>
                <Typography variant="body1">v1.0.0-42d6bce</Typography>
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
        </Box>

        {/* Data Management */}
        <Box sx={{ width: '100%' }}>
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
                  WebSocket Debug
                </Typography>
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                WebSocket connection is now handled automatically.
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ width: '100%' }}>
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
        </Box>
      </Box>

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
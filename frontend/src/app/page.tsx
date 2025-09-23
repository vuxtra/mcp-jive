'use client';

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Paper,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Assignment as WorkItemsIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../components/providers/JiveApiProvider';
import {
  WorkItemsTab,
  AnalyticsTab,
  SettingsTab,
} from '../components/tabs';
import NamespaceSelector from '../components/NamespaceSelector';

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
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      style={{ height: '100%', display: value === index ? 'flex' : 'none', flexDirection: 'column' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'auto'
        }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `project-tab-${index}`,
    'aria-controls': `project-tabpanel-${index}`,
  };
}

export default function ProjectManagement() {
  const theme = useTheme();
  const {
    connectionState,
    isInitializing,
    error,
    clearError,
    connectWebSocket,
    disconnectWebSocket,
  } = useJiveApiContext();
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const getConnectionStatus = () => {
    if (connectionState.isConnecting) return 'connecting';
    if (connectionState.isConnected) return 'connected';
    return 'disconnected';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'disconnected': return 'error';
      default: return 'default';
    }
  };

  const tabs = [
    {
      label: 'Work Items',
      icon: <WorkItemsIcon />,
      component: <WorkItemsTab />,
    },
    {
      label: 'Analytics',
      icon: <AnalyticsIcon />,
      component: <AnalyticsTab />,
    },
    {
      label: 'Settings',
      icon: <SettingsIcon />,
      component: <SettingsTab />,
    },
  ];

  return (
    <Container maxWidth={false} disableGutters>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Paper
          elevation={0}
          sx={{
            borderBottom: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.background.paper,
            px: 4,
            py: 2,
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5,
                }}
              >
                Jive Project Management
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI-powered development workflow management
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <NamespaceSelector />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Status:
                </Typography>
                <Chip
                  label={getConnectionStatus()}
                  color={getStatusColor(getConnectionStatus())}
                  variant="outlined"
                  size="small"
                  sx={{
                    fontWeight: 600,
                    textTransform: 'capitalize',
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Tabs Navigation */}
        <Paper
          elevation={0}
          sx={{
            borderBottom: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.background.paper,
          }}
        >
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              px: 4,
              '& .MuiTab-root': {
                minHeight: 64,
                textTransform: 'none',
                fontSize: '0.95rem',
                fontWeight: 500,
                color: theme.palette.text.secondary,
                '&.Mui-selected': {
                  color: theme.palette.primary.main,
                  fontWeight: 600,
                },
                '&:hover': {
                  color: theme.palette.primary.main,
                  backgroundColor: alpha(theme.palette.primary.main, 0.04),
                },
              },
              '& .MuiTabs-indicator': {
                height: 3,
                borderRadius: '3px 3px 0 0',
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              },
            }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={index}
                icon={tab.icon}
                label={tab.label}
                iconPosition="start"
                {...a11yProps(index)}
                sx={{
                  '& .MuiSvgIcon-root': {
                    fontSize: '1.2rem',
                    mr: 1,
                  },
                }}
              />
            ))}
          </Tabs>
        </Paper>

        {/* Tab Content */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {tabs.map((tab, index) => (
            <TabPanel key={index} value={currentTab} index={index}>
              {tab.component}
            </TabPanel>
          ))}
        </Box>
      </Box>
    </Container>
  );
}

'use client';

import React from 'react';
import {
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Tooltip,
  Badge,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  AccountCircle as AccountIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { NamespaceSelector } from './NamespaceSelector';

interface HeaderProps {
  onMenuClick: () => void;
  showMenuButton?: boolean;
}

const Header: React.FC<HeaderProps> = ({ 
  onMenuClick, 
  showMenuButton = true 
}) => {
  const theme = useTheme();
  const { connectionState } = useJiveApiContext();
  
  // Mock notification count - in real app this would come from state
  const notificationCount = 3;

  const handleThemeToggle = () => {
    // TODO: Implement theme toggle functionality
    console.log('Theme toggle clicked');
  };

  const handleNotificationsClick = () => {
    // TODO: Implement notifications panel
    console.log('Notifications clicked');
  };

  const handleProfileClick = () => {
    // TODO: Implement profile menu
    console.log('Profile clicked');
  };

  const handleSettingsClick = () => {
    // TODO: Implement settings navigation
    console.log('Settings clicked');
  };

  return (
    <Toolbar sx={{ justifyContent: 'space-between' }}>
      {/* Left side - Menu button and title */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {showMenuButton && (
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            onClick={onMenuClick}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}
        
        <Typography 
          variant="h6" 
          noWrap 
          component="div"
          sx={{ 
            fontWeight: 600,
            letterSpacing: '-0.025em',
          }}
        >
          Jive Companion
        </Typography>

        {/* Connection status indicator */}
        <Box sx={{ ml: 2 }}>
          <Tooltip title={`WebSocket: ${connectionState?.isConnected ? 'Connected' : connectionState?.isConnecting ? 'Connecting' : 'Disconnected'}`}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: connectionState?.isConnected
                  ? theme.palette.success.main 
                  : connectionState?.isConnecting
                  ? theme.palette.warning.main
                  : theme.palette.error.main,
                animation: connectionState?.isConnected
                  ? 'none' 
                  : 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': {
                    opacity: 1,
                  },
                  '50%': {
                    opacity: 0.5,
                  },
                  '100%': {
                    opacity: 1,
                  },
                },
              }}
            />
          </Tooltip>
        </Box>
        
        {/* Namespace Selector */}
        <Box sx={{ ml: 2 }}>
          <NamespaceSelector />
        </Box>
      </Box>

      {/* Right side - Action buttons */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* Theme toggle */}
        <Tooltip title="Toggle theme">
          <IconButton
            color="inherit"
            onClick={handleThemeToggle}
            size="small"
          >
            {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Tooltip>

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            color="inherit"
            onClick={handleNotificationsClick}
            size="small"
          >
            <Badge badgeContent={notificationCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Settings */}
        <Tooltip title="Settings">
          <IconButton
            color="inherit"
            onClick={handleSettingsClick}
            size="small"
          >
            <SettingsIcon />
          </IconButton>
        </Tooltip>

        {/* Profile */}
        <Tooltip title="Profile">
          <IconButton
            color="inherit"
            onClick={handleProfileClick}
            size="small"
            sx={{ ml: 1 }}
          >
            <Avatar 
              sx={{ 
                width: 32, 
                height: 32,
                backgroundColor: theme.palette.primary.main,
                fontSize: '0.875rem',
              }}
            >
              AI
            </Avatar>
          </IconButton>
        </Tooltip>
      </Box>
    </Toolbar>
  );
};

export { Header };
export default Header;
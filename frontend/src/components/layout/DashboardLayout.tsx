'use client';

import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  useTheme,
  useMediaQuery,
  Container,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Work as WorkIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  SmartToy as AIIcon,
} from '@mui/icons-material';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DRAWER_WIDTH = 280;

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopOpen, setDesktopOpen] = useState(true);

  const handleDrawerToggle = () => {
    if (isMobile) {
      setMobileOpen(!mobileOpen);
    } else {
      setDesktopOpen(!desktopOpen);
    }
  };

  const navigationItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      href: '/',
      active: true,
    },
    {
      text: 'Work Items',
      icon: <WorkIcon />,
      href: '/work-items',
      active: false,
    },
    {
      text: 'AI Agent Monitor',
      icon: <AIIcon />,
      href: '/ai-monitor',
      active: false,
    },
    {
      text: 'Analytics',
      icon: <AnalyticsIcon />,
      href: '/analytics',
      active: false,
    },
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      href: '/settings',
      active: false,
    },
  ];

  const drawerContent = (
    <Sidebar 
      navigationItems={navigationItems}
      onItemClick={() => isMobile && setMobileOpen(false)}
    />
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Header */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(desktopOpen && !isMobile && {
            marginLeft: DRAWER_WIDTH,
            width: `calc(100% - ${DRAWER_WIDTH}px)`,
            transition: theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          }),
        }}
      >
        <Header 
          onMenuClick={handleDrawerToggle}
          showMenuButton={true}
        />
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ 
          width: { md: desktopOpen ? DRAWER_WIDTH : 0 }, 
          flexShrink: { md: 0 },
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
        }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: `1px solid ${theme.palette.divider}`,
            },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="persistent"
          open={desktopOpen}
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: `1px solid ${theme.palette.divider}`,
              position: 'relative',
              height: '100vh',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
        }}
      >
        {/* Toolbar spacer */}
        <Toolbar />
        
        {/* Page content */}
        <Container
          maxWidth={false}
          sx={{
            flexGrow: 1,
            py: 3,
            px: { xs: 2, sm: 3 },
            backgroundColor: theme.palette.background.default,
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default DashboardLayout;
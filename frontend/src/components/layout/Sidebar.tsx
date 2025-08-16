'use client';

import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Code as CodeIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavigationItem {
  text: string;
  icon: React.ReactNode;
  href: string;
  active?: boolean;
  badge?: string | number;
  disabled?: boolean;
}

interface SidebarProps {
  navigationItems: NavigationItem[];
  onItemClick?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  navigationItems, 
  onItemClick 
}) => {
  const theme = useTheme();
  const pathname = usePathname();

  const isItemActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.palette.background.paper,
      }}
    >
      {/* Logo/Brand section */}
      <Box
        sx={{
          p: 3,
          borderBottom: `1px solid ${theme.palette.divider}`,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}
        >
          <PsychologyIcon sx={{ fontSize: 24 }} />
        </Box>
        <Box>
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 700,
              lineHeight: 1.2,
              color: theme.palette.text.primary,
            }}
          >
            Jive
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              color: theme.palette.text.secondary,
              fontWeight: 500,
            }}
          >
            AI Companion
          </Typography>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, py: 2 }}>
        <List sx={{ px: 2 }}>
          {navigationItems.map((item, index) => {
            const isActive = isItemActive(item.href);
            
            return (
              <ListItem key={index} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  component={Link}
                  href={item.href}
                  onClick={onItemClick}
                  disabled={item.disabled}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    px: 2,
                    transition: 'all 0.2s ease-in-out',
                    backgroundColor: isActive 
                      ? alpha(theme.palette.primary.main, 0.12)
                      : 'transparent',
                    color: isActive 
                      ? theme.palette.primary.main
                      : theme.palette.text.primary,
                    '&:hover': {
                      backgroundColor: isActive 
                        ? alpha(theme.palette.primary.main, 0.16)
                        : alpha(theme.palette.action.hover, 0.08),
                      transform: 'translateX(4px)',
                    },
                    '&.Mui-disabled': {
                      opacity: 0.5,
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: 'inherit',
                      minWidth: 40,
                      '& .MuiSvgIcon-root': {
                        fontSize: 20,
                      },
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 500,
                    }}
                  />
                  {item.badge && (
                    <Chip
                      label={item.badge}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.75rem',
                        backgroundColor: isActive 
                          ? theme.palette.primary.main
                          : theme.palette.action.selected,
                        color: isActive 
                          ? theme.palette.primary.contrastText
                          : theme.palette.text.secondary,
                      }}
                    />
                  )}
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* Footer section */}
      <Box
        sx={{
          p: 2,
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box
          sx={{
            p: 2,
            borderRadius: 2,
            backgroundColor: alpha(theme.palette.info.main, 0.08),
            border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <CodeIcon sx={{ fontSize: 16, color: theme.palette.info.main }} />
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 600,
                color: theme.palette.info.main,
              }}
            >
              Development Mode
            </Typography>
          </Box>
          <Typography 
            variant="caption" 
            sx={{ 
              color: theme.palette.text.secondary,
              lineHeight: 1.3,
            }}
          >
            Connected to MCP server for real-time work item management.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default Sidebar;
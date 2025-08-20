'use client';

import React from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import { createAppTheme } from '@/theme/theme';
import { ThemeProvider as AppThemeProvider, useTheme } from '@/contexts/ThemeContext';

interface ThemeProviderProps {
  children: React.ReactNode;
}

function MuiThemeWrapper({ children }: { children: React.ReactNode }) {
  const { effectiveMode } = useTheme();
  const theme = createAppTheme(effectiveMode);

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  return (
    <AppRouterCacheProvider>
      <AppThemeProvider>
        <MuiThemeWrapper>
          {children}
        </MuiThemeWrapper>
      </AppThemeProvider>
    </AppRouterCacheProvider>
  );
}
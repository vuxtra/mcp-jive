'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { PaletteMode } from '@mui/material/styles';

interface ThemeContextType {
  mode: PaletteMode | 'auto';
  setMode: (mode: PaletteMode | 'auto') => void;
  effectiveMode: PaletteMode;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [mode, setModeState] = useState<PaletteMode | 'auto'>('light');
  const [effectiveMode, setEffectiveMode] = useState<PaletteMode>('light');

  // Load theme from localStorage on mount
  useEffect(() => {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedSettings = localStorage.getItem('jive-app-settings');
      if (savedSettings) {
        try {
          const settings = JSON.parse(savedSettings);
          if (settings.theme) {
            setModeState(settings.theme);
          }
        } catch (error) {
          console.error('Failed to parse saved settings:', error);
        }
      }
    }
  }, []);

  // Handle auto mode and system preference detection
  useEffect(() => {
    const updateEffectiveMode = () => {
      if (mode === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setEffectiveMode(prefersDark ? 'dark' : 'light');
      } else {
        setEffectiveMode(mode as PaletteMode);
      }
    };

    updateEffectiveMode();

    // Listen for system theme changes when in auto mode
    if (mode === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addEventListener('change', updateEffectiveMode);
      return () => mediaQuery.removeEventListener('change', updateEffectiveMode);
    }
  }, [mode]);

  // Update document data-theme attribute
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', effectiveMode);
  }, [effectiveMode]);

  const setMode = (newMode: PaletteMode | 'auto') => {
    setModeState(newMode);
    
    // Update localStorage
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedSettings = localStorage.getItem('jive-app-settings');
      let settings = { theme: newMode };
      
      if (savedSettings) {
        try {
          settings = { ...JSON.parse(savedSettings), theme: newMode };
        } catch (error) {
          console.error('Failed to parse saved settings:', error);
        }
      }
      
      localStorage.setItem('jive-app-settings', JSON.stringify(settings));
    }
  };

  return (
    <ThemeContext.Provider value={{ mode, setMode, effectiveMode }}>
      {children}
    </ThemeContext.Provider>
  );
};
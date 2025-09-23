'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  Select,
  MenuItem,
  Typography,
  Chip,
  CircularProgress,
  Tooltip,
  IconButton,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AccountTree as NamespaceIcon,
} from '@mui/icons-material';
import { useNamespace } from '@/contexts/NamespaceContext';

export const NamespaceSelector: React.FC = () => {
  const theme = useTheme();
  const {
    currentNamespace,
    availableNamespaces,
    isLoading,
    error,
    setNamespace,
  } = useNamespace();
  
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // Handle client-side mounting to prevent hydration issues
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleNamespaceChange = async (event: any) => {
    const namespaceName = event.target.value;
    if (!namespaceName || namespaceName === currentNamespace) return;
    
    try {
      await setNamespace(namespaceName);
    } catch (error) {
      console.error('Failed to switch namespace:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // Trigger a page reload to refresh namespaces from the server
      window.location.reload();
    } catch (error) {
      console.error('Failed to refresh namespaces:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading && !currentNamespace) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <NamespaceIcon fontSize="small" color="action" />
        <CircularProgress size={16} />
        <Typography variant="body2" color="text.secondary">
          Loading...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <NamespaceIcon fontSize="small" color="error" />
        <Chip
          label="Error"
          color="error"
          variant="outlined"
          size="small"
        />
        <Tooltip title="Refresh namespaces">
          <IconButton
            size="small"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <NamespaceIcon fontSize="small" color="action" />
      <Typography variant="body2" color="text.secondary">
        Namespace:
      </Typography>
      
      <FormControl size="small" variant="outlined">
        <Select
          value={isMounted ? (currentNamespace || 'default') : 'default'}
          onChange={handleNamespaceChange}
          displayEmpty
          sx={{
            minWidth: 120,
            height: 32,
            '& .MuiSelect-select': {
              py: 0.5,
              px: 1,
              fontSize: '0.875rem',
              fontWeight: 500,
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: alpha(theme.palette.primary.main, 0.3),
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: theme.palette.primary.main,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: theme.palette.primary.main,
            },
          }}
        >
          {!currentNamespace && (
            <MenuItem value="" disabled>
              <em>No namespace selected</em>
            </MenuItem>
          )}
          {availableNamespaces.map((namespace) => (
            <MenuItem key={namespace} value={namespace}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {namespace}
              </Typography>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Tooltip title="Refresh namespaces">
        <IconButton
          size="small"
          onClick={handleRefresh}
          disabled={isRefreshing || isLoading}
          sx={{
            color: theme.palette.text.secondary,
            '&:hover': {
              color: theme.palette.primary.main,
            },
          }}
        >
          {isRefreshing ? (
            <CircularProgress size={16} />
          ) : (
            <RefreshIcon fontSize="small" />
          )}
        </IconButton>
      </Tooltip>

      {currentNamespace && (
        <Chip
          label={isMounted ? currentNamespace : 'default'}
          color="primary"
          variant="outlined"
          size="small"
          sx={{
            fontWeight: 600,
            fontSize: '0.75rem',
            height: 24,
          }}
        />
      )}
    </Box>
  );
};

export default NamespaceSelector;
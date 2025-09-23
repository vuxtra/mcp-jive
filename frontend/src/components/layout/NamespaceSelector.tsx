'use client';

import React from 'react';
import {
  FormControl,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  Tooltip,
  SelectChangeEvent,
  CircularProgress,
} from '@mui/material';
import {
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { useNamespace } from '../../contexts/NamespaceContext';

interface NamespaceSelectorProps {
  // Props are now optional since we use context
}

const NamespaceSelector: React.FC<NamespaceSelectorProps> = () => {
  const { connectionState } = useJiveApiContext();
  const { 
    currentNamespace, 
    availableNamespaces, 
    setNamespace, 
    isLoading, 
    error 
  } = useNamespace();

  const handleNamespaceChange = async (event: SelectChangeEvent<string>) => {
    const newNamespace = event.target.value;
    if (newNamespace !== '__add_new__') {
      try {
        await setNamespace(newNamespace);
      } catch (err) {
        console.error('Failed to change namespace:', err);
      }
    }
  };

  const getNamespaceDisplayName = (namespace: string) => {
    if (namespace === 'default') return 'Default Project';
    return namespace
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getNamespaceIcon = (namespace: string) => {
    return namespace === currentNamespace ? <FolderOpenIcon /> : <FolderIcon />;
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Typography
        variant="caption"
        sx={{
          color: 'text.secondary',
          fontSize: '0.75rem',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        Project
      </Typography>
      
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <Select
          value={currentNamespace}
          onChange={handleNamespaceChange}
          disabled={!connectionState?.isConnected || isLoading}
          sx={{
            '& .MuiSelect-select': {
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              py: 0.5,
              fontSize: '0.875rem',
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'divider',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
            },
          }}
          renderValue={(value) => (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getNamespaceIcon(value)}
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {getNamespaceDisplayName(value)}
              </Typography>
            </Box>
          )}
        >
          {availableNamespaces.map((namespace) => (
            <MenuItem key={namespace} value={namespace}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                {getNamespaceIcon(namespace)}
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {getNamespaceDisplayName(namespace)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {namespace}
                  </Typography>
                </Box>
                {namespace === currentNamespace && (
                  <Chip
                    label="Active"
                    size="small"
                    color="primary"
                    sx={{ height: 20, fontSize: '0.6rem' }}
                  />
                )}
              </Box>
            </MenuItem>
          ))}
          
          {/* Add new namespace option */}
          <MenuItem value="__add_new__" disabled>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, opacity: 0.6 }}>
              <AddIcon fontSize="small" />
              <Typography variant="body2">
                Add New Project...
              </Typography>
            </Box>
          </MenuItem>
        </Select>
      </FormControl>
      
      {!connectionState?.isConnected && (
        <Tooltip title="Connect to server to switch projects">
          <Chip
            label="Offline"
            size="small"
            color="warning"
            sx={{ height: 20, fontSize: '0.6rem' }}
          />
        </Tooltip>
      )}
    </Box>
  );
};

export { NamespaceSelector };
export default NamespaceSelector;
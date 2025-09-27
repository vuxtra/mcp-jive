'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  CircularProgress,
} from '@mui/material';
import { useJiveApi } from '../../hooks/useJiveApi';
import { useNamespace } from '../../contexts/NamespaceContext';
import { WorkItem } from '../../types';

export function WorkItemsTabSimple() {
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { searchWorkItems, isInitializing } = useJiveApi();
  const { currentNamespace } = useNamespace();

  const loadWorkItems = async () => {
    if (isInitializing || typeof searchWorkItems !== 'function') {
      console.log('Cannot load work items - not ready');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      console.log('Loading work items...');
      
      const response = await searchWorkItems({ query: '', limit: 100 });
      console.log('Response:', response);
      
      if (response && response.results) {
        const transformedItems = response.results.map((item: any) => ({
          ...item,
          type: item.item_type,
          children: []
        }));
        setWorkItems(transformedItems);
        console.log('Set work items:', transformedItems.length);
      } else {
        setWorkItems([]);
      }
    } catch (error) {
      console.error('Error loading work items:', error);
      setError('Failed to load work items');
      setWorkItems([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Work Items (Simple)</Typography>
        <Button 
          variant="contained" 
          onClick={loadWorkItems}
          disabled={loading || isInitializing}
        >
          {loading ? <CircularProgress size={20} /> : 'Load Work Items'}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Namespace: {currentNamespace} | Initializing: {isInitializing ? 'Yes' : 'No'} | Items: {workItems.length}
      </Typography>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} sx={{ textAlign: 'center', py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : workItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} sx={{ textAlign: 'center', py: 4 }}>
                  No work items found. Click "Load Work Items" to fetch data.
                </TableCell>
              </TableRow>
            ) : (
              workItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.title}</TableCell>
                  <TableCell>{item.type}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  <TableCell>{item.priority}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
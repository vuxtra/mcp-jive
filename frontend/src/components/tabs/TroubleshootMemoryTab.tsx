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
  IconButton,
  Chip,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Toolbar,
  Tooltip,
  useTheme,
  alpha,
  Snackbar,
  Alert,
  Stack,
  Fab,
  Zoom,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Build as TroubleshootIcon,
  Refresh as RefreshIcon,
  KeyboardArrowUp as ScrollTopIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { useNamespace } from '../../contexts/NamespaceContext';
import { TroubleshootMemoryModal } from '../modals/TroubleshootMemoryModal';
import { ConfirmDeleteDialog } from '../modals/ConfirmDeleteDialog';
import type { TroubleshootItem } from '../../types/memory';

export function TroubleshootMemoryTab() {
  const theme = useTheme();
  const { currentNamespace } = useNamespace();
  const [items, setItems] = useState<TroubleshootItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({ open: false, message: '', severity: 'info' });

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<TroubleshootItem | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<TroubleshootItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadTroubleshootItems = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/memory?memory_type=troubleshoot&action=list`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Namespace': currentNamespace || 'default',
        },
      });

      const result = await response.json();

      if (result.success && result.data && result.data.data) {
        setItems(result.data.data.items || []);
      } else {
        throw new Error(result.error || 'Failed to load troubleshoot items');
      }
    } catch (error) {
      console.error('Failed to load troubleshoot items:', error);
      showSnackbar('Failed to load troubleshoot items', 'error');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTroubleshootItems();
  }, [currentNamespace]);

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const filteredItems = items.filter(item =>
    item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.slug.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase())) ||
    item.ai_use_case.some(uc => uc.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getSuccessRate = (item: TroubleshootItem): number => {
    if (item.usage_count === 0) return 0;
    return (item.success_count / item.usage_count) * 100;
  };

  const getSuccessRateColor = (rate: number): string => {
    if (rate >= 70) return theme.palette.success.main;
    if (rate >= 40) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // CRUD handlers
  const handleOpenCreateModal = () => {
    setSelectedItem(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (item: TroubleshootItem) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  const handleSave = async (itemData: Partial<TroubleshootItem>) => {
    try {
      const action = selectedItem ? 'update' : 'create';
      const response = await fetch('/api/memory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Namespace': currentNamespace || 'default',
        },
        body: JSON.stringify({
          memory_type: 'troubleshoot',
          action,
          ...itemData,
        }),
      });

      const result = await response.json();

      if (result.success) {
        showSnackbar(
          selectedItem
            ? 'Troubleshoot item updated successfully'
            : 'Troubleshoot item created successfully',
          'success'
        );
        await loadTroubleshootItems();
      } else {
        throw new Error(result.error || 'Failed to save item');
      }
    } catch (error) {
      console.error('Error saving troubleshoot item:', error);
      throw error;
    }
  };

  const handleOpenDeleteDialog = (item: TroubleshootItem) => {
    setItemToDelete(item);
    setIsDeleteDialogOpen(true);
  };

  const handleCloseDeleteDialog = () => {
    setIsDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;

    setIsDeleting(true);
    try {
      const response = await fetch('/api/memory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Namespace': currentNamespace || 'default',
        },
        body: JSON.stringify({
          memory_type: 'troubleshoot',
          action: 'delete',
          slug: itemToDelete.slug,
        }),
      });

      const result = await response.json();

      if (result.success) {
        showSnackbar('Troubleshoot item deleted successfully', 'success');
        await loadTroubleshootItems();
        handleCloseDeleteDialog();
      } else {
        throw new Error(result.error || 'Failed to delete item');
      }
    } catch (error) {
      console.error('Error deleting troubleshoot item:', error);
      showSnackbar('Failed to delete troubleshoot item', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 3 }}>
      {/* Toolbar */}
      <Paper
        elevation={0}
        sx={{
          mb: 2,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
        }}
      >
        <Toolbar sx={{ gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search troubleshooting items..."
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ flexGrow: 1, minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadTroubleshootItems}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenCreateModal}
            >
              New Solution
            </Button>
          </Stack>
        </Toolbar>
      </Paper>

      {/* Content Area */}
      <Paper
        elevation={0}
        sx={{
          flexGrow: 1,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {filteredItems.length === 0 ? (
          <Box
            sx={{
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              p: 4,
              textAlign: 'center',
            }}
          >
            <TroubleshootIcon sx={{ fontSize: 80, color: theme.palette.grey[300], mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchTerm ? 'No troubleshooting items found' : 'No troubleshooting items yet'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Create your first troubleshooting solution to get started'}
            </Typography>
            {!searchTerm && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenCreateModal}
              >
                Create Troubleshooting Item
              </Button>
            )}
          </Box>
        ) : (
          <TableContainer sx={{ flexGrow: 1 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Title</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Slug</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Use Cases</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Keywords</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Usage</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Success Rate</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Updated</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredItems.map((item) => {
                  const successRate = getSuccessRate(item);
                  return (
                    <TableRow
                      key={item.id}
                      hover
                      sx={{
                        '&:last-child td': { border: 0 },
                        cursor: 'pointer',
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {item.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.slug}
                          size="small"
                          variant="outlined"
                          sx={{ fontFamily: 'monospace' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {item.use_case_count || item.use_cases?.length || item.ai_use_case?.length || 0} use case{(item.use_case_count || item.use_cases?.length || item.ai_use_case?.length || 0) !== 1 ? 's' : ''}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                          {item.keywords.slice(0, 3).map((keyword, idx) => (
                            <Chip key={idx} label={keyword} size="small" />
                          ))}
                          {item.keywords.length > 3 && (
                            <Chip label={`+${item.keywords.length - 3}`} size="small" />
                          )}
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {item.usage_count}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flexGrow: 1, minWidth: 60 }}>
                            <LinearProgress
                              variant="determinate"
                              value={successRate}
                              sx={{
                                height: 6,
                                borderRadius: 1,
                                backgroundColor: alpha(getSuccessRateColor(successRate), 0.2),
                                '& .MuiLinearProgress-bar': {
                                  backgroundColor: getSuccessRateColor(successRate),
                                },
                              }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            sx={{ color: getSuccessRateColor(successRate), fontWeight: 600 }}
                          >
                            {successRate.toFixed(0)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(item.last_updated_on).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOpenEditModal(item);
                              }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOpenDeleteDialog(item);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Scroll to top button */}
      <Zoom in={showScrollTop}>
        <Fab
          color="primary"
          size="small"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
          }}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <ScrollTopIcon />
        </Fab>
      </Zoom>

      {/* Create/Edit Modal */}
      <TroubleshootMemoryModal
        open={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        item={selectedItem}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDeleteDialog
        open={isDeleteDialogOpen}
        onClose={handleCloseDeleteDialog}
        onConfirm={handleConfirmDelete}
        title="Delete Troubleshoot Item"
        itemName={itemToDelete?.title}
        description="This will permanently delete this troubleshooting solution and its usage statistics."
        isDeleting={isDeleting}
      />
    </Box>
  );
}
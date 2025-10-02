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
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AccountTree as ArchitectureIcon,
  Refresh as RefreshIcon,
  KeyboardArrowUp as ScrollTopIcon,
} from '@mui/icons-material';
import { useNamespace } from '../../contexts/NamespaceContext';
import { ArchitectureMemoryModal } from '../modals/ArchitectureMemoryModal';
import { ConfirmDeleteDialog } from '../modals/ConfirmDeleteDialog';
import type { ArchitectureItem } from '../../types/memory';

export function ArchitectureMemoryTab() {
  const theme = useTheme();
  const { currentNamespace } = useNamespace();
  const [items, setItems] = useState<ArchitectureItem[]>([]);
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
  const [selectedItem, setSelectedItem] = useState<ArchitectureItem | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<ArchitectureItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadArchitectureItems = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/memory?memory_type=architecture&action=list`, {
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
        throw new Error(result.error || 'Failed to load architecture items');
      }
    } catch (error) {
      console.error('Failed to load architecture items:', error);
      showSnackbar('Failed to load architecture items', 'error');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArchitectureItems();
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
    item.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // CRUD handlers
  const handleOpenCreateModal = () => {
    setSelectedItem(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (item: ArchitectureItem) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  const handleSave = async (itemData: Partial<ArchitectureItem>) => {
    try {
      const action = selectedItem ? 'update' : 'create';
      const response = await fetch('/api/memory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Namespace': currentNamespace || 'default',
        },
        body: JSON.stringify({
          memory_type: 'architecture',
          action,
          ...itemData,
        }),
      });

      const result = await response.json();

      if (result.success) {
        showSnackbar(
          selectedItem
            ? 'Architecture item updated successfully'
            : 'Architecture item created successfully',
          'success'
        );
        await loadArchitectureItems();
      } else {
        throw new Error(result.error || 'Failed to save item');
      }
    } catch (error) {
      console.error('Error saving architecture item:', error);
      throw error;
    }
  };

  const handleOpenDeleteDialog = (item: ArchitectureItem) => {
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
          memory_type: 'architecture',
          action: 'delete',
          slug: itemToDelete.slug,
        }),
      });

      const result = await response.json();

      if (result.success) {
        showSnackbar('Architecture item deleted successfully', 'success');
        await loadArchitectureItems();
        handleCloseDeleteDialog();
      } else {
        throw new Error(result.error || 'Failed to delete item');
      }
    } catch (error) {
      console.error('Error deleting architecture item:', error);
      showSnackbar('Failed to delete architecture item', 'error');
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
            placeholder="Search architecture items..."
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
              onClick={loadArchitectureItems}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenCreateModal}
            >
              New Architecture
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
            <ArchitectureIcon sx={{ fontSize: 80, color: theme.palette.grey[300], mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchTerm ? 'No architecture items found' : 'No architecture items yet'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Create your first architecture item to get started'}
            </Typography>
            {!searchTerm && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenCreateModal}
              >
                Create Architecture Item
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
                  <TableCell sx={{ fontWeight: 600 }}>Keywords</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Children</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Related</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Updated</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredItems.map((item) => (
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
                        {item.children_count || item.children_slugs?.length || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {item.related_count || item.related_slugs?.length || 0}
                      </Typography>
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
                ))}
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
      <ArchitectureMemoryModal
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
        title="Delete Architecture Item"
        itemName={itemToDelete?.title}
        description="This will permanently delete this architecture item and all associated data."
        isDeleting={isDeleting}
      />
    </Box>
  );
}
'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Snackbar,
  Typography,
  IconButton,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import {
  Close as CloseIcon,
  List as ListIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { useNamespace } from '../../contexts/NamespaceContext';
import WorkItemForm from './WorkItemForm';
import WorkItemList from './WorkItemList';
import WorkItemDetails from './WorkItemDetails';
import type { WorkItem, CreateWorkItemRequest, UpdateWorkItemRequest } from '../../types';

interface WorkItemManagerProps {
  parentId?: string;
  initialView?: 'list' | 'grid';
  showCreateButton?: boolean;
  title?: string;
}

interface DialogState {
  type: 'create' | 'edit' | 'view' | 'delete' | null;
  workItem?: WorkItem;
  isOpen: boolean;
}

interface NotificationState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

export const WorkItemManager: React.FC<WorkItemManagerProps> = ({
  parentId,
  initialView = 'list',
  showCreateButton = true,
  title = 'Work Items',
}) => {
  const {
    createWorkItem,
    updateWorkItem,
    deleteWorkItem,
    isLoading,
    error,
  } = useJiveApiContext();
  
  const { currentNamespace } = useNamespace();

  const [currentView, setCurrentView] = useState<'list' | 'grid'>(initialView);
  const [dialogState, setDialogState] = useState<DialogState>({
    type: null,
    isOpen: false,
  });
  const [notification, setNotification] = useState<NotificationState>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Trigger refresh of work item list
  const triggerRefresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Listen for namespace changes and refresh data
  useEffect(() => {
    const handleNamespaceChange = () => {
      triggerRefresh();
    };

    window.addEventListener('namespace-changed', handleNamespaceChange);
    return () => {
      window.removeEventListener('namespace-changed', handleNamespaceChange);
    };
  }, [triggerRefresh]);

  // Refresh when namespace changes
  useEffect(() => {
    triggerRefresh();
  }, [currentNamespace, triggerRefresh]);

  // Show notification
  const showNotification = useCallback((message: string, severity: NotificationState['severity'] = 'success') => {
    setNotification({ open: true, message, severity });
  }, []);

  // Close notification
  const closeNotification = useCallback(() => {
    setNotification(prev => ({ ...prev, open: false }));
  }, []);

  // Dialog handlers
  const openDialog = useCallback((type: DialogState['type'], workItem?: WorkItem) => {
    setDialogState({ type, workItem, isOpen: true });
  }, []);

  const closeDialog = useCallback(() => {
    setDialogState({ type: null, isOpen: false });
  }, []);

  // CRUD operation handlers
  const handleCreate = useCallback(() => {
    openDialog('create');
  }, [openDialog]);

  const handleEdit = useCallback((workItem: WorkItem) => {
    openDialog('edit', workItem);
  }, [openDialog]);

  const handleView = useCallback((workItem: WorkItem) => {
    openDialog('view', workItem);
  }, [openDialog]);

  const handleDelete = useCallback((workItem: WorkItem) => {
    openDialog('delete', workItem);
  }, [openDialog]);



  // Form submission handlers
  const handleFormSubmit = useCallback(async (data: CreateWorkItemRequest | UpdateWorkItemRequest) => {
    try {
      if (dialogState.type === 'create') {
        const workItem = await createWorkItem({
          ...data as CreateWorkItemRequest,
        });
        
        showNotification('Work item created successfully');
        triggerRefresh();
        closeDialog();
      } else if (dialogState.type === 'edit') {
        if (!dialogState.workItem?.id) {
          throw new Error('No work item ID available for update');
        }
        
        const workItem = await updateWorkItem(
          dialogState.workItem.id,
          data as UpdateWorkItemRequest
        );
        
        showNotification('Work item updated successfully');
        triggerRefresh();
        closeDialog();
      }
    } catch (err) {
      console.error('Form submission error:', err);
      showNotification('An unexpected error occurred', 'error');
    }
  }, [dialogState.type, createWorkItem, updateWorkItem, showNotification, triggerRefresh, closeDialog]);

  // Delete confirmation handler
  const handleDeleteConfirm = useCallback(async () => {
    if (!dialogState.workItem) return;
    
    try {
      await deleteWorkItem(dialogState.workItem.id);
      
      showNotification('Work item deleted successfully');
      triggerRefresh();
      closeDialog();
    } catch (err) {
      console.error('Delete error:', err);
      showNotification('An unexpected error occurred', 'error');
    }
  }, [dialogState.workItem, deleteWorkItem, showNotification, triggerRefresh, closeDialog]);



  // Render dialog content based on type
  const renderDialogContent = () => {
    switch (dialogState.type) {
      case 'create':
      case 'edit':
        return (
          <WorkItemForm
            workItem={dialogState.workItem}
            parentId={parentId}
            onSubmit={handleFormSubmit}
            onCancel={closeDialog}
            isLoading={isLoading}
            mode={dialogState.type}
          />
        );
      
      case 'view':
        return dialogState.workItem ? (
          <WorkItemDetails
            workItemId={dialogState.workItem.id}
            onEdit={handleEdit}
            onDelete={handleDelete}
    
            showActions={true}
          />
        ) : null;
      
      case 'delete':
        return (
          <Box>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete this work item?
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>{dialogState.workItem?.title}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              This action cannot be undone.
            </Typography>
          </Box>
        );
      

      
      default:
        return null;
    }
  };

  // Get dialog title
  const getDialogTitle = () => {
    switch (dialogState.type) {
      case 'create': return 'Create Work Item';
      case 'edit': return 'Edit Work Item';
      case 'view': return 'Work Item Details';
      case 'delete': return 'Delete Work Item';

      default: return '';
    }
  };

  // Get dialog max width
  const getDialogMaxWidth = () => {
    switch (dialogState.type) {
      case 'view': return 'lg';
      case 'create':
      case 'edit': return 'md';
      default: return 'sm';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">{title}</Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* View Toggle */}
          <Paper sx={{ display: 'flex' }}>
            <Tabs
              value={currentView}
              onChange={(_, newValue) => setCurrentView(newValue)}
              variant="fullWidth"
              sx={{ minHeight: 'auto' }}
            >
              <Tab
                icon={<ListIcon />}
                value="list"
                sx={{ minHeight: 'auto', py: 1 }}
              />
              <Tab
                icon={<ViewModuleIcon />}
                value="grid"
                sx={{ minHeight: 'auto', py: 1 }}
              />
            </Tabs>
          </Paper>
          
          {/* Create Button */}
          {showCreateButton && (
            <Button
              variant="contained"
              onClick={handleCreate}
              disabled={isLoading}
            >
              Create Work Item
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Work Item List */}
      <WorkItemList
        key={refreshTrigger} // Force refresh when trigger changes
        parentId={parentId}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onView={handleView}

        onCreate={showCreateButton ? handleCreate : undefined}
        showActions={true}
        compact={currentView === 'grid'}
      />

      {/* Dialog */}
      <Dialog
        open={dialogState.isOpen}
        onClose={closeDialog}
        maxWidth={getDialogMaxWidth()}
        fullWidth
        PaperProps={{
          sx: {
            minHeight: dialogState.type === 'view' ? '80vh' : 'auto',
          },
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {getDialogTitle()}
          <IconButton onClick={closeDialog} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent sx={{ p: dialogState.type === 'view' ? 1 : 3 }}>
          {renderDialogContent()}
        </DialogContent>
        
        {/* Dialog Actions for delete */}
        {dialogState.type === 'delete' && (
          <DialogActions>
            <Button onClick={closeDialog} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              color="error"
              variant="contained"
              disabled={isLoading}
            >
              Delete
            </Button>
          </DialogActions>
        )}
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={closeNotification}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WorkItemManager;
'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Box,
  Typography,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Close as CloseIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  OpenInFull as ExpandIcon,
  CloseFullscreen as CollapseIcon,
} from '@mui/icons-material';
import { Resizable } from 're-resizable';
import WorkItemModalForm from '../work-items/WorkItemModalForm';
import type { WorkItem, WorkItemType } from '../../types';

interface WorkItemModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (workItem: Partial<WorkItem>) => Promise<void>;
  workItem?: WorkItem | null;
  parentId?: string;
  defaultType?: WorkItemType;
  title?: string;
}

const WorkItemModal: React.FC<WorkItemModalProps> = ({
  open,
  onClose,
  onSave,
  workItem,
  parentId,
  defaultType = 'task',
  title,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [modalSize, setModalSize] = useState({ 
    width: 800, 
    height: 600 
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize modal size on client side
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setModalSize({
        width: Math.min(window.innerWidth * 0.5, 800),
        height: Math.min(window.innerHeight * 0.5, 600)
      });
    }
  }, []);

  // Reset modal state when opening/closing
  useEffect(() => {
    if (open) {
      setIsExpanded(false);
      setIsFullscreen(false);
      if (typeof window !== 'undefined') {
        setModalSize({ 
          width: Math.min(window.innerWidth * 0.5, 800), 
          height: Math.min(window.innerHeight * 0.5, 600) 
        });
      }
    }
  }, [open]);

  // Determine modal title
  const modalTitle = title || (workItem ? 'Edit Work Item' : 'Create Work Item');

  // Handle form submission
  const handleSave = async (formData: Partial<WorkItem>) => {
    setIsSubmitting(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error saving work item:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle expanded state
  const toggleExpanded = () => {
    if (isExpanded) {
      // Return to default size (50% of screen)
      setModalSize({ 
        width: Math.min(window.innerWidth * 0.5, 800), 
        height: Math.min(window.innerHeight * 0.5, 600) 
      });
    } else {
      // Expand to 80% of screen
      setModalSize({ 
        width: Math.min(window.innerWidth * 0.8, 1200), 
        height: Math.min(window.innerHeight * 0.8, 900) 
      });
    }
    setIsExpanded(!isExpanded);
  };

  // Toggle fullscreen state
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Get dialog styles based on state
  const getDialogStyles = () => {
    if (isFullscreen) {
      return {
        '& .MuiDialog-paper': {
          margin: 0,
          width: '100vw',
          height: '100vh',
          maxWidth: 'none',
          maxHeight: 'none',
          borderRadius: 0,
        },
      };
    }

    if (isMobile) {
      return {
        '& .MuiDialog-paper': {
          margin: theme.spacing(1),
          width: 'calc(100vw - 16px)',
          height: 'calc(100vh - 16px)',
          maxWidth: 'none',
          maxHeight: 'none',
        },
      };
    }

    return {
      '& .MuiDialog-paper': {
        width: modalSize.width,
        height: modalSize.height,
        maxWidth: 'none',
        maxHeight: 'none',
      },
    };
  };

  const DialogWrapper = ({ children }: { children: React.ReactNode }) => {
    if (isFullscreen || isMobile) {
      return <>{children}</>;
    }

    return (
      <Resizable
        size={modalSize}
        onResizeStop={(e, direction, ref, d) => {
          setModalSize({
            width: modalSize.width + d.width,
            height: modalSize.height + d.height,
          });
        }}
        minWidth={400}
        minHeight={300}
        maxWidth={window.innerWidth - 100}
        maxHeight={window.innerHeight - 100}
        enable={{
          top: true,
          right: true,
          bottom: true,
          left: true,
          topRight: true,
          bottomRight: true,
          bottomLeft: true,
          topLeft: true,
        }}
        style={{
          position: 'relative',
          border: `2px solid ${theme.palette.primary.main}`,
          borderRadius: theme.shape.borderRadius,
          overflow: 'hidden',
        }}
      >
        {children}
      </Resizable>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={false}
      fullWidth={false}
      sx={getDialogStyles()}
      PaperProps={{
        sx: {
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        },
      }}
    >
      <DialogWrapper>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Header */}
          <DialogTitle
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              pb: 1,
              borderBottom: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
              position: 'relative',
              zIndex: 1,
            }}
          >
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              {modalTitle}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {/* Expand/Collapse Button */}
              {!isMobile && (
                <IconButton
                  onClick={toggleExpanded}
                  size="small"
                  title={isExpanded ? 'Collapse' : 'Expand'}
                  sx={{ color: theme.palette.text.secondary }}
                >
                  {isExpanded ? <CollapseIcon /> : <ExpandIcon />}
                </IconButton>
              )}
              
              {/* Fullscreen Button */}
              <IconButton
                onClick={toggleFullscreen}
                size="small"
                title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                sx={{ color: theme.palette.text.secondary }}
              >
                {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
              
              {/* Close Button */}
              <IconButton
                onClick={onClose}
                size="small"
                title="Close"
                sx={{ color: theme.palette.text.secondary }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>

          {/* Content */}
          <DialogContent
            sx={{
              flex: 1,
              overflow: 'auto',
              p: 0,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box sx={{ p: 3, flex: 1 }}>
              <WorkItemModalForm
                workItem={workItem}
                parentId={parentId}
                defaultType={defaultType}
                onSave={handleSave}
                onCancel={onClose}
                isSubmitting={isSubmitting}
                showActions={false} // We'll handle actions in the dialog footer
              />
            </Box>
          </DialogContent>

          {/* Footer */}
          <Divider />
          <DialogActions
            sx={{
              p: 2,
              backgroundColor: theme.palette.background.paper,
              borderTop: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Button
              onClick={onClose}
              variant="outlined"
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                // Trigger form submission
                const form = document.querySelector('form[data-work-item-form]') as HTMLFormElement;
                if (form) {
                  form.requestSubmit();
                }
              }}
              variant="contained"
              disabled={isSubmitting}
              sx={{ ml: 1 }}
            >
              {isSubmitting ? 'Saving...' : (workItem ? 'Update' : 'Create')}
            </Button>
          </DialogActions>
        </Box>
      </DialogWrapper>
    </Dialog>
  );
};

export default WorkItemModal;
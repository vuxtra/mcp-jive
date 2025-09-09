'use client';

import React, { useState, useEffect, useRef } from 'react';
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
  Collapse,
  Button,
  TextField,
  InputAdornment,
  Toolbar,
  Tooltip,
  Menu,
  MenuItem,
  useTheme,
  alpha,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Divider,
  Snackbar,
  Alert,
  Fab,
  Zoom,
  Stack,
  Badge,
} from '@mui/material';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  KeyboardArrowUp as ScrollTopIcon,
  Assignment as TaskIcon,
  Flag as EpicIcon,
  Star as FeatureIcon,
  BookmarkBorder as StoryIcon,
  RocketLaunch as InitiativeIcon,
  AccountTree as HierarchyIcon,
  Link as LinkIcon,
  LinkOff as UnlinkIcon,
  AddBox as AddChildIcon,
  DragIndicator as DragIndicatorIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { useJiveApi } from '../../hooks/useJiveApi';
import { usePeriodicRefresh } from '../../hooks/usePeriodicRefresh';
import { WorkItem } from '../../types';
import { WorkItemModal } from '../modals';

// Custom tooltip component for work items
interface WorkItemTooltipProps {
  workItem: WorkItem;
  children: React.ReactElement;
}

function WorkItemPopup({ workItem, children }: WorkItemTooltipProps) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString();
  };
  
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    setOpen(true);
  };
  
  const handleClose = () => {
    setOpen(false);
    setAnchorEl(null);
  };
  
  const popupContent = (
    <Box sx={{ maxWidth: 350, p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, flex: 1, pr: 1 }}>
          {workItem.title}
        </Typography>
        <IconButton 
          size="small" 
          onClick={handleClose}
          sx={{ 
            ml: 1,
            color: 'text.secondary',
            '&:hover': {
              backgroundColor: alpha(theme.palette.action.hover, 0.5)
            }
          }}
        >
          <CloseIcon sx={{ fontSize: '16px' }} />
        </IconButton>
      </Box>
      
      {workItem.description && (
        <Typography variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
          {workItem.description}
        </Typography>
      )}
      
      <Stack spacing={0.5}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Type:</Typography>
          <Chip label={workItem.type} size="small" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Status:</Typography>
          <Chip 
            label={workItem.status.replace('_', ' ')} 
            size="small" 
            sx={{ fontSize: '0.7rem', height: 20, textTransform: 'capitalize' }} 
          />
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Priority:</Typography>
          <Chip 
            label={workItem.priority} 
            size="small" 
            variant="outlined"
            sx={{ fontSize: '0.7rem', height: 20, textTransform: 'capitalize' }} 
          />
        </Box>
        
        {workItem.complexity && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">Complexity:</Typography>
            <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
              {workItem.complexity}
            </Typography>
          </Box>
        )}
        
        {workItem.context_tags && workItem.context_tags.length > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>Tags:</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {workItem.context_tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 18 }}
                />
              ))}
            </Box>
          </Box>
        )}
        
        {workItem.acceptance_criteria && workItem.acceptance_criteria.length > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>Acceptance Criteria:</Typography>
            <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
              {workItem.acceptance_criteria.length} criteria defined
            </Typography>
          </Box>
        )}
        
        <Divider sx={{ my: 0.5 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Created:</Typography>
          <Typography variant="caption">{formatDate(workItem.created_at)}</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Updated:</Typography>
          <Typography variant="caption">{formatDate(workItem.updated_at)}</Typography>
        </Box>
      </Stack>
    </Box>
  );
  
  return (
    <>
      <Box onClick={handleClick} sx={{ cursor: 'pointer' }}>
        {children}
      </Box>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            bgcolor: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            boxShadow: theme.shadows[8],
            maxWidth: 400,
          },
        }}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        {popupContent}
      </Menu>
    </>
  );
}

interface WorkItemRowProps {
  workItem: WorkItem;
  level: number;
  onEdit: (workItem: WorkItem) => void;
  onDelete: (workItem: WorkItem) => void;
  onViewHierarchy: (workItem: WorkItem) => void;
  onAddChild: (workItem: WorkItem) => void;
  children?: WorkItem[];
  isDragging?: boolean;
  sortableRef?: any;
  sortableStyle?: any;
}

// Sortable wrapper for WorkItemRow
function SortableWorkItemRow(props: WorkItemRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: props.workItem.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <WorkItemRow 
      {...props} 
      isDragging={isDragging} 
      dragHandleProps={{ ...attributes, ...listeners }}
      sortableRef={setNodeRef}
      sortableStyle={style}
    />
  );
}

function WorkItemRow({ workItem, level, onEdit, onDelete, onViewHierarchy, onAddChild, children, isDragging, dragHandleProps, sortableRef, sortableStyle }: WorkItemRowProps & { dragHandleProps?: any }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const hasChildren = children && children.length > 0;

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'initiative': return <InitiativeIcon sx={{ fontSize: '1rem' }} />;
      case 'epic': return <EpicIcon sx={{ fontSize: '1rem' }} />;
      case 'feature': return <FeatureIcon sx={{ fontSize: '1rem' }} />;
      case 'story': return <StoryIcon sx={{ fontSize: '1rem' }} />;
      case 'task': return <TaskIcon sx={{ fontSize: '1rem' }} />;
      default: return <TaskIcon sx={{ fontSize: '1rem' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'primary';
      case 'blocked': return 'error';
      case 'not_started': return 'default';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getProgressValue = () => {
    // Use actual progress from work item, fallback to status-based calculation
    if (workItem.progress !== undefined && workItem.progress !== null) {
      return Math.round(workItem.progress);
    }
    
    // Fallback to status-based calculation if progress is not set
    // This matches the backend ProgressCalculator logic
    switch (workItem.status) {
      case 'completed': return 100;
      case 'in_progress': return 50;
      case 'blocked': return 25;
      case 'not_started': return 0;
      case 'cancelled': return 0;
      default: return 0;
    }
  };

  return (
    <>
      <TableRow
        ref={sortableRef}
        sx={{
          backgroundColor: level > 0 ? alpha(theme.palette.primary.main, 0.02 + level * 0.01) : 'inherit',
          borderLeft: level > 0 ? `3px solid ${alpha(theme.palette.primary.main, 0.3)}` : 'none',
          '&:hover': {
            backgroundColor: alpha(theme.palette.primary.main, 0.06),
          },
          ...sortableStyle,
        }}
      >
        {/* Sequence Number Column with Drag Handle */}
        <TableCell sx={{ 
          textAlign: 'center',
          width: '8%',
          minWidth: '70px',
          fontWeight: 500,
          color: theme.palette.text.secondary
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
            <IconButton
              size="small"
              sx={{ 
                cursor: 'grab',
                '&:active': { cursor: 'grabbing' },
                opacity: 0.6,
                '&:hover': { opacity: 1 }
              }}
              {...dragHandleProps}
            >
              <DragIndicatorIcon fontSize="small" />
            </IconButton>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {workItem.displaySequence || ''}
            </Typography>
          </Box>
        </TableCell>
        
        {/* Combined Work Item Column with Type & Hierarchy */}
        <TableCell sx={{ 
          width: '45%',
          minWidth: '350px',
          pl: 1 + level * 2
        }}>
          <WorkItemPopup workItem={workItem}>
            <Box sx={{ 
              position: 'relative',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1
            }}>              {/* Fixed-width container for expand icon and type icon */}
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  gap: 0.5,
                  minWidth: '40px', // Fixed width to ensure consistent alignment
                  mt: 0.25,
                }}
              >
                {/* Expand/collapse icon for parents */}
                {hasChildren ? (
                  <IconButton 
                    size="small" 
                    sx={{ 
                      width: 16, 
                      height: 16, 
                      p: 0,
                      color: theme.palette.text.secondary,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'transparent', // Remove gray highlight
                        color: theme.palette.primary.main
                      }
                    }}
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent popup from opening
                      setExpanded(!expanded);
                    }}
                  >
                    {expanded ? 
                      <ExpandMoreIcon sx={{ fontSize: '12px' }} /> : 
                      <ChevronRightIcon sx={{ fontSize: '12px' }} />
                    }
                  </IconButton>
                ) : (
                  <Box sx={{ width: 16, height: 16 }} /> // Placeholder to maintain alignment
                )}
                
                {/* Type icon */}
                <Box sx={{ 
                  display: 'flex',
                  alignItems: 'center',
                  color: level > 0 ? alpha(theme.palette.text.secondary, 0.8) : theme.palette.text.primary,
                  fontSize: '1rem'
                }}>
                  {getTypeIcon(workItem.type)}
                </Box>
              </Box>
              
              {/* Work item content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: level === 0 ? 600 : 500,
                    color: level > 0 ? alpha(theme.palette.text.primary, 0.9) : theme.palette.text.primary,
                    lineHeight: 1.3,
                    fontSize: level > 0 ? '0.875rem' : '0.9rem',
                    wordBreak: 'break-word',
                  }}
                >
                  {workItem.title}
                </Typography>
                {workItem.description && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      mt: 0.5,
                      lineHeight: 1.2,
                      fontSize: '0.75rem',
                      opacity: level > 0 ? 0.8 : 1,
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      wordBreak: 'break-word',
                    }}
                  >
                    {workItem.description}
                  </Typography>
                )}
              </Box>
            </Box>
          </WorkItemPopup>
        </TableCell>
        
        <TableCell sx={{
          width: '11%',
          minWidth: '80px'
        }}>
          <Tooltip
            title={`Status: ${workItem.status.replace('_', ' ')} • Last updated: ${workItem.updated_at ? new Date(workItem.updated_at).toLocaleDateString() : 'Unknown'}`}
            arrow
          >
            <Chip
              label={workItem.status.replace('_', ' ')}
              size="small"
              color={getStatusColor(workItem.status)}
              sx={{
                textTransform: 'capitalize',
                fontWeight: 500,
                fontSize: '0.75rem',
                cursor: 'help',
              }}
            />
          </Tooltip>
        </TableCell>
        
        <TableCell sx={{
          width: '8%',
          minWidth: '100px'
        }}>
          <Tooltip
            title={`Priority: ${workItem.priority} • Complexity: ${workItem.complexity || 'Not set'}`}
            arrow
          >
            <Chip
              label={workItem.priority}
              size="small"
              color={getPriorityColor(workItem.priority)}
              variant="outlined"
              sx={{
                textTransform: 'capitalize',
                fontWeight: 500,
                fontSize: '0.75rem',
                cursor: 'help',
              }}
            />
          </Tooltip>
        </TableCell>
        
        <TableCell sx={{
          width: '13%',
          minWidth: '100px'
        }}>
          <Tooltip
            title={`Progress: ${getProgressValue()}% • Acceptance Criteria: ${workItem.acceptance_criteria?.length || 0} defined`}
            arrow
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120, cursor: 'help' }}>
              <LinearProgress
                variant="determinate"
                value={getProgressValue()}
                sx={{
                  flexGrow: 1,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                {getProgressValue()}%
              </Typography>
            </Box>
          </Tooltip>
        </TableCell>
        
        <TableCell sx={{
          width: '13%',
          minWidth: '100px'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => onEdit(workItem)}>
                <EditIcon sx={{ fontSize: '1rem' }} />
              </IconButton>
            </Tooltip>
            
            <IconButton size="small" onClick={handleMenuClick}>
              <MoreVertIcon sx={{ fontSize: '1rem' }} />
            </IconButton>
            
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <MenuItem onClick={() => { onViewHierarchy(workItem); handleMenuClose(); }}>
                <HierarchyIcon sx={{ mr: 1, fontSize: '1rem' }} />
                View Hierarchy
              </MenuItem>
              <MenuItem onClick={() => { onAddChild(workItem); handleMenuClose(); }}>
                <AddChildIcon sx={{ mr: 1, fontSize: '1rem' }} />
                Add Child Item
              </MenuItem>
              <MenuItem onClick={() => { onDelete(workItem); handleMenuClose(); }}>
                <DeleteIcon sx={{ mr: 1, fontSize: '1rem' }} />
                Delete
              </MenuItem>
            </Menu>
          </Box>
        </TableCell>
      </TableRow>
      
      {hasChildren && expanded && (
        <>
          {children?.map((child) => (
            <WorkItemRow
              key={child.id}
              workItem={child}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewHierarchy={onViewHierarchy}
              onAddChild={onAddChild}
              children={child.children}
            />
          ))}
        </>
      )}
    </>
  );
}

export function WorkItemsTab() {
  const theme = useTheme();
  const { searchWorkItems, createWorkItem, updateWorkItem, deleteWorkItem, getWorkItemHierarchy, reorderWorkItems, isInitializing, subscribeToEvents } = useJiveApi();
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkItem, setSelectedWorkItem] = useState<WorkItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [workItemToDelete, setWorkItemToDelete] = useState<WorkItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'success' | 'error' | 'warning' | 'info' });
  const [hierarchyDialogOpen, setHierarchyDialogOpen] = useState(false);
  const [hierarchyData, setHierarchyData] = useState<any>(null);
  const [currentFilter, setCurrentFilter] = useState<string>('all');
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const tableContainerRef = useRef<HTMLDivElement | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'task' as const,
    status: 'not_started' as const,
    priority: 'medium' as const,
    parent_id: '',
    context_tags: [] as string[],
    complexity: 'simple' as const,
    notes: '',
    acceptance_criteria: [] as string[]
  });

  // Drag and drop state
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draggedItem, setDraggedItem] = useState<WorkItem | null>(null);

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Handle scroll events to show/hide scroll-to-top button
  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = event.currentTarget.scrollTop;
    setShowScrollTop(scrollTop > 200);
  };

  // Scroll to top function
  const scrollToTop = () => {
    if (tableContainerRef.current) {
      tableContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  // Ref callback to capture table container element
  const tableContainerRefCallback = (element: HTMLDivElement | null) => {
    tableContainerRef.current = element;
  };

  const loadWorkItems = async () => {
    try {
      setLoading(true);
      const response = await searchWorkItems({ query: '', limit: 100 });
      
      if (!response) {
        setWorkItems([]);
        setError('No response from API');
        return;
      }
      
      // Handle the response structure properly
      if (response && response.results) {
        // Transform API WorkItems to frontend WorkItems
        const transformedItems = response.results.map((item: any) => ({
          ...item,
          type: item.item_type, // Map item_type to type for frontend compatibility
          children: [] // Initialize empty children array
        }));
        setWorkItems(transformedItems);
      } else if (response && Array.isArray(response)) {
        // Fallback if response is directly an array
        const transformedItems = response.map((item: any) => ({
          ...item,
          type: item.item_type, // Map item_type to type for frontend compatibility
          children: [] // Initialize empty children array
        }));
        setWorkItems(transformedItems);
      } else {
        setWorkItems([]);
      }
    } catch (error) {
      console.error('Error loading work items:', error);
      setWorkItems([]);
      setError('Failed to load work items: ' + (error instanceof Error ? error.message : String(error)));
    } finally {
      setLoading(false);
    }
  };

  // Periodic refresh functionality - disabled since we use WebSocket for real-time updates
  const { manualRefresh, isRefreshing } = usePeriodicRefresh({
    refreshFunction: loadWorkItems,
    enabled: false, // Disabled - WebSocket handles real-time updates
    dependencies: [searchQuery] // Restart refresh when search query changes
  });

  useEffect(() => {
    // Only load work items after the API client is initialized
    if (!isInitializing) {
      loadWorkItems();
    }
  }, [isInitializing]);

  // Subscribe to WebSocket work item updates for real-time updates
  useEffect(() => {
    if (!subscribeToEvents) return;

    const unsubscribe = subscribeToEvents('work_item_update', (message) => {
      console.log('Received work item update via WebSocket:', message);
      // Refresh work items when any work item is updated
      loadWorkItems();
    });

    return unsubscribe;
  }, [subscribeToEvents, loadWorkItems]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadWorkItems();
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      console.log('Search query:', searchQuery);
      const response = await searchWorkItems({ query: searchQuery, limit: 100 });
      console.log('Search response:', response);
      
      // Handle the response structure properly
      if (response && response.success && response.results) {
        const transformedItems = Array.isArray(response.results) 
          ? response.results.map((item: any) => ({ ...item, type: item.item_type, children: [] }))
          : [];
        setWorkItems(transformedItems);
        if (response.results.length === 0) {
          setSnackbar({
            open: true,
            message: `No work items found for "${searchQuery}"`,
            severity: 'info'
          });
        }
      } else if (response && response.results) {
        // Handle case where success field might be missing
        const transformedItems = Array.isArray(response.results) 
          ? response.results.map((item: any) => ({ ...item, type: item.item_type, children: [] }))
          : [];
        setWorkItems(transformedItems);
      } else if (response && Array.isArray(response)) {
        // Fallback if response is directly an array
        const transformedItems = response.map((item: any) => ({ ...item, type: item.item_type, children: [] }));
        setWorkItems(transformedItems);
      } else {
        console.warn('WorkItemsTab - Unexpected search response structure:', response);
        setWorkItems([]);
        setSnackbar({
          open: true,
          message: 'Search returned unexpected results',
          severity: 'warning'
        });
      }
    } catch (error) {
      console.error('Search failed:', error);
      setWorkItems([]);
      setSnackbar({
        open: true,
        message: `Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (workItem: WorkItem) => {
    setSelectedWorkItem(workItem);
    setModalOpen(true);
  };

  const handleCreate = () => {
    setSelectedWorkItem(null);
    setModalOpen(true);
  };

  const handleDelete = (workItem: WorkItem) => {
    setWorkItemToDelete(workItem);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!workItemToDelete) return;
    
    try {
      await deleteWorkItem(workItemToDelete.id);
      await loadWorkItems(); // Refresh the list
      setDeleteDialogOpen(false);
      setWorkItemToDelete(null);
      console.log('Work item deleted successfully:', workItemToDelete.id);
    } catch (error) {
      console.error('Failed to delete work item:', error);
      // TODO: Show error notification
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setWorkItemToDelete(null);
  };



  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedWorkItem(null);
  };

  const handleSave = async (workItemData: Partial<WorkItem>) => {
    try {
      if (selectedWorkItem) {
        // Update existing work item
        const response = await updateWorkItem(selectedWorkItem.id, workItemData as any);
        console.log('Work item updated successfully:', response);
      } else {
        // Create new work item
        const response = await createWorkItem(workItemData as any);
        console.log('Work item created successfully:', response);
      }
      await loadWorkItems(); // Refresh the list
    } catch (error) {
      console.error('Failed to save work item:', error);
      throw error; // Re-throw to let modal handle the error
    }
  };

  const handleFilterClick = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterClose = () => {
    setFilterAnchorEl(null);
  };

  const handleFilterSelect = (filter: string) => {
    setCurrentFilter(filter);
    setFilterAnchorEl(null);
  };

  // Filter work items based on current filter
  const getFilteredWorkItems = (items: WorkItem[]) => {
    if (currentFilter === 'all') {
      return items;
    }
    return items.filter(item => {
      switch (currentFilter) {
        case 'in_progress':
          return item.status === 'in_progress';
        case 'completed':
          return item.status === 'completed';
        case 'blocked':
          return item.status === 'blocked';
        case 'not_started':
          return item.status === 'not_started';
        default:
          return true;
      }
    });
  };

  // Group work items by hierarchy
  const organizeHierarchy = (items: WorkItem[]) => {
    // Create a map for quick lookup
    const itemMap = new Map(items.map(item => [item.id, { ...item, children: [] as WorkItem[] }]));
    const topLevelItems: (WorkItem & { children: WorkItem[] })[] = [];
    
    // Build the hierarchy
    items.forEach(item => {
      const itemWithChildren = itemMap.get(item.id)!;
      
      if (item.parent_id) {
        // This item has a parent, add it to parent's children
        const parent = itemMap.get(item.parent_id);
        if (parent) {
          parent.children.push(itemWithChildren);
        } else {
          // Parent not found, treat as top-level
          topLevelItems.push(itemWithChildren);
        }
      } else {
        // This is a top-level item
        topLevelItems.push(itemWithChildren);
      }
    });
    
    // Sort function by order_index
    const sortByOrderIndex = (a: WorkItem, b: WorkItem) => {
      return (a.order_index || 0) - (b.order_index || 0);
    };
    
    // Sort top-level items by order_index
    topLevelItems.sort(sortByOrderIndex);
    
    // Recursively organize and sort children
    const organizeChildren = (item: WorkItem & { children: WorkItem[] }) => {
      // Sort children by order_index
      item.children.sort(sortByOrderIndex);
      
      item.children.forEach(child => {
        organizeChildren(child as WorkItem & { children: WorkItem[] });
      });
    };
    
    topLevelItems.forEach(organizeChildren);
    
    return topLevelItems;
  };

  // Flatten hierarchical structure back to a flat array
  const flattenHierarchy = (hierarchicalItems: WorkItem[]): WorkItem[] => {
    const result: WorkItem[] = [];
    
    const flatten = (items: WorkItem[]) => {
      items.forEach(item => {
        // Add the item without the children property
        const { children, ...itemWithoutChildren } = item;
        result.push(itemWithoutChildren);
        
        // Recursively flatten children
        if (children && children.length > 0) {
          flatten(children);
        }
      });
    };
    
    flatten(hierarchicalItems);
    return result;
  };

  // Get all descendants of a work item recursively
  const getAllDescendants = (parentId: string, items: WorkItem[]): WorkItem[] => {
    const directChildren = items.filter(item => item.parent_id === parentId);
    const allDescendants = [...directChildren];
    
    directChildren.forEach(child => {
      const grandChildren = getAllDescendants(child.id, items);
      allDescendants.push(...grandChildren);
    });
    
    return allDescendants;
  };

  // Load hierarchy for a specific work item
  const loadWorkItemHierarchy = async (workItemId: string) => {
    try {
      const response = await getWorkItemHierarchy(workItemId, {
        relationship_type: 'full_hierarchy',
        max_depth: 5,
        include_completed: true,
        include_metadata: true
      });
      
      if (response && response.data) {
        setHierarchyData(response.data);
        setHierarchyDialogOpen(true);
      }
    } catch (error) {
      console.error('Failed to load hierarchy:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load hierarchy',
        severity: 'error'
      });
    }
  };

  // Handle viewing hierarchy for a work item
  const handleViewHierarchy = (workItem: WorkItem) => {
    loadWorkItemHierarchy(workItem.id);
  };

  // Handle adding a child work item
  const handleAddChild = (parentWorkItem: WorkItem) => {
    setSelectedWorkItem(null);
    setFormData({
      title: '',
      description: '',
      type: 'task',
      status: 'not_started',
      priority: 'medium',
      parent_id: parentWorkItem.id, // Set the parent ID
      context_tags: [],
      complexity: 'simple',
      notes: '',
      acceptance_criteria: []
    });
    setModalOpen(true);
  };

  const getChildren = (parentId: string) => {
    return workItems.filter(item => item.parent_id === parentId);
  };

  // Drag and drop handlers
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    setActiveId(active.id as string);
    
    // Find the dragged item
    const item = workItems.find(item => item.id === active.id);
    setDraggedItem(item || null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    
    setActiveId(null);
    setDraggedItem(null);
    
    if (!over || active.id === over.id) {
      return;
    }

    // Find the active and over items
    const activeItem = workItems.find(item => item.id === active.id);
    const overItem = workItems.find(item => item.id === over.id);
    
    if (!activeItem || !overItem) {
      return;
    }

    // For now, just reorder within the same parent
    if (activeItem.parent_id === overItem.parent_id) {
      // Set reordering flag to force sequence recalculation
      setIsReordering(true);
      
      const siblings = workItems.filter(item => item.parent_id === activeItem.parent_id);
      const oldIndex = siblings.findIndex(item => item.id === active.id);
      const newIndex = siblings.findIndex(item => item.id === over.id);
      
      if (oldIndex !== newIndex) {
        const reorderedSiblings = arrayMove(siblings, oldIndex, newIndex);
        
        // Update the work items array with new order indices
        const updatedWorkItems = workItems.map(item => {
          const reorderedItem = reorderedSiblings.find(sibling => sibling.id === item.id);
          if (reorderedItem) {
            return { ...item, order_index: reorderedSiblings.indexOf(reorderedItem) };
          }
          return item;
        });
        
        // Apply sequence numbers to the updated items for immediate display
        // Force recalculation to show new positions immediately
        const organizedItems = organizeHierarchy(updatedWorkItems);
        
        // Clear all sequence_number values to force complete recalculation
        const clearSequenceNumbers = (items: WorkItem[]): WorkItem[] => {
          return items.map(item => {
            const clearedItem = { ...item, children: item.children || [] };
            delete clearedItem.sequence_number;
            if (clearedItem.children && clearedItem.children.length > 0) {
              clearedItem.children = clearSequenceNumbers(clearedItem.children);
            }
            return clearedItem;
          });
        };
        
        const itemsWithClearedSequences = clearSequenceNumbers(organizedItems);
        const itemsWithSequences = addSequenceNumbers(itemsWithClearedSequences, '', true);
        const flattenedItems = flattenHierarchy(itemsWithSequences);
        
        setWorkItems(flattenedItems);
        
        // Call the reorder API endpoint
        try {
          await reorderWorkItems(
            reorderedSiblings.map(item => item.id),
            activeItem.parent_id || undefined
          );
          
          console.log('Successfully reordered items:', {
            activeId: active.id,
            overId: over.id,
            oldIndex,
            newIndex
          });
        } catch (error) {
          console.error('Failed to reorder items:', error);
          // Revert the local state on error
          setWorkItems(workItems);
        } finally {
          setIsReordering(false);
        }
      }
    }
  };

  // Generate sequence numbers for hierarchical display
  const generateSequenceNumber = (workItem: WorkItem, parentSequence: string = '', siblingIndex: number = 0, forceRecalculate: boolean = false): string => {
    // Use stored sequence_number from MCP server to maintain consistency with AI agents
    // unless we're forcing recalculation (e.g., during drag-and-drop)
    if (workItem.sequence_number && !forceRecalculate) {
      return workItem.sequence_number;
    }
    
    // Generate sequence based on position
    if (parentSequence) {
      return `${parentSequence}.${siblingIndex + 1}`;
    } else {
      return `${siblingIndex + 1}`;
    }
  };

  // Add sequence numbers to work items for display
  const addSequenceNumbers = (items: WorkItem[], parentSequence: string = '', forceRecalculate: boolean = false): WorkItem[] => {
    return items.map((item, index) => {
      const sequenceNumber = generateSequenceNumber(item, parentSequence, index, forceRecalculate);
      const itemWithSequence = { ...item, displaySequence: sequenceNumber, children: item.children || [] };
      
      if (item.children && item.children.length > 0) {
        itemWithSequence.children = addSequenceNumbers(item.children, sequenceNumber, forceRecalculate);
      }
      
      return itemWithSequence;
    });
  };

  const filteredWorkItems = getFilteredWorkItems(workItems);
  console.log('workItems:', workItems.length, 'filteredWorkItems:', filteredWorkItems.length, 'currentFilter:', currentFilter);
  const topLevelItems = addSequenceNumbers(organizeHierarchy(filteredWorkItems), '', isReordering);
  console.log('topLevelItems:', topLevelItems.length);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <Paper
        elevation={0}
        sx={{
          borderBottom: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Toolbar sx={{ gap: 2, minHeight: '64px !important' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            New Work Item
          </Button>
          
          <TextField
            placeholder="Search work items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            size="small"
            sx={{ minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSearchQuery('');
                      loadWorkItems();
                    }}
                    sx={{ color: 'text.secondary' }}
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          
          <Button
            variant="outlined"
            onClick={handleSearch}
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            Search
          </Button>
          
          <Tooltip title="Refresh work items">
            <IconButton
              onClick={manualRefresh}
              disabled={isRefreshing}
              sx={{ 
                color: 'text.secondary',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  color: 'primary.main'
                }
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant={currentFilter !== 'all' ? 'contained' : 'outlined'}
            startIcon={<FilterIcon />}
            onClick={handleFilterClick}
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            Filter {currentFilter !== 'all' && `(${currentFilter.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())})`}
          </Button>
          
          <Menu
            anchorEl={filterAnchorEl}
            open={Boolean(filterAnchorEl)}
            onClose={handleFilterClose}
          >
            <MenuItem onClick={() => handleFilterSelect('all')}>All Items</MenuItem>
            <MenuItem onClick={() => handleFilterSelect('not_started')}>Not Started</MenuItem>
            <MenuItem onClick={() => handleFilterSelect('in_progress')}>In Progress</MenuItem>
            <MenuItem onClick={() => handleFilterSelect('completed')}>Completed</MenuItem>
            <MenuItem onClick={() => handleFilterSelect('blocked')}>Blocked</MenuItem>
          </Menu>
        </Toolbar>
      </Paper>

      {/* Work Items Table */}
      <Box 
        sx={{ 
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0, // Important for flex child to shrink
        }}
      >
        <TableContainer 
          component={Paper} 
          elevation={0}
          ref={tableContainerRefCallback}
          onScroll={handleScroll}
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            scrollBehavior: 'smooth',
            '&::-webkit-scrollbar': {
              width: '8px',
              height: '8px'
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: theme.palette.action.hover,
              borderRadius: '4px'
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: theme.palette.action.disabled,
              borderRadius: '4px',
              '&:hover': {
                backgroundColor: theme.palette.action.selected
              }
            }
          }}
        >
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '10%',
                    minWidth: '70px'
                  }}
                >
                  #
                </TableCell>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '45%',
                    minWidth: '350px'
                  }}
                >
                  Work Item
                </TableCell>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '13%',
                    minWidth: '90px'
                  }}
                >
                  Status
                </TableCell>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '11%',
                    minWidth: '80px'
                  }}
                >
                  Priority
                </TableCell>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '13%',
                    minWidth: '100px'
                  }}
                >
                  Progress
                </TableCell>
                <TableCell 
                  sx={{ 
                    fontWeight: 600, 
                    backgroundColor: theme.palette.background.paper,
                    width: '8%',
                    minWidth: '100px'
                  }}
                >
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary">Loading work items...</Typography>
                  </TableCell>
                </TableRow>
              ) : topLevelItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary">No work items found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                <SortableContext
                  items={topLevelItems.map(item => item.id)}
                  strategy={verticalListSortingStrategy}
                >
                  {topLevelItems.map((workItem) => (
                    <SortableWorkItemRow
                      key={workItem.id}
                      workItem={workItem}
                      level={0}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onViewHierarchy={handleViewHierarchy}
                      onAddChild={handleAddChild}
                      children={workItem.children}
                      isDragging={activeId === workItem.id}
                    />
                  ))}
                </SortableContext>
              )}
            </TableBody>
          </Table>
          </DndContext>
        </TableContainer>
      </Box>

      {/* Work Item Modal */}
      <WorkItemModal
        open={modalOpen}
        onClose={handleModalClose}
        onSave={handleSave}
        workItem={selectedWorkItem}
        parentId={formData.parent_id || undefined}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Delete Work Item
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete "{workItemToDelete?.title}"? This action cannot be undone.
            {workItemToDelete?.type && (
              <Box component="span" sx={{ display: 'block', mt: 1, fontWeight: 500 }}>
                Type: {workItemToDelete.type.charAt(0).toUpperCase() + workItemToDelete.type.slice(1)}
              </Box>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Hierarchy Dialog */}
      <Dialog
        open={hierarchyDialogOpen}
        onClose={() => setHierarchyDialogOpen(false)}
        aria-labelledby="hierarchy-dialog-title"
        maxWidth="md"
        fullWidth
      >
        <DialogTitle id="hierarchy-dialog-title">
          Work Item Hierarchy
        </DialogTitle>
        <DialogContent>
          <DialogContentText component="div">
            {hierarchyData ? (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Hierarchy Information
                </Typography>
                <pre style={{ 
                  backgroundColor: '#f5f5f5', 
                  padding: '16px', 
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '12px',
                  fontFamily: 'monospace'
                }}>
                  {JSON.stringify(hierarchyData, null, 2)}
                </pre>
              </Box>
            ) : (
              <Typography>No hierarchy data available.</Typography>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHierarchyDialogOpen(false)} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Scroll to Top Button */}
      <Zoom in={showScrollTop}>
        <Fab
          color="primary"
          size="small"
          onClick={scrollToTop}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000,
            backgroundColor: theme.palette.primary.main,
            '&:hover': {
              backgroundColor: theme.palette.primary.dark,
            },
          }}
        >
          <ScrollTopIcon />
        </Fab>
      </Zoom>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
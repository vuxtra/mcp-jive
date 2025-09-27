'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  Badge,
  Divider,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import { useNamespace } from '../../contexts/NamespaceContext';
import type { WorkItem } from '../../types';

interface WorkItemListProps {
  parentId?: string;
  onEdit?: (workItem: WorkItem) => void;
  onDelete?: (workItem: WorkItem) => void;
  onView?: (workItem: WorkItem) => void;
  onCreate?: () => void;
  showActions?: boolean;
  compact?: boolean;
}

interface FilterState {
  search: string;
  type: string;
  status: string;
  priority: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const WORK_ITEM_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'initiative', label: 'Initiative' },
  { value: 'epic', label: 'Epic' },
  { value: 'feature', label: 'Feature' },
  { value: 'story', label: 'Story' },
  { value: 'task', label: 'Task' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'not_started', label: 'Not Started' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'cancelled', label: 'Cancelled' },
];

const PRIORITY_OPTIONS = [
  { value: '', label: 'All Priorities' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const SORT_OPTIONS = [
  { value: 'title', label: 'Title' },
  { value: 'priority', label: 'Priority' },
  { value: 'status', label: 'Status' },
  { value: 'created_at', label: 'Created Date' },
  { value: 'updated_at', label: 'Updated Date' },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'not_started': return 'default';
    case 'in_progress': return 'primary';
    case 'completed': return 'success';
    case 'blocked': return 'error';
    case 'cancelled': return 'secondary';
    default: return 'default';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'error';
    case 'critical': return 'error';
    default: return 'default';
  }
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'initiative': return '🎯';
    case 'epic': return '📚';
    case 'feature': return '⭐';
    case 'story': return '📖';
    case 'task': return '✅';
    default: return '📋';
  }
};

export const WorkItemList: React.FC<WorkItemListProps> = ({
  parentId,
  onEdit,
  onDelete,
  onView,
  onCreate,
  showActions = true,
  compact = false,
}) => {
  const { searchWorkItems, isLoading, error } = useJiveApiContext();
  const { currentNamespace } = useNamespace();

  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<WorkItem[]>([]);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedItem, setSelectedItem] = useState<WorkItem | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    type: '',
    status: '',
    priority: '',
    sortBy: 'updated_at',
    sortOrder: 'desc',
  });

  // Load work items - reload when namespace or parentId changes
  useEffect(() => {
    loadWorkItems();
  }, [loadWorkItems]);

  // Listen for namespace change events
  useEffect(() => {
    const handleNamespaceChange = () => {
      loadWorkItems();
    };

    window.addEventListener('namespace-changed', handleNamespaceChange);
    return () => {
      window.removeEventListener('namespace-changed', handleNamespaceChange);
    };
  }, []);

  // Apply filters when work items or filters change
  useEffect(() => {
    applyFilters();
  }, [workItems, filters]);

  const loadWorkItems = useCallback(async () => {
    try {
      let query = '*'; // Search all items
      if (parentId) {
        query = `parent_id:${parentId}`;
      }
      
      const response = await searchWorkItems({
        query,
        search_type: 'hybrid',
        limit: 100,
      });
      
      // Handle the response structure properly
      if (response && response.results) {
        setWorkItems(response.results);
      } else if (response && Array.isArray(response)) {
        // Fallback if response is directly an array
        setWorkItems(response);
      } else {
        console.warn('Unexpected response structure:', response);
        setWorkItems([]);
      }
    } catch (err) {
      console.error('Failed to load work items:', err);
      setWorkItems([]);
    }
  }, [searchWorkItems, parentId, currentNamespace]);

  const applyFilters = () => {
    let filtered = [...workItems];

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(item => 
        item.title.toLowerCase().includes(searchLower) ||
        item.description.toLowerCase().includes(searchLower)
      );
    }

    // Apply type filter
    if (filters.type) {
      filtered = filtered.filter(item => item.item_type === filters.type);
    }

    // Apply status filter
    if (filters.status) {
      filtered = filtered.filter(item => item.status === filters.status);
    }

    // Apply priority filter
    if (filters.priority) {
      filtered = filtered.filter(item => item.priority === filters.priority);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[filters.sortBy as keyof WorkItem];
      let bValue = b[filters.sortBy as keyof WorkItem];
      
      // Handle priority sorting with custom order
      if (filters.sortBy === 'priority') {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        aValue = priorityOrder[a.priority as keyof typeof priorityOrder] || 0;
        bValue = priorityOrder[b.priority as keyof typeof priorityOrder] || 0;
      }
      
      // Handle undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return filters.sortOrder === 'asc' ? 1 : -1;
      if (bValue == null) return filters.sortOrder === 'asc' ? -1 : 1;
      
      if (aValue < bValue) return filters.sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return filters.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    setFilteredItems(filtered);
  };

  const handleFilterChange = (field: keyof FilterState, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, item: WorkItem) => {
    setAnchorEl(event.currentTarget);
    setSelectedItem(item);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedItem(null);
  };

  const handleAction = (action: string) => {
    if (!selectedItem) return;
    
    switch (action) {
      case 'view':
        onView?.(selectedItem);
        break;
      case 'edit':
        onEdit?.(selectedItem);
        break;
      case 'delete':
        onDelete?.(selectedItem);
        break;
    }
    
    handleMenuClose();
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      type: '',
      status: '',
      priority: '',
      sortBy: 'updated_at',
      sortOrder: 'desc',
    });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load work items: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header and Controls */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          Work Items
          <Badge badgeContent={filteredItems.length} color="primary" sx={{ ml: 2 }} />
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
            size="small"
          >
            Filters
          </Button>
          
          {onCreate && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={onCreate}
              size="small"
            >
              Create
            </Button>
          )}
        </Box>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, alignItems: 'center' }}>
              <Box sx={{ flex: 1, minWidth: { xs: '100%', md: '200px' } }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Search"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Box>
              
              <Box sx={{ minWidth: { xs: '100%', md: '150px' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={filters.type}
                    label="Type"
                    onChange={(e) => handleFilterChange('type', e.target.value)}
                  >
                    {WORK_ITEM_TYPES.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <Box sx={{ minWidth: { xs: '100%', md: '150px' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status}
                    label="Status"
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    {STATUS_OPTIONS.map((status) => (
                      <MenuItem key={status.value} value={status.value}>
                        {status.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <Box sx={{ minWidth: { xs: '100%', md: '150px' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={filters.priority}
                    label="Priority"
                    onChange={(e) => handleFilterChange('priority', e.target.value)}
                  >
                    {PRIORITY_OPTIONS.map((priority) => (
                      <MenuItem key={priority.value} value={priority.value}>
                        {priority.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <Box sx={{ minWidth: { xs: '100%', md: '150px' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={filters.sortBy}
                    label="Sort By"
                    onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                  >
                    {SORT_OPTIONS.map((sort) => (
                      <MenuItem key={sort.value} value={sort.value}>
                        {sort.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <Box sx={{ minWidth: { xs: '100%', md: '80px' } }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleFilterChange('sortOrder', filters.sortOrder === 'asc' ? 'desc' : 'asc')}
                  startIcon={<SortIcon />}
                >
                  {filters.sortOrder === 'asc' ? '↑' : '↓'}
                </Button>
              </Box>
            </Box>
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button size="small" onClick={resetFilters}>
                Reset Filters
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Work Items List */}
      {filteredItems.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No work items found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {workItems.length === 0 
                ? 'Create your first work item to get started'
                : 'Try adjusting your filters'
              }
            </Typography>
            {onCreate && workItems.length === 0 && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={onCreate}
                sx={{ mt: 2 }}
              >
                Create Work Item
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: compact ? 'repeat(auto-fit, minmax(400px, 1fr))' : '1fr', gap: 2 }}>
          {filteredItems.map((item) => (
            <Box key={item.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6" component="span">
                        {getTypeIcon(item.item_type)}
                      </Typography>
                      <Typography variant="h6" sx={{ flexGrow: 1 }}>
                        {item.title}
                      </Typography>
                    </Box>
                    
                    {showActions && (
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, item)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    )}
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {item.description}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    <Chip
                      label={item.item_type}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={item.status.replace('_', ' ')}
                      size="small"
                      color={getStatusColor(item.status) as any}
                    />
                    <Chip
                      label={item.priority}
                      size="small"
                      color={getPriorityColor(item.priority) as any}
                      variant="outlined"
                    />
                  </Box>
                  
                  {item.context_tags && item.context_tags.length > 0 && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {item.context_tags.map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {onView && (
          <MenuItem onClick={() => handleAction('view')}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
        )}
        
        {onEdit && (
          <MenuItem onClick={() => handleAction('edit')}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
        )}
        
        <Divider />
        
        {onDelete && (
          <MenuItem onClick={() => handleAction('delete')} sx={{ color: 'error.main' }}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        )}
      </Menu>
    </Box>
  );
};

export default WorkItemList;
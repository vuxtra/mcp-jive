'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,

  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  AccountTree as HierarchyIcon,
  Link as LinkIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Flag as FlagIcon,
} from '@mui/icons-material';
import { useJiveApi } from '../../hooks/useJiveApi';
import type { WorkItem } from '../../types';

interface WorkItemDetailsProps {
  workItemId: string;
  onEdit?: (workItem: WorkItem) => void;
  onDelete?: (workItem: WorkItem) => void;
  onClose?: () => void;
  showActions?: boolean;
}

interface HierarchyData {
  children?: WorkItem[];
  parents?: WorkItem[];
  dependencies?: WorkItem[];
  dependents?: WorkItem[];
}

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

const calculateProgress = (workItem: WorkItem, children?: WorkItem[]): number => {
  if (!children || children.length === 0) {
    return workItem.status === 'completed' ? 100 : workItem.status === 'in_progress' ? 50 : 0;
  }
  
  const completedChildren = children.filter(child => child.status === 'completed').length;
  return Math.round((completedChildren / children.length) * 100);
};

export const WorkItemDetails: React.FC<WorkItemDetailsProps> = ({
  workItemId,
  onEdit,
  onDelete,
  onClose,
  showActions = true,
}) => {
  const { getWorkItem, getHierarchy, isLoading, error } = useJiveApi();
  
  const [workItem, setWorkItem] = useState<WorkItem | null>(null);
  const [hierarchy, setHierarchy] = useState<HierarchyData>({});
  const [loadingHierarchy, setLoadingHierarchy] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    details: true,
    acceptance: true,
    hierarchy: false,
    dependencies: false,
  });

  useEffect(() => {
    loadWorkItem();
  }, [workItemId]);

  useEffect(() => {
    if (workItem) {
      loadHierarchy();
    }
  }, [workItem]);

  const loadWorkItem = async () => {
    try {
      const response = await getWorkItem({
        work_item_id: workItemId,
        include_children: false,
        include_metadata: true,
      });
      
      if (response.success && response.data) {
        setWorkItem(response.data);
      }
    } catch (err) {
      console.error('Failed to load work item:', err);
    }
  };

  const loadHierarchy = async () => {
    if (!workItem) return;
    
    setLoadingHierarchy(true);
    try {
      // Load children
      const childrenResponse = await getHierarchy({
        work_item_id: workItem.id,
        relationship_type: 'children',
        include_metadata: true,
      });
      
      // Load parents
      const parentsResponse = await getHierarchy({
        work_item_id: workItem.id,
        relationship_type: 'parents',
        include_metadata: true,
      });
      
      // Load dependencies
      const dependenciesResponse = await getHierarchy({
        work_item_id: workItem.id,
        relationship_type: 'dependencies',
        include_metadata: true,
      });
      
      // Load dependents
      const dependentsResponse = await getHierarchy({
        work_item_id: workItem.id,
        relationship_type: 'dependents',
        include_metadata: true,
      });
      
      setHierarchy({
        children: childrenResponse.success ? childrenResponse.data?.relationships || [] : [],
        parents: parentsResponse.success ? parentsResponse.data?.relationships || [] : [],
        dependencies: dependenciesResponse.success ? dependenciesResponse.data?.relationships || [] : [],
        dependents: dependentsResponse.success ? dependentsResponse.data?.relationships || [] : [],
      });
    } catch (err) {
      console.error('Failed to load hierarchy:', err);
    } finally {
      setLoadingHierarchy(false);
    }
  };

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !workItem) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load work item: {error || 'Work item not found'}
      </Alert>
    );
  }

  const progress = calculateProgress(workItem, hierarchy.children);

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
              <Typography variant="h4" component="span">
                {getTypeIcon(workItem.item_type)}
              </Typography>
              <Box>
                <Typography variant="h5" gutterBottom>
                  {workItem.title}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    label={workItem.item_type}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={workItem.status.replace('_', ' ')}
                    size="small"
                    color={getStatusColor(workItem.status) as any}
                  />
                  <Chip
                    label={workItem.priority}
                    size="small"
                    color={getPriorityColor(workItem.priority) as any}
                    variant="outlined"
                  />
                  {workItem.complexity && (
                    <Chip
                      label={`${workItem.complexity} complexity`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>
            </Box>
            
            {showActions && (
              <Box sx={{ display: 'flex', gap: 1 }}>
                {onEdit && (
                  <Tooltip title="Edit">
                    <IconButton onClick={() => onEdit(workItem)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                )}

                {onDelete && (
                  <Tooltip title="Delete">
                    <IconButton onClick={() => onDelete(workItem)} color="error">
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            )}
          </Box>
          
          {/* Progress Bar */}
          {hierarchy.children && hierarchy.children.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Progress
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {progress}%
                </Typography>
              </Box>
              <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4 }} />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Details Section */}
      <Accordion 
        expanded={expandedSections.details} 
        onChange={() => handleSectionToggle('details')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Details</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="body1" paragraph>
                {workItem.description}
              </Typography>
            </Grid>
            
            {workItem.notes && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Notes
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2">
                    {workItem.notes}
                  </Typography>
                </Paper>
              </Grid>
            )}
            
            {workItem.context_tags && workItem.context_tags.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Context Tags
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {workItem.context_tags.map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Timeline
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Created: {formatDate(workItem.created_at)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Updated: {formatDate(workItem.updated_at)}
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <FlagIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Properties
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ID: {workItem.id}
              </Typography>
              {workItem.parent_id && (
                <Typography variant="body2" color="text.secondary">
                  Parent ID: {workItem.parent_id}
                </Typography>
              )}
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Acceptance Criteria */}
      {workItem.acceptance_criteria && workItem.acceptance_criteria.length > 0 && (
        <Accordion 
          expanded={expandedSections.acceptance} 
          onChange={() => handleSectionToggle('acceptance')}
          sx={{ mb: 2 }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Acceptance Criteria</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {workItem.acceptance_criteria.map((criteria, index) => (
                <ListItem key={index} sx={{ pl: 0 }}>
                  <ListItemIcon>
                    {workItem.status === 'completed' ? (
                      <CheckCircleIcon color="success" />
                    ) : (
                      <RadioButtonUncheckedIcon color="disabled" />
                    )}
                  </ListItemIcon>
                  <ListItemText primary={criteria} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Hierarchy */}
      <Accordion 
        expanded={expandedSections.hierarchy} 
        onChange={() => handleSectionToggle('hierarchy')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            <HierarchyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Hierarchy
          </Typography>
          {loadingHierarchy && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {/* Parents */}
            {hierarchy.parents && hierarchy.parents.length > 0 && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Parent Items
                </Typography>
                <List dense>
                  {hierarchy.parents.map((parent) => (
                    <ListItem key={parent.id} sx={{ pl: 0 }}>
                      <ListItemIcon>
                        <Typography variant="body2">
                          {getTypeIcon(parent.item_type)}
                        </Typography>
                      </ListItemIcon>
                      <ListItemText 
                        primary={parent.title}
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                            <Chip
                              label={parent.status.replace('_', ' ')}
                              size="small"
                              color={getStatusColor(parent.status) as any}
                            />
                            <Chip
                              label={parent.priority}
                              size="small"
                              color={getPriorityColor(parent.priority) as any}
                              variant="outlined"
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
            
            {/* Children */}
            {hierarchy.children && hierarchy.children.length > 0 && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Child Items ({hierarchy.children.length})
                </Typography>
                <List dense>
                  {hierarchy.children.map((child) => (
                    <ListItem key={child.id} sx={{ pl: 0 }}>
                      <ListItemIcon>
                        <Typography variant="body2">
                          {getTypeIcon(child.item_type)}
                        </Typography>
                      </ListItemIcon>
                      <ListItemText 
                        primary={child.title}
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                            <Chip
                              label={child.status.replace('_', ' ')}
                              size="small"
                              color={getStatusColor(child.status) as any}
                            />
                            <Chip
                              label={child.priority}
                              size="small"
                              color={getPriorityColor(child.priority) as any}
                              variant="outlined"
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Dependencies */}
      {((hierarchy.dependencies && hierarchy.dependencies.length > 0) || 
        (hierarchy.dependents && hierarchy.dependents.length > 0)) && (
        <Accordion 
          expanded={expandedSections.dependencies} 
          onChange={() => handleSectionToggle('dependencies')}
          sx={{ mb: 2 }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">
              <LinkIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Dependencies
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              {/* Dependencies (blocks this) */}
              {hierarchy.dependencies && hierarchy.dependencies.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom color="error">
                    Blocked By ({hierarchy.dependencies.length})
                  </Typography>
                  <List dense>
                    {hierarchy.dependencies.map((dep) => (
                      <ListItem key={dep.id} sx={{ pl: 0 }}>
                        <ListItemIcon>
                          <Typography variant="body2">
                            {getTypeIcon(dep.item_type)}
                          </Typography>
                        </ListItemIcon>
                        <ListItemText 
                          primary={dep.title}
                          secondary={
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              <Chip
                                label={dep.status.replace('_', ' ')}
                                size="small"
                                color={getStatusColor(dep.status) as any}
                              />
                              <Chip
                                label={dep.priority}
                                size="small"
                                color={getPriorityColor(dep.priority) as any}
                                variant="outlined"
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}
              
              {/* Dependents (this blocks) */}
              {hierarchy.dependents && hierarchy.dependents.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom color="warning.main">
                    Blocking ({hierarchy.dependents.length})
                  </Typography>
                  <List dense>
                    {hierarchy.dependents.map((dep) => (
                      <ListItem key={dep.id} sx={{ pl: 0 }}>
                        <ListItemIcon>
                          <Typography variant="body2">
                            {getTypeIcon(dep.item_type)}
                          </Typography>
                        </ListItemIcon>
                        <ListItemText 
                          primary={dep.title}
                          secondary={
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              <Chip
                                label={dep.status.replace('_', ' ')}
                                size="small"
                                color={getStatusColor(dep.status) as any}
                              />
                              <Chip
                                label={dep.priority}
                                size="small"
                                color={getPriorityColor(dep.priority) as any}
                                variant="outlined"
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};

export default WorkItemDetails;
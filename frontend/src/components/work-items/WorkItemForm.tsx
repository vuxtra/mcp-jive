'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  Chip,
  FormHelperText,
  Autocomplete,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import type { WorkItem, CreateWorkItemRequest, UpdateWorkItemRequest } from '../../types';

interface WorkItemFormProps {
  workItem?: WorkItem;
  parentId?: string;
  onSubmit: (data: CreateWorkItemRequest | UpdateWorkItemRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}

const WORK_ITEM_TYPES = [
  { value: 'initiative', label: 'Initiative' },
  { value: 'epic', label: 'Epic' },
  { value: 'feature', label: 'Feature' },
  { value: 'story', label: 'Story' },
  { value: 'task', label: 'Task' },
] as const;

const STATUS_OPTIONS = [
  { value: 'not_started', label: 'Not Started' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'cancelled', label: 'Cancelled' },
] as const;

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
] as const;

const COMPLEXITY_OPTIONS = [
  { value: 'simple', label: 'Simple' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'complex', label: 'Complex' },
] as const;

export const WorkItemForm: React.FC<WorkItemFormProps> = ({
  workItem,
  parentId,
  onSubmit,
  onCancel,
  isLoading = false,
  mode,
}) => {
  const { error } = useJiveApiContext();
  
  // Form state
  const [formData, setFormData] = useState({
    type: workItem?.item_type || 'task',
    title: workItem?.title || '',
    description: workItem?.description || '',
    status: workItem?.status || 'not_started',
    priority: workItem?.priority || 'medium',
    complexity: workItem?.complexity || 'moderate',
    notes: workItem?.notes || '',
    context_tags: workItem?.context_tags || [],
    acceptance_criteria: workItem?.acceptance_criteria || [''],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [contextTagInput, setContextTagInput] = useState('');

  // Validation
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.acceptance_criteria.filter(criteria => criteria.trim()).length === 0) {
      newErrors.acceptance_criteria = 'At least one acceptance criteria is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const submitData = {
      ...formData,
      parent_id: parentId,
      acceptance_criteria: formData.acceptance_criteria.filter(criteria => criteria.trim()),
    };

    if (mode === 'edit' && workItem) {
      await onSubmit({ work_item_id: workItem.id, ...submitData });
    } else {
      await onSubmit(submitData);
    }
  };

  // Handle input changes
  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Handle acceptance criteria changes
  const handleAcceptanceCriteriaChange = (index: number, value: string) => {
    const newCriteria = [...formData.acceptance_criteria];
    newCriteria[index] = value;
    handleInputChange('acceptance_criteria', newCriteria);
  };

  const addAcceptanceCriteria = () => {
    handleInputChange('acceptance_criteria', [...formData.acceptance_criteria, '']);
  };

  const removeAcceptanceCriteria = (index: number) => {
    const newCriteria = formData.acceptance_criteria.filter((_, i) => i !== index);
    handleInputChange('acceptance_criteria', newCriteria);
  };

  // Handle context tags
  const handleAddContextTag = () => {
    if (contextTagInput.trim() && !formData.context_tags.includes(contextTagInput.trim())) {
      handleInputChange('context_tags', [...formData.context_tags, contextTagInput.trim()]);
      setContextTagInput('');
    }
  };

  const handleRemoveContextTag = (tagToRemove: string) => {
    handleInputChange('context_tags', formData.context_tags.filter(tag => tag !== tagToRemove));
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {mode === 'create' ? 'Create Work Item' : 'Edit Work Item'}
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Basic Information */}
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
              <Box sx={{ flex: 1 }}>
              <FormControl fullWidth error={!!errors.type}>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  label="Type"
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  disabled={mode === 'edit'}
                >
                  {WORK_ITEM_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.type && <FormHelperText>{errors.type}</FormHelperText>}
              </FormControl>
              </Box>

              <Box sx={{ flex: 1 }}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  label="Priority"
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                >
                  {PRIORITY_OPTIONS.map((priority) => (
                    <MenuItem key={priority.value} value={priority.value}>
                      {priority.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              </Box>
            </Box>

            <Box>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                error={!!errors.title}
                helperText={errors.title}
                required
              />
            </Box>

            <Box>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                error={!!errors.description}
                helperText={errors.description}
                multiline
                rows={4}
                required
              />
            </Box>

            {/* Status and Complexity */}
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
              <Box sx={{ flex: 1 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  label="Status"
                  onChange={(e) => handleInputChange('status', e.target.value)}
                >
                  {STATUS_OPTIONS.map((status) => (
                    <MenuItem key={status.value} value={status.value}>
                      {status.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              </Box>

              <Box sx={{ flex: 1 }}>
                <FormControl fullWidth>
                  <InputLabel>Complexity</InputLabel>
                  <Select
                    value={formData.complexity}
                    label="Complexity"
                    onChange={(e) => handleInputChange('complexity', e.target.value)}
                  >
                    {COMPLEXITY_OPTIONS.map((complexity) => (
                      <MenuItem key={complexity.value} value={complexity.value}>
                        {complexity.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </Box>

            {/* Context Tags */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Context Tags
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                {formData.context_tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleRemoveContextTag(tag)}
                    size="small"
                  />
                ))}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  size="small"
                  label="Add tag"
                  value={contextTagInput}
                  onChange={(e) => setContextTagInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddContextTag();
                    }
                  }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleAddContextTag}
                  startIcon={<AddIcon />}
                >
                  Add
                </Button>
              </Box>
            </Box>

            {/* Acceptance Criteria */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Acceptance Criteria *
              </Typography>
              {formData.acceptance_criteria.map((criteria, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <TextField
                    fullWidth
                    size="small"
                    label={`Criteria ${index + 1}`}
                    value={criteria}
                    onChange={(e) => handleAcceptanceCriteriaChange(index, e.target.value)}
                    error={!!errors.acceptance_criteria && !criteria.trim()}
                  />
                  {formData.acceptance_criteria.length > 1 && (
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      onClick={() => removeAcceptanceCriteria(index)}
                    >
                      Remove
                    </Button>
                  )}
                </Box>
              ))}
              <Button
                variant="outlined"
                size="small"
                onClick={addAcceptanceCriteria}
                startIcon={<AddIcon />}
                sx={{ mt: 1 }}
              >
                Add Criteria
              </Button>
              {errors.acceptance_criteria && (
                <FormHelperText error>{errors.acceptance_criteria}</FormHelperText>
              )}
            </Box>

            {/* Notes */}
            <Box>
              <TextField
                fullWidth
                label="Notes"
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                multiline
                rows={3}
                placeholder="Additional notes, constraints, or context..."
              />
            </Box>
          </Box>
        </Box>
      </CardContent>
      
      <Divider />
      
      <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
        <Button
          variant="outlined"
          onClick={onCancel}
          startIcon={<CancelIcon />}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
          disabled={isLoading}
        >
          {mode === 'create' ? 'Create' : 'Update'}
        </Button>
      </CardActions>
    </Card>
  );
};

export default WorkItemForm;
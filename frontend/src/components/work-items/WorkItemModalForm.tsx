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
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Stack,
  Paper,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Flag as FlagIcon,
  Speed as SpeedIcon,
  Label as LabelIcon,
  CheckCircle as CheckCircleIcon,
  Notes as NotesIcon,
} from '@mui/icons-material';
import { useJiveApiContext } from '../providers/JiveApiProvider';
import type { WorkItem, WorkItemType } from '../../types';

interface WorkItemModalFormProps {
  workItem?: WorkItem | null;
  parentId?: string;
  defaultType?: WorkItemType;
  onSave: (data: Partial<WorkItem>) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
  showActions?: boolean;
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

export const WorkItemModalForm: React.FC<WorkItemModalFormProps> = ({
  workItem,
  parentId,
  defaultType = 'task',
  onSave,
  onCancel,
  isSubmitting = false,
  showActions = true,
}) => {
  const { error } = useJiveApiContext();
  
  // Form state
  const [formData, setFormData] = useState({
    type: workItem?.item_type || defaultType,
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
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Title validation
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.trim().length < 3) {
      newErrors.title = 'Title must be at least 3 characters long';
    } else if (formData.title.trim().length > 200) {
      newErrors.title = 'Title must be less than 200 characters';
    }

    // Description validation
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters long';
    } else if (formData.description.trim().length > 2000) {
      newErrors.description = 'Description must be less than 2000 characters';
    }

    // Acceptance criteria validation
    if (formData.acceptance_criteria.length === 0) {
      newErrors.acceptance_criteria = 'At least one acceptance criteria is required';
    } else {
      const validCriteria = formData.acceptance_criteria.filter(criteria => criteria.trim().length > 0);
      if (validCriteria.length === 0) {
        newErrors.acceptance_criteria = 'At least one acceptance criteria must have content';
      } else {
        // Check individual criteria length
        const invalidCriteria = formData.acceptance_criteria.some(criteria => 
          criteria.trim().length > 0 && criteria.trim().length < 5
        );
        if (invalidCriteria) {
          newErrors.acceptance_criteria = 'Each acceptance criteria must be at least 5 characters long';
        }
      }
    }

    // Context tags validation
    if (formData.context_tags.length > 10) {
      newErrors.context_tags = 'Maximum 10 context tags allowed';
    }

    // Notes validation
    if (formData.notes && formData.notes.length > 1000) {
      newErrors.notes = 'Notes must be less than 1000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Real-time validation for specific fields
  const validateField = (fieldName: string, value: any): string => {
    switch (fieldName) {
      case 'title':
        if (!value.trim()) return 'Title is required';
        if (value.trim().length < 3) return 'Title must be at least 3 characters long';
        if (value.trim().length > 200) return 'Title must be less than 200 characters';
        return '';
      
      case 'description':
        if (!value.trim()) return 'Description is required';
        if (value.trim().length < 10) return 'Description must be at least 10 characters long';
        if (value.trim().length > 2000) return 'Description must be less than 2000 characters';
        return '';
      
      case 'notes':
        if (value && value.length > 1000) return 'Notes must be less than 1000 characters';
        return '';
      
      default:
        return '';
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      // Scroll to first error field
      const firstErrorField = Object.keys(errors)[0];
      if (firstErrorField) {
        const element = document.querySelector(`[name="${firstErrorField}"]`) as HTMLElement;
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.focus();
        }
      }
      return;
    }

    try {
      const submitData: Partial<WorkItem> = {
        item_type: formData.type as WorkItemType,
        title: formData.title.trim(),
        description: formData.description.trim(),
        status: formData.status as any,
        priority: formData.priority as any,
        complexity: formData.complexity as any,
        notes: formData.notes?.trim() || '',
        context_tags: formData.context_tags.filter(tag => tag.trim().length > 0),
        acceptance_criteria: formData.acceptance_criteria
          .filter(criteria => criteria.trim().length > 0)
          .map(criteria => criteria.trim()),
      };

      if (parentId) {
        submitData.parent_id = parentId;
      }

      if (workItem) {
        submitData.id = workItem.id;
      }

      await onSave(submitData);
    } catch (error) {
      console.error('Error saving work item:', error);
      // Set a general error message
      setErrors(prev => ({ 
        ...prev, 
        submit: error instanceof Error ? error.message : 'Failed to save work item. Please try again.' 
      }));
    }
  };

  // Handle input changes with real-time validation
  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Real-time validation for specific fields
    if (['title', 'description', 'notes'].includes(field)) {
      const fieldError = validateField(field, value);
      setErrors(prev => ({ ...prev, [field]: fieldError }));
    } else {
      // Clear error when user starts typing for other fields
      if (errors[field]) {
        setErrors(prev => ({ ...prev, [field]: '' }));
      }
    }
  };

  // Handle acceptance criteria changes
  const handleAcceptanceCriteriaChange = (index: number, value: string) => {
    const newCriteria = [...formData.acceptance_criteria];
    newCriteria[index] = value;
    handleInputChange('acceptance_criteria', newCriteria);
    
    // Clear acceptance criteria errors when user starts typing
    if (errors.acceptance_criteria && value.trim().length > 0) {
      setErrors(prev => ({ ...prev, acceptance_criteria: '' }));
    }
  };

  // Add new acceptance criteria
  const addAcceptanceCriteria = () => {
    if (formData.acceptance_criteria.length >= 10) {
      setErrors(prev => ({ ...prev, acceptance_criteria: 'Maximum 10 acceptance criteria allowed' }));
      return;
    }
    handleInputChange('acceptance_criteria', [...formData.acceptance_criteria, '']);
  };

  // Remove acceptance criteria
  const removeAcceptanceCriteria = (index: number) => {
    const newCriteria = formData.acceptance_criteria.filter((_, i) => i !== index);
    handleInputChange('acceptance_criteria', newCriteria.length > 0 ? newCriteria : ['']);
    
    // Re-validate acceptance criteria after removal
    if (newCriteria.length === 0) {
      setErrors(prev => ({ ...prev, acceptance_criteria: 'At least one acceptance criteria is required' }));
    } else if (newCriteria.filter(criteria => criteria.trim().length > 0).length === 0) {
      setErrors(prev => ({ ...prev, acceptance_criteria: 'At least one acceptance criteria must have content' }));
    } else {
      setErrors(prev => ({ ...prev, acceptance_criteria: '' }));
    }
  };

  // Handle context tags
  const handleAddContextTag = () => {
    const trimmedTag = contextTagInput.trim();
    
    if (!trimmedTag) {
      return;
    }
    
    if (formData.context_tags.includes(trimmedTag)) {
      setErrors(prev => ({ ...prev, context_tags: 'Tag already exists' }));
      return;
    }
    
    if (formData.context_tags.length >= 10) {
      setErrors(prev => ({ ...prev, context_tags: 'Maximum 10 context tags allowed' }));
      return;
    }
    
    if (trimmedTag.length > 50) {
      setErrors(prev => ({ ...prev, context_tags: 'Tag must be less than 50 characters' }));
      return;
    }
    
    handleInputChange('context_tags', [...formData.context_tags, trimmedTag]);
    setContextTagInput('');
    // Clear any previous context_tags errors
    if (errors.context_tags) {
      setErrors(prev => ({ ...prev, context_tags: '' }));
    }
  };

  const handleRemoveContextTag = (tagToRemove: string) => {
    handleInputChange('context_tags', formData.context_tags.filter(tag => tag !== tagToRemove));
  };

  const handleContextTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddContextTag();
    }
  };

  return (
    <Box
      component="form"
      data-work-item-form
      onSubmit={handleSubmit}
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Form Submission Error Alert */}
      {errors.submit && (
        <Alert 
          severity="error" 
          onClose={() => setErrors(prev => ({ ...prev, submit: '' }))}
          sx={{ mb: 2 }}
        >
          {errors.submit}
        </Alert>
      )}
      
      {/* Parent Work Item Indicator */}
      {parentId && (
        <Alert 
          severity="info" 
          sx={{ mb: 2 }}
        >
          Creating child work item under parent: {parentId}
        </Alert>
      )}

      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        <Stack spacing={3}>
          {/* Header Section - Title and Type */}
          <Card elevation={0} sx={{ bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent sx={{ pb: 2 }}>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  name="title"
                  placeholder="Enter work item title..."
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  error={!!errors.title}
                  helperText={errors.title || `${formData.title.length}/200 characters`}
                  required
                  variant="outlined"
                  disabled={isSubmitting}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      fontSize: '1.25rem',
                      fontWeight: 500,
                      bgcolor: 'white',
                      '& fieldset': {
                        borderColor: 'grey.300',
                      },
                      '&:hover fieldset': {
                        borderColor: 'primary.main',
                      },
                    },
                  }}
                />
                
                <Stack direction="row" spacing={2}>
                  <FormControl sx={{ minWidth: 120 }} error={!!errors.type}>
                    <InputLabel size="small">Type</InputLabel>
                    <Select
                      size="small"
                      value={formData.type}
                      label="Type"
                      onChange={(e) => handleInputChange('type', e.target.value)}
                      sx={{ bgcolor: 'white' }}
                    >
                      {WORK_ITEM_TYPES.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.type && <FormHelperText>{errors.type}</FormHelperText>}
                  </FormControl>
                  
                  <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel size="small">Status</InputLabel>
                    <Select
                      size="small"
                      value={formData.status}
                      label="Status"
                      onChange={(e) => handleInputChange('status', e.target.value)}
                      sx={{ bgcolor: 'white' }}
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <MenuItem key={status.value} value={status.value}>
                          {status.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {/* Description Section */}
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                  Description
                </Typography>
                <TextField
                  fullWidth
                  name="description"
                  placeholder="Describe what needs to be done..."
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  multiline
                  rows={4}
                  error={!!errors.description}
                  helperText={errors.description || `${formData.description.length}/2000 characters`}
                  required
                  variant="outlined"
                  disabled={isSubmitting}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'grey.300',
                      },
                    },
                  }}
                />
              </Stack>
            </CardContent>
          </Card>

          {/* Properties Section */}
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent>
              <Stack spacing={3}>
                <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                  Properties
                </Typography>
                
                <Stack direction="row" spacing={3}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                    <FlagIcon sx={{ color: 'grey.600', fontSize: '1.2rem' }} />
                    <FormControl fullWidth size="small">
                      <InputLabel>Priority</InputLabel>
                      <Select
                        value={formData.priority}
                        label="Priority"
                        onChange={(e) => handleInputChange('priority', e.target.value)}
                        disabled={isSubmitting}
                      >
                        {PRIORITY_OPTIONS.map((priority) => (
                          <MenuItem key={priority.value} value={priority.value}>
                            {priority.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                    <SpeedIcon sx={{ color: 'grey.600', fontSize: '1.2rem' }} />
                    <FormControl fullWidth size="small">
                      <InputLabel>Complexity</InputLabel>
                      <Select
                        value={formData.complexity}
                        label="Complexity"
                        onChange={(e) => handleInputChange('complexity', e.target.value)}
                        disabled={isSubmitting}
                      >
                        {COMPLEXITY_OPTIONS.map((complexity) => (
                          <MenuItem key={complexity.value} value={complexity.value}>
                            {complexity.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {/* Context Tags Section */}
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LabelIcon sx={{ color: 'grey.600', fontSize: '1.2rem' }} />
                  <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                    Context Tags
                  </Typography>
                </Box>
                
                {formData.context_tags.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {formData.context_tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        onDelete={() => handleRemoveContextTag(tag)}
                        size="small"
                        sx={{
                          bgcolor: 'primary.50',
                          color: 'primary.700',
                          '& .MuiChip-deleteIcon': {
                            color: 'primary.600',
                          },
                        }}
                      />
                    ))}
                  </Box>
                )}
                
                <TextField
                  fullWidth
                  size="small"
                  name="context_tags"
                  placeholder="Add context tag and press Enter"
                  value={contextTagInput}
                  onChange={(e) => setContextTagInput(e.target.value)}
                  onKeyPress={handleContextTagKeyPress}
                  error={!!errors.context_tags}
                  helperText={errors.context_tags}
                  disabled={isSubmitting}
                  InputProps={{
                    endAdornment: (
                      <Button
                        size="small"
                        onClick={handleAddContextTag}
                        disabled={!contextTagInput.trim() || formData.context_tags.length >= 10}
                        sx={{ minWidth: 'auto', px: 2 }}
                      >
                        Add
                      </Button>
                    ),
                  }}
                />
              </Stack>
            </CardContent>
          </Card>

          {/* Acceptance Criteria Section */}
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon sx={{ color: 'grey.600', fontSize: '1.2rem' }} />
                  <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                    Acceptance Criteria *
                  </Typography>
                </Box>
                
                <Stack spacing={1.5}>
                  {formData.acceptance_criteria.map((criteria, index) => (
                    <Paper
                      key={index}
                      elevation={0}
                      sx={{
                        p: 1.5,
                        border: '1px solid',
                        borderColor: 'grey.200',
                        bgcolor: 'grey.50',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          minWidth: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          bgcolor: 'primary.main',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {index + 1}
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        name={`acceptance_criteria_${index}`}
                        placeholder={`Define acceptance criteria ${index + 1}...`}
                        value={criteria}
                        onChange={(e) => handleAcceptanceCriteriaChange(index, e.target.value)}
                        error={!!errors.acceptance_criteria && !criteria.trim()}
                        variant="standard"
                        disabled={isSubmitting}
                        InputProps={{
                          disableUnderline: true,
                        }}
                        sx={{
                          '& .MuiInputBase-input': {
                            bgcolor: 'transparent',
                            border: 'none',
                            '&:focus': {
                              bgcolor: 'white',
                              borderRadius: 1,
                              px: 1,
                            },
                          },
                        }}
                      />
                      {formData.acceptance_criteria.length > 1 && (
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => removeAcceptanceCriteria(index)}
                          sx={{ ml: 1 }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      )}
                    </Paper>
                  ))}
                </Stack>
                
                <Button
                  variant="outlined"
                  size="small"
                  onClick={addAcceptanceCriteria}
                  startIcon={<AddIcon />}
                  disabled={formData.acceptance_criteria.length >= 10}
                  sx={{
                    alignSelf: 'flex-start',
                    borderStyle: 'dashed',
                    borderColor: 'grey.400',
                    color: 'grey.600',
                    '&:hover': {
                      borderColor: 'primary.main',
                      color: 'primary.main',
                      bgcolor: 'primary.50',
                    },
                    '&:disabled': {
                      borderColor: 'grey.300',
                      color: 'grey.400',
                    },
                  }}
                >
                  Add Criteria {formData.acceptance_criteria.length >= 10 ? '(Max 10)' : ''}
                </Button>
                
                {errors.acceptance_criteria && (
                  <FormHelperText error>{errors.acceptance_criteria}</FormHelperText>
                )}
              </Stack>
            </CardContent>
          </Card>

          {/* Notes Section */}
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'grey.200' }}>
            <CardContent>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <NotesIcon sx={{ color: 'grey.600', fontSize: '1.2rem' }} />
                  <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>
                    Notes
                  </Typography>
                </Box>
                
                <TextField
                  fullWidth
                  name="notes"
                  placeholder="Additional notes, constraints, or context..."
                  value={formData.notes}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  multiline
                  rows={3}
                  variant="outlined"
                  error={!!errors.notes}
                  helperText={errors.notes || `${formData.notes.length}/1000 characters`}
                  disabled={isSubmitting}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'grey.300',
                      },
                    },
                  }}
                />
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Box>
      
      {/* Action Buttons */}
      {showActions && (
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'grey.200', bgcolor: 'grey.50' }}>
          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button
              variant="outlined"
              onClick={onCancel}
              disabled={isSubmitting}
              sx={{ minWidth: 100 }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting}
              startIcon={isSubmitting ? <CircularProgress size={16} /> : null}
              sx={{ minWidth: 100 }}
            >
              {isSubmitting ? 'Saving...' : (workItem ? 'Update' : 'Create')}
            </Button>
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default WorkItemModalForm;
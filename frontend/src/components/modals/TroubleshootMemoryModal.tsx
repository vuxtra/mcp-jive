'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  IconButton,
  Box,
  Typography,
  Chip,
  useTheme,
  Alert,
  Stack,
  Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import type { TroubleshootItem } from '../../types/memory';

interface TroubleshootMemoryModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (item: Partial<TroubleshootItem>) => Promise<void>;
  item?: TroubleshootItem | null;
}

export function TroubleshootMemoryModal({
  open,
  onClose,
  onSave,
  item,
}: TroubleshootMemoryModalProps) {
  const theme = useTheme();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [slug, setSlug] = useState('');
  const [title, setTitle] = useState('');
  const [aiSolutions, setAiSolutions] = useState('');
  const [aiUseCase, setAiUseCase] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);

  // Temporary input fields for adding items to arrays
  const [newUseCase, setNewUseCase] = useState('');
  const [newKeyword, setNewKeyword] = useState('');
  const [newTag, setNewTag] = useState('');

  // Initialize form when item changes
  useEffect(() => {
    if (item) {
      setSlug(item.slug || '');
      setTitle(item.title || '');
      setAiSolutions(item.ai_solutions || '');
      setAiUseCase(item.ai_use_case || []);
      setKeywords(item.keywords || []);
      setTags(item.tags || []);
    } else {
      // Reset form
      setSlug('');
      setTitle('');
      setAiSolutions('');
      setAiUseCase([]);
      setKeywords([]);
      setTags([]);
    }
    setError(null);
  }, [item, open]);

  const handleSave = async () => {
    // Validation
    if (!slug.trim()) {
      setError('Slug is required');
      return;
    }
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    if (!aiSolutions.trim()) {
      setError('Solutions are required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const itemData: Partial<TroubleshootItem> = {
        slug: slug.trim(),
        title: title.trim(),
        ai_solutions: aiSolutions.trim(),
        ai_use_case: aiUseCase,
        keywords,
        tags,
      };

      if (item) {
        itemData.id = item.id;
      }

      await onSave(itemData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save item');
    } finally {
      setIsSubmitting(false);
    }
  };

  const addToArray = (
    value: string,
    array: string[],
    setter: (arr: string[]) => void,
    inputSetter: (val: string) => void,
    maxLength?: number
  ) => {
    const trimmed = value.trim();
    if (trimmed && !array.includes(trimmed)) {
      if (maxLength && array.length >= maxLength) {
        setError(`Maximum ${maxLength} items allowed`);
        return;
      }
      setter([...array, trimmed]);
      inputSetter('');
      setError(null);
    }
  };

  const removeFromArray = (
    value: string,
    array: string[],
    setter: (arr: string[]) => void
  ) => {
    setter(array.filter(item => item !== value));
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '70vh',
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
          {item ? 'Edit Troubleshoot Item' : 'Create Troubleshoot Item'}
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Stack spacing={3}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Basic Fields */}
          <TextField
            label="Slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            fullWidth
            required
            disabled={!!item} // Slug cannot be changed after creation
            helperText="Unique identifier (lowercase, hyphens, max 100 chars)"
            inputProps={{ maxLength: 100 }}
          />

          <TextField
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            fullWidth
            required
            helperText="Human-friendly short name (max 200 chars)"
            inputProps={{ maxLength: 200 }}
          />

          <TextField
            label="AI Solutions"
            value={aiSolutions}
            onChange={(e) => setAiSolutions(e.target.value)}
            fullWidth
            required
            multiline
            rows={8}
            helperText="Solutions with tips and steps in Markdown (max 10,000 chars)"
            inputProps={{ maxLength: 10000 }}
          />

          <Divider />

          {/* Use Cases */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Problem Descriptions / Use Cases (max 10)
            </Typography>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Describe when to use this troubleshooting guide
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1, mt: 1 }}>
              <TextField
                placeholder="Add problem description..."
                value={newUseCase}
                onChange={(e) => setNewUseCase(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addToArray(newUseCase, aiUseCase, setAiUseCase, setNewUseCase, 10);
                  }
                }}
                size="small"
                fullWidth
              />
              <IconButton
                onClick={() => addToArray(newUseCase, aiUseCase, setAiUseCase, setNewUseCase, 10)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {aiUseCase.map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  onDelete={() => removeFromArray(item, aiUseCase, setAiUseCase)}
                  size="small"
                  color="warning"
                />
              ))}
            </Box>
          </Box>

          {/* Keywords */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Keywords (max 20)
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField
                placeholder="Add keyword..."
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addToArray(newKeyword, keywords, setKeywords, setNewKeyword, 20);
                  }
                }}
                size="small"
                fullWidth
              />
              <IconButton
                onClick={() => addToArray(newKeyword, keywords, setKeywords, setNewKeyword, 20)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {keywords.map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  onDelete={() => removeFromArray(item, keywords, setKeywords)}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>

          {/* Tags */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Tags
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField
                placeholder="Add tag..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addToArray(newTag, tags, setTags, setNewTag);
                  }
                }}
                size="small"
                fullWidth
              />
              <IconButton
                onClick={() => addToArray(newTag, tags, setTags, setNewTag)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {tags.map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  onDelete={() => removeFromArray(item, tags, setTags)}
                  size="small"
                />
              ))}
            </Box>
          </Box>

          {item && (
            <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.grey[50], borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Usage Statistics:</strong> Used {item.usage_count || 0} times,
                Successful {item.success_count || 0} times
                {item.usage_count > 0 && (
                  <> (Success Rate: {Math.round((item.success_count / item.usage_count) * 100)}%)</>
                )}
              </Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>

      <Divider />
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : item ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
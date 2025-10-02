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
  Grid,
  useTheme,
  Alert,
  Stack,
  Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import type { ArchitectureItem } from '../../types/memory';

interface ArchitectureMemoryModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (item: Partial<ArchitectureItem>) => Promise<void>;
  item?: ArchitectureItem | null;
}

export function ArchitectureMemoryModal({
  open,
  onClose,
  onSave,
  item,
}: ArchitectureMemoryModalProps) {
  const theme = useTheme();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [slug, setSlug] = useState('');
  const [title, setTitle] = useState('');
  const [aiRequirements, setAiRequirements] = useState('');
  const [aiWhenToUse, setAiWhenToUse] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [childrenSlugs, setChildrenSlugs] = useState<string[]>([]);
  const [relatedSlugs, setRelatedSlugs] = useState<string[]>([]);
  const [linkedEpicIds, setLinkedEpicIds] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);

  // Temporary input fields for adding items to arrays
  const [newWhenToUse, setNewWhenToUse] = useState('');
  const [newKeyword, setNewKeyword] = useState('');
  const [newChildSlug, setNewChildSlug] = useState('');
  const [newRelatedSlug, setNewRelatedSlug] = useState('');
  const [newEpicId, setNewEpicId] = useState('');
  const [newTag, setNewTag] = useState('');

  // Initialize form when item changes
  useEffect(() => {
    if (item) {
      setSlug(item.slug || '');
      setTitle(item.title || '');
      setAiRequirements(item.ai_requirements || '');
      setAiWhenToUse(item.ai_when_to_use || []);
      setKeywords(item.keywords || []);
      setChildrenSlugs(item.children_slugs || []);
      setRelatedSlugs(item.related_slugs || []);
      setLinkedEpicIds(item.linked_epic_ids || []);
      setTags(item.tags || []);
    } else {
      // Reset form
      setSlug('');
      setTitle('');
      setAiRequirements('');
      setAiWhenToUse([]);
      setKeywords([]);
      setChildrenSlugs([]);
      setRelatedSlugs([]);
      setLinkedEpicIds([]);
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
    if (!aiRequirements.trim()) {
      setError('Requirements are required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const itemData: Partial<ArchitectureItem> = {
        slug: slug.trim(),
        title: title.trim(),
        ai_requirements: aiRequirements.trim(),
        ai_when_to_use: aiWhenToUse,
        keywords,
        children_slugs: childrenSlugs,
        related_slugs: relatedSlugs,
        linked_epic_ids: linkedEpicIds,
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
          minHeight: '80vh',
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
          {item ? 'Edit Architecture Item' : 'Create Architecture Item'}
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
            label="AI Requirements"
            value={aiRequirements}
            onChange={(e) => setAiRequirements(e.target.value)}
            fullWidth
            required
            multiline
            rows={6}
            helperText="Detailed specifications in Markdown (max 10,000 chars)"
            inputProps={{ maxLength: 10000 }}
          />

          <Divider />

          {/* When to Use */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              When to Use (max 10)
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField
                placeholder="Add usage scenario..."
                value={newWhenToUse}
                onChange={(e) => setNewWhenToUse(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addToArray(newWhenToUse, aiWhenToUse, setAiWhenToUse, setNewWhenToUse, 10);
                  }
                }}
                size="small"
                fullWidth
              />
              <IconButton
                onClick={() => addToArray(newWhenToUse, aiWhenToUse, setAiWhenToUse, setNewWhenToUse, 10)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {aiWhenToUse.map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  onDelete={() => removeFromArray(item, aiWhenToUse, setAiWhenToUse)}
                  size="small"
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

          <Divider />

          {/* Hierarchical Relationships */}
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Children Slugs (max 50)
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField
                    placeholder="Add child slug..."
                    value={newChildSlug}
                    onChange={(e) => setNewChildSlug(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addToArray(newChildSlug, childrenSlugs, setChildrenSlugs, setNewChildSlug, 50);
                      }
                    }}
                    size="small"
                    fullWidth
                  />
                  <IconButton
                    onClick={() => addToArray(newChildSlug, childrenSlugs, setChildrenSlugs, setNewChildSlug, 50)}
                    color="primary"
                    size="small"
                  >
                    <AddIcon fontSize="small" />
                  </IconButton>
                </Stack>
                <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                  <Stack spacing={0.5}>
                    {childrenSlugs.map((item, index) => (
                      <Chip
                        key={index}
                        label={item}
                        onDelete={() => removeFromArray(item, childrenSlugs, setChildrenSlugs)}
                        size="small"
                      />
                    ))}
                  </Stack>
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Related Slugs (max 20)
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField
                    placeholder="Add related slug..."
                    value={newRelatedSlug}
                    onChange={(e) => setNewRelatedSlug(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addToArray(newRelatedSlug, relatedSlugs, setRelatedSlugs, setNewRelatedSlug, 20);
                      }
                    }}
                    size="small"
                    fullWidth
                  />
                  <IconButton
                    onClick={() => addToArray(newRelatedSlug, relatedSlugs, setRelatedSlugs, setNewRelatedSlug, 20)}
                    color="primary"
                    size="small"
                  >
                    <AddIcon fontSize="small" />
                  </IconButton>
                </Stack>
                <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                  <Stack spacing={0.5}>
                    {relatedSlugs.map((item, index) => (
                      <Chip
                        key={index}
                        label={item}
                        onDelete={() => removeFromArray(item, relatedSlugs, setRelatedSlugs)}
                        size="small"
                      />
                    ))}
                  </Stack>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Linked Epic IDs */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Linked Epic IDs (max 20)
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField
                placeholder="Add epic ID..."
                value={newEpicId}
                onChange={(e) => setNewEpicId(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addToArray(newEpicId, linkedEpicIds, setLinkedEpicIds, setNewEpicId, 20);
                  }
                }}
                size="small"
                fullWidth
              />
              <IconButton
                onClick={() => addToArray(newEpicId, linkedEpicIds, setLinkedEpicIds, setNewEpicId, 20)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {linkedEpicIds.map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  onDelete={() => removeFromArray(item, linkedEpicIds, setLinkedEpicIds)}
                  size="small"
                  color="secondary"
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
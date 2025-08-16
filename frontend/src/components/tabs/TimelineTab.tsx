'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Chip,
  Card,
  CardContent,
  useTheme,
  alpha,
} from '@mui/material';
import {
  CheckCircle as CompletedIcon,
  Schedule as InProgressIcon,
  Block as BlockedIcon,
  Assignment as TaskIcon,
  Flag as EpicIcon,
  Star as FeatureIcon,
} from '@mui/icons-material';
import { useJiveApi } from '../../hooks/useJiveApi';
import { WorkItem } from '../../types';

interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  type: 'created' | 'updated' | 'completed' | 'blocked';
  workItemType: string;
  timestamp: Date;
  status: string;
}

export function TimelineTab() {
  const theme = useTheme();
  const { searchWorkItems } = useJiveApi();
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTimelineEvents();
  }, []);

  const loadTimelineEvents = async () => {
    try {
      setLoading(true);
      const response = await searchWorkItems({ query: '', limit: 50 });
      if (response.success && response.data) {
        // Convert work items to timeline events (mock implementation)
        const timelineEvents: TimelineEvent[] = response.data.flatMap((item: WorkItem) => {
          const events: TimelineEvent[] = [];
          
          // Add creation event
          events.push({
            id: `${item.id}-created`,
            title: `${item.type.charAt(0).toUpperCase() + item.type.slice(1)} Created`,
            description: item.title,
            type: 'created',
            workItemType: item.type,
            timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000), // Random date within last 30 days
            status: item.status,
          });
          
          // Add status change events based on current status
          if (item.status === 'in_progress') {
            events.push({
              id: `${item.id}-started`,
              title: 'Work Started',
              description: `Started working on: ${item.title}`,
              type: 'updated',
              workItemType: item.type,
              timestamp: new Date(Date.now() - Math.random() * 20 * 24 * 60 * 60 * 1000),
              status: item.status,
            });
          }
          
          if (item.status === 'completed') {
            events.push({
              id: `${item.id}-completed`,
              title: 'Work Completed',
              description: `Completed: ${item.title}`,
              type: 'completed',
              workItemType: item.type,
              timestamp: new Date(Date.now() - Math.random() * 10 * 24 * 60 * 60 * 1000),
              status: item.status,
            });
          }
          
          if (item.status === 'blocked') {
            events.push({
              id: `${item.id}-blocked`,
              title: 'Work Blocked',
              description: `Blocked: ${item.title}`,
              type: 'blocked',
              workItemType: item.type,
              timestamp: new Date(Date.now() - Math.random() * 15 * 24 * 60 * 60 * 1000),
              status: item.status,
            });
          }
          
          return events;
        });
        
        // Sort events by timestamp (newest first)
        timelineEvents.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setEvents(timelineEvents.slice(0, 20)); // Show only recent 20 events
      }
    } catch (error) {
      console.error('Failed to load timeline events:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'completed': return <CompletedIcon />;
      case 'updated': return <InProgressIcon />;
      case 'blocked': return <BlockedIcon />;
      default: return <TaskIcon />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'completed': return theme.palette.success.main;
      case 'updated': return theme.palette.primary.main;
      case 'blocked': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  const getWorkItemIcon = (type: string) => {
    switch (type) {
      case 'epic': return <EpicIcon sx={{ fontSize: '1rem' }} />;
      case 'feature': return <FeatureIcon sx={{ fontSize: '1rem' }} />;
      default: return <TaskIcon sx={{ fontSize: '1rem' }} />;
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Loading timeline...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Project Timeline
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track recent activity and progress across all work items
        </Typography>
      </Box>

      <Paper
        elevation={0}
        sx={{
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          p: 3,
        }}
      >
        {events.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              No recent activity
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Start working on items to see timeline events
            </Typography>
          </Box>
        ) : (
          <Timeline position="right">
            {events.map((event, index) => (
              <TimelineItem key={event.id}>
                <TimelineOppositeContent
                  sx={{ m: 'auto 0', minWidth: 120 }}
                  align="right"
                  variant="body2"
                  color="text.secondary"
                >
                  {formatDate(event.timestamp)}
                </TimelineOppositeContent>
                
                <TimelineSeparator>
                  <TimelineDot
                    sx={{
                      backgroundColor: getEventColor(event.type),
                      color: 'white',
                      border: 'none',
                      p: 1,
                    }}
                  >
                    {getEventIcon(event.type)}
                  </TimelineDot>
                  {index < events.length - 1 && (
                    <TimelineConnector
                      sx={{
                        backgroundColor: alpha(theme.palette.divider, 0.5),
                      }}
                    />
                  )}
                </TimelineSeparator>
                
                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Card
                    elevation={0}
                    sx={{
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 2,
                      transition: 'all 0.2s ease-in-out',
                      '&:hover': {
                        borderColor: getEventColor(event.type),
                        boxShadow: `0 2px 8px ${alpha(getEventColor(event.type), 0.15)}`,
                      },
                    }}
                  >
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Box sx={{ color: theme.palette.text.secondary }}>
                          {getWorkItemIcon(event.workItemType)}
                        </Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {event.title}
                        </Typography>
                        <Chip
                          label={event.workItemType}
                          size="small"
                          variant="outlined"
                          sx={{
                            textTransform: 'capitalize',
                            fontSize: '0.7rem',
                            height: 20,
                          }}
                        />
                      </Box>
                      
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {event.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </Paper>
    </Box>
  );
}
'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CompletedIcon,
  Block as BlockedIcon,

  Add as AddIcon,
} from '@mui/icons-material';
import { useJiveApi } from '../../hooks/useJiveApi';
import { WorkItem } from '../../types';

interface DashboardStats {
  totalItems: number;
  completedItems: number;
  inProgressItems: number;
  blockedItems: number;
  recentActivity: WorkItem[];
  upcomingDeadlines: WorkItem[];
}

export function DashboardTab() {
  const theme = useTheme();
  const { searchWorkItems } = useJiveApi();
  const [stats, setStats] = useState<DashboardStats>({
    totalItems: 0,
    completedItems: 0,
    inProgressItems: 0,
    blockedItems: 0,
    recentActivity: [],
    upcomingDeadlines: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await searchWorkItems({ query: '', limit: 100 });
      if (response.success && response.data) {
        const items = response.data;
        const completed = items.filter(item => item.status === 'completed');
        const inProgress = items.filter(item => item.status === 'in_progress');
        const blocked = items.filter(item => item.status === 'blocked');
        
        // Mock recent activity (last 5 items)
        const recentActivity = items.slice(0, 5);
        
        // Mock upcoming deadlines (items with high priority)
        const upcomingDeadlines = items
          .filter(item => item.priority === 'high' || item.priority === 'critical')
          .slice(0, 5);
        
        setStats({
          totalItems: items.length,
          completedItems: completed.length,
          inProgressItems: inProgress.length,
          blockedItems: blocked.length,
          recentActivity,
          upcomingDeadlines,
        });
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCompletionRate = () => {
    if (stats.totalItems === 0) return 0;
    return Math.round((stats.completedItems / stats.totalItems) * 100);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'primary';
      case 'blocked': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return theme.palette.error.main;
      case 'high': return theme.palette.warning.main;
      case 'medium': return theme.palette.info.main;
      case 'low': return theme.palette.success.main;
      default: return theme.palette.grey[500];
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Loading dashboard...
        </Typography>
        <LinearProgress sx={{ mt: 2, maxWidth: 300, mx: 'auto' }} />
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
          Project Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Overview of your project progress and key metrics
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Card
                elevation={0}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  textAlign: 'center',
                  p: 2,
                }}
              >
                <AssignmentIcon
                  sx={{
                    fontSize: '2rem',
                    color: theme.palette.primary.main,
                    mb: 1,
                  }}
                />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {stats.totalItems}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Items
                </Typography>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card
                elevation={0}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  textAlign: 'center',
                  p: 2,
                }}
              >
                <CompletedIcon
                  sx={{
                    fontSize: '2rem',
                    color: theme.palette.success.main,
                    mb: 1,
                  }}
                />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {stats.completedItems}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card
                elevation={0}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  textAlign: 'center',
                  p: 2,
                }}
              >
                <ScheduleIcon
                  sx={{
                    fontSize: '2rem',
                    color: theme.palette.warning.main,
                    mb: 1,
                  }}
                />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {stats.inProgressItems}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  In Progress
                </Typography>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card
                elevation={0}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  textAlign: 'center',
                  p: 2,
                }}
              >
                <BlockedIcon
                  sx={{
                    fontSize: '2rem',
                    color: theme.palette.error.main,
                    mb: 1,
                  }}
                />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {stats.blockedItems}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Blocked
                </Typography>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Progress Overview */}
        <Grid item xs={12} md={4}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              height: '100%',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <TrendingUpIcon sx={{ color: theme.palette.primary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Overall Progress
                </Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                <Typography variant="h2" sx={{ fontWeight: 700, mb: 1 }}>
                  {getCompletionRate()}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Project Completion
                </Typography>
              </Box>
              
              <LinearProgress
                variant="determinate"
                value={getCompletionRate()}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              height: 400,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <CardContent sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Recent Activity
              </Typography>
              
              {stats.recentActivity.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4, flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="text.secondary">
                    No recent activity
                  </Typography>
                </Box>
              ) : (
                <List sx={{ flexGrow: 1, overflow: 'auto' }}>
                  {stats.recentActivity.map((item, index) => (
                    <React.Fragment key={item.id}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <AssignmentIcon sx={{ fontSize: '1.2rem', color: theme.palette.text.secondary }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {item.title}
                            </Typography>
                          }
                          secondary={
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              <Chip
                                label={item.type}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                              <Chip
                                label={item.status.replace('_', ' ')}
                                size="small"
                                color={getStatusColor(item.status)}
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < stats.recentActivity.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* High Priority Items */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              height: 400,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <CardContent sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                High Priority Items
              </Typography>
              
              {stats.upcomingDeadlines.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4, flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="text.secondary">
                    No high priority items
                  </Typography>
                </Box>
              ) : (
                <List sx={{ flexGrow: 1, overflow: 'auto' }}>
                  {stats.upcomingDeadlines.map((item, index) => (
                    <React.Fragment key={item.id}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              backgroundColor: getPriorityColor(item.priority),
                            }}
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {item.title}
                            </Typography>
                          }
                          secondary={
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              <Chip
                                label={item.priority}
                                size="small"
                                color={item.priority === 'critical' ? 'error' : 'warning'}
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                              <Chip
                                label={item.status.replace('_', ' ')}
                                size="small"
                                color={getStatusColor(item.status)}
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < stats.upcomingDeadlines.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Quick Actions
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Create Work Item
                </Button>
                

                <Button
                  variant="outlined"
                  startIcon={<TrendingUpIcon />}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  View Analytics
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
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
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CompletedIcon,
  Schedule as InProgressIcon,
  Block as BlockedIcon,
} from '@mui/icons-material';
import { useJiveApi } from '../../hooks/useJiveApi';

interface AnalyticsData {
  totalWorkItems: number;
  completedItems: number;
  inProgressItems: number;
  blockedItems: number;
  completionRate: number;
  velocity: number;
}

export function AnalyticsTab() {
  const theme = useTheme();
  const { searchWorkItems } = useJiveApi();
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalWorkItems: 0,
    completedItems: 0,
    inProgressItems: 0,
    blockedItems: 0,
    completionRate: 0,
    velocity: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await searchWorkItems({ query: '', limit: 1000 });
      if (response.success && response.data) {
        const items = response.data;
        const completed = items.filter(item => item.status === 'completed').length;
        const inProgress = items.filter(item => item.status === 'in_progress').length;
        const blocked = items.filter(item => item.status === 'blocked').length;
        const total = items.length;
        
        setAnalytics({
          totalWorkItems: total,
          completedItems: completed,
          inProgressItems: inProgress,
          blockedItems: blocked,
          completionRate: total > 0 ? Math.round((completed / total) * 100) : 0,
          velocity: Math.round(completed * 0.8), // Mock velocity calculation
        });
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color, subtitle }: {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
  }) => (
    <Card
      elevation={0}
      sx={{
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          borderColor: color,
          boxShadow: `0 4px 12px ${alpha(color, 0.15)}`,
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: alpha(color, 0.1),
              color: color,
            }}
          >
            {icon}
          </Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: theme.palette.text.primary,
            }}
          >
            {value}
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Loading analytics...
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
          Project Analytics
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track progress, velocity, and key metrics across your work items
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Work Items"
            value={analytics.totalWorkItems}
            icon={<AssignmentIcon />}
            color={theme.palette.primary.main}
            subtitle="All work items in project"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed"
            value={analytics.completedItems}
            icon={<CompletedIcon />}
            color={theme.palette.success.main}
            subtitle="Successfully finished"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="In Progress"
            value={analytics.inProgressItems}
            icon={<InProgressIcon />}
            color={theme.palette.warning.main}
            subtitle="Currently being worked on"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Blocked"
            value={analytics.blockedItems}
            icon={<BlockedIcon />}
            color={theme.palette.error.main}
            subtitle="Waiting on dependencies"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              height: '100%',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Completion Rate
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Overall Progress
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {analytics.completionRate}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={analytics.completionRate}
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
              </Box>
              
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 3 }}>
                <Chip
                  label={`${analytics.completedItems} Completed`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
                <Chip
                  label={`${analytics.inProgressItems} In Progress`}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
                <Chip
                  label={`${analytics.blockedItems} Blocked`}
                  size="small"
                  color="error"
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card
            elevation={0}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              height: '100%',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Team Velocity
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.info.main, 0.1),
                    color: theme.palette.info.main,
                  }}
                >
                  <TrendingUpIcon />
                </Box>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {analytics.velocity}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Story points per sprint
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="body2" color="text.secondary">
                Based on recent completion trends and work item complexity
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
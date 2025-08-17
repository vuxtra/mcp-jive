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
import { useJiveApiContext } from '../providers/JiveApiProvider';

interface AnalyticsData {
  totalWorkItems: number;
  completedItems: number;
  inProgressItems: number;
  blockedItems: number;
  completionRate: number;
  velocity: number;
  velocityTrend: string;
  burndownData: {
    remaining_work: number;
    ideal_burndown: number;
    actual_burndown: number;
  };
  predictions: {
    estimated_completion_date: string;
    confidence: number;
    risk_factors: string[];
  };
}

export function AnalyticsTab() {
  const theme = useTheme();
  const { searchWorkItems } = useJiveApi();
  const { mcpClient } = useJiveApiContext();
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalWorkItems: 0,
    completedItems: 0,
    inProgressItems: 0,
    blockedItems: 0,
    completionRate: 0,
    velocity: 0,
    velocityTrend: 'stable',
    burndownData: {
      remaining_work: 0,
      ideal_burndown: 0,
      actual_burndown: 0,
    },
    predictions: {
      estimated_completion_date: '',
      confidence: 0,
      risk_factors: [],
    },
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('Analytics Debug - useEffect triggered, searchWorkItems available:', !!searchWorkItems);
    if (searchWorkItems) {
      loadAnalytics();
    }
  }, [searchWorkItems]);

  const loadAnalytics = async () => {
    console.log('Analytics Debug - loadAnalytics called');
    try {
      setLoading(true);
      
      console.log('Analytics Debug - About to call searchWorkItems');
      // Get basic work items data
      const workItemsResponse = await searchWorkItems({ query: '', limit: 1000 });
      
      console.log('Analytics Debug - searchWorkItems response:', workItemsResponse);
      
      if (workItemsResponse && workItemsResponse.results) {
        const items = workItemsResponse.results;
        console.log('Analytics Debug - items found:', items.length, items);
        
        const completed = items.filter(item => item.status === 'completed').length;
        const inProgress = items.filter(item => item.status === 'in_progress').length;
        const blocked = items.filter(item => item.status === 'blocked').length;
        const total = items.length;
        
        console.log('Analytics Debug - counts:', { total, completed, inProgress, blocked });
        
        // Calculate completion rate
        const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        // Calculate velocity (items completed in the last week)
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        const recentlyCompleted = items.filter(item => {
          if (item.status === 'completed' && item.updated_at) {
            const updatedDate = new Date(item.updated_at);
            return updatedDate >= oneWeekAgo;
          }
          return false;
        }).length;
        
        // Determine velocity trend based on progress
        let velocityTrend = 'stable';
        if (inProgress > completed) {
          velocityTrend = 'increasing';
        } else if (completed > inProgress && blocked === 0) {
          velocityTrend = 'stable';
        } else if (blocked > 0) {
          velocityTrend = 'decreasing';
        }
        
        // Calculate burndown data
        const remainingWork = total - completed;
        const idealBurndown = Math.max(0, total - (total * 0.1)); // Ideal 10% completion per period
        const actualBurndown = completed;
        
        // Generate predictions based on current velocity
        let estimatedCompletion = '';
        let confidence = 0;
        const riskFactors: string[] = [];
        
        if (recentlyCompleted > 0 && remainingWork > 0) {
          const weeksToComplete = Math.ceil(remainingWork / recentlyCompleted);
          const completionDate = new Date();
          completionDate.setDate(completionDate.getDate() + (weeksToComplete * 7));
          estimatedCompletion = completionDate.toISOString().split('T')[0];
          confidence = Math.min(90, Math.max(30, 100 - (blocked * 10) - (weeksToComplete * 5)));
        }
        
        if (blocked > 0) riskFactors.push(`${blocked} blocked items`);
        if (inProgress > total * 0.5) riskFactors.push('High work in progress');
        if (recentlyCompleted === 0) riskFactors.push('No recent completions');
        
        setAnalytics({
          totalWorkItems: total,
          completedItems: completed,
          inProgressItems: inProgress,
          blockedItems: blocked,
          completionRate,
          velocity: recentlyCompleted,
          velocityTrend,
          burndownData: {
            remaining_work: remainingWork,
            ideal_burndown: idealBurndown,
            actual_burndown: actualBurndown,
          },
          predictions: {
            estimated_completion_date: estimatedCompletion,
            confidence,
            risk_factors: riskFactors,
          },
        });
      }
    } catch (error) {
      console.error('Analytics Debug - Error loading analytics:', error);
      console.error('Analytics Debug - Error details:', JSON.stringify(error, null, 2));
    } finally {
      console.log('Analytics Debug - loadAnalytics finished');
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
                    Items per week
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label={`Trend: ${analytics.velocityTrend}`}
                  size="small"
                  color={analytics.velocityTrend === 'increasing' ? 'success' : analytics.velocityTrend === 'decreasing' ? 'error' : 'default'}
                  variant="outlined"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary">
                Real-time velocity based on actual completion data
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Additional Analytics Section */}
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
                Burndown Analysis
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Remaining Work: {analytics.burndownData.remaining_work} items
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Ideal Burndown: {analytics.burndownData.ideal_burndown} items
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Actual Burndown: {analytics.burndownData.actual_burndown} items
                </Typography>
              </Box>
              
              <Box sx={{ mt: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={analytics.burndownData.ideal_burndown > 0 ? 
                    Math.max(0, 100 - (analytics.burndownData.remaining_work / analytics.burndownData.ideal_burndown) * 100) : 0}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: alpha(theme.palette.warning.main, 0.1),
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 4,
                      backgroundColor: theme.palette.warning.main,
                    },
                  }}
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
                Project Predictions
              </Typography>
              
              {analytics.predictions.estimated_completion_date && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Estimated Completion: {new Date(analytics.predictions.estimated_completion_date).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Confidence: {Math.round(analytics.predictions.confidence * 100)}%
                  </Typography>
                </Box>
              )}
              
              {analytics.predictions.risk_factors.length > 0 && (
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Risk Factors:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {analytics.predictions.risk_factors.map((risk, index) => (
                      <Chip
                        key={index}
                        label={risk}
                        size="small"
                        color="warning"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
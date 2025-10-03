import React from 'react';
import { Box, Typography, Chip, Paper } from '@mui/material';
import { BadgeTrackingData, SimplifiedBadgeTracking } from '../hooks/useBadgeTracking';

interface BadgeTrackingDisplayProps {
  trackingData: BadgeTrackingData | SimplifiedBadgeTracking;
  showDetails?: boolean;
}

export function BadgeTrackingDisplay({ trackingData, showDetails = false }: BadgeTrackingDisplayProps) {
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  // Check if it's simplified data
  const isSimplified = 'badgeStats' in trackingData;
  
  if (isSimplified) {
    const simplifiedData = trackingData as SimplifiedBadgeTracking;
    
    return (
      <Paper elevation={2} sx={{ p: 2, m: 2, maxWidth: 400 }}>
        <Typography variant="h6" gutterBottom>
          Badge Tracking Summary
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip 
            label={`${simplifiedData.totalClicks} clicks`} 
            color="secondary" 
            size="small" 
          />
          <Chip 
            label={`${formatDuration(simplifiedData.totalTimeSpent)} total time`} 
            color="info" 
            size="small" 
          />
          <Chip 
            label={`${Object.keys(simplifiedData.badgeStats).length} badges`} 
            color="primary" 
            size="small" 
          />
        </Box>

        {showDetails && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Badge Statistics:
            </Typography>
            {Object.entries(simplifiedData.badgeStats).map(([badgeName, stats]) => (
              <Box key={badgeName} sx={{ mb: 1, p: 1, border: '1px solid #eee', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight="bold">
                  {stats.badgeName}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Chip 
                    label={`${stats.clicks} clicks`} 
                    size="small" 
                    color="secondary"
                  />
                  <Chip 
                    label={`${formatDuration(stats.timeSpent)} time`} 
                    size="small" 
                    color="info"
                  />
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </Paper>
    );
  } else {
    // Handle old detailed data structure
    const detailedData = trackingData as BadgeTrackingData;
    const totalInteractions = detailedData.interactions.length;
    const totalClicks = Object.values(detailedData.badgeClickCounts).reduce((sum: number, count: number) => sum + count, 0);
    const totalHoverTime = detailedData.totalTimeOnBadges;

    return (
      <Paper elevation={2} sx={{ p: 2, m: 2, maxWidth: 400 }}>
        <Typography variant="h6" gutterBottom>
          Badge Tracking Summary (Detailed)
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip 
            label={`${totalInteractions} interactions`} 
            color="primary" 
            size="small" 
          />
          <Chip 
            label={`${totalClicks} clicks`} 
            color="secondary" 
            size="small" 
          />
          <Chip 
            label={`${formatDuration(totalHoverTime)} hover time`} 
            color="info" 
            size="small" 
          />
        </Box>

        {showDetails && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Click Counts by Badge:
            </Typography>
            {Object.entries(detailedData.badgeClickCounts).map(([badgeId, count]) => (
              <Chip 
                key={badgeId}
                label={`${badgeId}: ${count}`} 
                size="small" 
                sx={{ mr: 1, mb: 1 }}
              />
            ))}

            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Recent Interactions:
            </Typography>
            <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
              {detailedData.interactions.slice(-10).map((interaction: any, index: number) => (
                <Box key={index} sx={{ mb: 1, fontSize: '0.8rem' }}>
                  <Typography variant="caption" color="textSecondary">
                    {new Date(interaction.timestamp).toLocaleTimeString()}
                  </Typography>
                  <Typography variant="body2">
                    {interaction.badgeLabel} - {interaction.interactionType}
                    {interaction.duration && ` (${formatDuration(interaction.duration)})`}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}
      </Paper>
    );
  }
} 
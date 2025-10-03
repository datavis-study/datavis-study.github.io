import { BadgeTrackingData } from '../hooks/useBadgeTracking';

export interface BadgeTrackingSummary {
  totalInteractions: number;
  totalClicks: number;
  totalHoverTime: number;
  uniqueBadgesInteracted: number;
  averageHoverTime: number;
  mostClickedBadge: string | null;
  clickDistribution: Record<string, number>;
  interactionTimeline: Array<{
    timestamp: number;
    badgeId: string;
    badgeLabel: string;
    interactionType: string;
    duration?: number;
  }>;
}

export function generateTrackingSummary(trackingData: BadgeTrackingData): BadgeTrackingSummary {
  const totalInteractions = trackingData.interactions.length;
  const totalClicks = Object.values(trackingData.badgeClickCounts).reduce((sum, count) => sum + count, 0);
  const totalHoverTime = trackingData.totalTimeOnBadges;
  const uniqueBadgesInteracted = new Set(trackingData.interactions.map(i => i.badgeId)).size;
  
  const averageHoverTime = totalInteractions > 0 ? totalHoverTime / totalInteractions : 0;
  
  // Find most clicked badge
  let mostClickedBadge: string | null = null;
  let maxClicks = 0;
  Object.entries(trackingData.badgeClickCounts).forEach(([badgeId, count]) => {
    if (count > maxClicks) {
      maxClicks = count;
      mostClickedBadge = badgeId;
    }
  });

  // Create interaction timeline
  const interactionTimeline = trackingData.interactions
    .map(interaction => ({
      timestamp: interaction.timestamp,
      badgeId: interaction.badgeId,
      badgeLabel: interaction.badgeLabel,
      interactionType: interaction.interactionType,
      duration: interaction.duration,
    }))
    .sort((a, b) => a.timestamp - b.timestamp);

  return {
    totalInteractions,
    totalClicks,
    totalHoverTime,
    uniqueBadgesInteracted,
    averageHoverTime,
    mostClickedBadge,
    clickDistribution: trackingData.badgeClickCounts,
    interactionTimeline,
  };
}

export function exportTrackingDataAsCSV(trackingData: BadgeTrackingData): string {
  const headers = ['timestamp', 'badgeId', 'badgeLabel', 'interactionType', 'duration', 'coordinates'];
  const rows = trackingData.interactions.map(interaction => [
    new Date(interaction.timestamp).toISOString(),
    interaction.badgeId,
    interaction.badgeLabel,
    interaction.interactionType,
    interaction.duration || '',
    interaction.coordinates ? `${interaction.coordinates[0]},${interaction.coordinates[1]}` : '',
  ]);

  const csvContent = [headers, ...rows]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n');

  return csvContent;
}

export function exportTrackingDataAsJSON(trackingData: BadgeTrackingData): string {
  return JSON.stringify(trackingData, null, 2);
}

export function downloadTrackingData(trackingData: BadgeTrackingData, format: 'csv' | 'json' = 'json') {
  const content = format === 'csv' 
    ? exportTrackingDataAsCSV(trackingData)
    : exportTrackingDataAsJSON(trackingData);
  
  const blob = new Blob([content], { 
    type: format === 'csv' ? 'text/csv' : 'application/json' 
  });
  
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `badge-tracking-data.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
} 
import { useRef, useCallback, useEffect } from 'react';
import { useWindowEvents } from '../../../../store/hooks/useWindowEvents';
import { EventType } from '../../../../store/types';

export interface BadgeInteraction {
  badgeId: string;
  badgeLabel: string;
  interactionType: 'click' | 'hover_start' | 'hover_end' | 'drawer_open' | 'drawer_close' | 'tooltip_show' | 'tooltip_hide';
  timestamp: number;
  coordinates?: [number, number];
  duration?: number; // for hover events
  // Enhanced tracking properties
  badgeType?: string;
  badgeCategory?: string;
  badgeTopics?: string[];
  hasDetailedInfo?: boolean;
  hasExternalLink?: boolean;
  // Interaction context
  interactionContext?: {
    timeSinceLastInteraction?: number;
    totalInteractionsInSession?: number;
    previousInteractionType?: string;
    sessionDuration?: number;
  };
  // UI state at time of interaction
  uiState?: {
    drawerOpen?: boolean;
    tooltipVisible?: boolean;
    otherBadgesInteracted?: string[];
    scrollPosition?: number;
    viewportSize?: { width: number; height: number };
  };
}

export interface BadgeTrackingData {
  interactions: BadgeInteraction[];
  hoverStartTimes: Record<string, number>;
  totalTimeOnBadges: number;
  badgeClickCounts: Record<string, number>;
  drawerOpenTimes: Record<string, number>;
}

// New simplified interface for cleaner data
export interface SimplifiedBadgeTracking {
  badgeStats: Record<string, {
    badgeName: string;
    clicks: number;
    timeSpent: number; // in milliseconds
  }>;
  totalClicks: number;
  totalTimeSpent: number;
}

export function useBadgeTracking() {
  const windowEvents = useWindowEvents();
  const trackingData = useRef<BadgeTrackingData>({
    interactions: [],
    hoverStartTimes: {},
    totalTimeOnBadges: 0,
    badgeClickCounts: {},
    drawerOpenTimes: {},
  });

  // Track badge click
  const trackBadgeClick = useCallback((badgeId: string, badgeLabel: string, coordinates?: [number, number], badgeData?: any) => {
    const interaction: BadgeInteraction = {
      badgeId,
      badgeLabel,
      interactionType: 'click',
      timestamp: Date.now(),
      coordinates,
      // Enhanced tracking properties
      badgeType: badgeData?.badgeType,
      badgeCategory: badgeData?.type,
      badgeTopics: badgeData?.topics,
      hasDetailedInfo: !!badgeData?.detailedDescription,
      hasExternalLink: !!badgeData?.link,
      // Interaction context
      interactionContext: {
        timeSinceLastInteraction: trackingData.current.interactions.length > 0 ? 
          Date.now() - trackingData.current.interactions[trackingData.current.interactions.length - 1].timestamp : 0,
        totalInteractionsInSession: trackingData.current.interactions.length + 1,
        previousInteractionType: trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[trackingData.current.interactions.length - 1].interactionType : undefined,
        sessionDuration: Date.now() - (trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[0].timestamp : Date.now()),
      },
      // UI state
      uiState: {
        drawerOpen: Object.keys(trackingData.current.drawerOpenTimes).length > 0,
        tooltipVisible: Object.keys(trackingData.current.hoverStartTimes).length > 0,
        otherBadgesInteracted: Object.keys(trackingData.current.badgeClickCounts),
        viewportSize: { width: window.innerWidth, height: window.innerHeight },
      },
    };

    trackingData.current.interactions.push(interaction);
    
    // Update click count using badge name as key
    trackingData.current.badgeClickCounts[badgeLabel] = 
      (trackingData.current.badgeClickCounts[badgeLabel] || 0) + 1;

    // Add to window events for existing tracking system
    if (windowEvents && 'current' in windowEvents && windowEvents.current) {
      windowEvents.current.push([Date.now(), 'mousedown', coordinates || [0, 0]]);
      windowEvents.current.push([Date.now(), 'mouseup', coordinates || [0, 0]]);
    }

    console.log(`[BadgeTracking] Badge clicked: ${badgeLabel} (${badgeId})`);
  }, [windowEvents]);

  // Track hover start
  const trackHoverStart = useCallback((badgeId: string, badgeLabel: string, badgeData?: any) => {
    const timestamp = Date.now();
    trackingData.current.hoverStartTimes[badgeLabel] = timestamp; // Use badge name as key

    const interaction: BadgeInteraction = {
      badgeId,
      badgeLabel,
      interactionType: 'hover_start',
      timestamp,
      // Enhanced tracking properties
      badgeType: badgeData?.badgeType,
      badgeCategory: badgeData?.type,
      badgeTopics: badgeData?.topics,
      hasDetailedInfo: !!badgeData?.detailedDescription,
      hasExternalLink: !!badgeData?.link,
      // Interaction context
      interactionContext: {
        timeSinceLastInteraction: trackingData.current.interactions.length > 0 ? 
          timestamp - trackingData.current.interactions[trackingData.current.interactions.length - 1].timestamp : 0,
        totalInteractionsInSession: trackingData.current.interactions.length + 1,
        previousInteractionType: trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[trackingData.current.interactions.length - 1].interactionType : undefined,
        sessionDuration: timestamp - (trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[0].timestamp : timestamp),
      },
      // UI state
      uiState: {
        drawerOpen: Object.keys(trackingData.current.drawerOpenTimes).length > 0,
        tooltipVisible: true,
        otherBadgesInteracted: Object.keys(trackingData.current.badgeClickCounts),
        viewportSize: { width: window.innerWidth, height: window.innerHeight },
      },
    };

    trackingData.current.interactions.push(interaction);
    console.log(`[BadgeTracking] Hover started on: ${badgeLabel} (${badgeId})`);
  }, []);

  // Track hover end
  const trackHoverEnd = useCallback((badgeId: string, badgeLabel: string, badgeData?: any) => {
    const startTime = trackingData.current.hoverStartTimes[badgeLabel]; // Use badge name as key
    if (startTime) {
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      const interaction: BadgeInteraction = {
        badgeId,
        badgeLabel,
        interactionType: 'hover_end',
        timestamp: endTime,
        duration,
        // Enhanced tracking properties
        badgeType: badgeData?.badgeType,
        badgeCategory: badgeData?.type,
        badgeTopics: badgeData?.topics,
        hasDetailedInfo: !!badgeData?.detailedDescription,
        hasExternalLink: !!badgeData?.link,
        // Interaction context
        interactionContext: {
          timeSinceLastInteraction: trackingData.current.interactions.length > 0 ? 
            endTime - trackingData.current.interactions[trackingData.current.interactions.length - 1].timestamp : 0,
          totalInteractionsInSession: trackingData.current.interactions.length + 1,
          previousInteractionType: trackingData.current.interactions.length > 0 ? 
            trackingData.current.interactions[trackingData.current.interactions.length - 1].interactionType : undefined,
          sessionDuration: endTime - (trackingData.current.interactions.length > 0 ? 
            trackingData.current.interactions[0].timestamp : endTime),
        },
        // UI state
        uiState: {
          drawerOpen: Object.keys(trackingData.current.drawerOpenTimes).length > 0,
          tooltipVisible: false,
          otherBadgesInteracted: Object.keys(trackingData.current.badgeClickCounts),
          viewportSize: { width: window.innerWidth, height: window.innerHeight },
        },
      };

      trackingData.current.interactions.push(interaction);
      trackingData.current.totalTimeOnBadges += duration;
      delete trackingData.current.hoverStartTimes[badgeLabel];
      console.log(`[BadgeTracking] Hover ended on: ${badgeLabel} (${badgeId}) - Duration: ${duration}ms`);
    }
  }, []);

  // Track drawer open
  const trackDrawerOpen = useCallback((badgeId: string, badgeLabel: string, badgeData?: any) => {
    const timestamp = Date.now();
    trackingData.current.drawerOpenTimes[badgeLabel] = timestamp;

    const interaction: BadgeInteraction = {
      badgeId,
      badgeLabel,
      interactionType: 'drawer_open',
      timestamp,
      // Enhanced tracking properties
      badgeType: badgeData?.badgeType,
      badgeCategory: badgeData?.type,
      badgeTopics: badgeData?.topics,
      hasDetailedInfo: !!badgeData?.detailedDescription,
      hasExternalLink: !!badgeData?.link,
      // Interaction context
      interactionContext: {
        timeSinceLastInteraction: trackingData.current.interactions.length > 0 ? 
          timestamp - trackingData.current.interactions[trackingData.current.interactions.length - 1].timestamp : 0,
        totalInteractionsInSession: trackingData.current.interactions.length + 1,
        previousInteractionType: trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[trackingData.current.interactions.length - 1].interactionType : undefined,
        sessionDuration: timestamp - (trackingData.current.interactions.length > 0 ? 
          trackingData.current.interactions[0].timestamp : timestamp),
      },
      // UI state
      uiState: {
        drawerOpen: true,
        tooltipVisible: Object.keys(trackingData.current.hoverStartTimes).length > 0,
        otherBadgesInteracted: Object.keys(trackingData.current.badgeClickCounts),
        viewportSize: { width: window.innerWidth, height: window.innerHeight },
      },
    };

    trackingData.current.interactions.push(interaction);
    console.log(`[BadgeTracking] Drawer opened for: ${badgeLabel} (${badgeId})`);
  }, []);

  // Track drawer close
  const trackDrawerClose = useCallback((badgeId: string, badgeLabel: string, badgeData?: any) => {
    const startTime = trackingData.current.drawerOpenTimes[badgeLabel];
    if (startTime) {
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      const interaction: BadgeInteraction = {
        badgeId,
        badgeLabel,
        interactionType: 'drawer_close',
        timestamp: endTime,
        duration,
        // Enhanced tracking properties
        badgeType: badgeData?.badgeType,
        badgeCategory: badgeData?.type,
        badgeTopics: badgeData?.topics,
        hasDetailedInfo: !!badgeData?.detailedDescription,
        hasExternalLink: !!badgeData?.link,
        // Interaction context
        interactionContext: {
          timeSinceLastInteraction: trackingData.current.interactions.length > 0 ? 
            endTime - trackingData.current.interactions[trackingData.current.interactions.length - 1].timestamp : 0,
          totalInteractionsInSession: trackingData.current.interactions.length + 1,
          previousInteractionType: trackingData.current.interactions.length > 0 ? 
            trackingData.current.interactions[trackingData.current.interactions.length - 1].interactionType : undefined,
          sessionDuration: endTime - (trackingData.current.interactions.length > 0 ? 
            trackingData.current.interactions[0].timestamp : endTime),
        },
        // UI state
        uiState: {
          drawerOpen: false,
          tooltipVisible: Object.keys(trackingData.current.hoverStartTimes).length > 0,
          otherBadgesInteracted: Object.keys(trackingData.current.badgeClickCounts),
          viewportSize: { width: window.innerWidth, height: window.innerHeight },
        },
      };

      trackingData.current.interactions.push(interaction);
      delete trackingData.current.drawerOpenTimes[badgeLabel];
      console.log(`[BadgeTracking] Drawer closed for: ${badgeLabel} (${badgeId}) - Duration: ${duration}ms`);
    }
  }, []);

  // Get full tracking data
  const getTrackingData = useCallback((): BadgeTrackingData => {
    return {
      interactions: [...trackingData.current.interactions],
      hoverStartTimes: { ...trackingData.current.hoverStartTimes },
      totalTimeOnBadges: trackingData.current.totalTimeOnBadges,
      badgeClickCounts: { ...trackingData.current.badgeClickCounts },
      drawerOpenTimes: { ...trackingData.current.drawerOpenTimes },
    };
  }, []);

  // Get simplified tracking data
  const getSimplifiedTrackingData = useCallback((): SimplifiedBadgeTracking => {
    const badgeStats: Record<string, { badgeName: string; clicks: number; timeSpent: number }> = {};
    
    // Initialize badge stats from click counts
    Object.entries(trackingData.current.badgeClickCounts).forEach(([badgeName, clicks]) => {
      badgeStats[badgeName] = {
        badgeName,
        clicks,
        timeSpent: 0,
      };
    });

    // Calculate time spent from interactions
    trackingData.current.interactions.forEach(interaction => {
      if (!badgeStats[interaction.badgeLabel]) {
        badgeStats[interaction.badgeLabel] = {
          badgeName: interaction.badgeLabel,
          clicks: 0,
          timeSpent: 0,
        };
      }

      // Add time from hover and drawer interactions
      if (interaction.duration) {
        badgeStats[interaction.badgeLabel].timeSpent += interaction.duration;
      }
    });

    // Add any ongoing hover times
    Object.entries(trackingData.current.hoverStartTimes).forEach(([badgeName, startTime]) => {
      if (!badgeStats[badgeName]) {
        badgeStats[badgeName] = {
          badgeName,
          clicks: 0,
          timeSpent: 0,
        };
      }
      const currentTime = Date.now();
      badgeStats[badgeName].timeSpent += (currentTime - startTime);
    });

    // Add any ongoing drawer times
    Object.entries(trackingData.current.drawerOpenTimes).forEach(([badgeName, startTime]) => {
      if (!badgeStats[badgeName]) {
        badgeStats[badgeName] = {
          badgeName,
          clicks: 0,
          timeSpent: 0,
        };
      }
      const currentTime = Date.now();
      badgeStats[badgeName].timeSpent += (currentTime - startTime);
    });

    const totalClicks = Object.values(badgeStats).reduce((sum, badge) => sum + badge.clicks, 0);
    const totalTimeSpent = Object.values(badgeStats).reduce((sum, badge) => sum + badge.timeSpent, 0);

    return {
      badgeStats,
      totalClicks,
      totalTimeSpent,
    };
  }, []);

  // Get comprehensive tracking data for JSON export
  const getComprehensiveTrackingData = useCallback(() => {
    const simplifiedData = getSimplifiedTrackingData();
    const fullData = getTrackingData();
    
    // Group interactions by badge and create flat objects per badge
    const badgeInteractions = fullData.interactions.reduce((acc, interaction) => {
      const badgeId = interaction.badgeId;
      const badgeLabel = interaction.badgeLabel;
      
      if (!acc[badgeId]) {
        acc[badgeId] = {
          badgeId,
          badgeLabel,
          badgeType: interaction.badgeType,
          badgeCategory: interaction.badgeCategory,
          badgeTopics: interaction.badgeTopics,
          hasDetailedInfo: interaction.hasDetailedInfo,
          hasExternalLink: interaction.hasExternalLink,
          
          // Interaction counts
          totalInteractions: 0,
          totalClicks: 0,
          totalHoverStarts: 0,
          totalHoverEnds: 0,
          totalDrawerOpens: 0,
          totalDrawerCloses: 0,
          
          // Time tracking
          totalTimeSpent: 0,
          totalHoverTime: 0,
          totalDrawerTime: 0,
          
          // Individual interaction details (arrays)
          interactions: [],
          
          // First and last interaction info
          firstInteractionTime: null,
          lastInteractionTime: null,
          firstInteractionType: null,
          lastInteractionType: null,
        };
      }
      
      const badge = acc[badgeId];
      badge.totalInteractions++;
      
      // Count by interaction type
      switch (interaction.interactionType) {
        case 'click':
          badge.totalClicks++;
          break;
        case 'hover_start':
          badge.totalHoverStarts++;
          break;
        case 'hover_end':
          badge.totalHoverEnds++;
          badge.totalHoverTime += interaction.duration || 0;
          badge.totalTimeSpent += interaction.duration || 0;
          break;
        case 'drawer_open':
          badge.totalDrawerOpens++;
          break;
        case 'drawer_close':
          badge.totalDrawerCloses++;
          badge.totalDrawerTime += interaction.duration || 0;
          badge.totalTimeSpent += interaction.duration || 0;
          break;
      }
      
      // Track first and last interactions
      if (!badge.firstInteractionTime || interaction.timestamp < badge.firstInteractionTime) {
        badge.firstInteractionTime = interaction.timestamp;
        badge.firstInteractionType = interaction.interactionType;
      }
      if (!badge.lastInteractionTime || interaction.timestamp > badge.lastInteractionTime) {
        badge.lastInteractionTime = interaction.timestamp;
        badge.lastInteractionType = interaction.interactionType;
      }
      
      // Add detailed interaction info
      badge.interactions.push({
        interactionId: `${badgeId}_${interaction.timestamp}`,
        interactionType: interaction.interactionType,
        timestamp: interaction.timestamp,
        duration: interaction.duration || 0,
        timeSinceLastInteraction: interaction.interactionContext?.timeSinceLastInteraction || 0,
        totalInteractionsInSession: interaction.interactionContext?.totalInteractionsInSession || 0,
        previousInteractionType: interaction.interactionContext?.previousInteractionType || null,
        sessionDuration: interaction.interactionContext?.sessionDuration || 0,
        drawerOpen: interaction.uiState?.drawerOpen || false,
        tooltipVisible: interaction.uiState?.tooltipVisible || false,
        otherBadgesInteracted: interaction.uiState?.otherBadgesInteracted || [],
        viewportWidth: interaction.uiState?.viewportSize?.width || 0,
        viewportHeight: interaction.uiState?.viewportSize?.height || 0,
      });
      
      return acc;
    }, {} as Record<string, any>);

    // Calculate session analytics
    const sessionStart = fullData.interactions.length > 0 ? 
      Math.min(...fullData.interactions.map(i => i.timestamp)) : Date.now();
    const sessionEnd = Date.now();
    const sessionDuration = sessionEnd - sessionStart;

    return {
      // Summary statistics
      summary: {
        totalInteractions: fullData.interactions.length,
        totalClicks: simplifiedData.totalClicks,
        totalTimeSpent: simplifiedData.totalTimeSpent,
        totalTimeOnBadges: fullData.totalTimeOnBadges,
        uniqueBadgesInteracted: Object.keys(fullData.badgeClickCounts).length,
        sessionDuration,
        averageTimeBetweenInteractions: fullData.interactions.length > 1 ? 
          (sessionDuration / (fullData.interactions.length - 1)) : 0,
        interactionRate: sessionDuration > 0 ? (fullData.interactions.length / (sessionDuration / 1000)) : 0,
      },
      // Flat badge objects - one object per badge
      badgeInteractions,
      // Badge statistics
      badgeStats: simplifiedData.badgeStats,
      clickCounts: fullData.badgeClickCounts,
      // Timestamps
      sessionStartTime: sessionStart,
      sessionEndTime: sessionEnd,
    };
  }, [getSimplifiedTrackingData, getTrackingData]);

  // Reset tracking data
  const resetTracking = useCallback(() => {
    trackingData.current = {
      interactions: [],
      hoverStartTimes: {},
      totalTimeOnBadges: 0,
      badgeClickCounts: {},
      drawerOpenTimes: {},
    };
  }, []);

  // Clean up any lingering hover times when component unmounts
  useEffect(() => {
    return () => {
      // End any ongoing hovers
      Object.keys(trackingData.current.hoverStartTimes).forEach(badgeName => {
        const startTime = trackingData.current.hoverStartTimes[badgeName];
        if (startTime) {
          const duration = Date.now() - startTime;
          trackingData.current.totalTimeOnBadges += duration;
        }
      });
    };
  }, []);

  return {
    trackBadgeClick,
    trackHoverStart,
    trackHoverEnd,
    trackDrawerOpen,
    trackDrawerClose,
    getTrackingData,
    getSimplifiedTrackingData,
    getComprehensiveTrackingData,
    resetTracking,
  };
} 
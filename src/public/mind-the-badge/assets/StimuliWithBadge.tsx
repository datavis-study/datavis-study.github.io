import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Box, Drawer, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';
import BadgeInfoDrawer from './BadgeInfoDrawer';
import type { BadgeData } from './BadgeInfoDrawer';
import BadgeRow from './BadgeRow';
import { PREFIX } from '../../../utils/Prefix';
import { StimulusParams } from '../../../store/types';
import { useBadgeTracking } from './hooks/useBadgeTracking';
import { BadgeTrackingDisplay } from './components/BadgeTrackingDisplay';
import { initializeTrrack, Registry } from '@trrack/core';

interface BadgeStimulusParams {
  imageSrc?: string;
  detailedInformation?: string;
  badgeScale?: number;
  }

const StimuliWithBadge: React.FC<StimulusParams<BadgeStimulusParams>> = ({ parameters, setAnswer }) => {
  const imageSrc = parameters?.imageSrc;
  const imageAlt = 'Visualization stimuli';
  const detailedInformation = parameters?.detailedInformation;
  const badgeScale = typeof parameters?.badgeScale === 'number' ? parameters!.badgeScale! : 0.85;

  const [badges, setBadges] = useState<BadgeData[]>([]);
  const [selectedBadge, setSelectedBadge] = useState<BadgeData | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showTrackingDebug, setShowTrackingDebug] = useState(false);

  // Track stimulus start time for latency and engagement metrics
  const stimulusStartTimeRef = useRef<number>(Date.now());

  // Initialize badge tracking
  const {
    trackBadgeClick,
    trackHoverStart,
    trackHoverEnd,
    trackDrawerOpen,
    trackDrawerClose,
    getTrackingData,
    getSimplifiedTrackingData,
    getComprehensiveTrackingData,
  } = useBadgeTracking();

  // Initialize provenance (Trrack) to enable replay of badge interactions
  const { trrack, actions } = useMemo(() => {
    const reg = Registry.create();
    const logAction = reg.register('log', (state, payload: { kind: string; data: Record<string, unknown> }) => {
      if (!Array.isArray((state as any).events)) {
        (state as any).events = [];
      }
      (state as any).events.push({ t: Date.now(), ...payload });
      return state;
    });
    const trr = initializeTrrack({
      registry: reg,
      initialState: { events: [] },
    });
    return { trrack: trr, actions: { logAction } } as const;
  }, []);

  const logProv = useCallback((kind: string, data: Record<string, unknown>) => {
    trrack.apply('log', actions.logAction({ kind, data }));
  }, [trrack, actions]);

  // Compute per-badge aggregates, trial engagement, and coverage from tracking data
  const computeAnalysisFields = useCallback(() => {
    const simplifiedData = getSimplifiedTrackingData();
    const comprehensiveData = getComprehensiveTrackingData() as any;

    // Flatten all interactions across badges
    const allBadgeEntries: any[] = Object.values(comprehensiveData?.badgeInteractions || {});
    const allInteractions = allBadgeEntries.flatMap((b: any) => b.interactions || []);

    const timeOnStimulusMs = Math.max(0, Date.now() - stimulusStartTimeRef.current);

    // First hover and click across all badges
    let firstHoverTs: number | null = null;
    let firstClickTs: number | null = null;
    for (const entry of allBadgeEntries) {
      const hoverStartTs = (entry.interactions || [])
        .filter((i: any) => i.interactionType === 'hover_start')
        .map((i: any) => i.timestamp);
      const clickTs = (entry.interactions || [])
        .filter((i: any) => i.interactionType === 'click')
        .map((i: any) => i.timestamp);
      if (hoverStartTs.length) {
        const minHover = Math.min(...hoverStartTs);
        firstHoverTs = firstHoverTs === null ? minHover : Math.min(firstHoverTs, minHover);
      }
      if (clickTs.length) {
        const minClick = Math.min(...clickTs);
        firstClickTs = firstClickTs === null ? minClick : Math.min(firstClickTs, minClick);
      }
    }

    const timeToFirstBadgeHoverMs = firstHoverTs !== null ? Math.max(0, firstHoverTs - stimulusStartTimeRef.current) : null;
    const timeToFirstBadgeClickMs = firstClickTs !== null ? Math.max(0, firstClickTs - stimulusStartTimeRef.current) : null;

    const totalBadgeInteractions = allInteractions.length;
    const uniqueBadgesInteracted = Object.keys(comprehensiveData?.badgeInteractions || {}).length;
    const totalTimeOnBadges = comprehensiveData?.summary?.totalTimeOnBadges || 0;
    const proportionTimeOnBadges = timeOnStimulusMs > 0 ? (totalTimeOnBadges / timeOnStimulusMs) : 0;

    const trialEngagement = {
      timeOnStimulusMs,
      timeToFirstBadgeHoverMs,
      timeToFirstBadgeClickMs,
      totalBadgeInteractions,
      uniqueBadgesInteracted,
      proportionTimeOnBadges,
    } as any;

    // Per-badge aggregates
    const badgeAggregates: Record<string, any> = {};
    for (const entry of allBadgeEntries) {
      const badgeId = entry.badgeId;
      const interactions: any[] = entry.interactions || [];
      const hoverEnds = interactions.filter((i) => i.interactionType === 'hover_end');
      const drawerCloses = interactions.filter((i) => i.interactionType === 'drawer_close');
      const clicks = interactions.filter((i) => i.interactionType === 'click');
      const maxHoverTimeMs = hoverEnds.length ? Math.max(...hoverEnds.map((i) => i.duration || 0)) : 0;
      const firstClickTsForBadge = clicks.length ? Math.min(...clicks.map((i) => i.timestamp)) : null;
      const firstClickLatencyMs = firstClickTsForBadge !== null ? Math.max(0, firstClickTsForBadge - stimulusStartTimeRef.current) : null;

      badgeAggregates[badgeId] = {
        badgeId,
        badgeLabel: entry.badgeLabel,
        badgeType: entry.badgeType,
        badgeCategory: entry.badgeCategory,
        badgeTopics: entry.badgeTopics,
        clickCount: entry.totalClicks || 0,
        totalHoverCount: entry.totalHoverEnds || 0,
        totalHoverTimeMs: entry.totalHoverTime || 0,
        averageHoverTimeMs: (entry.totalHoverEnds || 0) > 0 ? (entry.totalHoverTime / entry.totalHoverEnds) : 0,
        maxHoverTimeMs,
        drawerOpenCount: entry.totalDrawerOpens || 0,
        totalDrawerOpenTimeMs: entry.totalDrawerTime || 0,
        averageDrawerOpenTimeMs: (entry.totalDrawerCloses || 0) > 0 ? (entry.totalDrawerTime / entry.totalDrawerCloses) : 0,
        firstClickLatencyMs,
        lastInteractionTs: entry.lastInteractionTime || null,
      } as any;
    }

    // Coverage/semantics
    const badgesSeenCount = uniqueBadgesInteracted;
    const badgesClickedCount = allBadgeEntries.filter((e) => (e.totalClicks || 0) > 0).length;
    const badgesWithDetailsViewedCount = allBadgeEntries.filter((e) => (e.totalDrawerOpens || 0) > 0 || (e.totalDrawerTime || 0) > 0).length;

    const categoriesSeenCounts: Record<string, number> = {};
    const topicsSeenCounts: Record<string, number> = {};
    for (const e of allBadgeEntries) {
      if (e.badgeCategory) {
        categoriesSeenCounts[e.badgeCategory] = (categoriesSeenCounts[e.badgeCategory] || 0) + 1;
      }
      (e.badgeTopics || []).forEach((t: string) => {
        topicsSeenCounts[t] = (topicsSeenCounts[t] || 0) + 1;
      });
    }

    // First badge interaction overall
    let firstBadgeId: string | null = null;
    let firstBadgeCategory: string | null = null;
    let firstBadgeTs: number | null = null;
    for (const e of allBadgeEntries) {
      const firstTs = e.firstInteractionTime || null;
      if (firstTs !== null && (firstBadgeTs === null || firstTs < firstBadgeTs)) {
        firstBadgeTs = firstTs;
        firstBadgeId = e.badgeId;
        firstBadgeCategory = e.badgeCategory || null;
      }
    }
    const firstBadge = firstBadgeId ? {
      id: firstBadgeId,
      category: firstBadgeCategory,
      latencyMs: firstBadgeTs !== null ? Math.max(0, firstBadgeTs - stimulusStartTimeRef.current) : null,
    } : null;

    const badgeCoverage = {
      badgesSeenCount,
      badgesClickedCount,
      badgesWithDetailsViewedCount,
      categoriesSeenCounts,
      topicsSeenCounts,
      firstBadge,
    } as any;

    return { simplifiedData, comprehensiveData, trialEngagement, badgeAggregates, badgeCoverage } as const;
  }, [getSimplifiedTrackingData, getComprehensiveTrackingData]);

  // Load badge data from JSON file
  useEffect(() => {
    if (!detailedInformation) {
      console.warn('[StimuliWithBadge] No detailedInformation path provided');
      return;
    }
    
    // Resolve the path for both local and deployed environments
    let resolvedPath = detailedInformation;
    if (!detailedInformation.startsWith('http')) {
      // Remove leading slash if present to avoid double slashes
      const cleanPath = detailedInformation.startsWith('/') ? detailedInformation.slice(1) : detailedInformation;
      resolvedPath = `${PREFIX}${cleanPath}`;
    }
    
    console.log('[StimuliWithBadge] Fetching badge data from:', resolvedPath);
    
    fetch(resolvedPath)
      .then((res) => res.json())
      .then((data) => {
        let loadedBadges: BadgeData[] = [];
        if (Array.isArray(data)) {
          loadedBadges = data;
        } else if (Array.isArray(data.badges)) {
          loadedBadges = data.badges;
        }
        setBadges(loadedBadges);
        console.log('[StimuliWithBadge] Loaded badges:', loadedBadges);
        if (loadedBadges.length === 0) {
          console.warn('[StimuliWithBadge] No badges found in badge data:', data);
        }
      })
      .catch((err) => {
        setBadges([]);
        console.error('[StimuliWithBadge] Error loading badge data:', err);
      });
  }, [detailedInformation]);

  const handleBadgeClick = (badge: BadgeData, coordinates?: [number, number]) => {
    setSelectedBadge(badge);
    setIsDrawerOpen(true);
    
    // Track the click with enhanced data
    trackBadgeClick(badge.id, badge.label, coordinates, badge);
    logProv('badge_click', { badgeId: badge.id, label: badge.label, coordinates });
    
    // Track drawer open
    trackDrawerOpen(badge.id, badge.label, badge);
    logProv('drawer_open', { badgeId: badge.id, label: badge.label });
  };

  // Extract base path from detailedInformation for relative markdown links
  const getBasePath = () => {
    if (!detailedInformation) return undefined;
    // Remove the filename and get the directory path
    const lastSlashIndex = detailedInformation.lastIndexOf('/');
    if (lastSlashIndex === -1) return undefined;
    return detailedInformation.substring(0, lastSlashIndex);
  };

  // Compute the correct image path
  let resolvedImageSrc = '';
  if (imageSrc) {
    if (imageSrc.startsWith('http')) {
      resolvedImageSrc = imageSrc;
    } else {
      // Remove leading slash if present to avoid double slashes
      const cleanPath = imageSrc.startsWith('/') ? imageSrc.slice(1) : imageSrc;
      resolvedImageSrc = `${PREFIX}${cleanPath}`;
    }
    console.log('[StimuliWithBadge] Resolved imageSrc:', resolvedImageSrc);
  } else {
    console.warn('[StimuliWithBadge] No imageSrc provided');
  }

  // Log when rendering badges
  useEffect(() => {
    if (badges.length > 0) {
      console.log('[StimuliWithBadge] Rendering badges:', badges.map((b) => b.label));
    } else {
      console.warn('[StimuliWithBadge] Badge row is empty');
    }
  }, [badges]);

  // Save tracking data to answers when component unmounts or when requested
  useEffect(() => {
    return () => {
      const { simplifiedData, comprehensiveData, trialEngagement, badgeAggregates, badgeCoverage } = computeAnalysisFields();
      
      // Always save tracking data, even if no interactions occurred
      setAnswer({
        status: true,
        provenanceGraph: trrack.graph.backend,
        answers: {
          badgeStats: simplifiedData.badgeStats as any,
          totalBadgeClicks: simplifiedData.totalClicks,
          totalBadgeTimeSpent: simplifiedData.totalTimeSpent,
          // Add comprehensive tracking data as proper objects
          badgeTrackingData: comprehensiveData as any,
          badgeInteractions: comprehensiveData.badgeInteractions as any,
          badgeClickCounts: comprehensiveData.clickCounts as any,
          totalTimeOnBadges: comprehensiveData.summary.totalTimeOnBadges,
          // Add summary statistics as proper object
          badgeTrackingSummary: comprehensiveData.summary as any,
          // Analysis additions
          trialEngagement: trialEngagement as any,
          badgeAggregates: badgeAggregates as any,
          badgeCoverage: badgeCoverage as any,
          // Always include all available badges as proper object
          availableBadges: badges.map(badge => ({
            id: badge.id,
            label: badge.label,
            description: badge.description,
            type: badge.type,
            badgeType: badge.badgeType,
            intent: badge.intent,
            topics: badge.topics,
            link: badge.link,
            avatar: badge.avatar,
            badgeName: badge.badgeName,
            descriptionPath: badge.descriptionPath,
            detailedDescription: badge.detailedDescription,
            // Add tooltip and drawer interaction tracking
            hasTooltip: true,
            hasDrawer: true,
            tooltipContent: badge.description,
            drawerContent: badge.detailedDescription || badge.description,
            // Add categorization for analysis
            category: badge.type,
            subcategory: badge.badgeType,
            tags: badge.topics,
            // Add metadata for analysis
            isInteractive: true,
            canBeClicked: true,
            canBeHovered: true,
            hasDetailedInfo: !!badge.detailedDescription,
            hasExternalLink: !!badge.link,
            // Add positioning info if available
            position: {
              row: 'bottom',
              order: badges.indexOf(badge)
            }
          })) as any,
        },
      });
    };
  }, [getSimplifiedTrackingData, getComprehensiveTrackingData, setAnswer, badges, trrack.graph.backend, computeAnalysisFields]);

  // Also save tracking data periodically to ensure we don't lose data
  useEffect(() => {
    const interval = setInterval(() => {
      const { simplifiedData, comprehensiveData, trialEngagement, badgeAggregates, badgeCoverage } = computeAnalysisFields();
      
      // Always save tracking data, regardless of interactions
      setAnswer({
        status: true,
        provenanceGraph: trrack.graph.backend,
        answers: {
          badgeStats: simplifiedData.badgeStats as any,
          totalBadgeClicks: simplifiedData.totalClicks,
          totalBadgeTimeSpent: simplifiedData.totalTimeSpent,
          // Add comprehensive tracking data as proper objects
          badgeTrackingData: comprehensiveData as any,
          badgeInteractions: comprehensiveData.badgeInteractions as any,
          badgeClickCounts: comprehensiveData.clickCounts as any,
          totalTimeOnBadges: comprehensiveData.summary.totalTimeOnBadges,
          // Add summary statistics as proper object
          badgeTrackingSummary: comprehensiveData.summary as any,
          // Analysis additions
          trialEngagement: trialEngagement as any,
          badgeAggregates: badgeAggregates as any,
          badgeCoverage: badgeCoverage as any,
          // Always include all available badges as proper object
          availableBadges: badges.map(badge => ({
            id: badge.id,
            label: badge.label,
            description: badge.description,
            type: badge.type,
            badgeType: badge.badgeType,
            intent: badge.intent,
            topics: badge.topics,
            link: badge.link,
            avatar: badge.avatar,
            badgeName: badge.badgeName,
            descriptionPath: badge.descriptionPath,
            detailedDescription: badge.detailedDescription,
            // Add tooltip and drawer interaction tracking
            hasTooltip: true,
            hasDrawer: true,
            tooltipContent: badge.description,
            drawerContent: badge.detailedDescription || badge.description,
            // Add categorization for analysis
            category: badge.type,
            subcategory: badge.badgeType,
            tags: badge.topics,
            // Add metadata for analysis
            isInteractive: true,
            canBeClicked: true,
            canBeHovered: true,
            hasDetailedInfo: !!badge.detailedDescription,
            hasExternalLink: !!badge.link,
            // Add positioning info if available
            position: {
              row: 'bottom',
              order: badges.indexOf(badge)
            }
          })) as any,
        },
      });
    }, 5000); // Save every 5 seconds

    return () => clearInterval(interval);
  }, [getSimplifiedTrackingData, getComprehensiveTrackingData, setAnswer, badges, trrack.graph.backend, computeAnalysisFields]);

  return (
    <Box sx={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      {/* Main stimuli image */}
      {resolvedImageSrc && (
        <img
          src={resolvedImageSrc}
          alt={imageAlt}
          style={{
            width: '100%',
            height: 'auto',
            display: 'block',
          }}
        />
      )}

      {/* Badges row below the image */}
      <BadgeRow 
        badges={badges} 
        onBadgeClick={handleBadgeClick} 
        selectedBadgeId={selectedBadge?.id || null}
        scale={badgeScale}
        onBadgeHoverStart={(badgeId, badgeLabel) => {
          const badge = badges.find(b => b.id === badgeId);
          trackHoverStart(badgeId, badgeLabel, badge);
          logProv('hover_start', { badgeId, label: badgeLabel });
        }}
        onBadgeHoverEnd={(badgeId, badgeLabel) => {
          const badge = badges.find(b => b.id === badgeId);
          trackHoverEnd(badgeId, badgeLabel, badge);
          logProv('hover_end', { badgeId, label: badgeLabel });
        }}
      />

      {/* Badge Information Panel */}
      <BadgeInfoDrawer
        badge={selectedBadge}
        open={isDrawerOpen}
        onClose={() => {
          if (selectedBadge) {
            trackDrawerClose(selectedBadge.id, selectedBadge.label, selectedBadge);
            logProv('drawer_close', { badgeId: selectedBadge.id, label: selectedBadge.label });
          }
          setIsDrawerOpen(false);
        }}
        basePath={getBasePath()}
      />

      {/* Debug tracking display (only in development) */}
      {process.env.NODE_ENV === 'development' && (
        <Box sx={{ position: 'fixed', bottom: 10, left: 10, zIndex: 1000 }}>
          <button 
            onClick={() => setShowTrackingDebug(!showTrackingDebug)}
            style={{ 
              padding: '8px 12px', 
              background: '#007bff', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            {showTrackingDebug ? 'Hide' : 'Show'} Tracking
          </button>
          {showTrackingDebug && (
            <BadgeTrackingDisplay 
              trackingData={getSimplifiedTrackingData()} 
              showDetails={true} 
            />
          )}
        </Box>
      )}
    </Box>
  );
};

export default StimuliWithBadge;

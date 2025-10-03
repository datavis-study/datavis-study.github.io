# Badge Tracking Integration

This document explains how the custom badge tracking system integrates with the Revisit framework's data collection workflow.

## Overview

The badge tracking system automatically integrates with the framework's data collection system, ensuring that all badge interaction data is properly stored in the participant JSON files.

## Data Structure

When a participant interacts with badges, the following comprehensive data is automatically stored in the JSON:

```json
{
  "answers": {
    "1_badges-global-warming-by-gas-and-source_2": {
      "answer": {
        "badgeStats": {
          "Known Data-Gap": {
            "badgeName": "Known Data-Gap",
            "clicks": 3,
            "timeSpent": 2314
          },
          "Uncertainty Not Visualized": {
            "badgeName": "Uncertainty Not Visualized", 
            "clicks": 1,
            "timeSpent": 1142
          }
        },
        "totalBadgeClicks": 5,
        "totalBadgeTimeSpent": 4938,
        "badgeTrackingData": {
          "summary": {
            "totalInteractions": 35,
            "totalClicks": 5,
            "totalTimeSpent": 4938,
            "totalTimeOnBadges": 4938,
            "uniqueBadgesInteracted": 3,
            "sessionDuration": 120000,
            "averageTimeBetweenInteractions": 3428,
            "interactionRate": 0.29
          },
          "badgeStats": {...},
          "interactions": [...],
          "clickCounts": {...},
          "hoverStartTimes": {...},
          "drawerOpenTimes": {...},
          "interactionTypes": {
            "click": 5,
            "hover_start": 15,
            "hover_end": 15,
            "drawer_open": 3,
            "drawer_close": 3
          },
          "badgeCategories": {
            "data-quality": 8,
            "uncertainty": 12
          },
          "badgeTypes": {
            "warning": 10,
            "info": 10
          },
          "interactionPatterns": [...],
          "sessionStartTime": 1754401470204,
          "sessionEndTime": 1754401474133,
          "uiStateHistory": [...],
          "contextAnalysis": {
            "mostActiveBadge": "Known Data-Gap",
            "mostActiveCategory": "uncertainty",
            "mostActiveType": "warning",
            "interactionSequence": ["hover_start", "hover_end", "click", "drawer_open", "drawer_close"],
            "badgeInteractionSequence": ["CC BY License", "Known Data-Gap", "Known Data-Gap", "Known Data-Gap"]
          }
        },
        "badgeInteractions": {
          "1": {
            "badgeId": "1",
            "badgeLabel": "Fossil CO₂ Only",
            "badgeType": "BINARY",
            "badgeCategory": "DATA",
            "badgeTopics": ["Scope"],
            "hasDetailedInfo": true,
            "hasExternalLink": false,
            "totalInteractions": 6,
            "totalClicks": 1,
            "totalHoverStarts": 2,
            "totalHoverEnds": 2,
            "totalDrawerOpens": 1,
            "totalDrawerCloses": 1,
            "totalTimeSpent": 1102,
            "totalHoverTime": 356,
            "totalDrawerTime": 746,
            "firstInteractionTime": 1754405387407,
            "lastInteractionTime": 1754405388121,
            "firstInteractionType": "hover_start",
            "lastInteractionType": "hover_end",
            "interactions": [
              {
                "interactionId": "1_1754405387407",
                "interactionType": "hover_start",
                "timestamp": 1754405387407,
                "duration": 0,
                "timeSinceLastInteraction": 17,
                "totalInteractionsInSession": 25,
                "previousInteractionType": "hover_end",
                "sessionDuration": 4725,
                "drawerOpen": false,
                "tooltipVisible": true,
                "otherBadgesInteracted": [],
                "viewportWidth": 1512,
                "viewportHeight": 823
              },
              {
                "interactionId": "1_1754405387623",
                "interactionType": "hover_end",
                "timestamp": 1754405387623,
                "duration": 216,
                "timeSinceLastInteraction": 216,
                "totalInteractionsInSession": 26,
                "previousInteractionType": "hover_start",
                "sessionDuration": 4941,
                "drawerOpen": false,
                "tooltipVisible": false,
                "otherBadgesInteracted": [],
                "viewportWidth": 1512,
                "viewportHeight": 823
              },
              {
                "interactionId": "1_1754405388094",
                "interactionType": "click",
                "timestamp": 1754405388094,
                "duration": 0,
                "timeSinceLastInteraction": 329,
                "totalInteractionsInSession": 28,
                "previousInteractionType": "hover_start",
                "sessionDuration": 5412,
                "drawerOpen": false,
                "tooltipVisible": true,
                "otherBadgesInteracted": [],
                "viewportWidth": 1512,
                "viewportHeight": 823
              },
              {
                "interactionId": "1_1754405388094",
                "interactionType": "drawer_open",
                "timestamp": 1754405388094,
                "duration": 0,
                "timeSinceLastInteraction": 0,
                "totalInteractionsInSession": 29,
                "previousInteractionType": "click",
                "sessionDuration": 5412,
                "drawerOpen": true,
                "tooltipVisible": true,
                "otherBadgesInteracted": ["Fossil CO₂ Only"],
                "viewportWidth": 1512,
                "viewportHeight": 823
              }
            ]
          },
          "3": {
            "badgeId": "3",
            "badgeLabel": "International‑$ Unit",
            "badgeType": "BINARY",
            "badgeCategory": "ANALYSIS",
            "badgeTopics": ["Units"],
            "hasDetailedInfo": true,
            "hasExternalLink": false,
            "totalInteractions": 8,
            "totalClicks": 4,
            "totalHoverStarts": 2,
            "totalHoverEnds": 2,
            "totalDrawerOpens": 4,
            "totalDrawerCloses": 4,
            "totalTimeSpent": 6360,
            "totalHoverTime": 458,
            "totalDrawerTime": 5902,
            "firstInteractionTime": 1754405386932,
            "lastInteractionTime": 1754405391234,
            "firstInteractionType": "hover_start",
            "lastInteractionType": "drawer_close",
            "interactions": [...]
          }
        },
        "badgeClickCounts": {
          "Known Data-Gap": 3,
          "Uncertainty Not Visualized": 1,
          "Aggregated Data": 1
        },
        "totalTimeOnBadges": 4938,
        "badgeTrackingSummary": {
          "totalInteractions": 35,
          "totalClicks": 5,
          "totalTimeSpent": 4938,
          "totalTimeOnBadges": 4938,
          "uniqueBadgesInteracted": 3,
          "sessionDuration": 120000,
          "averageTimeBetweenInteractions": 3428,
          "interactionRate": 0.29
        },
        "availableBadges": [
          {
            "id": "3",
            "label": "Known Data-Gap",
            "description": "This visualization has known data gaps",
            "type": "data-quality",
            "badgeType": "warning",
            "intent": "inform",
            "topics": ["data-quality", "gaps"],
            "link": "https://example.com",
            "avatar": null,
            "badgeName": "Known Data-Gap",
            "descriptionPath": "/path/to/description.md",
            "detailedDescription": "Detailed explanation of data gaps...",
            "hasTooltip": true,
            "hasDrawer": true,
            "tooltipContent": "This visualization has known data gaps",
            "drawerContent": "Detailed explanation of data gaps...",
            "category": "data-quality",
            "subcategory": "warning",
            "tags": ["data-quality", "gaps"],
            "isInteractive": true,
            "canBeClicked": true,
            "canBeHovered": true,
            "hasDetailedInfo": true,
            "hasExternalLink": true,
            "position": {
              "row": "bottom",
              "order": 0
            }
          }
        ]
      },
      "startTime": 1754401470204,
      "endTime": 1754401474133,
      "provenanceGraph": {...},
      "windowEvents": [...]
    }
  }
}
```

## Enhanced Tracking Properties

### Badge Information
- **Basic Properties**: `id`, `label`, `description`, `type`
- **Detailed Properties**: `badgeType`, `intent`, `topics`, `link`, `avatar`
- **Content Properties**: `descriptionPath`, `detailedDescription`
- **UI Properties**: `hasTooltip`, `hasDrawer`, `tooltipContent`, `drawerContent`
- **Analysis Properties**: `category`, `subcategory`, `tags`
- **Interaction Properties**: `isInteractive`, `canBeClicked`, `canBeHovered`
- **Feature Properties**: `hasDetailedInfo`, `hasExternalLink`
- **Position Properties**: `position.row`, `position.order`

### Flat Badge Tracking
Each badge has one flat JSON object containing all its interaction data:

- **Badge Properties**: `badgeId`, `badgeLabel`, `badgeType`, `badgeCategory`, `badgeTopics`, `hasDetailedInfo`, `hasExternalLink`
- **Interaction Counts**: `totalInteractions`, `totalClicks`, `totalHoverStarts`, `totalHoverEnds`, `totalDrawerOpens`, `totalDrawerCloses`
- **Time Tracking**: `totalTimeSpent`, `totalHoverTime`, `totalDrawerTime`
- **Timing Info**: `firstInteractionTime`, `lastInteractionTime`, `firstInteractionType`, `lastInteractionType`
- **Detailed Interactions**: `interactions` array with individual interaction details

### Analysis Benefits
- **Per-Badge Analysis**: Each badge has its own flat object with all interaction data
- **Individual Time Tracking**: See exact time spent on tooltips, drawers, etc. per badge
- **Multiple Interactions**: If a user opens a drawer twice, you see both entries in the interactions array
- **Easy Filtering**: Filter badges by total clicks, time spent, interaction types, etc.
- **Sequential Analysis**: Track interaction patterns within each badge

### Interaction Tracking
- **Basic**: `badgeId`, `
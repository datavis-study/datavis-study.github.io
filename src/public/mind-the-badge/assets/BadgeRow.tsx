import React from 'react';
import { Box } from '@mui/material';
import BinaryBadge from './badge-components/BinaryBadge';
import { BadgeData } from './BadgeInfoDrawer';
import { BiSolidInfoSquare } from "react-icons/bi";

interface BadgeRowProps {
  badges: BadgeData[];
  onBadgeClick: (badge: BadgeData, coordinates?: [number, number]) => void;
  selectedBadgeId: string | null;
  onBadgeHoverStart?: (badgeId: string, badgeLabel: string) => void;
  onBadgeHoverEnd?: (badgeId: string, badgeLabel: string) => void;
  scale?: number;
}

const intentColorMap: Record<string, string> = {
  CONFIRMATION: 'success',
  INFORMATION: 'info',
  WARNING: 'warning',
};

// Define intent priority for sorting (Confirmation → Information → Warning)
const intentPriority: Record<string, number> = {
  CONFIRMATION: 1,
  INFORMATION: 2,
  WARNING: 3,
};

const BadgeRow: React.FC<BadgeRowProps> = ({
  badges,
  onBadgeClick,
  selectedBadgeId,
  onBadgeHoverStart,
  onBadgeHoverEnd,
  scale = 1,
}) => {
  const verticalGapPx = Math.max(1, Math.round(4 * scale));
  // Sort badges by intent priority, then by label
  const sortedBadges = [...badges].sort((a, b) => {
    const intentA = (a.intent || '').toUpperCase();
    const intentB = (b.intent || '').toUpperCase();

    // First sort by intent priority
    const priorityA = intentPriority[intentA] || 999;
    const priorityB = intentPriority[intentB] || 999;

    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }

    // Then sort by label alphabetically
    return (a.label || '').localeCompare(b.label || '');
  });

  // Calculate optimal distribution for balanced rows
  const totalBadges = sortedBadges.length;
  const maxBadgesPerRow = 8;

  let numRows = 1;
  let badgesPerRow = totalBadges;

  if (totalBadges > maxBadgesPerRow) {
    numRows = Math.ceil(totalBadges / maxBadgesPerRow);
    badgesPerRow = Math.ceil(totalBadges / numRows);
  }

  // Distribute badges evenly across rows
  const badgeRows = [];
  for (let i = 0; i < numRows; i++) {
    const startIndex = i * badgesPerRow;
    const endIndex = Math.min(startIndex + badgesPerRow, totalBadges);
    badgeRows.push(sortedBadges.slice(startIndex, endIndex));
  }

  return (
    <Box
      sx={{
        mt: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: `${verticalGapPx}px`,
        alignItems: 'flex-end',
        width: '100%',
        maxWidth: '100%',
      }}
    >
      {badgeRows.map((row, rowIndex) => (
        <Box
          key={rowIndex}
          sx={{
            display: 'flex',
            flexDirection: 'row',
            gap: '4px',
            alignItems: 'center',
            justifyContent: 'flex-end',
            transform: `scale(${scale})`,
            transformOrigin: 'right center',
          }}
        >
          {row.map((badge, idx) => {
            const chipColor = intentColorMap[(badge.intent || '').toUpperCase()] || 'default';
            return (
              <Box
                key={badge.id || `${rowIndex}-${idx}`}
                onClick={(e) => onBadgeClick(badge, [e.clientX, e.clientY])}
                onMouseEnter={() => onBadgeHoverStart?.(badge.id, badge.label)}
                onMouseLeave={() => onBadgeHoverEnd?.(badge.id, badge.label)}
                sx={{
                  cursor: 'pointer',
                  borderRadius: 2,
                  transition: 'border 0.2s',
                }}
              >
                <BinaryBadge
                  badge={badge}
                  size="medium"
                  variant="outlined"
                  rightIconKey=''
                  chipColor={chipColor}
                />
              </Box>
            );
          })}
        </Box>
      ))}
    </Box>
  );
};

export default BadgeRow;

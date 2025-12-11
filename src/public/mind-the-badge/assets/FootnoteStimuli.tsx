import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { PREFIX } from '../../../utils/Prefix';
import { StimulusParams } from '../../../store/types';
import type { BadgeData } from './BadgeInfoDrawer';

interface FootnoteStimulusParams {
  /**
   * Path or URL to the static PNG stimulus.
   * Can be absolute (starting with http) or relative to the public root.
   */
  imageSrc?: string;
  /**
   * Optional short title shown above the stimulus.
   */
  title?: string;
  /**
   * Whether to render the lorem ipsum "footnote" text under the image.
   * Defaults to true.
   */
  showFootnoteText?: boolean;
  /**
   * Optional path to the badge JSON (same as used for badges),
   * so we can render label + tooltip text as "footnotes".
   */
  detailedInformation?: string;
  /**
   * Optional font size for the footnote text, in rem units.
   * Defaults to 0.65 (the original size).
   */
  footnoteFontSize?: number;
}

const resolveImageSrc = (imageSrc?: string): string => {
  if (!imageSrc) {
    // eslint-disable-next-line no-console
    console.warn('[FootnoteStimuli] No imageSrc provided');
    return '';
  }

  if (imageSrc.startsWith('http')) {
    return imageSrc;
  }

  const cleanPath = imageSrc.startsWith('/') ? imageSrc.slice(1) : imageSrc;
  return `${PREFIX}${cleanPath}`;
};

const FootnoteStimuli: React.FC<StimulusParams<FootnoteStimulusParams>> = ({
  parameters,
}) => {
  const {
    imageSrc,
    title,
    showFootnoteText = true,
    detailedInformation,
  } = parameters || {};
  const footnoteFontSize = parameters?.footnoteFontSize ?? 0.65;
  const resolvedImageSrc = resolveImageSrc(imageSrc);

  const [badges, setBadges] = useState<BadgeData[]>([]);

  // Load badge data from JSON file when we actually want to show footnote text
  useEffect(() => {
    if (!showFootnoteText || !detailedInformation) {
      setBadges([]);
      return;
    }

    let resolvedPath = detailedInformation;
    if (!detailedInformation.startsWith('http')) {
      const cleanPath = detailedInformation.startsWith('/') ? detailedInformation.slice(1) : detailedInformation;
      resolvedPath = `${PREFIX}${cleanPath}`;
    }

    // eslint-disable-next-line no-console
    console.log('[FootnoteStimuli] Fetching badge data from:', resolvedPath);

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
        if (loadedBadges.length === 0) {
          // eslint-disable-next-line no-console
          console.warn('[FootnoteStimuli] No badges found in badge data:', data);
        }
      })
      .catch((err) => {
        setBadges([]);
        // eslint-disable-next-line no-console
        console.error('[FootnoteStimuli] Error loading badge data:', err);
      });
  }, [detailedInformation, showFootnoteText]);

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: 750,
        mx: 'auto',
        textAlign: 'left',
      }}
    >
      {title && (
        <Typography variant="subtitle2" gutterBottom>
          {title}
        </Typography>
      )}

      {resolvedImageSrc && (
        <Box
          component="img"
          src={resolvedImageSrc}
          alt={title || 'Visualization with footnotes'}
          sx={{
            width: '100%',
            maxWidth: 750,
            height: 'auto',
            display: 'block',
            mx: 'auto',
          }}
        />
      )}

      {/* "Footnote" text: use badge label + description (tooltip) */}
      {showFootnoteText && badges.length > 0 && (
        <Box
          sx={{
            // Increased spacing below the image so footnotes don't feel cramped
            mt: 3,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              m: 0,
              px: 0,
              py: 0,
              textAlign: 'left',
              fontSize: `${footnoteFontSize}rem`,
              lineHeight: 1.2,
              color: '#4b5563', // dark grey
            }}
          >
            {badges.map((badge, index) => (
              <React.Fragment key={badge.id}>
                {badge.label}
                {': '}
                {badge.description}
                {index < badges.length - 1 ? ' ' : null}
              </React.Fragment>
            ))}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default FootnoteStimuli;


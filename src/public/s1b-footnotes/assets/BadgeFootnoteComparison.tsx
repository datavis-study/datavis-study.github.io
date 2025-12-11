import React from 'react';
import { Box } from '@mui/material';
import { StimulusParams } from '../../../store/types';
import FootnoteStimuli from '../../mind-the-badge/assets/FootnoteStimuli';
import StimuliWithBadge from '../../mind-the-badge/assets/StimuliWithBadge';

interface BadgeFootnoteComparisonParams {
  globalFootnoteImageSrc?: string;
  co2FootnoteImageSrc?: string;
  globalBadgesImageSrc?: string;
  globalBadgesDetailedInformation?: string;
  co2BadgesImageSrc?: string;
  co2BadgesDetailedInformation?: string;
  badgeScale?: number;
  /**
   * Which comparison row(s) to show.
   * - "global": only the global warming row
   * - "co2": only the CO₂ emissions row
   * - "both": show both rows (default / original behavior)
   */
  mode?: 'global' | 'co2' | 'both';
}

const BadgeFootnoteComparison: React.FC<StimulusParams<BadgeFootnoteComparisonParams>> = ({
  parameters,
  answers,
  provenanceState,
}) => {
  const {
    globalFootnoteImageSrc,
    co2FootnoteImageSrc,
    globalBadgesImageSrc,
    globalBadgesDetailedInformation,
    co2BadgesImageSrc,
    co2BadgesDetailedInformation,
    badgeScale,
    mode = 'both',
  } = parameters || {};

  const showGlobal = mode === 'both' || mode === 'global';
  const showCO2 = mode === 'both' || mode === 'co2';

  const panelSx = {
    // At the minimum 1024px width:
    // - gap xs=0 → 0px total
    // - panels xs=512px → 512 * 2 = 1024 (maximized width)
    // On larger screens (md+), make panels noticeably larger.
    // Slightly narrower on desktop to create more space between left/right stimuli
    width: { xs: 512, md: 650 },
    maxWidth: '100%',
    mx: 'auto',
  } as const;

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: { xs: 1400, md: 1600 },
        mx: 'auto',
        px: 0,
        // Extra padding so the framing lines don't hug the stimuli
        pt: { xs: 0, md: 2 },
        pb: { xs: 0, md: 2 },
        mb: { xs: 2, md: 3 },
        display: 'grid',
        gridTemplateColumns: { xs: '0fr', md: '0fr 1fr' },
        gap: { xs: 0, md: 0 },
        alignItems: 'flex-start',
        position: 'relative',
      }}
    >
      {/* Central vertical divider + bottom horizontal divider (desktop only, subtle and rounded) */}
      {(showGlobal || showCO2) && (
        <>
          {/* Vertical center line */}
          <Box
            sx={{
              display: { xs: 'none', md: 'block' },
              position: 'absolute',
              top: 4,      // a bit closer to top for slightly longer line
              bottom: 4,   // a bit closer to bottom for slightly longer line
              left: '50%',
              width: '2px',
              bgcolor: '#d1d5db', // lighter grey for lower salience
              borderRadius: 9999, // fully rounded ends
              pointerEvents: 'none',
            }}
          />
          {/* Bottom horizontal divider between stimuli and questions */}
          <Box
            sx={{
              display: { xs: 'none', md: 'block' },
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '2px',
              bgcolor: '#d1d5db',
              borderRadius: 9999,
              pointerEvents: 'none',
            }}
          />
        </>
      )}
      {showGlobal && (
        <>
          {/* Global warming: Footnotes (left) */}
          <Box
            sx={{
              ...panelSx,
              ml: 0,
              mr: 'auto', // pin left stimulus to the left edge of its column
            }}
          >
            <FootnoteStimuli
              parameters={{
                imageSrc: globalBadgesImageSrc ?? globalFootnoteImageSrc,
                detailedInformation: globalBadgesDetailedInformation,
                showFootnoteText: true,
              }}
              // No data collection needed here – this is a purely visual comparison
              // eslint-disable-next-line @typescript-eslint/no-empty-function
              setAnswer={() => {}}
              answers={answers}
              provenanceState={provenanceState}
            />
          </Box>

          {/* Global warming: Badges (right) */}
          <Box
            sx={{
              ...panelSx,
              ml: 'auto',
              mr: 0, // pin right stimulus to the right edge of its column
            }}
          >
            <StimuliWithBadge
              parameters={{
                imageSrc: globalBadgesImageSrc,
                detailedInformation: globalBadgesDetailedInformation,
                // Slightly smaller badges for this comparison view
                badgeScale: typeof badgeScale === 'number' ? badgeScale : 0.75,
              }}
              // eslint-disable-next-line @typescript-eslint/no-empty-function
              setAnswer={() => {}}
              answers={answers}
              provenanceState={provenanceState}
            />
          </Box>
        </>
      )}

      {showCO2 && (
        <>
          {/* CO₂ emissions: Badges (left) */}
          <Box
            sx={{
              ...panelSx,
              ml: 0,
              mr: 'auto', // pin left stimulus to the left edge of its column
            }}
          >
            <StimuliWithBadge
              parameters={{
                imageSrc: co2BadgesImageSrc,
                detailedInformation: co2BadgesDetailedInformation,
                badgeScale: typeof badgeScale === 'number' ? badgeScale : 0.8,
              }}
              // eslint-disable-next-line @typescript-eslint/no-empty-function
              setAnswer={() => {}}
              answers={answers}
              provenanceState={provenanceState}
            />
          </Box>

          {/* CO₂ emissions: Footnotes (right) */}
          <Box
            sx={{
              ...panelSx,
              ml: 'auto',
              mr: 0, // pin right stimulus to the right edge of its column
            }}
          >
            <FootnoteStimuli
              parameters={{
                imageSrc: co2BadgesImageSrc ?? co2FootnoteImageSrc,
                detailedInformation: co2BadgesDetailedInformation,
                showFootnoteText: true,
              }}
              // eslint-disable-next-line @typescript-eslint/no-empty-function
              setAnswer={() => {}}
              answers={answers}
              provenanceState={provenanceState}
            />
          </Box>
        </>
      )}
    </Box>
  );
};

export default BadgeFootnoteComparison;

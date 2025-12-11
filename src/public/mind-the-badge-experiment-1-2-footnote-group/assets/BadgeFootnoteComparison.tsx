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
  } = parameters || {};

  const panelSx = {
    // At the minimum 1024px width:
    // - gap xs=0 → 0px total
    // - panels xs=512px → 512 * 2 = 1024 (maximized width)
    // On larger screens (md+), make panels noticeably larger.
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
        display: 'grid',
        gridTemplateColumns: { xs: '0fr', md: '0fr 1fr' },
        gap: { xs: 0, md: 0 },
        alignItems: 'flex-start',
      }}
    >
      {/* Global warming: Footnotes (left) */}
      <Box sx={panelSx}>
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
      <Box sx={panelSx}>
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

      {/* CO₂ emissions: Footnotes (left) */}
      <Box sx={panelSx}>
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

      {/* CO₂ emissions: Badges (right) */}
      <Box sx={panelSx}>
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
    </Box>
  );
};

export default BadgeFootnoteComparison;

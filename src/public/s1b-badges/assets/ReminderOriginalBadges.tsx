import React from 'react';
import { Box } from '@mui/material';
import { StimulusParams } from '../../../store/types';
import StimuliWithBadge from '../../mind-the-badge/assets/StimuliWithBadge';

interface ReminderOriginalBadgesParams {
  globalImageSrc?: string;
  globalDetailedInformation?: string;
  co2ImageSrc?: string;
  co2DetailedInformation?: string;
  badgeScale?: number;
}

const ReminderOriginalBadges: React.FC<StimulusParams<ReminderOriginalBadgesParams>> = ({
  parameters,
  answers,
  provenanceState,
}) => {
  const {
    globalImageSrc = 'mind-the-badge/assets/stimuli-global-warming-projection/grp-badges/source.png',
    globalDetailedInformation = '/mind-the-badge/assets/stimuli-global-warming-projection/grp-badges/visualization-badges.json',
    co2ImageSrc = 'mind-the-badge/assets/stimuli-co2-emissions/grp-badges/source.png',
    co2DetailedInformation = '/mind-the-badge/assets/stimuli-co2-emissions/grp-badges/visualization-badges.json',
    badgeScale = 0.8,
  } = parameters || {};

  const panelSx = {
    width: '100%',
    maxWidth: 750,
    mx: 'auto',
    border: '1px solid #e5e7eb',
    borderRadius: 1.5,
    p: 1.5,
    bgcolor: '#ffffff',
  } as const;

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: 900,
        mx: 'auto',
        px: 0,
        pt: 1,
        pb: 1,
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: 3,
        alignItems: 'flex-start',
      }}
    >
      <Box sx={panelSx}>
        <StimuliWithBadge
          parameters={{
            imageSrc: globalImageSrc,
            detailedInformation: globalDetailedInformation,
            badgeScale,
          }}
          // This reminder screen is purely visual; we do not collect answers here.
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          setAnswer={() => {}}
          answers={answers}
          provenanceState={provenanceState}
        />
      </Box>

      <Box sx={panelSx}>
        <StimuliWithBadge
          parameters={{
            imageSrc: co2ImageSrc,
            detailedInformation: co2DetailedInformation,
            badgeScale,
          }}
          // This reminder screen is purely visual; we do not collect answers here.
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          setAnswer={() => {}}
          answers={answers}
          provenanceState={provenanceState}
        />
      </Box>
    </Box>
  );
};

export default ReminderOriginalBadges;


import React from 'react';
import { Box, Typography } from '@mui/material';
import { PREFIX } from '../../../utils/Prefix';
import { StimulusParams } from '../../../store/types';

interface FootnoteStimulusParams {
  imageSrc?: string;
  footnoteText?: string;
}

const StimuliWithFootnote: React.FC<StimulusParams<FootnoteStimulusParams>> = ({ parameters }) => {
  const imageSrc = parameters?.imageSrc;
  const footnoteText = parameters?.footnoteText;
  const imageAlt = 'Visualization stimuli';

  // Compute the correct image path (mirrors StimuliWithBadge logic)
  let resolvedImageSrc = '';
  if (imageSrc) {
    if (imageSrc.startsWith('http')) {
      resolvedImageSrc = imageSrc;
    } else {
      const cleanPath = imageSrc.startsWith('/') ? imageSrc.slice(1) : imageSrc;
      resolvedImageSrc = `${PREFIX}${cleanPath}`;
    }
  } else {
    // eslint-disable-next-line no-console
    console.warn('[StimuliWithFootnote] No imageSrc provided');
  }

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
      }}
    >
      {resolvedImageSrc && (
        <img
          src={resolvedImageSrc}
          alt={imageAlt}
          style={{
            width: '640px',
            height: 'auto',
            display: 'block',
            maxWidth: '100%',
          }}
        />
      )}

      {footnoteText && (
        <Box
          component="footer"
          sx={{
            mt: 1,
            width: '100%',
            maxWidth: 520,
            textAlign: 'left',
            color: 'text.secondary',
            fontStyle: 'italic',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              fontSize: '0.7rem',
              lineHeight: 1.3,
              display: 'block',
            }}
          >
            * {footnoteText}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default StimuliWithFootnote;



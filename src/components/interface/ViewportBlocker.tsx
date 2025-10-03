import { Alert, Overlay, Stack, Text, Title, Paper } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

type Props = {
  minWidth?: number;
  minHeight?: number;
  /** If true, treat narrow devices (phones) as unsupported regardless of pixel size */
  blockPhoneLike?: boolean;
  /** Optional custom message */
  message?: string;
};

const DEFAULT_MIN_WIDTH = 900;
const DEFAULT_MIN_HEIGHT = 600;

function isPhoneLikeDevice() {
  const userAgent = navigator.userAgent || navigator.vendor || (window as unknown as { opera?: string }).opera || '';
  const ua = String(userAgent).toLowerCase();
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  const narrowViewport = Math.min(window.innerWidth, window.innerHeight) < 600;
  const phoneHints = /(iphone|ipod|android.*mobile|windows phone)/.test(ua);
  return (phoneHints && hasTouch) || narrowViewport;
}

export function ViewportBlocker({
  minWidth = DEFAULT_MIN_WIDTH,
  minHeight = DEFAULT_MIN_HEIGHT,
  blockPhoneLike = true,
  message,
}: Props) {
  const [size, setSize] = useState<{ w: number; h: number }>({ w: window.innerWidth, h: window.innerHeight });

  useEffect(() => {
    const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const blocked = useMemo(() => {
    const tooSmall = size.w < minWidth || size.h < minHeight;
    const isPhone = blockPhoneLike && isPhoneLikeDevice();
    return tooSmall || isPhone;
  }, [size, minWidth, minHeight, blockPhoneLike]);

  if (!blocked) return null;

  const defaultMsg = `Your window is too small to continue. Please enlarge your browser window to at least ${minWidth} × ${minHeight} pixels on a tablet or desktop to proceed.`;

  return (
    <Overlay fixed zIndex={1000} blur={6} color="#000" opacity={1}>
      <Stack align="center" justify="center" style={{ height: '100vh' }} p="lg">
        <Paper withBorder shadow="xl" radius="md" p="xl" maw={720} style={{ backdropFilter: 'saturate(110%)', backgroundColor: 'rgba(255,255,255,0.95)' }}>
          <Stack gap="md">
            <Title order={2}>Screen too small</Title>
            <Alert color="yellow" radius="md" variant="light" icon={<IconAlertTriangle />}>
              <Text size="md">
                {message || defaultMsg}
              </Text>
              <Text size="sm" mt="sm" c="dimmed">
                Current viewport: {size.w} × {size.h}px
              </Text>
            </Alert>
            <Text size="sm" c="dimmed">Resize the window or switch to a larger device to continue.</Text>
          </Stack>
        </Paper>
      </Stack>
    </Overlay>
  );
}



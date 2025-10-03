import React, { useMemo } from 'react';
import { Box, Drawer, Typography, IconButton, Chip, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ReactMarkdown from 'react-markdown';
import useMarkdown from './useMarkdown';
import { PREFIX } from '../../../utils/Prefix';
import BinaryBadge from './badge-components/BinaryBadge';
import { useBadgeTracking } from './hooks/useBadgeTracking';

// AI Transparency Badges Data
const AI_TRANSPARENCY_BADGES = {
  "ai-derived-insight": {
    badgeType: "BINARY",
    id: "ai-derived-insight",
    label: "AI-Derived Insight",
    description: "This detailed information was generated using AI assistance.",
    type: "DATA",
    intent: "WARNING",
    topics: ["AI"],
    link: ""
  },
  "human-verified-ai": {
    badgeType: "BINARY",
    id: "human-verified-ai",
    label: "Human-Verified AI",
    description: "Two visualization experts have verified and validated this AI-generated content.",
    type: "DATA",
    intent: "CONFIRMATION",
    topics: ["AI"],
    link: ""
  }
};

export interface BadgeData {
  badgeType: string;
  id: string;
  label: string;
  description: string;
  type: string;
  intent: string;
  topics: string[];
  link: string;
  avatar?: any;
  badgeName?: string;
  descriptionPath?: string;
  detailedDescription?: string;
}

interface BadgeInfoDrawerProps {
  badge: BadgeData | null;
  open: boolean;
  onClose: () => void;
  basePath?: string;
}

const BadgeInfoDrawer: React.FC<BadgeInfoDrawerProps> = ({ badge, open, onClose, basePath }) => {
  const { trackBadgeClick, trackHoverStart, trackHoverEnd } = useBadgeTracking();

  const getFullMarkdownPath = (detailedDescription?: string) => {
    if (!detailedDescription) return undefined;

    // If it's already a full URL, return as is
    if (detailedDescription.startsWith('http')) {
      return detailedDescription;
    }

    // If it starts with a slash, it's an absolute path
    if (detailedDescription.startsWith('/')) {
      return `${PREFIX}${detailedDescription}`;
    }

    // If we have a basePath, construct the full path
    if (basePath) {
      // Remove leading slash from basePath if present
      const cleanBasePath = basePath.startsWith('/') ? basePath.slice(1) : basePath;
      return `${PREFIX}${cleanBasePath}/${detailedDescription}`;
    }

    // Fallback: try with PREFIX
    return `${PREFIX}${detailedDescription}`;
  };

  const { content, loading, error } = useMarkdown(getFullMarkdownPath(badge?.detailedDescription));

  // Calculate dynamic width based on content
  const dynamicWidth = useMemo(() => {
    if (!badge) return 420;

    const hasDetailedContent = badge.detailedDescription && content && content.length > 0;
    const contentLength = content?.length || 0;
    const descriptionLength = badge.description?.length || 0;
    const topicsCount = badge.topics?.length || 0;

    // Base width for minimal content
    let width = 360;

    // Adjust based on content complexity
    if (hasDetailedContent) {
      if (contentLength > 2000) width = 520; // Very long content
      else if (contentLength > 1000) width = 480; // Long content
      else if (contentLength > 500) width = 440; // Medium content
      else width = 400; // Short detailed content
    } else if (descriptionLength > 200) {
      width = 420; // Long description
    } else if (descriptionLength > 100) {
      width = 400; // Medium description
    } else {
      width = 380; // Short description
    }

    // Adjust for many topics
    if (topicsCount > 6) width += 20;
    else if (topicsCount > 3) width += 10;

    // Ensure minimum and maximum bounds
    return Math.max(360, Math.min(width, 600));
  }, [badge, content]);

  // Calculate if content is extensive
  const isExtensiveContent = useMemo(() => {
    if (!content) return false;
    return content.length > 1500 || (content.match(/\n/g) || []).length > 20;
  }, [content]);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: dynamicWidth,
          maxWidth: '95vw',
          minWidth: 360,
          padding: 0,
          marginTop: 0,
          marginRight: 0,
          marginBottom: 0,
          marginLeft: 'auto',
          zIndex: 9999,
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15), 0 6px 20px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
          borderTopLeftRadius: 24,
          borderBottomLeftRadius: 24,
          borderTopRightRadius: 0,
          borderBottomRightRadius: 0,
          border: '1px solid rgba(255, 255, 255, 0.9)',
          borderRight: 'none',
          backdropFilter: 'blur(24px)',
          position: 'fixed',
          right: 0,
          top: 0,
          bottom: 0,
          height: '100vh',
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%)',
            borderRadius: 'inherit',
            pointerEvents: 'none',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            width: '1px',
            height: '100%',
            background: 'linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.6) 50%, transparent 100%)',
            borderRadius: 'inherit',
            pointerEvents: 'none',
          },
        },
      }}
    >
      <Box
        sx={{
          width: '100%',
          p: isExtensiveContent ? 4 : 3.5,
          position: 'relative',
          minHeight: '100vh',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 50%, rgba(241, 245, 249, 0.95) 100%)',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: 'linear-gradient(90deg, transparent 0%, rgba(59, 130, 246, 0.3) 50%, transparent 100%)',
          },
        }}
      >
        {/* Header with close button */}
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: isExtensiveContent ? 3 : 2.5,
          flexShrink: 0,
        }}>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: '#1a1a1a',
              fontSize: isExtensiveContent ? '1.7rem' : '1.6rem',
              lineHeight: 1.2,
              letterSpacing: '-0.02em',
              background: 'linear-gradient(135deg, #1a1a1a 0%, #2d3748 50%, #4a5568 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              flex: 1,
              pr: 2,
            }}
          >
            {badge?.label}
          </Typography>
          <IconButton
            onClick={onClose}
            sx={{
              color: '#64748b',
              backgroundColor: 'rgba(255, 255, 255, 0.6)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.8)',
              flexShrink: 0,
              '&:hover': {
                color: '#1e293b',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                transform: 'scale(1.05)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              },
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            aria-label="Close"
          >
            <CloseIcon fontSize="medium" />
          </IconButton>
        </Box>

        {/* Metadata section */}
        {badge && (
          <Box sx={{
            mb: 2,
            display: 'flex',
            flexWrap: 'wrap',
            gap: 0.5,
            alignItems: 'center'
          }}>
            <Chip
              label={badge.intent}
              size="small"
              sx={{
                backgroundColor: '#f1f5f9',
                color: '#475569',
                fontWeight: 500,
                fontSize: '0.7rem',
                height: '20px',
                '& .MuiChip-label': { px: 1 },
              }}
            />
            <Chip
              label={badge.type}
              size="small"
              sx={{
                backgroundColor: '#fef3c7',
                color: '#92400e',
                fontWeight: 500,
                fontSize: '0.7rem',
                height: '20px',
                '& .MuiChip-label': { px: 1 },
              }}
            />
            {badge.topics && badge.topics.length > 0 && badge.topics.map((topic: string, idx: number) => (
              <Chip
                key={idx}
                label={`#${topic}`}
                size="small"
                sx={{
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  fontWeight: 400,
                  fontSize: '0.65rem',
                  height: '18px',
                  '& .MuiChip-label': { px: 0.8 },
                }}
              />
            ))}
          </Box>
        )}

        {/* Content area */}
        <Box sx={{
          flex: 1,
          mb: isExtensiveContent ? 3 : 2.5,
          fontSize: isExtensiveContent ? '1rem' : '0.95rem',
          color: '#374151',
          lineHeight: 1.6,
          overflow: 'auto',
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(0, 0, 0, 0.02)',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(0, 0, 0, 0.15)',
            borderRadius: '3px',
            '&:hover': {
              background: 'rgba(0, 0, 0, 0.25)',
            },
          },
        }}>
          {badge?.detailedDescription ? (
            loading ? (
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                py: 4,
                color: '#6b7280',
                fontStyle: 'italic',
              }}>
                <Typography>Loading content...</Typography>
              </Box>
            ) : error ? (
              <Typography sx={{ color: '#ef4444' }}>
                {error}
              </Typography>
            ) : (
              <Box sx={{
                '& p': {
                  mb: isExtensiveContent ? 2 : 1.5,
                  fontSize: isExtensiveContent ? '1rem' : '0.95rem',
                  maxWidth: '100%',
                  wordWrap: 'break-word',
                },
                '& h1, & h2, & h3': {
                  color: '#1f2937',
                  fontWeight: 600,
                  mb: isExtensiveContent ? 1.5 : 1,
                  mt: isExtensiveContent ? 3 : 2,
                  wordWrap: 'break-word',
                },
                '& h1': { fontSize: isExtensiveContent ? '1.4rem' : '1.25rem' },
                '& h2': { fontSize: isExtensiveContent ? '1.2rem' : '1.1rem' },
                '& h3': { fontSize: isExtensiveContent ? '1.1rem' : '1rem' },
                '& ul, & ol': {
                  pl: isExtensiveContent ? 3 : 2,
                  mb: isExtensiveContent ? 2 : 1.5,
                  wordWrap: 'break-word',
                },
                '& li': { mb: isExtensiveContent ? 0.8 : 0.5 },
                '& code': {
                  backgroundColor: '#f3f4f6',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  fontSize: isExtensiveContent ? '0.9rem' : '0.85rem',
                  wordBreak: 'break-all',
                },
                '& pre': {
                  backgroundColor: '#f9fafb',
                  padding: isExtensiveContent ? '16px' : '12px',
                  borderRadius: '6px',
                  overflow: 'auto',
                  border: '1px solid #e5e7eb',
                  fontSize: isExtensiveContent ? '0.9rem' : '0.85rem',
                },
                '& blockquote': {
                  borderLeft: '4px solid #e5e7eb',
                  pl: 2,
                  ml: 0,
                  fontStyle: 'italic',
                  color: '#6b7280',
                },
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: isExtensiveContent ? '0.9rem' : '0.85rem',
                },
                '& th, & td': {
                  border: '1px solid #e5e7eb',
                  padding: '8px 12px',
                  textAlign: 'left',
                },
                '& th': {
                  backgroundColor: '#f9fafb',
                  fontWeight: 600,
                },
              }}>
                <ReactMarkdown
                  components={{
                    table: ({ children, ...props }) => (
                      <Table {...props} sx={{ width: '100%', borderCollapse: 'collapse' }}>
                        {children}
                      </Table>
                    ),
                    thead: ({ children, ...props }) => (
                      <TableHead {...props}>
                        {children}
                      </TableHead>
                    ),
                    tbody: ({ children, ...props }) => (
                      <TableBody {...props}>
                        {children}
                      </TableBody>
                    ),
                    tr: ({ children, ...props }) => (
                      <TableRow {...props}>
                        {children}
                      </TableRow>
                    ),
                    th: ({ children, align, ...props }) => (
                      <TableCell
                        {...props}
                        component="th"
                        align={align === 'center' ? 'center' : align === 'right' ? 'right' : 'left'}
                        sx={{
                          border: '1px solid #e5e7eb',
                          padding: '8px 12px',
                          backgroundColor: '#f9fafb',
                          fontWeight: 600,
                        }}
                      >
                        {children}
                      </TableCell>
                    ),
                    td: ({ children, align, ...props }) => (
                      <TableCell
                        {...props}
                        align={align === 'center' ? 'center' : align === 'right' ? 'right' : 'left'}
                        sx={{
                          border: '1px solid #e5e7eb',
                          padding: '8px 12px',
                        }}
                      >
                        {children}
                      </TableCell>
                    ),
                  }}
                >
                  {content}
                </ReactMarkdown>
              </Box>
            )
          ) : (
            <Typography
              variant="body1"
              sx={{
                color: '#4b5563',
                fontSize: isExtensiveContent ? '1rem' : '0.95rem',
                lineHeight: 1.6,
                wordWrap: 'break-word',
              }}
            >
              {badge?.description}
            </Typography>
          )}
        </Box>
      </Box>
    </Drawer>
  );
};

export default BadgeInfoDrawer;

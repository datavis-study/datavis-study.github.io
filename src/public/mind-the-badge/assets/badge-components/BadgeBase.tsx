import React from 'react';
import { Avatar, Box, Chip, Tooltip } from '@mui/material';
import * as Icons from '@mui/icons-material';
import { getMuiIcon } from "./utils/getIcon";
import { icon_intent_map, icon_scope_map } from "./utils/iconMappings.js";

interface BadgeBaseProps {
    label: string;
    description?: string;
    avatar?: any;
    intent?: string;
    type?: string;
    size?: 'small' | 'medium' | 'large';
    variant?: 'filled' | 'outlined';
    leftIconKey?: string;
    rightIconKey?: string;
    chipColor?: string;
    chipSx?: any;
}

function mapChipSize(customSize: string) {
    switch (customSize) {
        case 'small':
            return { muiSize: 'small' as const, hideLabel: true };
        case 'medium':
            return { muiSize: 'small' as const, hideLabel: false };
        case 'large':
            return { muiSize: 'medium' as const, hideLabel: false };
        default:
            return { muiSize: 'medium' as const, hideLabel: false };
    }
}

function resolveIcon(key: string, { intent, type }: { intent?: string; type?: string }, size: string) {
    if (key !== 'none') {
        let iconValue = "";
        if (key === 'iconIntent') {
            iconValue = icon_intent_map[intent || ''] || "";
        } else if (key === 'iconScope') {
            iconValue = icon_scope_map[type || ''] || "";
        }
        return iconValue ? getMuiIcon(iconValue, size) : null;
    }
    return null;
}
const BadgeBase: React.FC<BadgeBaseProps> = ({
    label,
    description = '',
    intent,
    type,
    size = 'medium',
    variant = 'filled',
    leftIconKey = 'iconIntent',
    rightIconKey = 'iconIntent',
    chipColor = 'default',
    chipSx = {},
}) => {
    const { muiSize, hideLabel } = mapChipSize(size);
    const leftIcon = resolveIcon(leftIconKey, { intent, type }, size);
    const rightIcon = resolveIcon(rightIconKey, { intent, type }, size);
    const displayLabel = hideLabel ? undefined : label;

    console.info('[BadgeBase] intent:', intent, 'type:', type, 'leftIconKey:', leftIconKey, 'rightIconKey:', rightIconKey);
    console.info('[BadgeBase] leftIcon:', leftIcon, 'rightIcon:', rightIcon);

    return (
        <Box>
            <Tooltip
                title={description}
                arrow
                placement="top"
                enterDelay={200}
                enterNextDelay={200}
                leaveDelay={0}
                componentsProps={{
                    tooltip: {
                        sx: {
                            background: 'linear-gradient(135deg, rgba(15, 15, 15, 0.88) 0%, rgba(30, 30, 30, 0.88) 100%)',
                            color: 'rgba(255, 255, 255, 0.95)',
                            fontSize: '0.8rem !important',
                            fontWeight: 400,
                            lineHeight: 1.4,
                            padding: '4px 8px',
                            borderRadius: '6px',
                            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06)',
                            maxWidth: '200px',
                            textAlign: 'center',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255, 255, 255, 0.06)',
                            fontFamily: '"Apfel Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                            letterSpacing: '0.02em',
                            '& .MuiTooltip-arrow': {
                                color: 'rgba(15, 15, 15, 0.88)',
                                filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.06))',
                            },
                            animation: 'tooltipFadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                            '@keyframes tooltipFadeIn': {
                                '0%': {
                                    opacity: 0,
                                    transform: 'translateY(6px) scale(0.98)',
                                    filter: 'blur(2px)',
                                },
                                '100%': {
                                    opacity: 1,
                                    transform: 'translateY(0) scale(1)',
                                    filter: 'blur(0px)',
                                },
                            },
                        },
                    },
                }}
            >
                <Chip
                    label={displayLabel}
                    size={muiSize}
                    variant={variant}
                    icon={leftIconKey !== 'avatar' ? leftIcon || undefined : undefined}
                    deleteIcon={rightIcon || undefined}
                    onDelete={rightIcon ? (event) => {
                        event.stopPropagation();
                    } : undefined}
                    clickable
                    color={chipColor as any}
                    sx={{
                        ...chipSx,
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&::before': {
                            content: '""',
                            position: 'absolute',
                            top: 0,
                            left: '-100%',
                            width: '100%',
                            height: '100%',
                            background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent)',
                            transition: 'left 0.4s ease',
                        },
                        '&:hover': {
                            transform: 'translateY(-1px) scale(1.01)',
                            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.08)',
                            '&::before': {
                                left: '100%',
                            },
                        },
                        '&:active': {
                            transform: 'translateY(0px) scale(1.005)',
                            transition: 'all 0.1s ease',
                        },
                        ...(hideLabel && {
                            pl: 0,
                            pr: 0,
                            minWidth: 26,
                            '& .MuiChip-label': { display: 'none' },
                            '& .MuiChip-icon': { marginLeft: 0, marginRight: 0 },
                        }),
                    }}
                />
            </Tooltip>
        </Box>
    );
};

export default BadgeBase;

import React from 'react';
import BadgeBase from './BadgeBase';

interface BadgeData {
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
}

interface BinaryBadgeProps {
  badge: BadgeData;
  leftIconKey?: string;
  rightIconKey?: string;
  size?: 'small' | 'medium' | 'large';
  variant?: 'filled' | 'outlined';
  chipColor?: string;
  scale?: number;
  [key: string]: any;
}

const BinaryBadge: React.FC<BinaryBadgeProps> = function BinaryBadge(
    { badge, leftIconKey, rightIconKey, scale = 1, ...otherProps }
) {
    return (
        <div style={{ display: 'inline-block' }}>
            <BadgeBase
                label={badge.label}
                description={badge.description}
                avatar={badge.avatar}
                intent={badge.intent}
                type={badge.type}
                leftIconKey={leftIconKey}
                rightIconKey={rightIconKey}
                {...otherProps}
            />
        </div>
    );
};

export default BinaryBadge;

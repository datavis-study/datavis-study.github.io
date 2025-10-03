import React from "react";
import { CheckCircle, Warning, DatasetOutlined, AnalyticsOutlined, BubbleChartOutlined, TouchAppOutlined, QueryStatsOutlined } from "@mui/icons-material";
import { BiSolidInfoSquare } from "react-icons/bi";

export function getMuiIcon(iconName: string, size: string): React.ReactElement | null {
    if (!iconName) return null;

    if (iconName === 'Info') {
        const iconSize = size === 'large' ? 22 : 18;
        return <BiSolidInfoSquare size={iconSize} />;
    }

    const iconMap: { [key: string]: React.ComponentType<any> } = {
        'CheckCircle': CheckCircle,
        'Warning': Warning,
        'DatasetOutlined': DatasetOutlined,
        'AnalyticsOutlined': AnalyticsOutlined,
        'BubbleChartOutlined': BubbleChartOutlined,
        'TouchAppOutlined': TouchAppOutlined,
        'QueryStatsOutlined': QueryStatsOutlined
    };

    const IconComponent = iconMap[iconName];
    if (!IconComponent) return null;

    return React.createElement(IconComponent, { fontSize: "small" });
} 
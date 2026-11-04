import type { CSSProperties } from "react";

type IconProps = {
  size?: number;
  color?: string;
  style?: CSSProperties;
};

const wrap = (size: number, style?: CSSProperties): CSSProperties => ({
  width: size,
  height: size,
  flexShrink: 0,
  display: "inline-block",
  verticalAlign: "middle",
  ...style,
});

export const Icon = {
  chevronDown: ({ size = 14, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M6 9l6 6 6-6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chevronLeft: ({ size = 14, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M15 6l-6 6 6 6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chevronRight: ({ size = 14, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M9 6l6 6-6 6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  pin: ({ size = 14, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M12 22s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      <circle cx="12" cy="10" r="2.5" stroke={color} strokeWidth="2" />
    </svg>
  ),
  search: ({ size = 18, color = "#9ca3af", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <circle cx="11" cy="11" r="7" stroke={color} strokeWidth="2" />
      <path d="M20 20l-3.5-3.5" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  chat: ({ size = 20, color = "#5c6670", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M21 12a8 8 0 01-11.6 7.15L4 20l1-4.5A8 8 0 1121 12z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  ),
  heart: ({ size = 20, color = "#5c6670", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M20.8 6.6a5 5 0 00-8.8-2.2 5 5 0 00-8.8 2.2c0 3.9 4.4 7.5 8.8 11.2 4.4-3.7 8.8-7.3 8.8-11.2z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  ),
  heartFill: ({ size = 20, color = "#ef4444", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill={color}>
      <path d="M20.8 6.6a5 5 0 00-8.8-2.2 5 5 0 00-8.8 2.2c0 3.9 4.4 7.5 8.8 11.2 4.4-3.7 8.8-7.3 8.8-11.2z" />
    </svg>
  ),
  user: ({ size = 20, color = "#5c6670", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="8" r="4" stroke={color} strokeWidth="1.8" />
      <path d="M4 21c0-4 4-6 8-6s8 2 8 6" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  home: ({ size = 22, color = "#6b7280", style }: IconProps = {}) => {
    const filled = color === "#2563eb";
    return (
      <svg style={wrap(size, style)} viewBox="0 0 24 24" fill={filled ? color : "none"}>
        <path d="M3 11l9-7 9 7v9a2 2 0 01-2 2h-4v-6h-6v6H5a2 2 0 01-2-2v-9z"
          stroke={color} strokeWidth="1.8" strokeLinejoin="round" fill={filled ? color : "none"} />
      </svg>
    );
  },
  megaphone: ({ size = 22, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M3 10v4a1 1 0 001 1h3l7 4V5l-7 4H4a1 1 0 00-1 1z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M18 8a5 5 0 010 8" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  plus: ({ size = 24, color = "#ffffff", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M12 5v14M5 12h14" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  ),
  clipboard: ({ size = 22, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <rect x="5" y="4" width="14" height="17" rx="2" stroke={color} strokeWidth="1.8" />
      <path d="M9 3h6v3H9z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M8 10h8M8 14h8M8 18h5" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  bell: ({ size = 20, color = "#5c6670", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M6 8a6 6 0 1112 0v5l2 3H4l2-3V8z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M10 20a2 2 0 004 0" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  filter: ({ size = 18, color = "#374151", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M4 5h16M6 12h12M10 19h4" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  x: ({ size = 18, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M6 6l12 12M18 6L6 18" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  check: ({ size = 18, color = "#16a34a", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M5 12l5 5 9-11" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  edit: ({ size = 18, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M4 20h4l10-10-4-4L4 16v4z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M14 6l4 4" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  trash: ({ size = 18, color = "#dc2626", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M5 7h14M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  book: ({ size = 20, color = "#6b7280", style }: IconProps = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 24 24" fill="none">
      <path d="M4 5a2 2 0 012-2h12v18H6a2 2 0 01-2-2V5z" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M8 7h6M8 11h6" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  logo: ({ size = 42, style }: { size?: number; style?: CSSProperties } = {}) => (
    <svg style={wrap(size, style)} viewBox="0 0 48 48" fill="none">
      <path d="M6 10h14a4 4 0 014 4v26a3 3 0 00-3-3H6V10z" fill="#2563eb" fillOpacity="0.15" stroke="#2563eb" strokeWidth="2" strokeLinejoin="round" />
      <path d="M42 10H28a4 4 0 00-4 4v26a3 3 0 013-3h15V10z" fill="#2563eb" fillOpacity="0.15" stroke="#2563eb" strokeWidth="2" strokeLinejoin="round" />
      <path d="M10 16h10M10 20h10M10 24h8" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M28 16h10M28 20h10M28 24h8" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
} as const;

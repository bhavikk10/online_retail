import React from "react";

function Icon({ children, size = 24, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export const Menu = (p) => <Icon {...p}><path d="M4 6h16M4 12h16M4 18h16" /></Icon>;
export const X = (p) => <Icon {...p}><path d="M18 6 6 18M6 6l12 12" /></Icon>;
export const Search = (p) => <Icon {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></Icon>;
export const Download = (p) => <Icon {...p}><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></Icon>;
export const ImageOff = (p) => <Icon {...p}><path d="M3 3l18 18" /><path d="M21 15V5a2 2 0 0 0-2-2H9" /><path d="M3 9v10a2 2 0 0 0 2 2h10" /></Icon>;
export const ArrowRight = (p) => <Icon {...p}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></Icon>;
export const BadgePoundSterling = (p) => <Icon {...p}><circle cx="12" cy="12" r="9" /><path d="M14 8c-3-1-5 1-3 4l-2 4h6" /><path d="M8 12h6" /></Icon>;
export const Brain = (p) => <Icon {...p}><path d="M9 3a3 3 0 0 0-3 3v1a3 3 0 0 0 0 6v1a4 4 0 0 0 4 4h1V3Z" /><path d="M15 3a3 3 0 0 1 3 3v1a3 3 0 0 1 0 6v1a4 4 0 0 1-4 4h-1V3Z" /></Icon>;
export const LineChart = (p) => <Icon {...p}><path d="M4 19V5" /><path d="M4 19h16" /><path d="m6 15 4-4 3 3 5-7" /></Icon>;
export const Users = (p) => <Icon {...p}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></Icon>;
export const CheckCircle2 = (p) => <Icon {...p}><circle cx="12" cy="12" r="9" /><path d="m9 12 2 2 4-5" /></Icon>;
export const Activity = (p) => <Icon {...p}><path d="M22 12h-4l-3 8-6-16-3 8H2" /></Icon>;
export const Boxes = (p) => <Icon {...p}><path d="m7 8 5-3 5 3-5 3Z" /><path d="m7 16 5-3 5 3-5 3Z" /><path d="M2 12 7 9v6l-5 3Z" /><path d="m22 12-5-3v6l5 3Z" /></Icon>;
export const ChartBar = (p) => <Icon {...p}><path d="M4 19h16" /><path d="M7 16V9" /><path d="M12 16V5" /><path d="M17 16v-3" /></Icon>;
export const FlaskConical = (p) => <Icon {...p}><path d="M10 2v6L4 19a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3L14 8V2" /><path d="M8 2h8" /><path d="M7 16h10" /></Icon>;
export const FolderTree = (p) => <Icon {...p}><path d="M4 4h6l2 2h8v5H4Z" /><path d="M4 11v9h16v-9" /><path d="M8 15h8" /></Icon>;
export const Gauge = (p) => <Icon {...p}><path d="M12 14 16 8" /><path d="M4 14a8 8 0 1 1 16 0" /><path d="M5 19h14" /></Icon>;
export const GitBranch = (p) => <Icon {...p}><circle cx="6" cy="6" r="3" /><circle cx="18" cy="18" r="3" /><path d="M6 9v3a6 6 0 0 0 6 6h3" /></Icon>;
export const Lightbulb = (p) => <Icon {...p}><path d="M9 18h6" /><path d="M10 22h4" /><path d="M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 4H9c0-2 0-3-1-4Z" /></Icon>;
export const Table2 = (p) => <Icon {...p}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 4v16" /></Icon>;
export const TriangleAlert = (p) => <Icon {...p}><path d="M12 3 2 21h20Z" /><path d="M12 9v5" /><path d="M12 18h.01" /></Icon>;

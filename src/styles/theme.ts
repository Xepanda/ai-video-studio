export type ThemeName = 'obsidian-minimal' | 'blueprint-engineering' | 'cinema-editorial';

export interface ThemeConfig {
  name: ThemeName;
  background: string;
  gridOverlay?: {
    type: 'dots' | 'grid' | 'none';
    color: string;
    size: number;
  };
  titleGradient: string;
  titleColor: string;
  badgeBg: string;
  badgeColor: string;
  badgeBorder: string;
  cardBg: string;
  cardBorder: string;
  cardShadow: string;
  cardTitleColor: string;
  cardDescColor: string;
  accentColor: string;
  subtitleBarBg: string;
  subtitleBorder: string;
  subtitleTextColor: string;
  subtitleHighlightColor: string;
}

export const THEMES: Record<ThemeName, ThemeConfig> = {
  // 1. 默认旗舰：黑曜极简工科风 (Linear / Apple Keynote / 影视飓风质感)
  'obsidian-minimal': {
    name: 'obsidian-minimal',
    background: 'radial-gradient(circle at 50% 20%, #11141c 0%, #08090c 100%)',
    gridOverlay: {
      type: 'dots',
      color: 'rgba(255, 255, 255, 0.05)',
      size: 32,
    },
    titleGradient: 'linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%)',
    titleColor: '#ffffff',
    badgeBg: 'rgba(255, 255, 255, 0.06)',
    badgeColor: '#94a3b8',
    badgeBorder: '1px solid rgba(255, 255, 255, 0.12)',
    cardBg: 'rgba(17, 20, 28, 0.75)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.09)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
    cardTitleColor: '#f8fafc',
    cardDescColor: '#94a3b8',
    accentColor: '#6366f1',
    subtitleBarBg: 'rgba(10, 12, 16, 0.85)',
    subtitleBorder: '1px solid rgba(255, 255, 255, 0.14)',
    subtitleTextColor: '#f8fafc',
    subtitleHighlightColor: '#60a5fa',
  },

  // 2. 蓝图工科风：硬核技术架构、芯片与系统工程
  'blueprint-engineering': {
    name: 'blueprint-engineering',
    background: 'radial-gradient(circle at 50% 30%, #091729 0%, #030811 100%)',
    gridOverlay: {
      type: 'grid',
      color: 'rgba(56, 189, 248, 0.05)',
      size: 40,
    },
    titleGradient: 'linear-gradient(180deg, #f0f9ff 0%, #bae6fd 100%)',
    titleColor: '#f0f9ff',
    badgeBg: 'rgba(56, 189, 248, 0.10)',
    badgeColor: '#38bdf8',
    badgeBorder: '1px solid rgba(56, 189, 248, 0.25)',
    cardBg: 'rgba(10, 23, 40, 0.80)',
    cardBorder: '1px solid rgba(56, 189, 248, 0.20)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(56, 189, 248, 0.15)',
    cardTitleColor: '#e0f2fe',
    cardDescColor: '#7dd3fc',
    accentColor: '#38bdf8',
    subtitleBarBg: 'rgba(7, 16, 29, 0.90)',
    subtitleBorder: '1px solid rgba(56, 189, 248, 0.25)',
    subtitleTextColor: '#e0f2fe',
    subtitleHighlightColor: '#38bdf8',
  },

  // 3. 影视杂志风：深度纪录片、极客哲学与人物故事
  'cinema-editorial': {
    name: 'cinema-editorial',
    background: 'radial-gradient(circle at 50% 25%, #18181b 0%, #09090b 100%)',
    gridOverlay: {
      type: 'none',
      color: 'transparent',
      size: 0,
    },
    titleGradient: 'linear-gradient(180deg, #fafaf9 0%, #d6d3d1 100%)',
    titleColor: '#fafaf9',
    badgeBg: 'rgba(217, 119, 6, 0.10)',
    badgeColor: '#fbbf24',
    badgeBorder: '1px solid rgba(217, 119, 6, 0.25)',
    cardBg: 'rgba(24, 24, 27, 0.80)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.08)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.06)',
    cardTitleColor: '#fafaf9',
    cardDescColor: '#a8a29e',
    accentColor: '#f59e0b',
    subtitleBarBg: 'rgba(15, 15, 16, 0.90)',
    subtitleBorder: '1px solid rgba(255, 255, 255, 0.12)',
    subtitleTextColor: '#fafaf9',
    subtitleHighlightColor: '#fbbf24',
  },
};

export const getTheme = (name?: string): ThemeConfig => {
  if (name && Object.prototype.hasOwnProperty.call(THEMES, name)) {
    return THEMES[name as ThemeName];
  }
  return THEMES['obsidian-minimal'];
};

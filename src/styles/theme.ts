export type ThemeName =
  | 'linear-graphite'       // Linear.app 旗舰极客冷灰风 (深沉微紫/蓝光晕，顶级精英开发工具)
  | 'vercel-geist'         // Vercel Geist / Next.js 极简高反差金属风 (纯净银黑，硬核前沿技术)
  | 'motion-canvas-warm'   // Motion Canvas / 3B1B 温暖工科粉彩风 (温润深灰底，柔和琥珀与薄荷绿)
  | 'cyber-blueprint'      // 深海蓝图高科技架构风 (经典蓝图，Linux/云原生/微服务底层)
  | 'obsidian-minimal'     // 黑曜极简工科风 (经典升级版)
  | 'blueprint-engineering'// 兼容旧版蓝图别名
  | 'cinema-editorial';    // 影视杂志风

export interface SpotlightConfig {
  color: string;
  opacity: number;
  size?: string;
  position?: string;
}

export interface GridOverlayConfig {
  type: 'dots' | 'grid' | 'none';
  color: string;
  size: number;
  opacity?: number;
}

export interface ThemeConfig {
  name: ThemeName;
  displayName: string;
  description: string;
  background: string;
  spotlight?: SpotlightConfig;
  gridOverlay?: GridOverlayConfig;
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
  // 1. 【首选推荐】Linear 旗舰极客冷灰风 (Linear.app / Raycast 顶级精英质感)
  'linear-graphite': {
    name: 'linear-graphite',
    displayName: 'Linear Graphite (极客冷灰)',
    description: '灵感源自 Linear 与 Raycast，深灰碳素底色 + 柔和冷靛紫顶光，精英工程师工具质感',
    background: 'radial-gradient(ellipse 85% 60% at 50% 0%, #171827 0%, #0c0d14 55%, #07080b 100%)',
    spotlight: {
      color: 'rgba(99, 102, 241, 0.45)',
      opacity: 0.65,
      size: '80% 50%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'dots',
      color: 'rgba(255, 255, 255, 0.08)',
      size: 36,
      opacity: 0.7,
    },
    titleGradient: 'linear-gradient(180deg, #ffffff 0%, #e2e8f0 60%, #94a3b8 100%)',
    titleColor: '#ffffff',
    badgeBg: 'rgba(99, 102, 241, 0.12)',
    badgeColor: '#a5b4fc',
    badgeBorder: '1px solid rgba(99, 102, 241, 0.30)',
    cardBg: 'rgba(18, 20, 31, 0.85)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.08)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.85), inset 0 1px 0 rgba(255, 255, 255, 0.14)',
    cardTitleColor: '#f8fafc',
    cardDescColor: '#94a3b8',
    accentColor: '#6366f1',
    subtitleBarBg: 'rgba(11, 13, 20, 0.88)',
    subtitleBorder: '1px solid rgba(255, 255, 255, 0.12)',
    subtitleTextColor: '#f8fafc',
    subtitleHighlightColor: '#818cf8',
  },

  // 2. Vercel Geist 极简纯净金属风 (Vercel / Apple Keynote 高反差冷白)
  'vercel-geist': {
    name: 'vercel-geist',
    displayName: 'Vercel Geist (纯净金属)',
    description: '灵感源自 Vercel Geist 与 Apple Keynote，高反差银黑单色系，极致克制的前沿极简风',
    background: 'radial-gradient(circle at 50% 0%, #1a1a1a 0%, #0a0a0a 50%, #000000 100%)',
    spotlight: {
      color: 'rgba(255, 255, 255, 0.20)',
      opacity: 0.50,
      size: '70% 45%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'grid',
      color: 'rgba(255, 255, 255, 0.04)',
      size: 48,
      opacity: 0.6,
    },
    titleGradient: 'linear-gradient(180deg, #ffffff 0%, #d4d4d8 65%, #71717a 100%)',
    titleColor: '#ffffff',
    badgeBg: 'rgba(255, 255, 255, 0.08)',
    badgeColor: '#e4e4e7',
    badgeBorder: '1px solid rgba(255, 255, 255, 0.18)',
    cardBg: 'rgba(18, 18, 18, 0.88)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.12)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.95), inset 0 1px 0 rgba(255, 255, 255, 0.20)',
    cardTitleColor: '#ffffff',
    cardDescColor: '#a1a1aa',
    accentColor: '#f4f4f5',
    subtitleBarBg: 'rgba(12, 12, 12, 0.92)',
    subtitleBorder: '1px solid rgba(255, 255, 255, 0.16)',
    subtitleTextColor: '#ffffff',
    subtitleHighlightColor: '#38bdf8',
  },

  // 3. Motion Canvas 温暖工科粉彩风 (3Blue1Brown / 科普动画温润质感)
  'motion-canvas-warm': {
    name: 'motion-canvas-warm',
    displayName: 'Motion Canvas (温润粉彩)',
    description: '灵感源自 Motion Canvas 与科普视频，温润深炭灰底色 + 柔和琥珀与薄荷绿，久看不累',
    background: 'radial-gradient(ellipse 85% 65% at 50% 10%, #1f212a 0%, #13141a 60%, #0d0e12 100%)',
    spotlight: {
      color: 'rgba(245, 158, 11, 0.28)',
      opacity: 0.45,
      size: '80% 50%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'dots',
      color: 'rgba(245, 158, 11, 0.08)',
      size: 36,
      opacity: 0.6,
    },
    titleGradient: 'linear-gradient(180deg, #fffbeb 0%, #fef3c7 50%, #fcd34d 100%)',
    titleColor: '#fffbeb',
    badgeBg: 'rgba(245, 158, 11, 0.12)',
    badgeColor: '#fde68a',
    badgeBorder: '1px solid rgba(245, 158, 11, 0.25)',
    cardBg: 'rgba(24, 26, 34, 0.86)',
    cardBorder: '1px solid rgba(245, 158, 11, 0.15)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.10)',
    cardTitleColor: '#fef3c7',
    cardDescColor: '#cbd5e1',
    accentColor: '#f59e0b',
    subtitleBarBg: 'rgba(18, 19, 25, 0.92)',
    subtitleBorder: '1px solid rgba(245, 158, 11, 0.20)',
    subtitleTextColor: '#fef3c7',
    subtitleHighlightColor: '#fbbf24',
  },

  // 4. 深海蓝图高科技架构风 (GitHub Unwrapped / Linux 底层与云原生)
  'cyber-blueprint': {
    name: 'cyber-blueprint',
    displayName: 'Cyber Blueprint (深海蓝图)',
    description: '灵感源自 GitHub Unwrapped 与高规格系统蓝图，深邃海渊蓝 + 荧光青网格，专为内核与微服务打造',
    background: 'radial-gradient(ellipse 90% 70% at 50% 10%, #092244 0%, #041022 55%, #020710 100%)',
    spotlight: {
      color: 'rgba(56, 189, 248, 0.38)',
      opacity: 0.60,
      size: '85% 55%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'grid',
      color: 'rgba(56, 189, 248, 0.08)',
      size: 40,
      opacity: 0.8,
    },
    titleGradient: 'linear-gradient(180deg, #ffffff 0%, #bae6fd 60%, #38bdf8 100%)',
    titleColor: '#f0f9ff',
    badgeBg: 'rgba(56, 189, 248, 0.14)',
    badgeColor: '#7dd3fc',
    badgeBorder: '1px solid rgba(56, 189, 248, 0.32)',
    cardBg: 'rgba(8, 24, 48, 0.86)',
    cardBorder: '1px solid rgba(56, 189, 248, 0.22)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.9), inset 0 1px 0 rgba(56, 189, 248, 0.20)',
    cardTitleColor: '#f0f9ff',
    cardDescColor: '#93c5fd',
    accentColor: '#38bdf8',
    subtitleBarBg: 'rgba(4, 15, 30, 0.92)',
    subtitleBorder: '1px solid rgba(56, 189, 248, 0.28)',
    subtitleTextColor: '#f0f9ff',
    subtitleHighlightColor: '#38bdf8',
  },

  // 经典黑曜极简 (升级顶光漫射与便当盒双层阴影)
  'obsidian-minimal': {
    name: 'obsidian-minimal',
    displayName: 'Obsidian Minimal (经典黑曜)',
    description: '影视飓风与苹果工业极简风，沉稳暗调，克制内敛',
    background: 'radial-gradient(circle at 50% 20%, #11141c 0%, #08090c 100%)',
    spotlight: {
      color: 'rgba(99, 102, 241, 0.30)',
      opacity: 0.45,
      size: '70% 45%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'dots',
      color: 'rgba(255, 255, 255, 0.05)',
      size: 32,
      opacity: 0.7,
    },
    titleGradient: 'linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%)',
    titleColor: '#ffffff',
    badgeBg: 'rgba(255, 255, 255, 0.06)',
    badgeColor: '#94a3b8',
    badgeBorder: '1px solid rgba(255, 255, 255, 0.12)',
    cardBg: 'rgba(17, 20, 28, 0.80)',
    cardBorder: '1px solid rgba(255, 255, 255, 0.09)',
    cardShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.10)',
    cardTitleColor: '#f8fafc',
    cardDescColor: '#94a3b8',
    accentColor: '#6366f1',
    subtitleBarBg: 'rgba(10, 12, 16, 0.88)',
    subtitleBorder: '1px solid rgba(255, 255, 255, 0.14)',
    subtitleTextColor: '#f8fafc',
    subtitleHighlightColor: '#60a5fa',
  },

  // 兼容旧版蓝图别名
  'blueprint-engineering': {
    name: 'blueprint-engineering',
    displayName: 'Blueprint Engineering (工程蓝图)',
    description: '硬核技术架构、芯片与系统工程经典蓝图',
    background: 'radial-gradient(circle at 50% 30%, #091729 0%, #030811 100%)',
    spotlight: {
      color: 'rgba(56, 189, 248, 0.30)',
      opacity: 0.50,
      size: '80% 50%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'grid',
      color: 'rgba(56, 189, 248, 0.06)',
      size: 40,
      opacity: 0.7,
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

  // 兼容影视杂志风
  'cinema-editorial': {
    name: 'cinema-editorial',
    displayName: 'Cinema Editorial (影视纪实)',
    description: '深度纪录片、极客哲学与人物故事',
    background: 'radial-gradient(circle at 50% 25%, #18181b 0%, #09090b 100%)',
    spotlight: {
      color: 'rgba(217, 119, 6, 0.25)',
      opacity: 0.40,
      size: '70% 45%',
      position: '50% -10%',
    },
    gridOverlay: {
      type: 'none',
      color: 'transparent',
      size: 0,
      opacity: 0,
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
  return THEMES['linear-graphite'];
};

export const safeColorWithAlpha = (color: string | undefined, alphaHex: string, fallback: string = '#38bdf8'): string => {
  let base = (color && color.trim()) || fallback;
  if (base.startsWith('#')) {
    if (base.length === 4) {
      base = `#${base[1]}${base[1]}${base[2]}${base[2]}${base[3]}${base[3]}`;
    }
    if (base.length === 7) {
      const cleanAlpha = alphaHex.startsWith('#') ? alphaHex.slice(1) : alphaHex;
      return `${base}${cleanAlpha}`;
    }
  }
  return base;
};

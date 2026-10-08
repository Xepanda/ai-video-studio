import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Img, staticFile } from 'remotion';
import { ThemeConfig, safeColorWithAlpha } from '../styles/theme';

export interface CinematicHeroProps {
  heroImage: string;
  title?: string;
  badge?: string;
  pill?: string;
  highlights?: Array<{ label: string; value: string; color?: string }>;
  cameraMotion?: 'push-in' | 'pan-left' | 'pan-right' | 'pull-out';
  theme: ThemeConfig;
  durationInFrames: number;
  sceneIndex?: number;
  totalScenes?: number;
}

export const CinematicHeroScene: React.FC<CinematicHeroProps> = ({
  heroImage,
  title,
  badge,
  pill,
  highlights = [],
  cameraMotion = 'push-in',
  theme,
  durationInFrames,
  sceneIndex = 1,
  totalScenes = 6,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const safeDuration = Math.max(1, durationInFrames);
  const progress = Math.min(1, Math.max(0, frame / safeDuration));

  // 1. 电影级 2.5D 连续运镜 (Continuous Camera Motion - 拒绝 PPT 停滞感)
  let cameraScale = 1.0;
  let cameraTranslateX = 0;
  let cameraTranslateY = 0;
  let cameraRotateZ = 0;

  switch (cameraMotion) {
    case 'pan-left':
      cameraScale = interpolate(progress, [0, 1], [1.02, 1.08]);
      cameraTranslateX = interpolate(progress, [0, 1], [20, -25]);
      cameraTranslateY = interpolate(progress, [0, 1], [0, -10]);
      cameraRotateZ = interpolate(progress, [0, 1], [-0.3, 0.3]);
      break;
    case 'pan-right':
      cameraScale = interpolate(progress, [0, 1], [1.02, 1.08]);
      cameraTranslateX = interpolate(progress, [0, 1], [-25, 20]);
      cameraTranslateY = interpolate(progress, [0, 1], [-5, 10]);
      cameraRotateZ = interpolate(progress, [0, 1], [0.3, -0.3]);
      break;
    case 'pull-out':
      cameraScale = interpolate(progress, [0, 1], [1.09, 1.01]);
      cameraTranslateY = interpolate(progress, [0, 1], [-15, 0]);
      break;
    case 'push-in':
    default:
      cameraScale = interpolate(progress, [0, 1], [1.00, 1.08]);
      cameraTranslateY = interpolate(progress, [0, 1], [0, -18]);
      cameraRotateZ = interpolate(progress, [0, 1], [-0.2, 0.4]);
      break;
  }

  // 2. 起幅高光扫光与曝光冲击 (Anamorphic Flash Entry)
  const flashOpacity = interpolate(frame, [0, 6, 18], [0.35, 0.15, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 3. 悬浮 HUD 与主视效弹簧阻尼入场
  const hudSpring = spring({ frame: Math.max(0, frame - 2), fps, config: { damping: 18, stiffness: 120 } });
  const cardSpring = spring({ frame: Math.max(0, frame - 6), fps, config: { damping: 16, stiffness: 100 } });

  // 4. 连续粒子与全息扫描线 (Continuous Living Motion)
  const scanLineY = (progress * 100) % 100;
  const particleOffset = (frame * 0.8) % 100;

  return (
    <AbsoluteFill style={{ backgroundColor: '#05070e', overflow: 'hidden' }}>
      {/* 1. 2.5D 电影级动态原画背景 (Cinematic AI Generated Hero Asset) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          transform: `scale(${cameraScale}) translate3d(${cameraTranslateX}px, ${cameraTranslateY}px, 0) rotate(${cameraRotateZ}deg)`,
          transformOrigin: 'center center',
          filter: 'contrast(1.05) saturate(1.08)',
          transition: 'filter 0.3s ease',
        }}
      >
        <Img
          src={staticFile(heroImage)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* 2. 电影感光影与景深暗角 (Anamorphic Vignette & Depth Gradients) */}
      <AbsoluteFill
        style={{
          background: `
            radial-gradient(ellipse at 50% 40%, transparent 40%, rgba(5, 7, 14, 0.75) 100%),
            linear-gradient(180deg, rgba(5, 7, 14, 0.7) 0%, transparent 25%, transparent 60%, rgba(5, 7, 14, 0.92) 100%)
          `,
          pointerEvents: 'none',
        }}
      />

      {/* 3. 极客激光全息扫描线 (Cyber Holographic Scanner Line) */}
      <div
        style={{
          position: 'absolute',
          top: `${scanLineY}%`,
          left: 0,
          width: '100%',
          height: '2px',
          background: `linear-gradient(90deg, transparent, ${safeColorWithAlpha(theme.accentColor, '66')}, ${theme.accentColor}, ${safeColorWithAlpha(theme.accentColor, '66')}, transparent)`,
          boxShadow: `0 0 16px ${safeColorWithAlpha(theme.accentColor, 'aa')}`,
          opacity: 0.45,
          pointerEvents: 'none',
        }}
      />

      {/* 4. 动态漂浮光斑微粒 (Ambient Floating Dust / Light Motes) */}
      <svg
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          opacity: 0.6,
        }}
      >
        <circle cx={`${20 + (particleOffset * 0.4) % 60}%`} cy={`${80 - (particleOffset * 0.8) % 70}%`} r="2.5" fill={theme.accentColor} opacity="0.6" />
        <circle cx={`${75 - (particleOffset * 0.3) % 50}%`} cy={`${90 - (particleOffset * 0.9) % 80}%`} r="3.5" fill="#38bdf8" opacity="0.4" />
        <circle cx={`${45 + (particleOffset * 0.5) % 40}%`} cy={`${70 - (particleOffset * 0.7) % 60}%`} r="2" fill="#c084fc" opacity="0.7" />
        <circle cx={`${85 + (particleOffset * 0.2) % 15}%`} cy={`${50 - (particleOffset * 0.5) % 40}%`} r="1.8" fill="#ffffff" opacity="0.5" />
      </svg>

      {/* 5. 镜头开幅白光闪烁 (Camera Flash Entry Bloom) */}
      {flashOpacity > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: theme.accentColor,
            mixBlendMode: 'screen',
            opacity: flashOpacity,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 6. 顶部极客 HUD 水印与状态中枢 (Top Cyber HUD Overlay) */}
      <div
        style={{
          position: 'absolute',
          top: '40px',
          left: '60px',
          right: '60px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: hudSpring,
          transform: `translateY(${interpolate(hudSpring, [0, 1], [-16, 0])}px)`,
          pointerEvents: 'none',
          fontFamily: 'SF Mono, JetBrains Mono, Menlo, monospace',
        }}
      >
        {/* 左侧：系统运行状态与定位 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '20px',
              backgroundColor: 'rgba(7, 10, 20, 0.75)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
            }}
          >
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: theme.accentColor,
                boxShadow: `0 0 10px ${theme.accentColor}`,
                animation: 'pulse 1.5s infinite',
              }}
            />
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', letterSpacing: '0.05em' }}>
              META MUSE · AGENT ARCHITECTURE
            </span>
          </div>

          <div
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              backgroundColor: 'rgba(7, 10, 20, 0.55)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '12px',
              color: '#94a3b8',
            }}
          >
            FPS: 30 · CFR 1080P
          </div>
        </div>

        {/* 右侧：分镜幕次指示器 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '6px 16px',
            borderRadius: '20px',
            backgroundColor: 'rgba(7, 10, 20, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <span style={{ fontSize: '12px', color: '#64748b' }}>SCENE</span>
          <span style={{ fontSize: '14px', fontWeight: 700, color: theme.accentColor }}>
            {String(sceneIndex).padStart(2, '0')}
          </span>
          <span style={{ fontSize: '12px', color: '#475569' }}>/</span>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>{String(totalScenes).padStart(2, '0')}</span>
        </div>
      </div>

      {/* 7. 左下侧沉浸式悬浮玻璃信息坞 (Floating Frosted Glass HUD Dock) */}
      <div
        style={{
          position: 'absolute',
          bottom: '160px',
          left: '60px',
          maxWidth: '820px',
          opacity: cardSpring,
          transform: `translate3d(0, ${interpolate(cardSpring, [0, 1], [30, 0])}px, 0)`,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            padding: '24px 32px',
            borderRadius: '20px',
            backgroundColor: 'rgba(9, 13, 24, 0.82)',
            border: '1px solid rgba(255, 255, 255, 0.16)',
            boxShadow: `0 16px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.25)`,
            backdropFilter: 'blur(28px)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* 卡片底边能量进度条 (随分镜播放实时填充) */}
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              height: '3px',
              width: `${progress * 100}%`,
              background: `linear-gradient(90deg, ${theme.accentColor}, #38bdf8)`,
              boxShadow: `0 0 10px ${theme.accentColor}`,
            }}
          />

          {/* 徽章与核心胶囊 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            {badge && (
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  color: theme.accentColor,
                  textTransform: 'uppercase',
                  padding: '4px 12px',
                  borderRadius: '6px',
                  backgroundColor: safeColorWithAlpha(theme.accentColor, '1a'),
                  border: `1px solid ${safeColorWithAlpha(theme.accentColor, '33')}`,
                }}
              >
                {badge}
              </div>
            )}

            {pill && (
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: '#f8fafc',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>{pill}</span>
              </div>
            )}
          </div>

          {/* 核心标题：纯净冷金属渐变 */}
          {title && (
            <h1
              style={{
                margin: 0,
                fontSize: '36px',
                fontWeight: 800,
                lineHeight: 1.25,
                background: theme.titleGradient,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.02em',
                textShadow: '0 2px 20px rgba(0,0,0,0.5)',
              }}
            >
              {title}
            </h1>
          )}

          {/* 核心亮点标签矩阵 (紧凑胶囊，绝非冗长文字段落) */}
          {highlights.length > 0 && (
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
              {highlights.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 16px',
                    borderRadius: '12px',
                    backgroundColor: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#94a3b8' }}>{item.label}:</span>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: item.color || '#38bdf8' }}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

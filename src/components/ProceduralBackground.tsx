import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { ThemeConfig } from '../styles/theme';

export const ProceduralBackground: React.FC<{ theme: ThemeConfig }> = ({ theme }) => {
  const frame = useCurrentFrame();

  // 极缓平滑呼吸漂移与粒子位移
  const driftY = (frame * 0.25) % 64;
  const driftX = (frame * 0.15) % 64;
  const glowOpacity = interpolate(
    Math.sin(frame * 0.03),
    [-1, 1],
    [0.15, 0.28]
  );

  return (
    <AbsoluteFill style={{ overflow: 'hidden', pointerEvents: 'none' }}>
      {/* 1. 主题底色渐变 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: theme.background,
        }}
      />

      {/* 2. 工科网格/点阵覆盖图层 (纯 CSS 矢量无损极轻量) */}
      {theme.gridOverlay && theme.gridOverlay.type === 'dots' && (
        <div
          style={{
            position: 'absolute',
            inset: '-64px',
            backgroundImage: `radial-gradient(${theme.gridOverlay.color} 1.5px, transparent 1.5px)`,
            backgroundSize: `${theme.gridOverlay.size}px ${theme.gridOverlay.size}px`,
            transform: `translate(${driftX}px, ${driftY}px)`,
            opacity: 0.8,
          }}
        />
      )}

      {theme.gridOverlay && theme.gridOverlay.type === 'grid' && (
        <div
          style={{
            position: 'absolute',
            inset: '-64px',
            backgroundImage: `
              linear-gradient(to right, ${theme.gridOverlay.color} 1px, transparent 1px),
              linear-gradient(to bottom, ${theme.gridOverlay.color} 1px, transparent 1px)
            `,
            backgroundSize: `${theme.gridOverlay.size}px ${theme.gridOverlay.size}px`,
            transform: `translate(${driftX}px, ${driftY}px)`,
            opacity: 0.85,
          }}
        />
      )}

      {/* 3. 顶部轻微工科渐变环境晕光 (模拟摄影棚顶部柔光箱，非俗套亮紫) */}
      <div
        style={{
          position: 'absolute',
          top: '-20%',
          left: '20%',
          width: '60%',
          height: '50%',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${theme.accentColor} 0%, transparent 70%)`,
          opacity: glowOpacity * 0.35,
          filter: 'blur(120px)',
        }}
      />

      {/* 4. 四角微弱摄影暗角 (Vignette)，提升电影质感与视觉聚焦 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 50%, transparent 60%, rgba(0, 0, 0, 0.65) 100%)',
          mixBlendMode: 'multiply',
        }}
      />
    </AbsoluteFill>
  );
};

import React from 'react';
import { AbsoluteFill, interpolate } from 'remotion';
import { ThemeConfig } from '../styles/theme';
import { useSafeFrameConfig } from './shorts/useSafeFrameConfig';

export const ProceduralBackground: React.FC<{ theme: ThemeConfig }> = ({ theme }) => {
  // SSR / 契约测试环境无 Remotion 上下文, 统一安全回退 frame=0 (初始网格位)
  const { frame } = useSafeFrameConfig();

  const gridSize = theme.gridOverlay?.size && theme.gridOverlay.size > 0 ? theme.gridOverlay.size : 32;
  // 按照实际网格大小执行严格周期取模，杜绝模数错位造成的跳跃卡顿
  const posX = (frame * 0.2) % gridSize;
  const posY = (frame * 0.3) % gridSize;

  const gridOpacity = theme.gridOverlay?.opacity ?? 0.75;

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

      {/* 2. 工科网格/点阵覆盖图层 (通过 backgroundPosition 实现无缝循环滚动) */}
      {theme.gridOverlay && theme.gridOverlay.type === 'dots' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `radial-gradient(${theme.gridOverlay.color} 1.5px, transparent 1.5px)`,
            backgroundSize: `${gridSize}px ${gridSize}px`,
            backgroundPosition: `${posX}px ${posY}px`,
            opacity: gridOpacity,
          }}
        />
      )}

      {theme.gridOverlay && theme.gridOverlay.type === 'grid' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `
              linear-gradient(to right, ${theme.gridOverlay.color} 1px, transparent 1px),
              linear-gradient(to bottom, ${theme.gridOverlay.color} 1px, transparent 1px)
            `,
            backgroundSize: `${gridSize}px ${gridSize}px`,
            backgroundPosition: `${posX}px ${posY}px`,
            opacity: gridOpacity,
          }}
        />
      )}

      {/* 3. 摄影棚级环境聚光灯 (Aceternity / Linear Spotlight 漫射顶光，几何定位与轻量化光栅优化) */}
      {theme.spotlight && (
        <div
          style={{
            position: 'absolute',
            top: theme.spotlight.position?.split(' ')[1] || '-15%',
            left: '50%',
            transform: 'translateX(-50%) translateZ(0)',
            width: theme.spotlight.size?.split(' ')[0] || '80%',
            height: theme.spotlight.size?.split(' ')[1] || '55%',
            borderRadius: '50%',
            background: `radial-gradient(ellipse at 50% 35%, ${theme.spotlight.color} 0%, transparent 75%)`,
            opacity: theme.spotlight.opacity * interpolate(
              Math.sin(frame * 0.025),
              [-1, 1],
              [0.88, 1.0]
            ),
            filter: 'blur(45px)',
          }}
        />
      )}

      {/* 4. 边缘暗角 (仅在深色模式下压暗，浅色模式下保持通透纯净) */}
      {!theme.isLight && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(ellipse at 50% 50%, transparent 55%, rgba(0, 0, 0, 0.70) 100%)',
            pointerEvents: 'none',
          }}
        />
      )}
    </AbsoluteFill>
  );
};

import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export interface WordInfo {
  text: string;
  startFrame: number;
  endFrame: number;
}

export interface DynamicSubtitlesProps {
  words: WordInfo[];
  baseStyle?: React.CSSProperties;
  activeColor?: string;
  inactiveColor?: string;
}

/**
 * 逐字动态弹跳高光字幕 (短视频 / 口播专属)
 */
export const DynamicSubtitles: React.FC<DynamicSubtitlesProps> = ({
  words,
  activeColor = '#facc15', // 醒目明黄
  inactiveColor = '#ffffff',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!words || words.length === 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '120px',
        left: 0,
        right: 0,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '12px',
        padding: '0 60px',
        zIndex: 50,
      }}
    >
      {words.map((w, idx) => {
        const isActive = frame >= w.startFrame && frame <= w.endFrame;

        // 弹跳动画
        const jump = spring({
          frame: frame - w.startFrame,
          fps,
          config: { damping: 12, stiffness: 200 },
        });

        const scale = isActive ? interpolate(jump, [0, 1], [1.0, 1.25]) : 1.0;
        const translateY = isActive ? interpolate(jump, [0, 1], [0, -8]) : 0;

        return (
          <span
            key={idx}
            style={{
              fontSize: '44px',
              fontWeight: 800,
              fontFamily: 'system-ui, -apple-system, sans-serif',
              color: isActive ? activeColor : inactiveColor,
              textShadow: isActive
                ? '0 0 25px rgba(250, 204, 21, 0.8), 0 4px 12px rgba(0,0,0,0.8)'
                : '0 4px 10px rgba(0,0,0,0.8)',
              transform: `scale(${scale}) translateY(${translateY}px)`,
              display: 'inline-block',
              transition: 'color 0.1s ease',
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};

import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export interface WordInfo {
  text: string;
  startFrame: number;
  endFrame: number;
}

export interface DynamicSubtitlesProps {
  words: WordInfo[];
  sceneStartFrame?: number;
  activeColor?: string;
}

/**
 * 现代高节奏逐句弹跳大字幕 (仅显示当前正在发音的一句)
 */
export const DynamicSubtitles: React.FC<DynamicSubtitlesProps> = ({
  words,
  sceneStartFrame = 0,
  activeColor = '#facc15', // 明黄高光
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!words || words.length === 0) return null;

  // Remotion Sequence 内部的 frame 是相对于该 Sequence 的 (0 ~ durationInFrames)
  // 如果 words 里的 startFrame 是全局绝对帧，则加上 sceneStartFrame 进行对齐
  const currentGlobalFrame = frame + sceneStartFrame;

  // 找到当前正在发音的一句话
  const activeWord = words.find((w) => {
    // 兼容全局帧或相对帧
    if (w.startFrame >= sceneStartFrame) {
      return currentGlobalFrame >= w.startFrame && currentGlobalFrame <= w.endFrame;
    }
    return frame >= w.startFrame && frame <= w.endFrame;
  });

  if (!activeWord) return null;

  // 相对发音起始帧计算入场弹跳
  const wordStartRelative = activeWord.startFrame >= sceneStartFrame
    ? activeWord.startFrame - sceneStartFrame
    : activeWord.startFrame;

  const jump = spring({
    frame: frame - wordStartRelative,
    fps,
    config: { damping: 14, stiffness: 200 },
  });

  const scale = interpolate(jump, [0, 1], [0.92, 1.05]);
  const translateY = interpolate(jump, [0, 1], [15, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '80px',
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 80px',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
          borderRadius: '24px',
          padding: '16px 36px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(250, 204, 21, 0.25)',
          transform: `scale(${scale}) translateY(${translateY}px)`,
        }}
      >
        <span
          style={{
            fontSize: '44px',
            fontWeight: 900,
            fontFamily: 'system-ui, -apple-system, sans-serif',
            color: activeColor,
            textShadow: '0 0 25px rgba(250, 204, 21, 0.6), 0 4px 12px rgba(0,0,0,0.9)',
            letterSpacing: '1px',
            display: 'inline-block',
          }}
        >
          {activeWord.text}
        </span>
      </div>
    </div>
  );
};

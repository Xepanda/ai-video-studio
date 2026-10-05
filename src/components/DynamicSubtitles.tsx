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
  // 判断 words 数组是用全局绝对帧还是分镜相对帧（相对于 Sequence 起始点 0）
  // 仅当首个词的起始帧大于等于场景全局偏移且场景全局偏移大于 0 时，才判定为全局帧数组
  const isGlobalFormat = Boolean(
    sceneStartFrame > 0 &&
    words.length > 0 &&
    words[0].startFrame >= sceneStartFrame
  );

  const currentGlobalFrame = frame + sceneStartFrame;

  // 找到当前正在发音的一句话
  let activeWord = words.find((w) => {
    if (isGlobalFormat) {
      return currentGlobalFrame >= w.startFrame && currentGlobalFrame < w.endFrame;
    }
    return frame >= w.startFrame && frame < w.endFrame;
  });

  // 容错防闪烁：如果处于两句微小缝隙或分镜结尾，回退到最近生效的句子
  if (!activeWord && words.length > 0) {
    if (isGlobalFormat) {
      if (currentGlobalFrame < words[0].startFrame) {
        activeWord = words[0];
      } else if (currentGlobalFrame >= words[words.length - 1].endFrame) {
        activeWord = words[words.length - 1];
      }
    } else {
      if (frame < words[0].startFrame) {
        activeWord = words[0];
      } else if (frame >= words[words.length - 1].endFrame) {
        activeWord = words[words.length - 1];
      }
    }
  }

  if (!activeWord) return null;

  // 相对发音起始帧计算入场弹跳
  const wordStartRelative = isGlobalFormat
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

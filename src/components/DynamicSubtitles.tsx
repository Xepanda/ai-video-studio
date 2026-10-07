import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { ThemeConfig, getTheme } from '../styles/theme';

export interface WordInfo {
  text: string;
  startFrame: number;
  endFrame: number;
}

export interface DynamicSubtitlesProps {
  words: WordInfo[];
  sceneStartFrame?: number;
  theme?: ThemeConfig;
  activeColor?: string;
}

/**
 * 现代影视级 Lower-Third 字幕 Dock (去 AI 味 · Apple Keynote / 影视飓风质感)
 */
export const DynamicSubtitles: React.FC<DynamicSubtitlesProps> = ({
  words,
  sceneStartFrame = 0,
  theme: themeProp,
  activeColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTheme = themeProp || getTheme();

  if (!words || words.length === 0) return null;

  // 判断 words 数组使用全局绝对帧还是分镜相对帧
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

  // 容错防闪烁：如果处于短暂停顿微小缝隙，回退至最近生效的句子
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

  // 相对发音起始帧计算入场平滑过渡 (微阻尼，杜绝夸张抖动)
  const wordStartRelative = isGlobalFormat
    ? activeWord.startFrame - sceneStartFrame
    : activeWord.startFrame;

  const entrySpring = spring({
    frame: frame - wordStartRelative,
    fps,
    config: { damping: 18, stiffness: 220 },
  });

  const scale = interpolate(entrySpring, [0, 1], [0.96, 1.0]);
  const translateY = interpolate(entrySpring, [0, 1], [10, 0]);
  const opacity = interpolate(entrySpring, [0, 1], [0.2, 1.0]);

  const highlight = activeColor || currentTheme.subtitleHighlightColor;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '64px',
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 60px',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          backgroundColor: currentTheme.subtitleBarBg,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: currentTheme.subtitleBorder,
          borderRadius: '16px',
          padding: '14px 32px',
          boxShadow: '0 16px 36px -8px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          transform: `scale(${scale}) translateY(${translateY}px)`,
          opacity,
        }}
      >
        {/* 左侧极简状态指示光点 */}
        <div
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '4px',
            backgroundColor: highlight,
            boxShadow: `0 0 10px ${highlight}`,
            flexShrink: 0,
          }}
        />

        {/* 字幕正文：高对比度纯净排版，移除土味黄色大光晕 */}
        <span
          style={{
            fontSize: '34px',
            fontWeight: 700,
            fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color: currentTheme.subtitleTextColor,
            letterSpacing: '0.8px',
            lineHeight: 1.3,
            textShadow: '0 2px 8px rgba(0, 0, 0, 0.8)',
          }}
        >
          {activeWord.text}
        </span>
      </div>
    </div>
  );
};

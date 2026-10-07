import React from 'react';
import { AbsoluteFill, Video, staticFile, useCurrentFrame, interpolate } from 'remotion';
import { ProceduralBackground } from './ProceduralBackground';
import { getTheme, ThemeName } from '../styles/theme';

export interface BrollVideoPlayerProps {
  src?: string;
  durationInFrames: number;
  startFromFrame?: number;
  playbackRate?: number;
  kenBurns?: boolean;
  blurBackground?: boolean;
  overlayOpacity?: number;
  theme?: ThemeName;
}

/**
 * 专为 Google Flow / AI 生成视频设计的 B-Roll 播放器
 * 支持电影级缓慢变焦 (Ken Burns) 与多比例自适应毛玻璃画中画
 * 当缺少外部 MP4 视频素材时，自动无缝降级为纯代码工科程序化动态背景
 */
export const BrollVideoPlayer: React.FC<BrollVideoPlayerProps> = ({
  src,
  durationInFrames,
  startFromFrame = 0,
  playbackRate = 1.0,
  kenBurns = true,
  blurBackground = true,
  overlayOpacity = 0.2,
  theme,
}) => {
  const frame = useCurrentFrame();

  // Ken Burns 慢推平移效果 (1.00 -> 1.08 微缩放)
  const scale = kenBurns
    ? interpolate(frame, [0, durationInFrames], [1.0, 1.06], {
        extrapolateRight: 'clamp',
      })
    : 1.0;

  const fadeOpacity = interpolate(
    frame,
    [0, 10, durationInFrames - 10, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // 兜底降级：当未提供外部视频源时，纯代码渲染工科程序背景
  if (!src) {
    const currentTheme = getTheme(theme);
    return (
      <AbsoluteFill style={{ overflow: 'hidden', opacity: fadeOpacity }}>
        <ProceduralBackground theme={currentTheme} />
        <AbsoluteFill
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${scale})`,
          }}
        >
          {/* 纯代码动态工程流光光标与坐标线 */}
          <div
            style={{
              width: '80%',
              height: '60%',
              border: `1px solid ${currentTheme.cardBorder}`,
              borderRadius: '20px',
              backgroundColor: currentTheme.cardBg,
              backdropFilter: 'blur(20px)',
              boxShadow: currentTheme.cardShadow,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px',
              textAlign: 'center',
            }}
          >
            <div style={{
              fontSize: '14px',
              fontWeight: 800,
              letterSpacing: '3px',
              color: currentTheme.accentColor,
              marginBottom: '12px',
              textTransform: 'uppercase',
            }}>
              [SYS:PROCEDURAL_FEED_ACTIVE]
            </div>
            <div style={{
              fontSize: '32px',
              fontWeight: 800,
              color: currentTheme.titleColor,
              letterSpacing: '-0.5px',
            }}>
              高维算力架构与流匹配推演
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '#000', opacity: fadeOpacity }}>
      {/* 模糊背景层 (针对 9:16 在 16:9 或反之情况) */}
      {blurBackground && (
        <AbsoluteFill style={{ filter: 'blur(30px) brightness(0.6)', transform: 'scale(1.2)' }}>
          <Video
            src={staticFile(src)}
            startFrom={startFromFrame}
            playbackRate={playbackRate}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </AbsoluteFill>
      )}

      {/* 主画面与电影级缓推 */}
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${scale})`,
        }}
      >
        <Video
          src={staticFile(src)}
          startFrom={startFromFrame}
          playbackRate={playbackRate}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            borderRadius: '16px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          }}
        />
      </AbsoluteFill>

      {/* 电影质感暗角与调色蒙版 */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle, transparent 40%, rgba(0,0,0,0.7) 100%)`,
          pointerEvents: 'none',
          opacity: overlayOpacity,
        }}
      />
    </AbsoluteFill>
  );
};

import React from 'react';
import { AbsoluteFill, Video, staticFile, useCurrentFrame, interpolate } from 'remotion';

export interface BrollVideoPlayerProps {
  src: string;
  durationInFrames: number;
  startFromFrame?: number;
  playbackRate?: number;
  kenBurns?: boolean;
  blurBackground?: boolean;
  overlayOpacity?: number;
}

/**
 * 专为 Google Flow / AI 生成视频设计的 B-Roll 播放器
 * 支持电影级缓慢变焦 (Ken Burns) 与多比例自适应毛玻璃画中画
 */
export const BrollVideoPlayer: React.FC<BrollVideoPlayerProps> = ({
  src,
  durationInFrames,
  startFromFrame = 0,
  playbackRate = 1.0,
  kenBurns = true,
  blurBackground = true,
  overlayOpacity = 0.2,
}) => {
  const frame = useCurrentFrame();

  // Ken Burns 慢推平移效果 (1.00 -> 1.08 微缩放)
  const scale = kenBurns
    ? interpolate(frame, [0, durationInFrames], [1.0, 1.08], {
        extrapolateRight: 'clamp',
      })
    : 1.0;

  const fadeOpacity = interpolate(
    frame,
    [0, 10, durationInFrames - 10, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

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

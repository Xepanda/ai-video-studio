import React from 'react';
import { Video, staticFile, useCurrentFrame } from 'remotion';

export interface PhoneFrameProps {
  videoSrc: string;
  width?: number;
  height?: number;
}

/**
 * 拟真金属圆角悬浮手机外壳 (实拍原片嵌入画中画)
 */
export const PhoneFrame: React.FC<PhoneFrameProps> = ({
  videoSrc,
  width = 340,
  height = 680,
}) => {
  const frame = useCurrentFrame();
  const floatY = Math.sin(frame / 15) * 8;
  const rotateZ = Math.sin(frame / 20) * 1.5;

  return (
    <div
      style={{
        width,
        height,
        borderRadius: '48px',
        backgroundColor: '#1f2937',
        padding: '12px',
        boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 0 4px #374151, 0 0 40px rgba(56, 189, 248, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        transform: `translateY(${floatY}px) rotate(${rotateZ}deg)`,
        transition: 'transform 0.1s ease',
      }}
    >
      {/* 顶部听筒与灵动岛 */}
      <div
        style={{
          position: 'absolute',
          top: '20px',
          width: '90px',
          height: '24px',
          backgroundColor: '#000',
          borderRadius: '12px',
          zIndex: 30,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#111827', marginRight: 6 }} />
        <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#0284c7' }} />
      </div>

      {/* 屏幕区域 (原生播放实拍视频) */}
      <div
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '38px',
          overflow: 'hidden',
          backgroundColor: '#000',
          position: 'relative',
        }}
      >
        <Video
          src={staticFile(videoSrc)}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />

        {/* 动态激光扫描线 */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, transparent, #38bdf8, #818cf8, transparent)',
            boxShadow: '0 0 15px #38bdf8',
            top: `${(frame * 4) % 100}%`,
            opacity: 0.8,
            pointerEvents: 'none',
          }}
        />
      </div>
    </div>
  );
};

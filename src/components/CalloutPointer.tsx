import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export interface CalloutPointerProps {
  label: string;
  sublabel?: string;
  targetX?: number; // 目标点 X (百分比 0~100)
  targetY?: number; // 目标点 Y (百分比 0~100)
}

/**
 * 实物发光指示线与追踪指针 (Callout Pointer)
 */
export const CalloutPointer: React.FC<CalloutPointerProps> = ({
  label,
  sublabel = 'ESP32-S3 双核 MCU (240MHz)',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const anim = spring({ frame: frame - 15, fps, config: { damping: 14, stiffness: 120 } });
  const lineWidth = interpolate(anim, [0, 1], [0, 160]);
  const opacity = interpolate(anim, [0, 1], [0, 1]);
  const pulse = Math.sin(frame / 5) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        top: '38%',
        left: '42%',
        display: 'flex',
        alignItems: 'center',
        zIndex: 50,
        opacity,
        pointerEvents: 'none',
      }}
    >
      {/* 瞄准发光同心圆 */}
      <div style={{ position: 'relative', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div
          style={{
            position: 'absolute',
            width: `${24 + pulse}px`,
            height: `${24 + pulse}px`,
            borderRadius: '50%',
            border: '2px solid #38bdf8',
            boxShadow: '0 0 15px #38bdf8',
          }}
        />
        <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#f43f5e' }} />
      </div>

      {/* 动态折线 */}
      <div
        style={{
          width: `${lineWidth}px`,
          height: '2px',
          background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
          boxShadow: '0 0 10px #38bdf8',
        }}
      />

      {/* 信息标签卡片 */}
      <div
        style={{
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #38bdf8',
          borderRadius: '12px',
          padding: '10px 18px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.8), 0 0 20px rgba(56, 189, 248, 0.3)',
          marginLeft: '4px',
        }}
      >
        <div style={{ color: '#38bdf8', fontSize: '18px', fontWeight: 800 }}>{label}</div>
        <div style={{ color: '#94a3b8', fontSize: '14px', marginTop: '2px' }}>{sublabel}</div>
      </div>
    </div>
  );
};

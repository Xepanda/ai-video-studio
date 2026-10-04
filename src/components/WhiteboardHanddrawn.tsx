import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

export interface WhiteboardHanddrawnProps {
  durationInFrames: number;
}

/**
 * 白板手绘擦除引擎 (story-to-handdrawn & pixel2motion 规范)
 * 利用 SVG strokeDashoffset 模拟真人铅笔笔触沿路径逐渐绘制与橡皮擦擦除
 */
export const WhiteboardHanddrawn: React.FC<WhiteboardHanddrawnProps> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();

  // 笔画绘制进度 (0 -> 1000 像素路径)
  const drawProgress = interpolate(frame, [15, 120], [1000, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 橡皮擦移动并擦除旧架构
  const eraseProgress = interpolate(frame, [140, 240], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '1300px',
        height: '520px',
        backgroundColor: '#fdfbf7',
        borderRadius: '24px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4), inset 0 0 80px rgba(217, 119, 6, 0.05)',
        border: '3px solid #e2d9cc',
        padding: '36px',
        position: 'relative',
        overflow: 'hidden',
        color: '#1e293b',
      }}
    >
      {/* 纸张网格微纹理 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)',
          backgroundSize: '24px 24px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* 白板顶部标记 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '26px' }}>✏️</span>
            <span style={{ fontSize: '26px', fontWeight: 800, color: '#1e293b', fontFamily: "'Comic Sans MS', cursive, sans-serif" }}>
              科普白板图解：SVG 笔触动态绘制与擦除
            </span>
          </div>
          <div style={{ backgroundColor: '#fef3c7', color: '#b45309', padding: '6px 14px', borderRadius: '12px', fontSize: '14px', fontWeight: 700 }}>
            stroke-dashoffset: {Math.floor(drawProgress)}px
          </div>
        </div>

        {/* 手绘矢量画板区域 */}
        <div style={{ flex: 1, display: 'flex', gap: '40px', alignItems: 'center', justifyContent: 'center' }}>
          {/* 左侧：将被擦除的旧误区 */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#fee2e2',
              border: '3px dashed #ef4444',
              borderRadius: '20px',
              padding: '24px',
              opacity: eraseProgress,
              transform: `scale(${0.9 + eraseProgress * 0.1})`,
              transition: 'opacity 0.1s linear',
            }}
          >
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#b91c1c', marginBottom: '12px' }}>
              ❌ 传统认知误区 (被动态擦除)
            </div>
            <div style={{ fontSize: '18px', color: '#7f1d1d', lineHeight: 1.6 }}>
              以为 AI 视频只能靠 Prompt 抽盲盒？文字不可控、画面乱晃、无法用于技术教学？
            </div>
          </div>

          {/* 中间动态手绘连接箭头 */}
          <svg width="120" height="60" style={{ overflow: 'visible' }}>
            <path
              d="M 10 30 Q 60 5 110 30"
              fill="none"
              stroke="#0284c7"
              strokeWidth="5"
              strokeLinecap="round"
              strokeDasharray="1000"
              strokeDashoffset={drawProgress}
            />
            <polygon points="105,20 120,30 105,40" fill="#0284c7" />
          </svg>

          {/* 右侧：手绘生成的矢量程序化框图 */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#e0f2fe',
              border: '3px solid #0284c7',
              borderRadius: '20px',
              padding: '24px',
              boxShadow: '8px 8px 0px #0369a1',
            }}
          >
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#0369a1', marginBottom: '12px' }}>
              ✅ 代码即视频 (程序化矢量绘制)
            </div>
            <div style={{ fontSize: '18px', color: '#075985', lineHeight: 1.6 }}>
              文字锐利清晰、架构逻辑 100% 确定，像素级精确同步！
            </div>
          </div>
        </div>

        {/* 底部手绘铅笔指示 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '16px' }}>
          <span>✒️ 模拟铅笔物理笔触运动</span>
          <span>📐 pixel2motion 动态矢量展开</span>
        </div>
      </div>
    </div>
  );
};

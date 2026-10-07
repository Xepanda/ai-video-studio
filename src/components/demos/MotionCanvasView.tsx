import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  staticFile,
} from 'remotion';
import { getTheme } from '../../styles/theme';
import { ProceduralBackground } from '../ProceduralBackground';
import { DynamicSubtitles } from '../DynamicSubtitles';
import motionTimeline from '../../../public/projects/demo_style_motion/timeline.json';

export const MotionCanvasView: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = getTheme('motion-canvas-warm');

  const scene = motionTimeline.scenes[0];
  const words = scene.words || [];

  // 镜头微动
  const cameraScale = interpolate(frame, [0, 288], [1.0, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 传送带位移计算
  const conveyorOffset = (frame * 3.5) % 360;

  // 生成连续 SVG 声波正弦路径
  const points: string[] = [];
  const width = 1200;
  for (let x = 0; x <= width; x += 10) {
    const freq = 0.02;
    const speed = frame * 0.15;
    const y = 80 + Math.sin((x * freq) - speed) * 45 * Math.sin(x / width * Math.PI);
    points.push(`${x},${y}`);
  }
  const wavePath = `M ${points.join(' L ')}`;

  // 冲压动作检测 (每个周期冲压一次)
  const stampCycle = Math.floor(frame / 60);
  const stampFrame = frame % 60;
  const stampImpact = spring({
    frame: stampFrame,
    fps,
    config: { damping: 12, stiffness: 220 },
  });

  const cards = [
    { id: '#001', title: '声学时钟', tag: '16kHz', color: '#f59e0b' },
    { id: '#002', title: '纯函数状态', tag: 'DETERMINISTIC', color: '#10b981' },
    { id: '#003', title: '代码生成', tag: 'CODE-DRIVEN', color: '#38bdf8' },
    { id: '#004', title: '光栅化导出', tag: '68 FPS', color: '#a855f7' },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: '#13141a', overflow: 'hidden' }}>
      {/* 1. 音频层 */}
      <Audio src={staticFile('projects/demo_style_motion/audio/scene_01.wav')} volume={1.0} />

      {/* 2. 背景与微光 (Motion Canvas 暖调粉彩) */}
      <ProceduralBackground theme={theme} />

      {/* 3. 运镜主视窗 */}
      <AbsoluteFill
        style={{
          transform: `scale(${cameraScale})`,
          transformOrigin: 'center center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '60px',
        }}
      >
        {/* 顶部数学函数推演标题 */}
        <div
          style={{
            position: 'absolute',
            top: '80px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              fontSize: '16px',
              fontWeight: 800,
              color: '#f59e0b',
              letterSpacing: '5px',
              textTransform: 'uppercase',
              marginBottom: '10px',
            }}
          >
            MATHEMATICAL VISUAL METAPHOR
          </div>
          <div
            style={{
              fontSize: '44px',
              fontWeight: 800,
              color: '#fef3c7',
              fontFamily: 'monospace',
              letterSpacing: '-1px',
            }}
          >
            Frame_k = f(t_acoustic, State)
          </div>
        </div>

        {/* 中部：声波波峰检测流 (Waveform Stream) */}
        <div
          style={{
            position: 'relative',
            width: '1200px',
            height: '160px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '40px',
          }}
        >
          {/* SVG 连续声波 */}
          <svg width="1200" height="160" style={{ overflow: 'visible' }}>
            <path
              d={wavePath}
              fill="none"
              stroke="#f59e0b"
              strokeWidth="4"
              strokeLinecap="round"
              style={{ filter: 'drop-shadow(0 0 12px rgba(245, 158, 11, 0.6))' }}
            />
          </svg>

          {/* 中央冲压感应针 (Stamping Head) */}
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: `${interpolate(stampImpact, [0, 1], [-20, 20])}px`,
              transform: 'translateX(-50%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                width: '6px',
                height: '80px',
                background: 'linear-gradient(180deg, #10b981 0%, #34d399 100%)',
                boxShadow: '0 0 20px #10b981',
                borderRadius: '3px',
              }}
            />
            <div
              style={{
                backgroundColor: '#064e3b',
                border: '2px solid #10b981',
                color: '#6ee7b7',
                padding: '4px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 800,
                marginTop: '8px',
                fontFamily: 'monospace',
              }}
            >
              TRIGGER GATE: t_k
            </div>
          </div>
        </div>

        {/* 底部：胶片流水线传送带 (Filmstrip Conveyor Belt) */}
        <div
          style={{
            width: '1280px',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          {/* 传送带导轨线 */}
          <div
            style={{
              width: '100%',
              height: '3px',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              position: 'relative',
              marginBottom: '32px',
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: 'repeating-linear-gradient(90deg, #f59e0b 0px, #f59e0b 20px, transparent 20px, transparent 40px)',
                backgroundPosition: `${conveyorOffset}px 0`,
                opacity: 0.8,
              }}
            />
          </div>

          {/* 正在冲压流出的卡片阵列 */}
          <div style={{ display: 'flex', gap: '32px' }}>
            {cards.map((card, i) => {
              const isCurrent = (stampCycle % cards.length) === i;
              return (
                <div
                  key={card.id}
                  style={{
                    width: '260px',
                    padding: '24px',
                    backgroundColor: 'rgba(26, 29, 40, 0.92)',
                    border: isCurrent
                      ? `2px solid ${card.color}`
                      : '1px solid rgba(255, 255, 255, 0.10)',
                    borderRadius: '20px',
                    boxShadow: isCurrent
                      ? `0 20px 40px rgba(0,0,0,0.8), 0 0 25px ${card.color}44`
                      : '0 15px 30px rgba(0,0,0,0.6)',
                    transform: isCurrent
                      ? `scale(${interpolate(stampImpact, [0, 1], [0.95, 1.05])})`
                      : 'scale(1.0)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <span style={{ color: card.color, fontFamily: 'monospace', fontWeight: 800, fontSize: '18px' }}>
                      {card.id}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 700, backgroundColor: 'rgba(255,255,255,0.08)', color: '#cbd5e1', padding: '3px 8px', borderRadius: '6px' }}>
                      {card.tag}
                    </span>
                  </div>
                  <div style={{ fontSize: '22px', fontWeight: 800, color: '#fef3c7', marginBottom: '8px' }}>
                    {card.title}
                  </div>
                  <div style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.5 }}>
                    精确声学打点冲压光栅化
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>

      {/* 4. 底部 Apple 级 Lower-Third 字幕 Dock */}
      <DynamicSubtitles words={words} sceneStartFrame={0} theme={theme} />
    </AbsoluteFill>
  );
};

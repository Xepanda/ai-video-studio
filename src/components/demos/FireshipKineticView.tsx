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
import fireshipTimeline from '../../../public/projects/demo_style_fireship/timeline.json';

export const FireshipKineticView: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = getTheme('linear-graphite');

  const scene = fireshipTimeline.scenes[0];
  const words = scene.words || [];

  // Phase 1: 0 - 82 痛点大字冲击 (Manual Timeline Glitch & Strike)
  // Phase 2: 82 - 210 3D 悬浮 IDE 与纯代码流
  // Phase 3: 210 - 325 镜头 Punch-in 推进与 68 FPS 极速里程表

  // 镜头微动与阶段 Punch-in
  const cameraScale = frame < 210
    ? interpolate(frame, [0, 210], [1.0, 1.05], { extrapolateRight: 'clamp' })
    : interpolate(frame, [210, 220, 325], [1.05, 1.20, 1.24], { extrapolateRight: 'clamp' });

  // 阶段 1: 痛点红字弹簧
  const title1Spring = spring({ frame, fps, config: { damping: 12, stiffness: 200 } });
  const strikeProgress = interpolate(frame, [45, 65], [0, 100], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // 阶段 2: 3D IDE 入场弹簧
  const ideSpring = spring({ frame: Math.max(0, frame - 82), fps, config: { damping: 16, stiffness: 120 } });

  // 阶段 3: 里程表数值计算
  const odoFrames = Math.max(0, frame - 215);
  const currentFpsOdo = Math.min(68, Math.floor(interpolate(odoFrames, [0, 30], [0, 68], { extrapolateRight: 'clamp' })));

  return (
    <AbsoluteFill style={{ backgroundColor: '#07080b', overflow: 'hidden' }}>
      {/* 1. 音频层 */}
      <Audio src={staticFile('projects/demo_style_fireship/audio/scene_01.wav')} volume={1.0} />

      {/* 2. 背景与微光 */}
      <ProceduralBackground theme={theme} />

      {/* 3. 运镜摄像机主画布 */}
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
        {/* ============================================================== */}
        {/* 阶段 1 (0 - 82 帧): 痛点大字冲击 (Kinetic Slam & Strike-through) */}
        {/* ============================================================== */}
        {frame < 85 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${title1Spring})`,
              opacity: interpolate(frame, [75, 85], [1, 0], { extrapolateRight: 'clamp' }),
            }}
          >
            <div
              style={{
                fontSize: '24px',
                fontWeight: 800,
                color: '#ef4444',
                letterSpacing: '6px',
                textTransform: 'uppercase',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span>⚠️ LEGACY EDITING WORKFLOW</span>
            </div>

            <div style={{ position: 'relative', display: 'inline-block' }}>
              <h1
                style={{
                  fontSize: '92px',
                  fontWeight: 900,
                  color: '#ffffff',
                  letterSpacing: '-2px',
                  textTransform: 'uppercase',
                  margin: 0,
                  textShadow: '0 20px 40px rgba(0,0,0,0.8)',
                }}
              >
                MANUAL TIMELINE DRAGGING
              </h1>

              {/* 红色划除斜线 */}
              <div
                style={{
                  position: 'absolute',
                  top: '52%',
                  left: '-4%',
                  width: `${strikeProgress * 1.08}%`,
                  height: '10px',
                  backgroundColor: '#ef4444',
                  boxShadow: '0 0 20px #ef4444',
                  transform: 'rotate(-4deg)',
                  borderRadius: '5px',
                }}
              />
            </div>

            <div
              style={{
                marginTop: '32px',
                fontSize: '36px',
                fontWeight: 700,
                color: '#f87171',
                opacity: strikeProgress > 30 ? 1 : 0,
                transition: 'opacity 0.2s',
              }}
            >
              改了一个字，整个时间轴全废！
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 阶段 2 (82 - 210 帧): 3D 透视悬浮 IDE 与纯代码直出 */}
        {/* ============================================================== */}
        {frame >= 82 && frame < 215 && (
          <div
            style={{
              width: '100%',
              maxWidth: '1280px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `scale(${ideSpring})`,
              opacity: interpolate(frame, [82, 92], [0, 1]),
            }}
          >
            {/* 顶部标语 */}
            <div
              style={{
                fontSize: '22px',
                fontWeight: 800,
                color: '#10b981',
                letterSpacing: '4px',
                textTransform: 'uppercase',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>⚡ THE PARADIGM SHIFT</span>
              <span>•</span>
              <span style={{ color: '#fff' }}>CODE AS VIDEO</span>
            </div>

            {/* 3D 透视 IDE 窗口 */}
            <div
              style={{
                width: '100%',
                backgroundColor: 'rgba(12, 14, 24, 0.92)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '24px',
                boxShadow: '0 40px 80px -15px rgba(0, 0, 0, 0.9), inset 0 1px 0 rgba(255, 255, 255, 0.15)',
                overflow: 'hidden',
                transform: 'perspective(1200px) rotateY(-8deg) rotateX(5deg)',
                position: 'relative',
              }}
            >
              {/* 窗口顶栏 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 24px',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#10b981' }} />
                </div>
                <div style={{ color: '#94a3b8', fontSize: '15px', fontFamily: 'monospace' }}>
                  video_orchestrator.ts — AI Video Studio
                </div>
                <div style={{ color: '#6366f1', fontSize: '13px', fontWeight: 700, fontFamily: 'monospace' }}>
                  TypeScript 5.8
                </div>
              </div>

              {/* 代码展示 */}
              <div style={{ padding: '32px 40px', fontFamily: 'monospace', fontSize: '24px', lineHeight: 1.8, color: '#f1f5f9' }}>
                <div><span style={{ color: '#818cf8' }}>import</span> &#123; renderVideo &#125; <span style={{ color: '#818cf8' }}>from</span> <span style={{ color: '#38bdf8' }}>"@ai-video/engine"</span>;</div>
                <div style={{ color: '#64748b' }}>// 0 手动拖拽 · 100% 纯代码即函数</div>
                <div><span style={{ color: '#818cf8' }}>const</span> video = <span style={{ color: '#818cf8' }}>await</span> renderVideo(&#123;</div>
                <div style={{ paddingLeft: '40px' }}>prompt: <span style={{ color: '#38bdf8' }}>"Redis核心架构底层原理"</span>,</div>
                <div style={{ paddingLeft: '40px' }}>voice: <span style={{ color: '#f59e0b' }}>"ChatTTS-4444"</span>,</div>
                <div style={{ paddingLeft: '40px' }}>engine: <span style={{ color: '#10b981' }}>"Paraformer-Acoustic-Clock"</span>,</div>
                <div>&#125;);</div>
              </div>

              {/* 悬浮状态徽章 */}
              <div
                style={{
                  position: 'absolute',
                  right: '40px',
                  bottom: '30px',
                  display: 'flex',
                  gap: '16px',
                }}
              >
                <div
                  style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.4)',
                    color: '#6ee7b7',
                    padding: '8px 18px',
                    borderRadius: '12px',
                    fontSize: '15px',
                    fontWeight: 700,
                  }}
                >
                  ✓ 零盲盒抽卡
                </div>
                <div
                  style={{
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    color: '#c7d2fe',
                    padding: '8px 18px',
                    borderRadius: '12px',
                    fontSize: '15px',
                    fontWeight: 700,
                  }}
                >
                  ✓ 纯函数确定性
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 阶段 3 (210 - 325 帧): Punch-in 冲刺与 68 FPS 里程表加速 */}
        {/* ============================================================== */}
        {frame >= 210 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: interpolate(frame, [210, 218], [0, 1]),
            }}
          >
            <div
              style={{
                fontSize: '24px',
                fontWeight: 800,
                color: '#38bdf8',
                letterSpacing: '5px',
                textTransform: 'uppercase',
                marginBottom: '16px',
              }}
            >
              HIGH-THROUGHPUT RENDERING CLUSTER
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '20px' }}>
              <div
                style={{
                  fontSize: '160px',
                  fontWeight: 900,
                  color: '#ffffff',
                  fontFamily: 'monospace',
                  lineHeight: 1,
                  textShadow: '0 0 60px rgba(56, 189, 248, 0.4)',
                }}
              >
                {currentFpsOdo}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '48px', fontWeight: 900, color: '#38bdf8' }}>FPS</span>
                <span style={{ fontSize: '20px', color: '#94a3b8', fontWeight: 600 }}>REMOTION 6核并行集群</span>
              </div>
            </div>

            <div
              style={{
                marginTop: '40px',
                padding: '16px 36px',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.5)',
                borderRadius: '100px',
                fontSize: '32px',
                fontWeight: 800,
                color: '#6ee7b7',
                boxShadow: '0 20px 40px rgba(16, 185, 129, 0.2)',
              }}
            >
              两行命令 · 回车即交付
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* 4. 底部 Apple 级 Lower-Third 字幕 Dock */}
      <DynamicSubtitles words={words} sceneStartFrame={0} theme={theme} />
    </AbsoluteFill>
  );
};

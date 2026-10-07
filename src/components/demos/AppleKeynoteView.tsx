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
import appleTimeline from '../../../public/projects/demo_style_apple/timeline.json';

export const AppleKeynoteView: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = getTheme('vercel-geist');

  const scene = appleTimeline.scenes[0];
  const words = scene.words || [];

  // 运镜推移与微距景深
  const cameraScale = interpolate(frame, [0, 298], [1.0, 1.06], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const explodeProgress = interpolate(frame, [85, 130], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 阶段 1: 核心声学圆柱入场
  const heroSpring = spring({ frame, fps, config: { damping: 18, stiffness: 100 } });

  // 动态音频波形震动条
  const waveBars = [0.3, 0.7, 1.0, 0.6, 0.9, 0.4, 0.8, 0.5, 0.95, 0.6, 0.85, 0.35];

  return (
    <AbsoluteFill style={{ backgroundColor: '#000000', overflow: 'hidden' }}>
      {/* 1. 音频层 */}
      <Audio src={staticFile('projects/demo_style_apple/audio/scene_01.wav')} volume={1.0} />

      {/* 2. 背景与微光 (Vercel Geist 纯净冷白顶光) */}
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
        {/* 顶部极简 Apple 标签 */}
        <div
          style={{
            position: 'absolute',
            top: '80px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            opacity: heroSpring,
          }}
        >
          <div
            style={{
              fontSize: '15px',
              fontWeight: 700,
              letterSpacing: '5px',
              color: '#a1a1aa',
              textTransform: 'uppercase',
              marginBottom: '8px',
            }}
          >
            PRECISION AUDIO-FIRST DECONSTRUCTION
          </div>
          <h1
            style={{
              fontSize: '48px',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '-1px',
              margin: 0,
            }}
          >
            声学时钟引擎 · 精密机械解构
          </h1>
        </div>

        {/* 中央机械主体 / 零件爆炸分解层 (Exploded View) */}
        <div
          style={{
            position: 'relative',
            width: '800px',
            height: '420px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* ============================================================== */}
          {/* 顶层：03 无头光栅化集群 (Layer Top) */}
          {/* ============================================================== */}
          <div
            style={{
              position: 'absolute',
              top: `${interpolate(explodeProgress, [0, 1], [150, 20])}px`,
              width: '540px',
              padding: '24px 32px',
              backgroundColor: 'rgba(24, 24, 27, 0.85)',
              border: '1px solid rgba(255, 255, 255, 0.22)',
              borderRadius: '20px',
              boxShadow: '0 30px 60px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 30,
              opacity: explodeProgress > 0.1 ? 1 : 0.9,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#38bdf8' }} />
              <div>
                <div style={{ color: '#ffffff', fontWeight: 800, fontSize: '20px' }}>03. 无头并行光栅化集群</div>
                <div style={{ color: '#71717a', fontSize: '14px', fontFamily: 'monospace' }}>Remotion WebGL · 30.00 FPS CFR</div>
              </div>
            </div>
            <div style={{ color: '#e4e4e7', fontFamily: 'monospace', fontSize: '15px', fontWeight: 700 }}>
              68.2 FPS
            </div>
          </div>

          {/* ============================================================== */}
          {/* 中层：02 纯函数状态机 (Layer Middle) */}
          {/* ============================================================== */}
          <div
            style={{
              position: 'absolute',
              top: '150px',
              width: '580px',
              padding: '24px 32px',
              backgroundColor: 'rgba(18, 18, 20, 0.92)',
              border: '1px solid rgba(255, 255, 255, 0.28)',
              borderRadius: '20px',
              boxShadow: '0 30px 60px rgba(0,0,0,0.95), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 20,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <div>
                <div style={{ color: '#ffffff', fontWeight: 800, fontSize: '20px' }}>02. 纯函数状态机中枢</div>
                <div style={{ color: '#71717a', fontSize: '14px', fontFamily: 'monospace' }}>Scene = f(frame, audioClock)</div>
              </div>
            </div>
            <div style={{ color: '#a1a1aa', fontFamily: 'monospace', fontSize: '14px', backgroundColor: 'rgba(255,255,255,0.06)', padding: '6px 12px', borderRadius: '8px' }}>
              DETERMINISTIC
            </div>
          </div>

          {/* ============================================================== */}
          {/* 底层：01 声学物理波形时钟 (Layer Bottom) */}
          {/* ============================================================== */}
          <div
            style={{
              position: 'absolute',
              top: `${interpolate(explodeProgress, [0, 1], [150, 280])}px`,
              width: '620px',
              padding: '24px 32px',
              backgroundColor: 'rgba(10, 10, 12, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.20)',
              borderRadius: '20px',
              boxShadow: '0 30px 60px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255, 255, 255, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 10,
              opacity: explodeProgress > 0.1 ? 1 : 0.8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
              <div>
                <div style={{ color: '#ffffff', fontWeight: 800, fontSize: '20px' }}>01. 物理声学时钟底座</div>
                <div style={{ color: '#71717a', fontSize: '14px', fontFamily: 'monospace' }}>Paraformer ASR · 16kHz 物理波形</div>
              </div>
            </div>

            {/* 动态跳动声波线 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', height: '36px' }}>
              {waveBars.map((baseVal, i) => {
                const osc = Math.sin((frame * 0.25) + i * 0.8);
                const height = Math.max(6, Math.min(32, baseVal * 28 * (0.8 + 0.4 * osc)));
                return (
                  <div
                    key={i}
                    style={{
                      width: '4px',
                      height: `${height}px`,
                      backgroundColor: '#f59e0b',
                      borderRadius: '2px',
                      boxShadow: '0 0 8px rgba(245, 158, 11, 0.5)',
                    }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* 底部高精度规格参数条 (Spec Sheet) */}
        <div
          style={{
            position: 'absolute',
            bottom: '120px',
            display: 'flex',
            gap: '24px',
            opacity: interpolate(frame, [140, 170], [0, 1]),
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#d4d4d8', fontSize: '16px', fontFamily: 'monospace' }}>
            <span style={{ color: '#10b981' }}>●</span> ±0.001ms 绝对时钟对齐
          </div>
          <div style={{ color: '#52525b' }}>|</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#d4d4d8', fontSize: '16px', fontFamily: 'monospace' }}>
            <span style={{ color: '#38bdf8' }}>●</span> 0.05 RTF 向量推理
          </div>
          <div style={{ color: '#52525b' }}>|</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#d4d4d8', fontSize: '16px', fontFamily: 'monospace' }}>
            <span style={{ color: '#a855f7' }}>●</span> CFR 30.00 恒定帧率
          </div>
        </div>
      </AbsoluteFill>

      {/* 4. 底部 Apple 级 Lower-Third 字幕 Dock */}
      <DynamicSubtitles words={words} sceneStartFrame={0} theme={theme} />
    </AbsoluteFill>
  );
};

import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import timelineData from '../public/timeline.json';
import { TerminalWindow } from './components/TerminalWindow';
import { DynamicSubtitles } from './components/DynamicSubtitles';

// --- 分镜 1：痛点引入与核心理念 (Explainer) ---
const Scene01Intro: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });
  const cardSpring = spring({ frame: frame - 20, fps, config: { damping: 12, stiffness: 100 } });

  const titleScale = interpolate(titleSpring, [0, 1], [0.85, 1.0]);
  const cardOpacity = interpolate(cardSpring, [0, 1], [0, 1]);
  const cardY = interpolate(cardSpring, [0, 1], [40, 0]);

  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
      {/* 头部发光大标题 */}
      <div style={{ transform: `scale(${titleScale})`, textAlign: 'center', marginBottom: '50px' }}>
        <div style={{
          fontSize: '68px',
          fontWeight: 900,
          background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-1px',
          textShadow: '0 0 40px rgba(56, 189, 248, 0.4)'
        }}>
          AI Video Studio
        </div>
        <div style={{ fontSize: '28px', color: '#94a3b8', marginTop: '12px', fontWeight: 500 }}>
          全链路 AI 视频自动化制作工作流 · 代码即视频
        </div>
      </div>

      {/* 核心对比卡片 */}
      <div style={{ display: 'flex', gap: '40px', width: '100%', maxWidth: '1400px', opacity: cardOpacity, transform: `translateY(${cardY}px)` }}>
        {/* 左侧：传统剪辑痛点 */}
        <div style={{
          flex: 1,
          backgroundColor: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '20px',
          padding: '36px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
        }}>
          <div style={{ fontSize: '26px', fontWeight: 700, color: '#f87171', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>❌ 传统人工剪辑 & 纯文生视频</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', color: '#cbd5e1', fontSize: '20px', lineHeight: 1.6 }}>
            <div>• 剪映 / PR 频繁打点对齐，文案一改全部错位</div>
            <div>• Sora / 可灵等文生模型文字乱码、不可控</div>
            <div>• 技术架构图无法精准指代引脚与代码逻辑</div>
            <div>• 难以实现批量化、工业级的稳定生产</div>
          </div>
        </div>

        {/* 右侧：程序化代码渲染优势 */}
        <div style={{
          flex: 1,
          backgroundColor: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.4)',
          borderRadius: '20px',
          padding: '36px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.5), 0 0 50px rgba(56, 189, 248, 0.1)',
        }}>
          <div style={{ fontSize: '26px', fontWeight: 700, color: '#38bdf8', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>✅ 程序化渲染 (Code-as-Video)</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', color: '#cbd5e1', fontSize: '20px', lineHeight: 1.6 }}>
            <div>• 声音先行：真实物理时长决定画面总帧数</div>
            <div>• 矢量级锐利：代码高亮、架构图 100% 确定性</div>
            <div>• 毫秒级音画同步：SenseVoice 自动打点与情绪提取</div>
            <div>• 极速复用：换套文案一键重新编译导出</div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --- 分镜 2：核心第一步 · 声音先行与时钟契约 ---
const Scene02Timeline: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const anim = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });
  const pulse = Math.sin(frame / 6) * 6;

  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{ fontSize: '22px', color: '#38bdf8', fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase' }}>
          STEP 01 · 绝对时间基准
        </div>
        <div style={{ fontSize: '56px', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
          声音先行与时间轴契约 (timeline.json)
        </div>
      </div>

      <div style={{ display: 'flex', gap: '40px', width: '100%', maxWidth: '1400px', alignItems: 'center' }}>
        {/* 左侧：SenseVoice 与音频脉冲可视化 */}
        <div style={{ flex: 1, backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '20px', padding: '36px' }}>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#10b981', marginBottom: '24px' }}>
            🎙️ 阿里 SenseVoice-Small 打点中枢
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', height: '80px', marginBottom: '30px' }}>
            {[24, 45, 60, 30, 70, 50, 85, 40, 65, 30, 90, 45, 60, 35, 75, 50, 80, 40].map((h, i) => {
              const dynHeight = Math.max(12, h + Math.sin(frame / 4 + i) * 18 + pulse);
              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: `${dynHeight}px`,
                    backgroundColor: i % 2 === 0 ? '#38bdf8' : '#818cf8',
                    borderRadius: '4px',
                    transition: 'height 0.1s ease',
                  }}
                />
              );
            })}
          </div>
          <div style={{ color: '#94a3b8', fontSize: '18px', lineHeight: 1.8 }}>
            <div>⚡ 纯 CPU 推理 (RTF 约 0.05，秒级对齐长音频)</div>
            <div>⏱️ 提取字词毫秒起始时间戳 [startMs, endMs]</div>
            <div>🎭 自动识别情绪标签: &lt;|HAPPY|&gt;, &lt;|NEUTRAL|&gt;</div>
          </div>
        </div>

        {/* 右侧：代码契约卡片 */}
        <div style={{ flex: 1, backgroundColor: '#0d1117', border: '1px solid #30363d', borderRadius: '20px', padding: '30px', fontFamily: 'monospace' }}>
          <div style={{ color: '#8b949e', fontSize: '16px', marginBottom: '14px' }}>// public/timeline.json (数据中枢契约)</div>
          <pre style={{ color: '#e6edf3', fontSize: '18px', lineHeight: 1.6, margin: 0 }}>
{`{
  "project": "workflow_introduction",
  "fps": 30,
  "totalDurationInFrames": 1544,
  "scenes": [
    {
      "id": "scene_01",
      "durationInFrames": 415,
      "audioPath": "audio/scene_01.mp3",
      "words": [
        { "text": "欢迎来到AIVideo", "startFrame": 0 },
        { "text": "全链路视频工作流", "startFrame": 83 }
      ]
    }
  ]
}`}
          </pre>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --- 分镜 3：核心第二步 · Google Flow 电影级镜头协同 ---
const Scene03GoogleFlow: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{ fontSize: '22px', color: '#c084fc', fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase' }}>
          STEP 02 · 画面装配与电影质感
        </div>
        <div style={{ fontSize: '56px', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
          组件化装配与 Google Flow 电影级镜头协同
        </div>
      </div>

      <div style={{ display: 'flex', gap: '40px', width: '100%', maxWidth: '1400px', alignItems: 'center' }}>
        {/* 左侧：极客终端打字机 */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
          <TerminalWindow
            title="ai-video-studio - zsh"
            command="python scripts/pipeline.py --project my_video"
            output={[
              "[✓] 1/3 Audio generated via Voice Clone",
              "[✓] 2/3 SenseVoice aligned timeline.json",
              "[✓] 3/3 Google Flow B-roll mounted: public/footage/",
              "✨ Starting Remotion visual state machine..."
            ]}
            width="100%"
            height={380}
          />
        </div>

        {/* 右侧：Google Flow 镜头渲染卡片 */}
        <div style={{
          flex: 1,
          height: '380px',
          backgroundColor: '#030712',
          border: '1px solid rgba(192, 132, 252, 0.4)',
          borderRadius: '20px',
          padding: '30px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 20px 50px rgba(192, 132, 252, 0.15)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* 装饰性网格背景 */}
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(192, 132, 252, 0.15) 0%, transparent 60%)',
            pointerEvents: 'none'
          }} />

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px', fontWeight: 800, color: '#c084fc' }}>🌐 Google Flow (Veo / VideoFX)</span>
              <span style={{ backgroundColor: '#2e1065', color: '#d8b4fe', padding: '4px 12px', borderRadius: '12px', fontSize: '14px', fontWeight: 600 }}>4K 60FPS</span>
            </div>
            <div style={{ color: '#e2e8f0', fontSize: '18px', fontStyle: 'italic', lineHeight: 1.6, backgroundColor: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '12px', borderLeft: '4px solid #c084fc' }}>
              "Extreme cinematic macro shot of a glowing microchip processor with pulsating neon traces, slow camera drift..."
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '16px' }}>
            <span>🎥 摄影机运镜: 慢速平移推镜 (Ken Burns)</span>
            <span>🧩 组件: &lt;BrollVideoPlayer /&gt;</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --- 分镜 4：核心第三步 · 五重质量门禁与极速渲染 ---
const Scene04AuditAndRender: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = Math.min(100, Math.floor(interpolate(frame, [20, durationInFrames - 40], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  })));

  const checks = [
    { name: "阶段 1：文案与分镜合规审查 (语速比 4.5字/秒)", passFrame: 10 },
    { name: "阶段 2：声音与 SenseVoice 毫秒时钟连续性对齐", passFrame: 35 },
    { name: "阶段 3：视觉动效物理弹簧阻尼与平台安全区", passFrame: 60 },
    { name: "阶段 4：自动化静态资产门禁 (validator.py)", passFrame: 85 },
    { name: "阶段 5：AMD 5800H 6进程并发硬件级压制 (yuv420p)", passFrame: 110 }
  ];

  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{ fontSize: '22px', color: '#10b981', fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase' }}>
          STEP 03 · 质量门禁与交付
        </div>
        <div style={{ fontSize: '56px', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
          五重审查门禁与并发无头光栅化压制
        </div>
      </div>

      <div style={{ width: '100%', maxWidth: '1200px', backgroundColor: '#090d16', border: '1px solid #1e293b', borderRadius: '24px', padding: '40px', boxShadow: '0 25px 50px rgba(0,0,0,0.6)' }}>
        {/* 5 重审查清单 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '36px' }}>
          {checks.map((item, idx) => {
            const isPassed = frame >= item.passFrame;
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 20px',
                  backgroundColor: isPassed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                  border: isPassed ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '12px',
                  fontSize: '20px',
                  fontWeight: 600,
                  color: isPassed ? '#34d399' : '#64748b',
                  transition: 'all 0.2s ease',
                }}
              >
                <span>{item.name}</span>
                <span>{isPassed ? "✅ [PASSED]" : "⏳ PENDING"}</span>
              </div>
            );
          })}
        </div>

        {/* 渲染进度条 */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '18px', marginBottom: '10px' }}>
            <span>🎬 Remotion Chrome Headless 多核渲染进度</span>
            <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{progress}%</span>
          </div>
          <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '7px', overflow: 'hidden' }}>
            <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, #38bdf8 0%, #10b981 100%)', borderRadius: '7px', transition: 'width 0.1s linear' }} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --- 主 MasterVideo 编排根组件 ---
export const MasterVideo: React.FC = () => {
  const { scenes } = timelineData;

  return (
    <AbsoluteFill style={{ backgroundColor: '#090d16', color: '#fff', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {scenes.map((scene, idx) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.durationInFrames}
        >
          {/* 配音音频 */}
          {scene.audioPath && <Audio src={staticFile(scene.audioPath)} />}

          {/* 各场景专业视觉组件 */}
          {idx === 0 && <Scene01Intro durationInFrames={scene.durationInFrames} />}
          {idx === 1 && <Scene02Timeline durationInFrames={scene.durationInFrames} />}
          {idx === 2 && <Scene03GoogleFlow durationInFrames={scene.durationInFrames} />}
          {idx === 3 && <Scene04AuditAndRender durationInFrames={scene.durationInFrames} />}

          {/* 逐字动态弹跳大字幕 */}
          {scene.words && scene.words.length > 0 && (
            <DynamicSubtitles words={scene.words} sceneStartFrame={scene.startFrame} />
          )}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  const fps = timelineData.fps || 30;
  const durationInFrames = Math.max(1, timelineData.totalDurationInFrames || 1544);

  return (
    <>
      <Composition
        id="MasterVideo"
        component={MasterVideo}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="SocialShorts"
        component={MasterVideo}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1080}
        height={1920}
      />
    </>
  );
};

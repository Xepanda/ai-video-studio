import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import timelineData from '../public/timeline.json';
import { TerminalWindow } from './components/TerminalWindow';
import { DynamicSubtitles } from './components/DynamicSubtitles';
import { WhiteboardHanddrawn } from './components/WhiteboardHanddrawn';
import { PhoneFrame } from './components/PhoneFrame';
import { CalloutPointer } from './components/CalloutPointer';
import { PinoutStream } from './components/PinoutStream';
import { UniversalScene, SceneMeta } from './components/UniversalScene';
import { getTheme, ThemeName } from './styles/theme';
import { FireshipKineticView } from './components/demos/FireshipKineticView';
import { AppleKeynoteView } from './components/demos/AppleKeynoteView';
import { MotionCanvasView } from './components/demos/MotionCanvasView';

// =========================================================================
// 分镜 1：自声音克隆底座与声纹时钟中枢 (Voice Clone & SenseVoice Aligner)
// =========================================================================
const Scene01VoiceClone: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });
  const pulse = Math.sin(frame / 5) * 5;

  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '50px' }}>
      <div style={{ transform: `scale(${interpolate(titleSpring, [0, 1], [0.85, 1.0])})`, textAlign: 'center', marginBottom: '36px' }}>
        <div style={{ fontSize: '20px', color: '#38bdf8', fontWeight: 800, letterSpacing: '3px', textTransform: 'uppercase' }}>
          FOUNDATION MODULE · 物理时钟中枢
        </div>
        <div style={{
          fontSize: '56px',
          fontWeight: 900,
          background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginTop: '6px'
        }}>
          自声音克隆 (TTS) 与 SenseVoice 毫秒时钟中枢
        </div>
      </div>

      <div style={{ display: 'flex', gap: '36px', width: '100%', maxWidth: '1400px' }}>
        {/* 左卡：个人声纹特征提取 */}
        <div style={{ flex: 1, backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '24px', padding: '32px', boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <span style={{ fontSize: '24px', fontWeight: 800, color: '#38bdf8' }}>🎙️ 个人专属声纹提取 (Speaker Embedding)</span>
            <span style={{ backgroundColor: '#0369a1', color: '#e0f2fe', padding: '4px 12px', borderRadius: '10px', fontSize: '13px', fontWeight: 700 }}>5秒干声采样</span>
          </div>

          {/* 动态梅尔频谱条 */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '90px', marginBottom: '24px', backgroundColor: '#020617', padding: '12px', borderRadius: '14px' }}>
            {[30, 60, 45, 80, 55, 90, 70, 40, 85, 60, 95, 50, 75, 65, 85, 45, 90, 70, 50, 80].map((h, i) => {
              const dyn = Math.max(10, h + Math.sin(frame / 3 + i * 1.5) * 20 + pulse);
              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: `${dyn}%`,
                    background: 'linear-gradient(180deg, #38bdf8 0%, #3b82f6 100%)',
                    borderRadius: '3px',
                  }}
                />
              );
            })}
          </div>

          <div style={{ color: '#94a3b8', fontSize: '16px', lineHeight: 1.8 }}>
            <div>📁 参考音频: <code style={{ color: '#38bdf8' }}>models/reference_audio/my_voice.wav</code></div>
            <div>🧬 声纹向量: 192维音色指纹 (Cosine Similarity: <span style={{ color: '#10b981' }}>99.2%</span>)</div>
            <div>🧠 神经生成: GPT-SoVITS / OmniVoice 零样本声学解码</div>
          </div>
        </div>

        {/* 右卡：SenseVoice 毫秒打点契约 */}
        <div style={{ flex: 1, backgroundColor: '#0d1117', border: '1px solid #30363d', borderRadius: '24px', padding: '30px', fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#10b981', fontSize: '16px', fontWeight: 700, marginBottom: '14px' }}>
            <span>⏱️ 阿里 SenseVoice-Small CPU 极速打点</span>
            <span>RTF: 0.05</span>
          </div>
          <pre style={{ color: '#e6edf3', fontSize: '16px', lineHeight: 1.6, margin: 0, backgroundColor: '#161b22', padding: '16px', borderRadius: '12px' }}>
{`// public/timeline.json
{
  "voiceModel": "CustomVoiceClone_01",
  "audioPath": "public/audio/scene_01.mp3",
  "words": [
    { "text": "第一模块", "startFrame": 0, "endFrame": 83 },
    { "text": "自声音克隆与毫秒时钟中枢", "startFrame": 83, "endFrame": 166 }
  ],
  "emotion": "<|NEUTRAL|>"
}`}
          </pre>
          <div style={{ color: '#8b949e', fontSize: '14px', marginTop: '12px' }}>
            ⚡ 声音先行原则：音频毫秒物理长度是画面的绝对唯一时钟
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =========================================================================
// 分镜 2：形态一 · 科普白板手绘 (Whiteboard & pixel2motion)
// =========================================================================
const Scene02Whiteboard: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '50px' }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <div style={{ fontSize: '20px', color: '#f59e0b', fontWeight: 800, letterSpacing: '3px', textTransform: 'uppercase' }}>
          SKILL 01 · story-to-handdrawn & pixel2motion
        </div>
        <div style={{ fontSize: '52px', fontWeight: 900, color: '#fff', marginTop: '6px' }}>
          形态一：科普视频白板手绘与矢量活化
        </div>
      </div>

      <WhiteboardHanddrawn durationInFrames={durationInFrames} />
    </AbsoluteFill>
  );
};

// =========================================================================
// 分镜 3：形态二 · 项目实战教程 (Terminal & Pinout Stream)
// =========================================================================
const Scene03HandsOn: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '50px' }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <div style={{ fontSize: '20px', color: '#10b981', fontWeight: 800, letterSpacing: '3px', textTransform: 'uppercase' }}>
          SKILL 02 · 极客终端与硬件引脚流光
        </div>
        <div style={{ fontSize: '52px', fontWeight: 900, color: '#fff', marginTop: '6px' }}>
          形态二：项目实战与软硬件架构深度对比
        </div>
      </div>

      <div style={{ display: 'flex', gap: '36px', width: '100%', maxWidth: '1400px', alignItems: 'center' }}>
        {/* 左侧：极客终端打字机 */}
        <div style={{ flex: 1 }}>
          <TerminalWindow
            title="bash - tutorial_demo"
            command="docker run -d -p 80:80 --name my_app esp32/embedded:latest"
            output={[
              "[✓] Pulling container image layer 1/3 (12.4 MB)",
              "[✓] Flashing microcode to GPIO 18/23 bus...",
              "[OK] Container initialized, HTTP server running on port 80"
            ]}
            width="100%"
            height={360}
          />
        </div>

        {/* 右侧：单片机引脚脉冲流光 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <PinoutStream />
          <div style={{ display: 'flex', gap: '14px' }}>
            <div style={{ flex: 1, backgroundColor: '#1e293b', padding: '16px', borderRadius: '12px', borderLeft: '4px solid #38bdf8' }}>
              <div style={{ color: '#38bdf8', fontWeight: 700, fontSize: '16px' }}>架构双卡阻尼对比</div>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginTop: '4px' }}>物理弹簧阻尼入场，Before vs After</div>
            </div>
            <div style={{ flex: 1, backgroundColor: '#1e293b', padding: '16px', borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
              <div style={{ color: '#10b981', fontWeight: 700, fontSize: '16px' }}>正弦波信号流</div>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginTop: '4px' }}>毫秒级同步硬件通信脉冲</div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =========================================================================
// 分镜 4：形态三 · 实拍视频混剪 (PhoneFrame & Callout Pointer)
// =========================================================================
const Scene04HybridLive: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '50px' }}>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{ fontSize: '20px', color: '#c084fc', fontWeight: 800, letterSpacing: '3px', textTransform: 'uppercase' }}>
          SKILL 03 · video-shotcraft & 画中画包装
        </div>
        <div style={{ fontSize: '52px', fontWeight: 900, color: '#fff', marginTop: '6px' }}>
          形态三：实拍视频混剪与 HUD 激光发光引线
        </div>
      </div>

      <div style={{ display: 'flex', gap: '50px', width: '100%', maxWidth: '1400px', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
        {/* 左侧：3D 悬浮手机外壳原生播放实拍视频 */}
        <PhoneFrame videoSrc="footage/real_sample.mp4" width={320} height={520} />

        {/* 右侧：实拍混剪技术解析卡片 */}
        <div style={{ flex: 1, backgroundColor: '#090d16', border: '1px solid #1e293b', borderRadius: '24px', padding: '36px', boxShadow: '0 20px 50px rgba(0,0,0,0.6)' }}>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#c084fc', marginBottom: '20px' }}>
            🎬 实拍原片 + 动态动画高能混合
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', color: '#cbd5e1', fontSize: '18px', lineHeight: 1.6 }}>
            <div>• <strong style={{ color: '#38bdf8' }}>拟真 3D 浮动手机壳</strong>：自动带有金属高光、圆角裁切与微幅浮动动效</div>
            <div>• <strong style={{ color: '#f43f5e' }}>HUD 激光扫描线</strong>：循环扫描原片画面，增强极客科技质感</div>
            <div>• <strong style={{ color: '#10b981' }}>发光引线 (Callout Pointer)</strong>：动态折线飞出，精准锚定实物元器件与芯片引脚</div>
          </div>
        </div>

        {/* 动态激光 Callout 引线 (指向手机屏幕内部) */}
        <CalloutPointer label="ESP32-S3 实物主控" sublabel="双核 Xtensa LX7 @ 240MHz" />
      </div>
    </AbsoluteFill>
  );
};

// =========================================================================
// 分镜 5：形态四 · 日常自媒体与 Google Flow 电影级 AI 镜头
// =========================================================================
const Scene05GoogleFlowShorts: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  return (
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '50px' }}>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{ fontSize: '20px', color: '#e11d48', fontWeight: 800, letterSpacing: '3px', textTransform: 'uppercase' }}>
          SKILL 04 · google-flow-broll & 9:16 自媒体
        </div>
        <div style={{ fontSize: '52px', fontWeight: 900, color: '#fff', marginTop: '6px' }}>
          形态四：日常自媒体短片与 Google Flow 映画镜头
        </div>
      </div>

      <div style={{ display: 'flex', gap: '40px', width: '100%', maxWidth: '1400px', alignItems: 'center' }}>
        {/* 左侧：Google Flow (Veo) 映画镜头卡片 */}
        <div style={{
          flex: 1.2,
          height: '460px',
          backgroundColor: '#050816',
          border: '1px solid rgba(225, 29, 72, 0.4)',
          borderRadius: '24px',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 20px 50px rgba(225, 29, 72, 0.2)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px', fontWeight: 800, color: '#fb7185' }}>🌐 Google Flow (Veo 映画级镜头)</span>
              <span style={{ backgroundColor: '#4c0519', color: '#fecdd3', padding: '4px 12px', borderRadius: '10px', fontSize: '13px', fontWeight: 700 }}>4K 60FPS</span>
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '17px', fontStyle: 'italic', lineHeight: 1.6, backgroundColor: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '14px', borderLeft: '4px solid #f43f5e' }}>
              "Extreme cinematic macro shot of a glowing microchip processor with pulsating blue circuit traces, anamorphic lens flare, smooth slow camera drift..."
            </div>
          </div>

          <div style={{ color: '#94a3b8', fontSize: '16px', lineHeight: 1.7 }}>
            <div>🎥 电影级运镜: 慢速平移推镜 (Ken Burns 微缩放)</div>
            <div>🧩 专用组件: &lt;BrollVideoPlayer blurBackground=&#123;true&#125; /&gt;</div>
            <div>🌈 调色预设: Cyber Glow / Warm Editorial 工业级调色</div>
          </div>
        </div>

        {/* 右侧：9:16 自媒体短视频视窗演示 */}
        <div style={{ flex: 0.8, display: 'flex', justifyContent: 'center' }}>
          <div style={{
            width: '260px',
            height: '460px',
            borderRadius: '36px',
            backgroundColor: '#000',
            border: '3px solid #334155',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 20px 40px rgba(0,0,0,0.8), 0 0 30px rgba(244, 63, 94, 0.2)',
            position: 'relative'
          }}>
            <div style={{ color: '#f43f5e', fontWeight: 800, fontSize: '15px' }}>📱 9:16 高节奏竖屏</div>
            <div style={{ textAlign: 'center', color: '#facc15', fontSize: '26px', fontWeight: 900, textShadow: '0 0 15px rgba(250,204,21,0.6)' }}>
              逐字弹跳<br/>爆款大字
            </div>
            <div style={{ color: '#64748b', fontSize: '12px', textAlign: 'center' }}>
              平台安全区防护 (避让头像与进度条)
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =========================================================================
// 主 MasterVideo 编排根组件
// =========================================================================
export const MasterVideo: React.FC = () => {
  const { scenes } = timelineData;
  const { fps } = useVideoConfig();
  const totalDuration = timelineData.totalDurationInFrames || 2032;
  const bgmPath = (timelineData as any).bgmPath || 'audio/bgm_cyber_ambient.wav';
  const bgmVolume = (timelineData as any).bgmVolume ?? 0.10;
  const enableBgm = (timelineData as any).enableBgm !== false;
  const enableSfx = (timelineData as any).enableSfx !== false;

  // 严格单调递增区间计算，杜绝短视频测试时总帧数过少引发的 interpolate 崩溃
  const fadeInFrames = Math.max(1, Math.min(45, Math.floor(totalDuration * 0.25)));
  const fadeOutFrames = Math.max(1, Math.min(60, Math.floor(totalDuration * 0.25)));
  const fadeOutStart = Math.max(fadeInFrames + 1, totalDuration - fadeOutFrames);
  const fadeOutEnd = Math.max(fadeOutStart + 1, totalDuration);
  const transitionFrames = Math.max(1, Math.round(0.8 * fps));

  // 智能音频闪避 (Audio Ducking): 提取全片声学语音活跃区间 (防范无配音静音分镜误闪避)
  const speechIntervals = React.useMemo(() => {
    return scenes.flatMap((scene) => {
      if (scene.words && scene.words.length > 0) {
        return scene.words.map((w: any) => ({
          start: (w.globalStartFrame ?? (scene.startFrame + w.startFrame)) as number,
          end: (w.globalEndFrame ?? (scene.startFrame + w.endFrame)) as number,
        }));
      }
      if (scene.audioPath) {
        return [{ start: scene.startFrame, end: scene.startFrame + scene.durationInFrames }];
      }
      return [];
    });
  }, [scenes]);

  const enableDucking = (timelineData as any).enableDucking !== false;
  const duckRatio = (timelineData as any).bgmDuckRatio ?? 0.45;
  const duckFrames = Math.max(5, Math.round(fps * 0.5)); // 帧率自适应 ~500ms 阻尼过渡

  return (
    <AbsoluteFill style={{ backgroundColor: '#090d16', color: '#fff', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* 全局极客科技氛围背景音乐 (轻柔垫乐 + 自动循环 + 首尾淡入淡出 + 语音智能闪避) */}
      {enableBgm && (
        <Audio
          src={staticFile(bgmPath)}
          volume={(f) => {
            const baseVol = interpolate(
              f,
              [0, fadeInFrames, fadeOutStart, fadeOutEnd],
              [0, bgmVolume, bgmVolume, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            if (!enableDucking || speechIntervals.length === 0) {
              return baseVol;
            }

            // 计算当前帧距离最近语音活跃区间的帧距
            let minDistToSpeech = Infinity;
            for (const interval of speechIntervals) {
              if (f >= interval.start && f <= interval.end) {
                minDistToSpeech = 0;
                break;
              }
              const dist = f < interval.start ? interval.start - f : f - interval.end;
              if (dist < minDistToSpeech) {
                minDistToSpeech = dist;
              }
            }

            // 平滑过渡：0 帧(正讲话)压低至 duckRatio (约 45%)，duckFrames 帧(~0.5s 停顿/转场)平滑回升至 100%
            const duckMultiplier = interpolate(
              minDistToSpeech,
              [0, duckFrames],
              [duckRatio, 1.0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            return baseVol * duckMultiplier;
          }}
          loop
        />
      )}

      {scenes.map((scene, idx) => {
        const sceneTheme = getTheme((scene as any).theme || (timelineData as any).theme);
        return (
          <Sequence
            key={scene.id}
            from={scene.startFrame}
            durationInFrames={scene.durationInFrames}
          >
            {/* 配音音频 */}
            {scene.audioPath && <Audio src={staticFile(scene.audioPath)} />}

            {/* 场景起幅转场高科技音效 (从第二镜开始触发，layout="none" 杜绝无意义绝对定位 DOM 污染) */}
            {enableSfx && idx > 0 && (
              <Sequence from={0} durationInFrames={transitionFrames} layout="none">
                <Audio src={staticFile('audio/sfx_transition.wav')} volume={0.18} />
              </Sequence>
            )}

            {/* 场景画面呈现：如果有自定义标题或分镜超过5个，使用通用高质感分镜渲染器，否则回退到经典演示场景 */}
            {(scene as any).title ? (
              <UniversalScene scene={scene as any} />
            ) : idx === 0 ? (
              <Scene01VoiceClone durationInFrames={scene.durationInFrames} />
            ) : idx === 1 ? (
              <Scene02Whiteboard durationInFrames={scene.durationInFrames} />
            ) : idx === 2 ? (
              <Scene03HandsOn durationInFrames={scene.durationInFrames} />
            ) : idx === 3 ? (
              <Scene04HybridLive durationInFrames={scene.durationInFrames} />
            ) : idx === 4 ? (
              <Scene05GoogleFlowShorts durationInFrames={scene.durationInFrames} />
            ) : (
              <UniversalScene scene={scene as any} />
            )}

            {/* 逐字动态弹跳大字幕 */}
            {scene.words && scene.words.length > 0 && (
              <DynamicSubtitles words={scene.words} sceneStartFrame={scene.startFrame} theme={sceneTheme} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

// =========================================================================
// 主题色彩风格样片对比组件 (用于给创作者和用户多维度比对调色方案)
// =========================================================================
export const ThemeShowcase: React.FC<{ themeName: ThemeName }> = ({ themeName }) => {
  const sampleScene: SceneMeta = {
    id: 'demo_theme',
    durationInFrames: 120,
    title: 'AI Video Studio: 声音先行与代码即视频范式',
    badge: 'PARADIGM SHIFT · 架构范式',
    theme: themeName,
    cards: [
      {
        title: '声音绝对时钟',
        desc: '以实际声学波形物理时长作为顶层单一真实时钟，画面全自动适配',
        tag: 'AUDIO FIRST'
      },
      {
        title: '纯函数状态机',
        desc: 'Scene = f(frame)，所有动画均由数学公式和物理阻尼计算，零盲盒抽卡',
        tag: 'DETERMINISTIC'
      },
      {
        title: '顶级工业美学',
        desc: '告别廉价荧光字与儿童画，吸纳 Silicon Valley 现代顶级深色设计系统',
        tag: 'DE-AI CRAFT'
      }
    ]
  };

  const theme = getTheme(themeName);
  const sampleWords = [
    { text: '欢迎进入 AI Video Studio 工业级视频自动化系统', startFrame: 0, endFrame: 120 }
  ];

  return (
    <AbsoluteFill>
      <UniversalScene scene={sampleScene} />
      <DynamicSubtitles words={sampleWords} sceneStartFrame={0} theme={theme} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  const fps = timelineData.fps || 30;
  const durationInFrames = Math.max(1, timelineData.totalDurationInFrames || 2032);

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

      {/* 4 大顶级设计流派样片演示 Composition (方便即时比对风格) */}
      <Composition
        id="DemoLinearGraphite"
        component={ThemeShowcase}
        defaultProps={{ themeName: 'linear-graphite' as ThemeName }}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="DemoVercelGeist"
        component={ThemeShowcase}
        defaultProps={{ themeName: 'vercel-geist' as ThemeName }}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="DemoMotionCanvasWarm"
        component={ThemeShowcase}
        defaultProps={{ themeName: 'motion-canvas-warm' as ThemeName }}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="DemoCyberBlueprint"
        component={ThemeShowcase}
        defaultProps={{ themeName: 'cyber-blueprint' as ThemeName }}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 3 大去 AI 化全新视频流派完整动态 Demo */}
      <Composition
        id="StyleDemoFireship"
        component={FireshipKineticView}
        durationInFrames={325}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="StyleDemoAppleKeynote"
        component={AppleKeynoteView}
        durationInFrames={298}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="StyleDemoMotionCanvas"
        component={MotionCanvasView}
        durationInFrames={288}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};

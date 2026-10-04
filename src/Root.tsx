import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, staticFile } from 'remotion';
import timelineData from '../public/timeline.json';
import { TerminalWindow } from './components/TerminalWindow';
import { DynamicSubtitles } from './components/DynamicSubtitles';

export const MasterVideo: React.FC = () => {
  const { scenes } = timelineData;

  return (
    <AbsoluteFill style={{ backgroundColor: '#090d16', color: '#fff' }}>
      {scenes.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.durationInFrames}
        >
          {/* 配音音频 */}
          {scene.audioPath && <Audio src={staticFile(scene.audioPath)} />}

          {/* 分镜画面呈现 */}
          <AbsoluteFill
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '60px',
            }}
          >
            {scene.type === 'TerminalCodeDemo' ? (
              <TerminalWindow
                title="ai-video-studio - bash"
                command="npx remotion render src/index.ts MasterVideo --concurrency=6"
                output={[
                  "[OK] Loading timeline contract...",
                  "[OK] Audio & ASR alignment verified.",
                  "[OK] Multi-core Headless Chromium rendering at 30 FPS..."
                ]}
              />
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '24px',
                  textAlign: 'center',
                }}
              >
                <div
                  style={{
                    fontSize: '64px',
                    fontWeight: 900,
                    background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  {scene.text || "全链路 AI 视频自动化生产工作室"}
                </div>
                <div style={{ fontSize: '24px', color: '#94a3b8' }}>
                  {scene.emotion && `情绪标签识别: ${scene.emotion}`}
                </div>
              </div>
            )}
          </AbsoluteFill>

          {/* 词级动态字幕 */}
          {scene.words && scene.words.length > 0 && (
            <DynamicSubtitles words={scene.words} />
          )}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  const fps = timelineData.fps || 30;
  const durationInFrames = Math.max(1, timelineData.totalDurationInFrames || 180);

  return (
    <>
      {/* 16:9 横屏全片 */}
      <Composition
        id="MasterVideo"
        component={MasterVideo}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1920}
        height={1080}
      />
      {/* 9:16 竖屏自媒体 */}
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

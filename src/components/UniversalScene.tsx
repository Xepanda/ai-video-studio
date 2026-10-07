import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Audio, Sequence, staticFile } from 'remotion';
import timelineData from '../../public/timeline.json';
import { TerminalWindow } from './TerminalWindow';
import { ArchitectureTopology, TopologyNode, TopologyLink } from './ArchitectureTopology';
import { MetricComparison, MetricCategory } from './MetricComparison';
import { ProceduralBackground } from './ProceduralBackground';
import { getTheme, ThemeName, ThemeConfig } from '../styles/theme';

export interface SceneMeta {
  id: string;
  type?: string;
  title?: string;
  badge?: string;
  subtitle?: string;
  bulletPoints?: string[];
  codeSnippet?: string;
  codeLang?: string;
  cards?: Array<{ title: string; desc: string; tag?: string; icon?: string }>;
  durationInFrames: number;
  text?: string;
  enableSfx?: boolean;
  topologyNodes?: TopologyNode[];
  topologyLinks?: TopologyLink[];
  metrics?: MetricCategory[];
  theme?: ThemeName;
}

export const UniversalScene: React.FC<{ scene: SceneMeta }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 获取活动主题 (优先分镜声明，次选全局时间轴，默认 obsidian-minimal)
  const activeThemeName = scene.theme || (timelineData as any).theme || 'obsidian-minimal';
  const theme: ThemeConfig = getTheme(activeThemeName);

  const isSfxEnabled = (timelineData as any).enableSfx !== false && scene.enableSfx !== false;

  // 1. Ken Burns 电影级微慢推运镜 (场景全长内 scale 从 1.00 平滑匀速推至 1.025，微移 Y 轴)
  const sceneProgress = Math.min(1, Math.max(0, frame / Math.max(1, scene.durationInFrames)));
  const cameraScale = interpolate(sceneProgress, [0, 1], [1.0, 1.025]);
  const cameraTranslateY = interpolate(sceneProgress, [0, 1], [0, -6]);

  // 2. 元素平滑入场弹簧 (沉稳工业阻尼，避免轻浮弹跳)
  const titleSpring = spring({ frame, fps, config: { damping: 18, stiffness: 140 } });
  const contentSpring = spring({ frame: Math.max(0, frame - 8), fps, config: { damping: 18, stiffness: 120 } });

  const title = scene.title || `第 ${scene.id.replace('scene_', '')} 幕 · 核心架构与实践`;
  const badge = scene.badge || 'TECHNICAL DEEP DIVE · 核心技术要点';

  const cards = scene.cards || [
    { title: '高性能计算底座', desc: '深度利用本地 AVX2 向量加速与量化运行时，零显卡依赖稳定运行', tag: 'CORE INFRA' },
    { title: '全链路时间契约', desc: '端到端对齐毫秒级音频打点，保障音画同步与逐字动画精准衔接', tag: 'ALIGNMENT' },
    { title: '工业级工程交付', desc: '静态质量门禁与多核光栅化渲染，保证每一次视频发布坚如磐石', tag: 'QUALITY GATE' }
  ];

  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      {/* 底层：纯代码渲染的程序化工科动态背景 */}
      <ProceduralBackground theme={theme} />

      {/* 内容层：承载 Ken Burns 微运镜 */}
      <AbsoluteFill style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 80px',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        transform: `scale(${cameraScale}) translateY(${cameraTranslateY}px)`,
        transformOrigin: 'center center',
      }}>
        {/* 顶部标签 Pill：极简工科边框与等宽字符 */}
        <div style={{
          transform: `translateY(${interpolate(titleSpring, [0, 1], [-16, 0])}px)`,
          opacity: titleSpring,
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '20px',
          backgroundColor: theme.badgeBg,
          border: theme.badgeBorder,
          color: theme.badgeColor,
          fontSize: '14px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '16px',
          backdropFilter: 'blur(8px)',
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: theme.accentColor,
            boxShadow: `0 0 8px ${theme.accentColor}`
          }} />
          {badge}
        </div>

        {/* 主标题：纯净高质感冷白金属渐变，告别俗套蓝紫 */}
        <div style={{
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.94, 1.0])})`,
          opacity: titleSpring,
          fontSize: '52px',
          fontWeight: 800,
          textAlign: 'center',
          background: theme.titleGradient,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '40px',
          maxWidth: '1440px',
          lineHeight: 1.25,
          letterSpacing: '-0.5px',
        }}>
          {title}
        </div>

        {/* 主展示区：根据 scene.type 动态匹配组件 */}
        {(scene.type === 'ArchitectureTopology' || scene.type === 'TopologyFlow') ? (
          <div style={{
            width: '100%',
            maxWidth: '1500px',
            transform: `translateY(${interpolate(contentSpring, [0, 1], [24, 0])}px)`,
            opacity: contentSpring
          }}>
            <ArchitectureTopology
              nodes={scene.topologyNodes}
              links={scene.topologyLinks}
            />
          </div>
        ) : (scene.type === 'MetricComparison' || scene.type === 'MetricChart') ? (
          <div style={{
            width: '100%',
            maxWidth: '1440px',
            transform: `translateY(${interpolate(contentSpring, [0, 1], [24, 0])}px)`,
            opacity: contentSpring
          }}>
            <MetricComparison
              metrics={scene.metrics}
            />
          </div>
        ) : scene.codeSnippet ? (
          <div style={{
            width: '100%',
            maxWidth: '1280px',
            transform: `translateY(${interpolate(contentSpring, [0, 1], [24, 0])}px)`,
            opacity: contentSpring
          }}>
            <TerminalWindow
              title={scene.codeLang || 'Architecture.rs'}
              content={scene.codeSnippet}
            />
          </div>
        ) : (
          <>
            {/* 独立音效层：完全脱离 Flexbox DOM 结构，且允许 30 帧完整音效尾韵 */}
            {isSfxEnabled && (
              <AbsoluteFill style={{ pointerEvents: 'none' }}>
                {cards.map((_, i) => {
                  const cardDelay = 12 + i * 5;
                  return (
                    <Sequence key={i} from={cardDelay} durationInFrames={30} layout="none">
                      <Audio src={staticFile('audio/sfx_pop.wav')} volume={0.06} />
                    </Sequence>
                  );
                })}
              </AbsoluteFill>
            )}

            <div style={{
              display: 'flex',
              gap: '28px',
              width: '100%',
              maxWidth: '1440px',
              transform: `translateY(${interpolate(contentSpring, [0, 1], [24, 0])}px)`,
              opacity: contentSpring
            }}>
              {cards.map((card, i) => {
                const cardDelay = 12 + i * 5;
                const cardSpring = spring({ frame: Math.max(0, frame - cardDelay), fps, config: { damping: 16, stiffness: 140 } });
                return (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      backgroundColor: theme.cardBg,
                      border: theme.cardBorder,
                      borderRadius: '20px',
                      padding: '36px 30px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      boxShadow: theme.cardShadow,
                      backdropFilter: 'blur(16px)',
                      WebkitBackdropFilter: 'blur(16px)',
                      transform: `scale(${interpolate(cardSpring, [0, 1], [0.94, 1.0])})`,
                      opacity: cardSpring
                    }}
                  >
                    <div>
                      {/* 顶部数字序号与标签 Pill，告别儿童画风格 Emoji */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                        <span style={{
                          fontFamily: 'JetBrains Mono, monospace, monospace',
                          fontSize: '18px',
                          fontWeight: 800,
                          color: theme.accentColor,
                          letterSpacing: '1px'
                        }}>
                          {String(i + 1).padStart(2, '0')}
                        </span>
                        {card.tag && (
                          <span style={{
                            backgroundColor: 'rgba(255, 255, 255, 0.05)',
                            color: theme.cardTitleColor,
                            padding: '4px 10px',
                            borderRadius: '6px',
                            fontSize: '12px',
                            fontWeight: 700,
                            letterSpacing: '0.5px',
                            border: '1px solid rgba(255, 255, 255, 0.1)'
                          }}>
                            {card.tag}
                          </span>
                        )}
                      </div>

                      <div style={{ fontSize: '24px', fontWeight: 700, color: theme.cardTitleColor, marginBottom: '14px', letterSpacing: '-0.3px' }}>
                        {card.title}
                      </div>

                      <div style={{ fontSize: '16px', color: theme.cardDescColor, lineHeight: 1.65 }}>
                        {card.desc}
                      </div>
                    </div>

                    {/* 底部极细工科强调线 */}
                    <div style={{
                      height: '2px',
                      borderRadius: '1px',
                      background: theme.accentColor,
                      opacity: 0.8,
                      marginTop: '28px',
                      width: `${interpolate(cardSpring, [0, 1], [0, 100])}%`
                    }} />
                  </div>
                );
              })}
            </div>
          </>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

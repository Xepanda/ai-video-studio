import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Audio, Sequence, staticFile } from 'remotion';
import timelineData from '../../public/timeline.json';
import { TerminalWindow } from './TerminalWindow';
import { ArchitectureTopology, TopologyNode, TopologyLink } from './ArchitectureTopology';
import { MetricComparison, MetricCategory } from './MetricComparison';
import { ProceduralBackground } from './ProceduralBackground';
import { CinematicHeroScene } from './CinematicHeroScene';
import { getTheme, ThemeName, ThemeConfig, safeColorWithAlpha } from '../styles/theme';
import { TechNewsShortsScene, TweetEmbedCardProps, BinaryBentoCardProps, TweetMetrics, ProtocolStackTower, ProtocolTowerProps, PacketAssemblyPipeline, PacketAssemblyProps, RouterPacketInspection, RouterInspectionProps, WeChatMobileMockup, WeChatMobileProps } from './shorts';
import { WebBrowserMockupScene } from './shorts/WebBrowserMockupScene';

export interface SceneMeta {
  id: string;
  type?: string;
  title?: string;
  badge?: string;
  pill?: string;
  heroImage?: string;
  heroVideo?: string;
  videoPath?: string;
  systemTag?: string;
  cameraMotion?: 'push-in' | 'pan-left' | 'pan-right' | 'pull-out';
  highlights?: Array<{ label: string; value: string; color?: string }>;
  sceneIndex?: number;
  totalScenes?: number;
  subtitle?: string;
  bulletPoints?: string[];
  codeSnippet?: string;
  codeTitle?: string;
  codeLang?: string;
  cards?: Array<{ title: string; desc: string; tag?: string; icon?: string }>;
  durationInFrames: number;
  text?: string;
  desc?: string;
  enableSfx?: boolean;
  topologyNodes?: TopologyNode[];
  topologyLinks?: TopologyLink[];
  metrics?: MetricCategory[] | TweetMetrics;
  theme?: ThemeName;
  tweet?: Partial<TweetEmbedCardProps>;
  binaryBento?: Partial<BinaryBentoCardProps>;
  protocolTower?: ProtocolTowerProps;
  packetAssembly?: PacketAssemblyProps;
  routerInspection?: RouterInspectionProps;
  wechat?: WeChatMobileProps;
  inverted?: boolean;
  category?: string;
  highlightWords?: string[];
  blocksActive?: number;
  blocksTotal?: number;
}

function useSafeRemotionConfig(): { frame: number; fps: number; width: number; height: number } {
  try {
    const frame = useCurrentFrame();
    const config = useVideoConfig();
    return { frame, fps: config.fps, width: config.width, height: config.height };
  } catch {
    return { frame: 0, fps: 30, width: 1920, height: 1080 };
  }
}

export const UniversalScene: React.FC<{ scene: SceneMeta }> = ({ scene }) => {
  const { frame, fps, width, height } = useSafeRemotionConfig();
  const isVertical = width < height;

  // 获取活动主题 (优先分镜声明，次选全局时间轴，由 getTheme 统一提供默认回退)
  const activeThemeName = scene.theme || (timelineData as any).theme;
  const theme: ThemeConfig = getTheme(activeThemeName);

  const allScenes = (timelineData as any).scenes || [];
  const derivedIndex = allScenes.findIndex((s: any) => s.id === scene.id) + 1;
  const sceneIndex = scene.sceneIndex || (derivedIndex > 0 ? derivedIndex : 1);
  const totalScenes = scene.totalScenes || (allScenes.length > 0 ? allScenes.length : 6);

  // 网页/代码仓库真实截图视窗场景
  if (scene.type === 'WebBrowserMockup' || scene.type === 'BrowserScreenshot' || Boolean((scene as any).browser)) {
    const browser = (scene as any).browser || {};
    return (
      <WebBrowserMockupScene
        url={browser.url || (scene as any).url}
        image={browser.image || scene.heroImage || (scene as any).image || ''}
        title={scene.title}
        subtitle={(scene as any).subtitle || (scene as any).desc}
        badge={scene.badge}
        pill={scene.pill}
        highlights={scene.highlights || browser.highlights}
        cameraMotion={scene.cameraMotion || browser.cameraMotion}
        theme={theme}
      />
    );
  }

  // 极简科技资讯 / 竖屏短视频场景优先路由
  if (
    scene.type === 'TechNewsShorts' ||
    scene.type === 'TechNews' ||
    scene.type === 'TweetEmbed' ||
    scene.type === 'BinaryBento' ||
    scene.type === 'MinimalHeadline' ||
    Boolean(scene.tweet) ||
    Boolean(scene.binaryBento)
  ) {
    return <TechNewsShortsScene scene={scene} activeTheme={theme} />;
  }

  // 网络协议科普组件族路由 (显式 scene.type 绝对优先, 嵌套配置对象隐式推断兜底, 与 tweet/binaryBento 同模式)
  if (scene.type === 'ProtocolStackTower' || Boolean(scene.protocolTower)) {
    return (
      <ProtocolStackTower
        protocolTower={scene.protocolTower}
        title={scene.title}
        category={scene.category}
      />
    );
  }

  if (scene.type === 'PacketAssemblyPipeline' || Boolean(scene.packetAssembly)) {
    return (
      <PacketAssemblyPipeline
        packetAssembly={scene.packetAssembly}
        title={scene.title}
        category={scene.category}
      />
    );
  }

  if (scene.type === 'RouterPacketInspection' || Boolean(scene.routerInspection)) {
    return (
      <RouterPacketInspection
        routerInspection={scene.routerInspection}
        title={scene.title}
        category={scene.category}
      />
    );
  }

  if (scene.type === 'WeChatMobileMockup' || Boolean(scene.wechat)) {
    return (
      <WeChatMobileMockup
        wechat={scene.wechat}
        title={scene.title}
        category={scene.category}
      />
    );
  }

  // 若分镜声明为 CinematicHero 或非特异组件类型且配置了 heroImage/heroVideo/videoPath，优先光栅化电影级 2.5D 原画或动态视频流
  const hasVisualMedia = Boolean(scene.heroImage || scene.heroVideo || scene.videoPath);
  const isDedicatedNonHeroType = ['ArchitectureTopology', 'TopologyFlow', 'MetricComparison', 'MetricChart', 'TerminalWindow', 'ProtocolStackTower', 'PacketAssemblyPipeline', 'RouterPacketInspection', 'WeChatMobileMockup'].includes(scene.type || '');
  if (scene.type === 'CinematicHero' || (!isDedicatedNonHeroType && hasVisualMedia)) {
    return (
      <CinematicHeroScene
        heroImage={scene.heroImage || ''}
        heroVideo={scene.heroVideo || scene.videoPath}
        title={scene.title}
        badge={scene.badge}
        pill={scene.pill}
        highlights={scene.highlights}
        cameraMotion={scene.cameraMotion}
        theme={theme}
        durationInFrames={scene.durationInFrames}
        sceneIndex={sceneIndex}
        totalScenes={totalScenes}
        systemTag={scene.systemTag || (timelineData as any).systemTag || 'DIGITAL GRAVITY · ANTIGRAVITY LAB'}
      />
    );
  }

  const isSfxEnabled = (timelineData as any).enableSfx !== false && scene.enableSfx !== false;

  // 1. Ken Burns 电影级微慢推运镜 (场景全长内 scale 从 1.00 平滑匀速推至 1.025，微移 Y 轴)
  const safeDuration = Math.max(1, scene.durationInFrames || 1);
  const sceneProgress = Math.min(1, Math.max(0, frame / safeDuration));
  const cameraScale = interpolate(sceneProgress, [0, 1], [1.0, 1.025]);
  const cameraTranslateY = interpolate(sceneProgress, [0, 1], [0, -6]);

  // 2. 长分镜时序逐级高亮联动 (消除长镜头静态疲劳，缺省 topologyNodes 时默认对标 5 阶段流水线)
  const topologyNodeCount = (scene.topologyNodes && scene.topologyNodes.length > 0)
    ? scene.topologyNodes.length
    : 5;
  const activeNodeIndex = Math.min(topologyNodeCount - 1, Math.floor(sceneProgress * topologyNodeCount));

  // 3. 元素平滑入场弹簧 (沉稳工业阻尼，避免轻浮弹跳)
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
        padding: isVertical ? '80px 48px' : '60px 80px',
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
          fontSize: isVertical ? '13px' : '14px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: isVertical ? '12px' : '16px',
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
          fontSize: isVertical ? '38px' : '52px',
          fontWeight: 800,
          textAlign: 'center',
          background: theme.titleGradient,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: isVertical ? '28px' : '40px',
          maxWidth: isVertical ? '920px' : '1440px',
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
              activeNodeIndex={activeNodeIndex}
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
              metrics={Array.isArray(scene.metrics) ? scene.metrics : undefined}
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
              title={scene.codeTitle || scene.codeLang || 'Architecture.rs'}
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
              flexDirection: isVertical ? 'column' : 'row',
              gap: isVertical ? '18px' : '28px',
              width: '100%',
              maxWidth: isVertical ? '880px' : '1440px',
              transform: `translateY(${interpolate(contentSpring, [0, 1], [24, 0])}px)`,
              opacity: contentSpring
            }}>
              {(() => {
                const activeCardIndex = cards.length > 0
                  ? Math.min(cards.length - 1, Math.floor(sceneProgress * cards.length))
                  : 0;

                return cards.map((card, i) => {
                  const cardDelay = 12 + i * 5;
                  const cardSpring = spring({ frame: Math.max(0, frame - cardDelay), fps, config: { damping: 16, stiffness: 140 } });
                  const isCardActive = i === activeCardIndex;

                  const baseScale = interpolate(cardSpring, [0, 1], [0.94, 1.0]);
                  const finalCardScale = isCardActive ? baseScale * 1.025 : baseScale;
                  const activeBorder = isCardActive ? `1px solid ${safeColorWithAlpha(theme.accentColor, '90')}` : theme.cardBorder;
                  const activeShadow = isCardActive
                    ? `0 24px 48px -12px rgba(0, 0, 0, 0.90), 0 0 36px ${safeColorWithAlpha(theme.accentColor, '25')}, inset 0 1px 0 rgba(255, 255, 255, 0.22)`
                    : theme.cardShadow;

                  return (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        backgroundColor: theme.cardBg,
                        border: activeBorder,
                        borderRadius: '20px',
                        padding: isVertical ? '22px 26px' : '36px 30px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        boxShadow: activeShadow,
                        backdropFilter: 'blur(16px)',
                        WebkitBackdropFilter: 'blur(16px)',
                        transform: `scale(${finalCardScale})`,
                        opacity: cardSpring
                      }}
                    >
                      <div>
                        {/* 顶部数字序号与标签 Pill，告别儿童画风格 Emoji */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: isVertical ? '14px' : '24px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{
                              fontFamily: 'JetBrains Mono, monospace',
                              fontSize: isVertical ? '16px' : '18px',
                              fontWeight: 800,
                              color: theme.accentColor,
                              letterSpacing: '1px'
                            }}>
                              {String(i + 1).padStart(2, '0')}
                            </span>
                            {isCardActive && (
                              <span style={{
                                width: '6px',
                                height: '6px',
                                borderRadius: '50%',
                                backgroundColor: theme.accentColor,
                                boxShadow: `0 0 8px ${theme.accentColor}`,
                                opacity: 0.6 + Math.sin(frame / 4) * 0.4,
                                transform: `scale(${1 + Math.sin(frame / 4) * 0.15})`
                              }} />
                            )}
                          </div>
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

                        <div style={{ fontSize: isVertical ? '20px' : '24px', fontWeight: 700, color: theme.cardTitleColor, marginBottom: isVertical ? '10px' : '14px', letterSpacing: '-0.3px' }}>
                          {card.title}
                        </div>

                        <div style={{ fontSize: isVertical ? '14px' : '16px', color: theme.cardDescColor, lineHeight: 1.65 }}>
                          {card.desc}
                        </div>
                      </div>

                      {/* 底部极细工科强调线 */}
                      <div style={{
                        height: '2px',
                        borderRadius: '1px',
                        background: isCardActive ? theme.accentColor : 'rgba(255, 255, 255, 0.15)',
                        opacity: isCardActive ? 1.0 : 0.4,
                        marginTop: isVertical ? '16px' : '28px',
                        width: `${interpolate(cardSpring, [0, 1], [0, 100])}%`
                      }} />
                    </div>
                  );
                });
              })()}
            </div>
          </>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

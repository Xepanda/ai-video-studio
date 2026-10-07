import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Audio, Sequence, staticFile } from 'remotion';
import timelineData from '../../public/timeline.json';
import { TerminalWindow } from './TerminalWindow';
import { WhiteboardHanddrawn } from './WhiteboardHanddrawn';
import { ArchitectureTopology, TopologyNode, TopologyLink } from './ArchitectureTopology';
import { MetricComparison, MetricCategory } from './MetricComparison';

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
}

export const UniversalScene: React.FC<{ scene: SceneMeta }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const isSfxEnabled = (timelineData as any).enableSfx !== false && scene.enableSfx !== false;

  const titleSpring = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });
  const contentSpring = spring({ frame: Math.max(0, frame - 10), fps, config: { damping: 14, stiffness: 100 } });
  
  // 呼吸脉冲动效
  const pulse = Math.sin(frame / 6) * 4;

  const title = scene.title || `第 ${scene.id.replace('scene_', '')} 幕 · 核心架构与实践`;
  const badge = scene.badge || 'TECHNICAL DEEP DIVE · 核心技术要点';
  const points = scene.bulletPoints || [
    '硬核实战架构与生产力工程化落地方案',
    '毫秒级吞吐优化与极致离线高保真表现',
    '全链路数据契约保障与自动化质量门禁'
  ];

  const cards = scene.cards || [
    { title: '高保真模型底座', desc: '深度利用本地 AVX2 向量加速与量化运行时，零显卡依赖稳定运行', tag: 'CORE INFRA', icon: '⚡' },
    { title: '全链路时间契约', desc: '端到端对齐毫秒级音频打点，保障音画同步与逐字动画完美衔接', tag: 'ALIGNMENT', icon: '🎯' },
    { title: '工业级工程交付', desc: '静态质量门禁与多核光栅化渲染，保证每一次视频发布坚如磐石', tag: 'QUALITY GATE', icon: '🛡️' }
  ];

  return (
    <AbsoluteFill style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 80px',
      background: 'radial-gradient(circle at 50% 30%, #0f172a 0%, #020617 100%)',
      color: '#f8fafc',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* 顶部标签 */}
      <div style={{
        transform: `translateY(${interpolate(titleSpring, [0, 1], [-20, 0])}px)`,
        opacity: titleSpring,
        fontSize: '18px',
        fontWeight: 800,
        color: '#38bdf8',
        letterSpacing: '4px',
        textTransform: 'uppercase',
        marginBottom: '12px'
      }}>
        {badge}
      </div>

      {/* 主标题 */}
      <div style={{
        transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1.0])})`,
        opacity: titleSpring,
        fontSize: '52px',
        fontWeight: 900,
        textAlign: 'center',
        background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        marginBottom: '40px',
        maxWidth: '1500px',
        lineHeight: 1.2
      }}>
        {title}
      </div>

      {/* 主展示区：根据 scene.type 或内容动态匹配最优视觉组件 */}
      {(scene.type === 'ArchitectureTopology' || scene.type === 'TopologyFlow') ? (
        <div style={{
          width: '100%',
          maxWidth: '1500px',
          transform: `translateY(${interpolate(contentSpring, [0, 1], [30, 0])}px)`,
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
          transform: `translateY(${interpolate(contentSpring, [0, 1], [30, 0])}px)`,
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
          transform: `translateY(${interpolate(contentSpring, [0, 1], [30, 0])}px)`,
          opacity: contentSpring
        }}>
          <TerminalWindow
            title={scene.codeLang || 'Architecture.rs'}
            content={scene.codeSnippet}
          />
        </div>
      ) : (
        <div style={{
          display: 'flex',
          gap: '32px',
          width: '100%',
          maxWidth: '1440px',
          transform: `translateY(${interpolate(contentSpring, [0, 1], [30, 0])}px)`,
          opacity: contentSpring
        }}>
          {cards.map((card, i) => {
            const cardDelay = 15 + i * 6;
            const cardSpring = spring({ frame: Math.max(0, frame - cardDelay), fps, config: { damping: 12 } });
            return (
              <React.Fragment key={i}>
                {/* 卡片弹出微音效 (layout="none" 杜绝 Flexbox 绝对定位 DOM 污染) */}
                {isSfxEnabled && (
                  <Sequence from={cardDelay} durationInFrames={10} layout="none">
                    <Audio src={staticFile('audio/sfx_pop.wav')} volume={0.06} />
                  </Sequence>
                )}
                <div
                  style={{
                  flex: 1,
                  backgroundColor: 'rgba(15, 23, 42, 0.75)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  borderRadius: '24px',
                  padding: '36px 30px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
                  backdropFilter: 'blur(12px)',
                  transform: `scale(${interpolate(cardSpring, [0, 1], [0.92, 1.0])})`,
                  opacity: cardSpring
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <span style={{ fontSize: '36px' }}>{card.icon || '💎'}</span>
                    {card.tag && (
                      <span style={{
                        backgroundColor: 'rgba(56, 189, 248, 0.15)',
                        color: '#38bdf8',
                        padding: '4px 12px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        fontWeight: 700,
                        border: '1px solid rgba(56, 189, 248, 0.3)'
                      }}>
                        {card.tag}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#f8fafc', marginBottom: '14px' }}>
                    {card.title}
                  </div>
                  <div style={{ fontSize: '18px', color: '#94a3b8', lineHeight: 1.6 }}>
                    {card.desc}
                  </div>
                </div>

                {/* 底部动态装饰线 */}
                <div style={{
                  height: '4px',
                  borderRadius: '2px',
                  background: 'linear-gradient(90deg, #38bdf8 0%, #818cf8 100%)',
                  marginTop: '28px',
                  width: `${interpolate(cardSpring, [0, 1], [0, 100])}%`
                }} />
              </div>
            </React.Fragment>
          );
        })}
        </div>
      )}
    </AbsoluteFill>
  );
};

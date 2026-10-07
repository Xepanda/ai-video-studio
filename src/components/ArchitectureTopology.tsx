import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

export interface TopologyNode {
  id: string;
  label: string;
  sublabel?: string;
  icon?: string;
  status?: string;
  statusColor?: string;
  x?: number; // 百分比 0 ~ 100
  y?: number; // 百分比 0 ~ 100
}

export interface TopologyLink {
  from: string;
  to: string;
  label?: string;
  active?: boolean;
}

export interface ArchitectureTopologyProps {
  nodes?: TopologyNode[];
  links?: TopologyLink[];
  title?: string;
  activeNodeIndex?: number;
  activeNodeId?: string;
}

const safeColorWithAlpha = (color: string | undefined, alphaHex: string, fallback: string = '#38bdf8') => {
  const base = color || fallback;
  if (base.startsWith('#') && (base.length === 7 || base.length === 4)) {
    return `${base}${alphaHex}`;
  }
  return base;
};

export const ArchitectureTopology: React.FC<ArchitectureTopologyProps> = ({
  nodes: customNodes,
  links: customLinks,
  title,
  activeNodeIndex,
  activeNodeId,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 默认拓扑架构节点配置 (5阶典型工业级视频流水线架构)
  const defaultNodes: TopologyNode[] = [
    { id: 'script', label: '剧本分镜中枢', sublabel: 'JSON Schema 声明式契约', icon: '📜', status: 'SOURCE', statusColor: '#818cf8', x: 12, y: 50 },
    { id: 'tts', label: 'ChatTTS 声学引擎', sublabel: 'Seed 4444 专属随和音色', icon: '🎙️', status: 'SYNTH', statusColor: '#38bdf8', x: 38, y: 26 },
    { id: 'aligner', label: 'Paraformer 物理打点', sublabel: '毫秒级双向约束时间戳', icon: '⏱️', status: 'ALIGNED', statusColor: '#34d399', x: 38, y: 74 },
    { id: 'timeline', label: 'Timeline 数据契约', sublabel: '全链路时间轴总线', icon: '🧬', status: 'SYNCED', statusColor: '#fbbf24', x: 65, y: 50 },
    { id: 'remotion', label: 'Remotion 多核光栅化', sublabel: '1080p 60FPS 极速成片', icon: '🎬', status: 'RENDER', statusColor: '#f43f5e', x: 90, y: 50 }
  ];

  const defaultLinks: TopologyLink[] = [
    { from: 'script', to: 'tts', label: 'TTS 文本派发', active: true },
    { from: 'script', to: 'aligner', label: '分镜原稿对齐', active: true },
    { from: 'tts', to: 'aligner', label: '波形时钟流', active: true },
    { from: 'tts', to: 'timeline', label: 'Audio 路径注册', active: true },
    { from: 'aligner', to: 'timeline', label: '字符级 Frame 打点', active: true },
    { from: 'timeline', to: 'remotion', label: '声明式总线渲染', active: true }
  ];

  const nodes = customNodes && customNodes.length > 0 ? customNodes : defaultNodes;
  const links = customLinks && customLinks.length > 0 ? customLinks : defaultLinks;

  // 节点 ID 到坐标查找表
  const nodeMap = new Map<string, TopologyNode>();
  nodes.forEach(n => nodeMap.set(n.id, n));

  // 全局 SVG 入场动效
  const svgSpring = spring({ frame, fps, config: { damping: 14 } });

  return (
    <div style={{
      width: '100%',
      maxWidth: '1500px',
      height: '520px',
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      border: '1px solid rgba(56, 189, 248, 0.25)',
      borderRadius: '24px',
      padding: '30px',
      boxShadow: '0 24px 48px rgba(0, 0, 0, 0.6)',
      backdropFilter: 'blur(16px)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* 顶部标题栏 */}
      {title && (
        <div style={{
          fontSize: '18px',
          fontWeight: 800,
          color: '#38bdf8',
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '10px'
        }}>
          {title}
        </div>
      )}

      {/* SVG 拓扑连线与光脉冲流动 (绑定标准 1500x520 viewBox，保证无论父容器何等分辨率比例均绝对精准重合) */}
      <svg
        viewBox="0 0 1500 520"
        preserveAspectRatio="none"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          opacity: svgSpring
        }}
      >
        <defs>
          <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0.4" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {links.map((link, idx) => {
          const fromNode = nodeMap.get(link.from);
          const toNode = nodeMap.get(link.to);
          if (!fromNode || !toNode) return null;

          const x1 = (fromNode.x ?? 10) * 15; // 0..100 -> 0..1500 viewBox 坐标
          const y1 = (fromNode.y ?? 50) * 5.2; // 0..100 -> 0..520 viewBox 坐标
          const x2 = (toNode.x ?? 90) * 15;
          const y2 = (toNode.y ?? 50) * 5.2;

          const dx = x2 - x1;
          const cx1 = x1 + dx * 0.5;
          const cy1 = y1;
          const cx2 = x1 + dx * 0.5;
          const cy2 = y2;
          const pathD = `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;

          // 光脉冲沿连线循环行进 (每 45 帧一个周期)
          const pulseT = ((frame + idx * 12) % 45) / 45;
          const t = pulseT;
          const px = (1 - t) ** 3 * x1 + 3 * (1 - t) ** 2 * t * cx1 + 3 * (1 - t) * t ** 2 * cx2 + t ** 3 * x2;
          const py = (1 - t) ** 3 * y1 + 3 * (1 - t) ** 2 * t * cy1 + 3 * (1 - t) * t ** 2 * cy2 + t ** 3 * y2;

          // 连线中点
          const midX = 0.125 * x1 + 0.375 * cx1 + 0.375 * cx2 + 0.125 * x2;
          const midY = 0.125 * y1 + 0.375 * cy1 + 0.375 * cy2 + 0.125 * y2;

          const isActive = link.active !== false;

          return (
            <g key={`link-${idx}`}>
              {/* 底层连接导轨 */}
              <path
                d={pathD}
                fill="none"
                stroke="url(#flowGrad)"
                strokeWidth="3"
                strokeDasharray="6 6"
              />

              {/* 连线文字标签 */}
              {link.label && (
                <g transform={`translate(${midX}, ${midY})`}>
                  <rect
                    x="-55"
                    y="-12"
                    width="110"
                    height="24"
                    rx="6"
                    fill="rgba(2, 6, 23, 0.85)"
                    stroke="rgba(56, 189, 248, 0.3)"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="4"
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="11"
                    fontFamily="system-ui, sans-serif"
                    fontWeight="600"
                  >
                    {link.label}
                  </text>
                </g>
              )}

              {/* 动态高亮行进脉冲光球 (仅在 active 时行进) */}
              {isActive && (
                <>
                  <circle
                    cx={px}
                    cy={py}
                    r="6"
                    fill="#38bdf8"
                    filter="url(#glow)"
                  />
                  <circle
                    cx={px}
                    cy={py}
                    r="3"
                    fill="#ffffff"
                  />
                </>
              )}
            </g>
          );
        })}
      </svg>

      {/* 节点渲染 */}
      {(() => {
        const currentActiveIndex = activeNodeIndex !== undefined
          ? activeNodeIndex
          : activeNodeId
            ? nodes.findIndex(n => n.id === activeNodeId)
            : -1;

        return nodes.map((node, i) => {
          const nodeSpring = spring({ frame: Math.max(0, frame - i * 5), fps, config: { damping: 13 } });
          const leftPct = node.x ?? 10;
          const topPct = node.y ?? 50;
          const statusColor = node.statusColor || '#38bdf8';
          const isCurrentActive = i === currentActiveIndex;

          const baseScale = interpolate(nodeSpring, [0, 1], [0.8, 1.0]);
          const finalScale = isCurrentActive ? baseScale * 1.05 : baseScale;
          const shadowStyle = isCurrentActive
            ? `0 16px 36px rgba(0, 0, 0, 0.8), 0 0 32px ${safeColorWithAlpha(statusColor, 'aa')}`
            : `0 10px 25px rgba(0, 0, 0, 0.5), 0 0 15px ${safeColorWithAlpha(statusColor, '33')}`;

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                left: `${leftPct}%`,
                top: `${topPct}%`,
                transform: `translate(-50%, -50%) scale(${finalScale})`,
                opacity: nodeSpring,
                backgroundColor: isCurrentActive ? 'rgba(7, 14, 34, 0.96)' : 'rgba(2, 6, 23, 0.92)',
                border: isCurrentActive ? `2.5px solid ${statusColor}` : `2px solid ${statusColor}`,
                borderRadius: '18px',
                padding: '16px 20px',
                minWidth: '200px',
                boxShadow: shadowStyle,
                zIndex: isCurrentActive ? 20 : 10,
                transition: 'box-shadow 0.2s ease, transform 0.2s ease'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '24px' }}>{node.icon || '📦'}</span>
                {node.status && (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 800,
                    color: statusColor,
                    backgroundColor: safeColorWithAlpha(statusColor, '22'),
                    padding: '2px 8px',
                    borderRadius: '6px',
                    border: `1px solid ${safeColorWithAlpha(statusColor, '44')}`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    {isCurrentActive && (
                      <span style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: statusColor,
                        boxShadow: `0 0 8px ${statusColor}`
                      }} />
                    )}
                    {node.status}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginBottom: '4px' }}>
                {node.label}
              </div>
              {node.sublabel && (
                <div style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.4 }}>
                  {node.sublabel}
                </div>
              )}
            </div>
          );
        });
      })()}
    </div>
  );
};

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
}

export const ArchitectureTopology: React.FC<ArchitectureTopologyProps> = ({
  nodes: customNodes,
  links: customLinks,
  title
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 默认拓扑架构节点配置 (4阶典型工业管线)
  const defaultNodes: TopologyNode[] = [
    { id: 'script', label: '剧本分镜中枢', sublabel: 'JSON Schema 声明式契约', icon: '📜', status: 'SOURCE', statusColor: '#818cf8', x: 12, y: 50 },
    { id: 'tts', label: 'ChatTTS 声学引擎', sublabel: 'Seed 4444 专属随和音色', icon: '🎙️', status: 'SYNTH', statusColor: '#38bdf8', x: 38, y: 26 },
    { id: 'aligner', label: 'Paraformer 物理打点', sublabel: '毫秒级双向约束时间戳', icon: '⏱️', status: 'ALIGNED', statusColor: '#34d399', x: 38, y: 74 },
    { id: 'timeline', label: 'Timeline 数据契约', sublabel: '全链路时间轴总线', icon: '🧬', status: 'SYNCED', statusColor: '#fbbf24', x: 65, y: 50 },
    { id: 'remotion', label: 'Remotion 多核光栅化', sublabel: '1080p 60FPS 极速成片', icon: '🎬', status: 'RENDER', statusColor: '#f43f5e', x: 90, y: 50 }
  ];

  const defaultLinks: TopologyLink[] = [
    { from: 'script', to: 'tts', label: 'TTS 文本派发' },
    { from: 'script', to: 'aligner', label: '分镜原稿对齐' },
    { from: 'tts', to: 'aligner', label: '波形时钟流' },
    { from: 'tts', to: 'timeline', label: 'Audio 路径注册' },
    { from: 'aligner', to: 'timeline', label: '字符级 Frame 打点' },
    { from: 'timeline', to: 'remotion', label: '声明式总线渲染' }
  ];

  const nodes = customNodes && customNodes.length > 0 ? customNodes : defaultNodes;
  const links = customLinks && customLinks.length > 0 ? customLinks : defaultLinks;

  // 节点 ID 到坐标查找表
  const nodeMap = new Map<string, TopologyNode>();
  nodes.forEach(n => nodeMap.set(n.id, n));

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

      {/* SVG 拓扑连线与光脉冲流动 */}
      <svg
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none'
        }}
      >
        <defs>
          <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0.8" />
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

          const x1 = (fromNode.x ?? 10) * 15; // 映射至 1500px 宽度
          const y1 = (fromNode.y ?? 50) * 5.2; // 映射至 520px 高度
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
          // 三次贝塞尔曲线公式采样脉冲坐标
          const px = (1 - t) ** 3 * x1 + 3 * (1 - t) ** 2 * t * cx1 + 3 * (1 - t) * t ** 2 * cx2 + t ** 3 * x2;
          const py = (1 - t) ** 3 * y1 + 3 * (1 - t) ** 2 * t * cy1 + 3 * (1 - t) * t ** 2 * cy2 + t ** 3 * y2;

          return (
            <g key={`link-${idx}`}>
              {/* 底层连接导轨 */}
              <path
                d={pathD}
                fill="none"
                stroke="rgba(56, 189, 248, 0.2)"
                strokeWidth="3"
                strokeDasharray="6 6"
              />
              {/* 动态高亮行进脉冲光球 */}
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
            </g>
          );
        })}
      </svg>

      {/* 节点渲染 */}
      {nodes.map((node, i) => {
        const nodeSpring = spring({ frame: Math.max(0, frame - i * 5), fps, config: { damping: 13 } });
        const leftPct = node.x ?? 10;
        const topPct = node.y ?? 50;

        return (
          <div
            key={node.id}
            style={{
              position: 'absolute',
              left: `${leftPct}%`,
              top: `${topPct}%`,
              transform: `translate(-50%, -50%) scale(${interpolate(nodeSpring, [0, 1], [0.8, 1.0])})`,
              opacity: nodeSpring,
              backgroundColor: 'rgba(2, 6, 23, 0.92)',
              border: `2px solid ${node.statusColor || '#38bdf8'}`,
              borderRadius: '18px',
              padding: '16px 20px',
              minWidth: '200px',
              boxShadow: `0 10px 25px rgba(0, 0, 0, 0.5), 0 0 15px ${node.statusColor || '#38bdf8'}33`,
              zIndex: 10
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '24px' }}>{node.icon || '📦'}</span>
              {node.status && (
                <span style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: node.statusColor || '#38bdf8',
                  backgroundColor: `${node.statusColor || '#38bdf8'}22`,
                  padding: '2px 8px',
                  borderRadius: '6px',
                  border: `1px solid ${node.statusColor || '#38bdf8'}44`
                }}>
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
      })}
    </div>
  );
};

import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
} from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';

export interface ProtocolTowerProps {
  activeLayer?: number; // 0: all, 1: PHY, 2: LINK, 3: NET, 4: TRANS, 5: APP
  showAllLayers?: boolean;
  title?: string;
  category?: string;
}

interface LayerItem {
  id: number;
  level: string;
  name: string;
  enName: string;
  color: string;
  protocols: string[];
  role: string;
  unit: string;
}

const LAYERS: LayerItem[] = [
  {
    id: 5,
    level: 'L5',
    name: '应用层',
    enName: 'Application',
    color: '#10b981',
    protocols: ['HTTP/3', 'WebSocket', 'DNS', 'Protobuf'],
    role: '用户数据报文 (Message)',
    unit: 'Payload',
  },
  {
    id: 4,
    level: 'L4',
    name: '传输层',
    enName: 'Transport',
    color: '#38bdf8',
    protocols: ['TCP', 'UDP', 'QUIC', '端口寻址'],
    role: '端到端可靠通信与分段',
    unit: 'Segment',
  },
  {
    id: 3,
    level: 'L3',
    name: '网络层',
    enName: 'Network',
    color: '#a855f7',
    protocols: ['IPv4', 'IPv6', 'BGP', 'OSPF'],
    role: '跨网络路由寻址与导航',
    unit: 'Packet',
  },
  {
    id: 2,
    level: 'L2',
    name: '数据链路层',
    enName: 'Data Link',
    color: '#f59e0b',
    protocols: ['Ethernet', 'Wi-Fi 7', 'MAC', 'CRC32'],
    role: '相邻节点跳步转发与检错',
    unit: 'Frame',
  },
  {
    id: 1,
    level: 'L1',
    name: '物理层',
    enName: 'Physical',
    color: '#06b6d4',
    protocols: ['光纤', '双绞线', '电磁波', '调制解调'],
    role: '光电物理信号高频传输',
    unit: 'Bitstream',
  },
];

export const ProtocolStackTower: React.FC<{ protocolTower?: ProtocolTowerProps; title?: string; category?: string }> = ({
  protocolTower = {},
  title: sceneTitle,
  category: sceneCategory,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const activeLayer = protocolTower.activeLayer ?? 0;
  const towerTitle = protocolTower.title || 'TCP/IP 五层协议大厦';

  // 流动光脉冲
  const photonProgress = (frame * 3.5) % 500;

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 48px 240px 48px',
        overflow: 'hidden',
      }}
    >
      {/* 顶部指示胶囊 */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 20px',
          borderRadius: '9999px',
          backgroundColor: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.35)',
          color: '#a5b4fc',
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '16px',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#6366f1', boxShadow: '0 0 10px #6366f1' }} />
        {sceneCategory || 'NETWORK ARCHITECTURE · 5 LAYERS'}
      </div>

      {/* 标题 */}
      <div
        style={{
          fontSize: '44px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          marginBottom: '36px',
          letterSpacing: '-0.5px',
        }}
      >
        {sceneTitle || towerTitle}
      </div>

      {/* 5层协议栈主卡片堆叠 */}
      <div
        style={{
          width: '100%',
          maxWidth: '860px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          position: 'relative',
        }}
      >
        {LAYERS.map((layer, idx) => {
          const layerSpring = spring({
            frame: Math.max(0, frame - idx * 4),
            fps,
            config: { damping: 14, stiffness: 140 },
          });

          const isActive = activeLayer === 0 || activeLayer === layer.id;
          const isFocused = activeLayer === layer.id;
          const glowIntensity = isFocused ? Math.sin(frame / 5) * 0.3 + 0.9 : 0.4;

          return (
            <div
              key={layer.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: isFocused ? 'rgba(30, 34, 48, 0.95)' : 'rgba(18, 20, 28, 0.85)',
                border: isFocused ? `2px solid ${layer.color}` : '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '20px',
                padding: '20px 28px',
                boxShadow: isFocused
                  ? `0 20px 40px -10px rgba(0,0,0,0.8), 0 0 30px ${layer.color}40`
                  : '0 10px 25px rgba(0,0,0,0.5)',
                transform: `translateX(${(1 - layerSpring) * -60}px) scale(${isFocused ? 1.03 : 1.0})`,
                opacity: layerSpring * (isActive ? 1.0 : 0.4),
                transition: 'border 0.2s ease',
              }}
            >
              {/* 层级标识 */}
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: `${layer.color}20`,
                  border: `1.5px solid ${layer.color}`,
                  color: layer.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontWeight: 900,
                  marginRight: '24px',
                  boxShadow: `0 0 15px ${layer.color}30`,
                }}
              >
                {layer.level}
              </div>

              {/* 中间信息 */}
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '26px', fontWeight: 800, color: '#f8fafc' }}>
                    {layer.name}
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: 600, color: '#64748b' }}>
                    {layer.enName}
                  </span>
                  <span
                    style={{
                      marginLeft: 'auto',
                      backgroundColor: `${layer.color}18`,
                      color: layer.color,
                      padding: '3px 10px',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: 700,
                    }}
                  >
                    数据单位: {layer.unit}
                  </span>
                </div>
                <div style={{ fontSize: '16px', color: '#94a3b8', lineHeight: '1.4' }}>
                  {layer.role}
                </div>
              </div>

              {/* 右侧协议徽章集合 */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '6px',
                  maxWidth: '220px',
                  justifyContent: 'flex-end',
                  marginLeft: '16px',
                }}
              >
                {layer.protocols.map((proto) => (
                  <span
                    key={proto}
                    style={{
                      fontSize: '13px',
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255,255,255,0.06)',
                      color: isFocused ? '#f1f5f9' : '#64748b',
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    {proto}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
} from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';

export interface RouterInspectionProps {
  mode?: 'switch' | 'router';
  deviceName?: string;
  action?: string;
  macMatch?: string;
  ipStatus?: string;
  title?: string;
  category?: string;
}

export const RouterPacketInspection: React.FC<{
  routerInspection?: RouterInspectionProps;
  title?: string;
  category?: string;
}> = ({
  routerInspection = {},
  title: sceneTitle,
  category: sceneCategory,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const mode = routerInspection.mode || 'switch';
  const deviceName = routerInspection.deviceName || (mode === 'switch' ? '二层以太网交换机' : '三层骨干路由器');
  const action = routerInspection.action || (mode === 'switch' ? '只读取最外层 MAC 帧头，不拆包秒级转发' : '剥除旧 MAC -> 查表匹配 IP -> 套上新 MAC 封箱');
  const macMatch = routerInspection.macMatch || '端口 #03 -> 匹配下一跳网卡';
  const ipStatus = routerInspection.ipStatus || 'IP 报头保持封闭保护';

  // 入场弹簧
  const cardSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 140 },
  });

  // 激光扫描线动画
  const laserX = interpolate((frame * 8) % 300, [0, 300], [0, 100]);
  const glow = Math.sin(frame / 6) * 0.2 + 0.8;

  const isSwitch = mode === 'switch';
  const accentColor = isSwitch ? '#f59e0b' : '#a855f7';

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
          backgroundColor: `${accentColor}18`,
          border: `1px solid ${accentColor}40`,
          color: accentColor,
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '20px',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: accentColor, boxShadow: `0 0 10px ${accentColor}` }} />
        {sceneCategory || (isSwitch ? 'L2 SWITCHING · HARDWARE ACCELERATED' : 'L3 ROUTING · PACKET RE-ENCAPSULATION')}
      </div>

      {/* 大标题 */}
      <div
        style={{
          fontSize: '44px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          marginBottom: '10px',
        }}
      >
        {sceneTitle || deviceName}
      </div>

      <div
        style={{
          fontSize: '20px',
          color: '#94a3b8',
          fontWeight: 600,
          marginBottom: '36px',
        }}
      >
        {isSwitch ? '「只看外壳」的极速检票闸机' : '「开箱换壳」的跨网导航枢纽'}
      </div>

      {/* 核心检查大视窗 */}
      <div
        style={{
          width: '100%',
          maxWidth: '920px',
          backgroundColor: 'rgba(18, 20, 28, 0.95)',
          border: `2px solid ${accentColor}50`,
          borderRadius: '32px',
          padding: '36px',
          boxShadow: `0 30px 60px -15px rgba(0,0,0,0.9), 0 0 40px ${accentColor}20`,
          display: 'flex',
          flexDirection: 'column',
          gap: '28px',
          transform: `scale(${cardSpring})`,
        }}
      >
        {/* 设备图标与工作状态 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                backgroundColor: `${accentColor}20`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '32px',
                border: `1.5px solid ${accentColor}60`,
              }}
            >
              {isSwitch ? '🔀' : '🌐'}
            </div>
            <div>
              <div style={{ fontSize: '26px', fontWeight: 800, color: '#f8fafc' }}>{deviceName}</div>
              <div style={{ fontSize: '15px', color: '#94a3b8' }}>{action}</div>
            </div>
          </div>

          <div
            style={{
              padding: '6px 16px',
              borderRadius: '10px',
              backgroundColor: isSwitch ? 'rgba(245, 158, 11, 0.2)' : 'rgba(168, 85, 247, 0.2)',
              color: accentColor,
              fontWeight: 800,
              fontSize: '15px',
            }}
          >
            {isSwitch ? '⚡ 硬件 ASIC 秒通' : '🧠 路由表转发引擎'}
          </div>
        </div>

        {/* 视窗动画主体 */}
        <div
          style={{
            backgroundColor: '#0c0e14',
            borderRadius: '20px',
            padding: '28px',
            border: '1px solid rgba(255,255,255,0.08)',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          {/* 模拟数据包扫描状态 */}
          {isSwitch ? (
            <>
              {/* 二层交换机：仅扫 MAC */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f59e0b', fontWeight: 800, fontSize: '17px' }}>
                  <span>🔍 正在扫描最外层以太网 MAC 地址...</span>
                  <span>7A:9C:12:34 ➔ B4:2E:99:88</span>
                </div>
                {/* 动态进度条 */}
                <div style={{ width: '100%', height: '8px', backgroundColor: '#1e2230', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${laserX}%`, height: '100%', backgroundColor: '#f59e0b', boxShadow: '0 0 10px #f59e0b' }} />
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '16px',
                  marginTop: '10px',
                }}
              >
                <div style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '14px', padding: '16px' }}>
                  <div style={{ color: '#f59e0b', fontWeight: 800, fontSize: '15px', marginBottom: '6px' }}>MAC 转发表匹配</div>
                  <div style={{ color: '#f1f5f9', fontSize: '16px' }}>{macMatch}</div>
                </div>
                <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '14px', padding: '16px' }}>
                  <div style={{ color: '#10b981', fontWeight: 800, fontSize: '15px', marginBottom: '6px' }}>报头隐私保护</div>
                  <div style={{ color: '#f1f5f9', fontSize: '16px' }}>{ipStatus}</div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* 三层路由器：拆包换壳 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ backgroundColor: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: '6px', fontSize: '13px', fontWeight: 800 }}>STEP 1</span>
                  <span style={{ color: '#fca5a5', fontSize: '17px', fontWeight: 700 }}>剥除旧以太网外壳: 剥离入站网卡 MAC 帧头</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ backgroundColor: '#a855f7', color: '#fff', padding: '2px 8px', borderRadius: '6px', fontSize: '13px', fontWeight: 800 }}>STEP 2</span>
                  <span style={{ color: '#e9d5ff', fontSize: '17px', fontWeight: 700 }}>{ipStatus}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ backgroundColor: '#10b981', color: '#fff', padding: '2px 8px', borderRadius: '6px', fontSize: '13px', fontWeight: 800 }}>STEP 3</span>
                  <span style={{ color: '#86efac', fontSize: '17px', fontWeight: 700 }}>封装新 MAC 地址并送入下一跳: {macMatch}</span>
                </div>
              </div>

              {/* 核心结论横幅 */}
              <div
                style={{
                  marginTop: '8px',
                  backgroundColor: 'rgba(168, 85, 247, 0.15)',
                  border: '1px solid rgba(168, 85, 247, 0.4)',
                  padding: '12px 18px',
                  borderRadius: '12px',
                  color: '#e9d5ff',
                  fontSize: '16px',
                  fontWeight: 700,
                  textAlign: 'center',
                }}
              >
                💡 核心法则：IP 全程保持不变指引终点，MAC 每跨过一个路由器就被撕掉换新！
              </div>
            </>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

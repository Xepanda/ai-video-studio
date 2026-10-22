import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
} from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';

export interface PacketAssemblyProps {
  stage?: 'payload' | 'tcp' | 'ip' | 'mac' | 'bits' | 'unpack';
  layerName?: string;
  payloadText?: string;
  payloadHex?: string;
  tcpHeader?: string;
  ipHeader?: string;
  macHeader?: string;
  crcTrailer?: string;
  bitstream?: string;
  headerBadge?: string;
  color?: string;
}

export const PacketAssemblyPipeline: React.FC<{
  packetAssembly?: PacketAssemblyProps;
  title?: string;
  category?: string;
}> = ({
  packetAssembly = {},
  title: sceneTitle,
  category: sceneCategory,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const stage = packetAssembly.stage || 'payload';
  const layerName = packetAssembly.layerName || 'L5 应用层';
  const payloadText = packetAssembly.payloadText || '在吗';
  const payloadHex = packetAssembly.payloadHex || 'e5 9c a8 e5 90 97';
  const tcpHeader = packetAssembly.tcpHeader || 'TCP: 52144 -> 443';
  const ipHeader = packetAssembly.ipHeader || '192.168.1.100 -> 120.232.145.88';
  const macHeader = packetAssembly.macHeader || 'MAC: 7A:9C -> B4:2E';
  const crcTrailer = packetAssembly.crcTrailer || 'CRC32 [OK]';
  const bitstream = packetAssembly.bitstream || '01101001 01101110 01100101 01110100';
  const badge = packetAssembly.headerBadge || '数据装配流水线';
  const themeColor = packetAssembly.color || '#38bdf8';

  // 装配滑块入场弹簧
  const assembleSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 150 },
  });

  // 扫描光束动效
  const scanX = (frame * 12) % 700;
  const pulse = Math.sin(frame / 6) * 0.15 + 0.85;

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
          backgroundColor: `${themeColor}20`,
          border: `1px solid ${themeColor}50`,
          color: themeColor,
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '20px',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: themeColor, boxShadow: `0 0 10px ${themeColor}` }} />
        {sceneCategory || 'PACKET ENCAPSULATION ASSEMBLY'}
      </div>

      {/* 分镜大标题 */}
      <div
        style={{
          fontSize: '44px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          marginBottom: '12px',
        }}
      >
        {sceneTitle || layerName}
      </div>

      <div
        style={{
          fontSize: '20px',
          color: '#94a3b8',
          fontWeight: 600,
          marginBottom: '40px',
        }}
      >
        {layerName} · 机械嵌套封装演示
      </div>

      {/* 机械套娃装配主展台 */}
      <div
        style={{
          width: '100%',
          maxWidth: '920px',
          backgroundColor: 'rgba(15, 18, 26, 0.9)',
          border: `2px solid ${themeColor}60`,
          borderRadius: '32px',
          padding: '40px 32px',
          boxShadow: `0 30px 60px -15px rgba(0,0,0,0.9), 0 0 40px ${themeColor}25`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
          position: 'relative',
        }}
      >
        {/* 顶部装配状态标识 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            width: '100%',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
            paddingBottom: '18px',
            fontSize: '17px',
            color: '#94a3b8',
            fontWeight: 700,
          }}
        >
          <span>📦 套娃层级: {stage.toUpperCase()}</span>
          <span style={{ color: themeColor }}>🏷️ {badge}</span>
        </div>

        {/* 套娃实体容器 */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '340px',
            position: 'relative',
          }}
        >
          {/* L2 最外层以太网 MAC 外壳 (MAC 与 CRC) */}
          {(stage === 'mac' || stage === 'bits') && (
            <div
              style={{
                width: '100%',
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                border: '2px solid #f59e0b',
                borderRadius: '24px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
                transform: `scale(${assembleSpring})`,
                boxShadow: '0 0 30px rgba(245, 158, 11, 0.25)',
              }}
            >
              {/* MAC 帧头条 */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: '#f59e0b',
                  color: '#000',
                  padding: '8px 16px',
                  borderRadius: '12px',
                  fontWeight: 900,
                  fontSize: '16px',
                }}
              >
                <span>[L2 Ethernet MAC Header]</span>
                <span>{macHeader}</span>
              </div>

              {/* L3 网络层 IP 外壳 */}
              <div
                style={{
                  backgroundColor: 'rgba(168, 85, 247, 0.15)',
                  border: '2px solid #a855f7',
                  borderRadius: '18px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: '#a855f7',
                    color: '#fff',
                    padding: '6px 14px',
                    borderRadius: '10px',
                    fontWeight: 800,
                    fontSize: '15px',
                  }}
                >
                  <span>[L3 IP Header]</span>
                  <span>{ipHeader}</span>
                </div>

                {/* L4 传输层 TCP 外壳 */}
                <div
                  style={{
                    backgroundColor: 'rgba(56, 189, 248, 0.18)',
                    border: '2px solid #38bdf8',
                    borderRadius: '14px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: '#38bdf8',
                      color: '#0f172a',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      fontWeight: 800,
                      fontSize: '14px',
                    }}
                  >
                    <span>[L4 TCP Header]</span>
                    <span>{tcpHeader}</span>
                  </div>

                  {/* L5 最核心原始 Payload */}
                  <div
                    style={{
                      backgroundColor: '#10b981',
                      color: '#ffffff',
                      padding: '20px 24px',
                      borderRadius: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      boxShadow: '0 10px 25px rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <span style={{ fontSize: '28px' }}>💬</span>
                      <div>
                        <div style={{ fontSize: '26px', fontWeight: 900 }}>"{payloadText}"</div>
                        <div style={{ fontSize: '14px', opacity: 0.85 }}>UTF-8 Payload: {payloadHex}</div>
                      </div>
                    </div>
                    <span style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '4px 10px', borderRadius: '6px', fontSize: '13px', fontWeight: 700 }}>
                      纯净载荷 6 Bytes
                    </span>
                  </div>
                </div>
              </div>

              {/* MAC 帧尾 FCS 校验 */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  backgroundColor: 'rgba(245, 158, 11, 0.25)',
                  color: '#fbbf24',
                  padding: '6px 16px',
                  borderRadius: '10px',
                  fontWeight: 800,
                  fontSize: '14px',
                }}
              >
                <span>[Frame Trailer: {crcTrailer}]</span>
              </div>
            </div>
          )}

          {/* L3 IP 阶段 */}
          {stage === 'ip' && (
            <div
              style={{
                width: '100%',
                backgroundColor: 'rgba(168, 85, 247, 0.15)',
                border: '2px solid #a855f7',
                borderRadius: '24px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
                transform: `scale(${assembleSpring})`,
                boxShadow: '0 0 35px rgba(168, 85, 247, 0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: '#a855f7',
                  color: '#fff',
                  padding: '10px 18px',
                  borderRadius: '12px',
                  fontWeight: 900,
                  fontSize: '17px',
                }}
              >
                <span>[L3 Network IP Header]</span>
                <span>{ipHeader}</span>
              </div>

              {/* 内部 TCP */}
              <div
                style={{
                  backgroundColor: 'rgba(56, 189, 248, 0.18)',
                  border: '2px solid #38bdf8',
                  borderRadius: '16px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: '#38bdf8', color: '#0f172a', padding: '6px 12px', borderRadius: '8px', fontWeight: 800, fontSize: '14px' }}>
                  <span>[L4 TCP]</span>
                  <span>{tcpHeader}</span>
                </div>

                <div style={{ backgroundColor: '#10b981', color: '#fff', padding: '18px 24px', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '26px', fontWeight: 900 }}>💬 "{payloadText}"</span>
                  <span style={{ fontSize: '14px', opacity: 0.85 }}>Hex: {payloadHex}</span>
                </div>
              </div>
            </div>
          )}

          {/* L4 TCP 阶段 */}
          {stage === 'tcp' && (
            <div
              style={{
                width: '100%',
                backgroundColor: 'rgba(56, 189, 248, 0.18)',
                border: '2px solid #38bdf8',
                borderRadius: '24px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                transform: `scale(${assembleSpring})`,
                boxShadow: '0 0 35px rgba(56, 189, 248, 0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: '#38bdf8',
                  color: '#0f172a',
                  padding: '10px 18px',
                  borderRadius: '12px',
                  fontWeight: 900,
                  fontSize: '17px',
                }}
              >
                <span>[L4 Transport TCP Header]</span>
                <span>{tcpHeader}</span>
              </div>

              <div style={{ backgroundColor: '#10b981', color: '#fff', padding: '22px 28px', borderRadius: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '28px', fontWeight: 900 }}>💬 "{payloadText}"</span>
                <span style={{ fontSize: '15px', opacity: 0.85 }}>Payload 载荷</span>
              </div>
            </div>
          )}

          {/* L5 单独 Payload 阶段 */}
          {stage === 'payload' && (
            <div
              style={{
                width: '100%',
                backgroundColor: '#10b981',
                borderRadius: '24px',
                padding: '36px',
                color: '#fff',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '16px',
                transform: `scale(${assembleSpring})`,
                boxShadow: `0 20px 50px rgba(16, 185, 129, ${0.4 * pulse})`,
              }}
            >
              <span style={{ fontSize: '48px' }}>💬</span>
              <div style={{ fontSize: '42px', fontWeight: 900, letterSpacing: '1px' }}>"{payloadText}"</div>
              <div style={{ fontSize: '18px', backgroundColor: 'rgba(0,0,0,0.25)', padding: '6px 18px', borderRadius: '10px', fontFamily: 'monospace' }}>
                十六进制: {payloadHex}
              </div>
            </div>
          )}

          {/* 比特发射阶段 */}
          {stage === 'bits' && (
            <div
              style={{
                marginTop: '24px',
                width: '100%',
                backgroundColor: '#051923',
                border: '1px solid #00f0ff',
                borderRadius: '16px',
                padding: '16px',
                color: '#00f0ff',
                fontFamily: 'monospace',
                fontSize: '20px',
                letterSpacing: '3px',
                textAlign: 'center',
                boxShadow: '0 0 25px rgba(0, 240, 255, 0.3)',
              }}
            >
              ⚡ PHY 光电比特流: {bitstream}
            </div>
          )}

          {/* 接收端解包阶段 */}
          {stage === 'unpack' && (
            <div
              style={{
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px',
                transform: `scale(${assembleSpring})`,
              }}
            >
              <div style={{ color: '#f59e0b', fontSize: '18px', fontWeight: 700 }}>1. 剥离并校验以太网 MAC 帧头 ➔ [OK]</div>
              <div style={{ color: '#a855f7', fontSize: '18px', fontWeight: 700 }}>2. 验证目标 IP 匹配本设备 ➔ [OK]</div>
              <div style={{ color: '#38bdf8', fontSize: '18px', fontWeight: 700 }}>3. TCP 确认 ACK 握手并重组字节流 ➔ [OK]</div>
              <div
                style={{
                  backgroundColor: '#10b981',
                  color: '#fff',
                  padding: '24px 36px',
                  borderRadius: '18px',
                  fontSize: '32px',
                  fontWeight: 900,
                  marginTop: '12px',
                  boxShadow: '0 15px 40px rgba(16, 185, 129, 0.4)',
                }}
              >
                💬 还原纯净数据: "{payloadText}"
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
} from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';

export interface WeChatMobileProps {
  mode?: 'send' | 'receive';
  senderName?: string;
  messageText?: string;
  sentTime?: string;
  avatarUrl?: string;
  latencyText?: string;
  title?: string;
  category?: string;
}

export const WeChatMobileMockup: React.FC<{ wechat?: WeChatMobileProps; title?: string; category?: string }> = ({
  wechat = {},
  title: sceneTitle,
  category: sceneCategory,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const mode = wechat.mode || 'send';
  const senderName = wechat.senderName || '好友';
  const messageText = wechat.messageText || '在吗';
  const sentTime = wechat.sentTime || '21:30';
  const latencyText = wechat.latencyText || '耗时: 80ms · 跨越 1200km';

  // 入场动画
  const phoneSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  // 微信气泡弹出弹簧
  const bubbleDelay = 15;
  const bubbleSpring = spring({
    frame: Math.max(0, frame - bubbleDelay),
    fps,
    config: { damping: 12, stiffness: 180 },
  });

  // 微距能量光晕 (后半段发光)
  const glowPulse = Math.sin(frame / 6) * 0.2 + 0.8;
  const zoomScale = interpolate(frame, [45, 120], [1.0, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
      {/* 顶部胶囊标签 */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 20px',
          borderRadius: '9999px',
          backgroundColor: 'rgba(7, 193, 96, 0.12)',
          border: '1px solid rgba(7, 193, 96, 0.35)',
          color: '#10b981',
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '24px',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981', boxShadow: '0 0 10px #10b981' }} />
        {sceneCategory || (mode === 'send' ? 'ORIGIN · WECHAT CLIENT' : 'DESTINATION · 0.08s REACHED')}
      </div>

      {/* 分镜大标题 (与组件族其他成员同一模式: sceneTitle 优先, 模式化文案兜底) */}
      <div
        style={{
          fontSize: '44px',
          fontWeight: 900,
          color: '#ffffff',
          textAlign: 'center',
          marginBottom: '28px',
          letterSpacing: '-0.5px',
        }}
      >
        {sceneTitle || (mode === 'send' ? '一条微信消息的星际航行' : '零点零八秒，消息抵达')}
      </div>

      {/* 手机外壳容器 */}
      <div
        style={{
          width: '760px',
          height: '1180px',
          borderRadius: '56px',
          backgroundColor: '#121317',
          border: '3px solid #2a2d38',
          boxShadow: '0 35px 80px -20px rgba(0, 0, 0, 0.9), 0 0 50px rgba(16, 185, 129, 0.15)',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          transform: `scale(${phoneSpring * zoomScale})`,
        }}
      >
        {/* 屏幕内框 */}
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: '44px',
            backgroundColor: '#191b22',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* 顶部灵动岛与状态栏 */}
          <div
            style={{
              height: '56px',
              padding: '0 32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#94a3b8',
              fontSize: '16px',
              fontWeight: 600,
            }}
          >
            <span>{sentTime}</span>
            {/* 灵动岛胶囊 */}
            <div
              style={{
                width: '130px',
                height: '28px',
                borderRadius: '14px',
                backgroundColor: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#0f172a' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#0284c7' }} />
            </div>
            <span>5G 📶 100%</span>
          </div>

          {/* 微信顶栏 */}
          <div
            style={{
              height: '68px',
              padding: '0 24px',
              borderBottom: '1px solid #262933',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#f8fafc',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '20px', fontWeight: 600 }}>
              <span style={{ color: '#94a3b8' }}>‹</span>
              <span>{senderName}</span>
            </div>
            <div style={{ fontSize: '22px', letterSpacing: '2px', color: '#94a3b8' }}>•••</div>
          </div>

          {/* 消息历史区域 */}
          <div
            style={{
              flex: 1,
              padding: '32px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: '24px',
            }}
          >
            {/* 时间戳 */}
            <div style={{ alignSelf: 'center', backgroundColor: 'rgba(255,255,255,0.06)', padding: '4px 16px', borderRadius: '8px', fontSize: '14px', color: '#64748b' }}>
              昨天 20:45
            </div>

            {/* 前序气泡 (左侧好友) */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                👨‍💻
              </div>
              <div
                style={{
                  maxWidth: '480px',
                  backgroundColor: '#262933',
                  color: '#f1f5f9',
                  padding: '16px 20px',
                  borderRadius: '16px',
                  borderTopLeftRadius: '4px',
                  fontSize: '22px',
                  lineHeight: '1.4',
                }}
              >
                明天有空一起讨论计算机网络架构吗？
              </div>
            </div>

            {/* 目标气泡 */}
            {mode === 'send' ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'flex-end',
                  gap: '14px',
                  transform: `scale(${bubbleSpring})`,
                  transformOrigin: 'right center',
                  opacity: bubbleSpring,
                }}
              >
                <div
                  style={{
                    backgroundColor: '#07c160',
                    color: '#ffffff',
                    padding: '16px 26px',
                    borderRadius: '18px',
                    borderTopRightRadius: '4px',
                    fontSize: '28px',
                    fontWeight: 700,
                    boxShadow: `0 8px 30px rgba(7, 193, 96, ${0.4 * glowPulse})`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                  }}
                >
                  <span>{messageText}</span>
                  <span style={{ fontSize: '16px', opacity: 0.8 }}>✓</span>
                </div>
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                  🚀
                </div>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '14px',
                  transform: `scale(${bubbleSpring})`,
                  transformOrigin: 'left center',
                  opacity: bubbleSpring,
                }}
              >
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                  👨‍💻
                </div>
                <div
                  style={{
                    backgroundColor: '#07c160',
                    color: '#ffffff',
                    padding: '16px 26px',
                    borderRadius: '18px',
                    borderTopLeftRadius: '4px',
                    fontSize: '28px',
                    fontWeight: 700,
                    boxShadow: `0 8px 30px rgba(7, 193, 96, ${0.4 * glowPulse})`,
                  }}
                >
                  {messageText}
                </div>
              </div>
            )}

            {/* 接收端时延指示器 */}
            {mode === 'receive' && frame > 30 && (
              <div
                style={{
                  alignSelf: 'center',
                  marginTop: '20px',
                  padding: '10px 24px',
                  borderRadius: '14px',
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#34d399',
                  fontSize: '18px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <span>⚡</span>
                <span>{latencyText}</span>
              </div>
            )}
          </div>

          {/* 底部打字输入栏 */}
          <div
            style={{
              height: '84px',
              padding: '0 20px',
              backgroundColor: '#1e212b',
              borderTop: '1px solid #2a2d38',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <div style={{ fontSize: '24px', color: '#94a3b8' }}>🎙️</div>
            <div
              style={{
                flex: 1,
                height: '48px',
                backgroundColor: '#13141a',
                borderRadius: '10px',
                border: '1px solid #334155',
                display: 'flex',
                alignItems: 'center',
                padding: '0 16px',
                color: '#64748b',
                fontSize: '18px',
              }}
            >
              {mode === 'send' && frame < 30 ? (
                <span style={{ color: '#38bdf8' }}>正在发送...</span>
              ) : (
                <span>发送消息...</span>
              )}
            </div>
            <div style={{ fontSize: '24px', color: '#94a3b8' }}>😀</div>
            <div style={{ fontSize: '24px', color: '#94a3b8' }}>⊕</div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, staticFile } from 'remotion';
import { ThemeConfig, getTheme } from '../../styles/theme';

export interface WebBrowserMockupSceneProps {
  url?: string;
  image: string;
  title?: string;
  subtitle?: string;
  badge?: string;
  pill?: string;
  highlights?: Array<{ label: string; value: string; color?: string }>;
  cameraMotion?: 'push-in' | 'pan-down' | 'float';
  theme?: ThemeConfig;
  style?: React.CSSProperties;
}

export const WebBrowserMockupScene: React.FC<WebBrowserMockupSceneProps> = ({
  url = 'https://github.com/eternity4719/HowToLiveBetter',
  image,
  title,
  subtitle,
  badge,
  pill,
  highlights = [],
  cameraMotion = 'push-in',
  theme: themeProp,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps, width = 1920, height = 1080 } = (() => {
    try {
      return useVideoConfig();
    } catch {
      return { fps: 30, width: 1920, height: 1080 };
    }
  })();
  const isVertical = width < height;
  const theme = themeProp || getTheme('editorial-paper-light');
  const isLight = theme.isLight ?? true;

  // 1. 入场弹簧动效
  const entrySpring = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 120 },
  });

  const entryScale = interpolate(entrySpring, [0, 1], [0.94, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const entryOpacity = interpolate(entrySpring, [0, 1], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 2. 持续微动微运镜 (Ken Burns 微推)
  let cameraProgress = 0;
  if (cameraMotion === 'push-in') {
    cameraProgress = interpolate(frame, [0, 300], [1.0, 1.04], {
      extrapolateRight: 'clamp',
    });
  } else if (cameraMotion === 'pan-down') {
    cameraProgress = interpolate(frame, [0, 300], [0, -30], {
      extrapolateRight: 'clamp',
    });
  }

  const resolvedImg = image
    ? (image.startsWith('http') || image.startsWith('/') || image.startsWith('data:')
        ? image
        : staticFile(image))
    : '';

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isVertical ? '40px 24px 220px 24px' : '40px 60px 100px 60px',
        boxSizing: 'border-box',
        overflow: 'hidden',
        background: isLight ? theme.background : '#090d16',
        color: isLight ? '#0f172a' : '#ffffff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        ...style,
      }}
    >
      {/* 顶部标题与标签区域 */}
      {(title || badge || pill) && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            marginBottom: isVertical ? 20 : 28,
            maxWidth: isVertical ? '95%' : 1200,
            opacity: entryOpacity,
          }}
        >
          {badge && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 14px',
                borderRadius: 20,
                backgroundColor: isLight ? 'rgba(79, 70, 229, 0.08)' : 'rgba(99, 102, 241, 0.15)',
                color: isLight ? '#4338ca' : '#a5b4fc',
                border: isLight ? '1px solid rgba(79, 70, 229, 0.20)' : '1px solid rgba(99, 102, 241, 0.30)',
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: '1px',
                marginBottom: 10,
              }}
            >
              <span>🌐</span>
              <span>{badge}</span>
            </div>
          )}

          {title && (
            <h2
              style={{
                fontSize: isVertical ? 36 : 44,
                fontWeight: 900,
                margin: 0,
                color: isLight ? '#0f172a' : '#ffffff',
                letterSpacing: '-0.02em',
                lineHeight: 1.25,
              }}
            >
              {title}
            </h2>
          )}

          {subtitle && (
            <p
              style={{
                fontSize: isVertical ? 18 : 22,
                color: isLight ? '#475569' : '#94a3b8',
                margin: '8px 0 0 0',
                fontWeight: 500,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* 真实高质感浏览器窗口外壳 (Mac Chrome 风格) */}
      <div
        style={{
          width: '100%',
          maxWidth: isVertical ? 960 : 1320,
          backgroundColor: isLight ? '#ffffff' : '#181824',
          borderRadius: 16,
          boxShadow: isLight
            ? '0 25px 60px -15px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.06)'
            : '0 30px 70px -15px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.1)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transform: `scale(${entryScale})`,
          opacity: entryOpacity,
          border: isLight ? '1px solid rgba(0,0,0,0.08)' : '1px solid rgba(255,255,255,0.12)',
          boxSizing: 'border-box',
        }}
      >
        {/* 浏览器顶部导航条 */}
        <div
          style={{
            height: 44,
            backgroundColor: isLight ? '#f1f5f9' : '#11121a',
            borderBottom: isLight ? '1px solid #e2e8f0' : '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 16px',
            gap: 14,
          }}
        >
          {/* Mac 红黄绿圆点 */}
          <div style={{ display: 'flex', gap: 7, alignItems: 'center' }}>
            <div style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#ff5f56' }} />
            <div style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#ffbd2e' }} />
            <div style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#27c93f' }} />
          </div>

          {/* 网址输入框 (带安全锁) */}
          <div
            style={{
              flex: 1,
              maxWidth: isVertical ? '80%' : 680,
              margin: '0 auto',
              height: 28,
              backgroundColor: isLight ? '#ffffff' : '#1e1f2b',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              padding: '0 12px',
              gap: 8,
              border: isLight ? '1px solid #cbd5e1' : '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: 13,
              color: isLight ? '#475569' : '#94a3b8',
              fontFamily: 'monospace',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{ color: '#10b981', fontSize: 11 }}>🔒</span>
            <span style={{ color: isLight ? '#0f172a' : '#f8fafc', fontWeight: 600 }}>{url}</span>
          </div>

          <div style={{ width: 44 }} />
        </div>

        {/* 网页截图内容视窗 (含轻微微推运镜) */}
        <div
          style={{
            width: '100%',
            height: isVertical ? 480 : 540,
            overflow: 'hidden',
            position: 'relative',
            backgroundColor: '#ffffff',
          }}
        >
          {resolvedImg ? (
            <img
              src={resolvedImg}
              alt={title || 'Screenshot'}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                objectPosition: 'top center',
                transform: cameraMotion === 'push-in'
                  ? `scale(${cameraProgress})`
                  : cameraMotion === 'pan-down'
                  ? `translateY(${cameraProgress}px)`
                  : 'none',
                transformOrigin: 'top center',
              }}
            />
          ) : (
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#94a3b8',
                fontSize: 18,
              }}
            >
              网页截图加载中...
            </div>
          )}
        </div>
      </div>

      {/* 底部悬浮重点数据胶囊 (Highlights) */}
      {highlights.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginTop: 22,
            flexWrap: 'wrap',
            justifyContent: 'center',
            opacity: entryOpacity,
          }}
        >
          {highlights.map((item, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: isLight ? '#ffffff' : 'rgba(30, 32, 48, 0.90)',
                border: isLight ? '1px solid rgba(0, 0, 0, 0.08)' : '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 12,
                padding: '10px 20px',
                boxShadow: isLight ? '0 4px 12px rgba(0,0,0,0.05)' : '0 8px 20px rgba(0,0,0,0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{ fontSize: 14, color: isLight ? '#64748b' : '#94a3b8', fontWeight: 600 }}>
                {item.label}
              </span>
              <span
                style={{
                  fontSize: 17,
                  fontWeight: 800,
                  color: item.color || (isLight ? '#4f46e5' : '#818cf8'),
                }}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

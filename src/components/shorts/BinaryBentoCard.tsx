import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export interface BentoSubCard {
  title: string;
  desc?: string;
  tag?: string;
  pill?: string; // 醒目胶囊标签，例如 "重置卡"、"限时免费"
  blocksTotal?: number; // 进度槽总格数（默认 5）
  blocksActive?: number; // 激活/点亮格数
  blocksDelay?: number; // 进度槽起始延迟帧数（可选）
  highlightWords?: string[];
  icon?: string;
  accentColor?: string;
}

export interface BinaryBentoCardProps {
  title?: string; // 顶部大标题，例如 "二选一规则" 或 "配额重置机制"
  subtitle?: string; // 副标题或说明
  leftCard: BentoSubCard;
  rightCard: BentoSubCard;
  dividerText?: string; // 中间分割圆圈文字，默认 "或" (也可以为 "VS" 等)
  theme?: 'dark' | 'light' | string;
  style?: React.CSSProperties;
  className?: string;
  animated?: boolean; // 是否启用 Remotion spring 动画，默认 true
}

export interface ProgressBlocksProps {
  total?: number; // 默认 5
  active?: number; // 激活格数，默认 3
  activeColor?: string; // 默认 '#6366f1' 或 '#8b5cf6'
  inactiveColor?: string; // 默认 'rgba(255, 255, 255, 0.12)'
  animated?: boolean; // 是否逐格点亮动画
  delay?: number; // 起始延迟帧数，默认 0
  style?: React.CSSProperties;
  className?: string;
}

/**
 * 安全获取 Remotion 上下文（若在非 Remotion 环境下如测试/SSR 中运行则优雅回退）
 */
function useSafeRemotion(): { frame: number; fps: number; isRemotion: boolean } {
  try {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    return { frame, fps, isRemotion: true };
  } catch {
    return { frame: 30, fps: 30, isRemotion: false };
  }
}

/**
 * 将文本中的重点高亮词用胶囊高亮呈现
 */
export function renderHighlightText(
  text: string,
  highlightWords?: string[],
  highlightColor = '#c084fc',
  highlightBg = 'rgba(139, 92, 246, 0.20)'
): React.ReactNode {
  if (!text) return null;
  if (!highlightWords || highlightWords.length === 0) {
    return text;
  }

  // 优先按长度降序排序，确保长短词汇重叠时最长词优先完整匹配
  const validWords = highlightWords
    .filter((w) => Boolean(w && w.trim()))
    .sort((a, b) => b.length - a.length);

  if (validWords.length === 0) return text;

  const escaped = validWords.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escaped.join('|')})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) => {
    const isMatch = validWords.some((hw) => hw.toLowerCase() === part.toLowerCase());
    if (isMatch) {
      return (
        <span
          key={index}
          style={{
            backgroundColor: highlightBg,
            color: highlightColor,
            padding: '2px 8px',
            borderRadius: '6px',
            fontWeight: 700,
            display: 'inline-block',
            margin: '0 2px',
            boxShadow: '0 0 12px rgba(139, 92, 246, 0.25)',
          }}
        >
          {part}
        </span>
      );
    }
    return part;
  });
}

/**
 * 动态点亮进度槽微组件 (ProgressBlocks)
 * 水平排列 5~7 个小方格胶囊，支持起始延迟与逐格点亮动效、电光发光阴影
 */
export const ProgressBlocks: React.FC<ProgressBlocksProps> = ({
  total = 5,
  active = 3,
  activeColor = '#6366f1',
  inactiveColor = 'rgba(255, 255, 255, 0.12)',
  animated = true,
  delay = 0,
  style,
  className,
}) => {
  const { frame, fps } = useSafeRemotion();

  const safeTotal = Math.max(1, total);
  const safeActive = Math.max(0, Math.min(safeTotal, active));

  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        ...style,
      }}
    >
      {Array.from({ length: safeTotal }).map((_, index) => {
        const isTargetActive = index < safeActive;

        // 若启用动画，每个激活小格子以 4 帧间隔逐格点亮，并支持整体 delay 延迟启动
        let isLit = isTargetActive;
        let scale = 1;
        let opacity = isTargetActive ? 1 : 0.45;

        if (animated) {
          const blockFrame = Math.max(0, frame - delay - index * 4);
          const blockProgress =
            frame - delay - index * 4 <= 0
              ? 0
              : spring({
                  frame: blockFrame,
                  fps,
                  config: { damping: 14, stiffness: 140 },
                });

          if (isTargetActive) {
            isLit = blockProgress >= 0.4;
            scale = interpolate(blockProgress, [0, 1], [0.85, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            opacity = interpolate(blockProgress, [0, 1], [0.25, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
          }
        }

        const bg = isLit ? activeColor : inactiveColor;
        const glow = isLit
          ? `0 0 10px ${activeColor}99, 0 0 4px ${activeColor}`
          : 'none';

        return (
          <div
            key={index}
            style={{
              width: 24,
              height: 12,
              borderRadius: 4,
              backgroundColor: bg,
              boxShadow: glow,
              opacity,
              transform: `scale(${scale})`,
              transformOrigin: 'center center',
              transition: animated ? 'none' : 'all 0.2s ease',
              flexShrink: 0,
            }}
          />
        );
      })}
    </div>
  );
};

/**
 * 内部单个 Bento 子卡片视图组件
 */
interface SubCardItemProps {
  card: BentoSubCard;
  isLight: boolean;
  animated: boolean;
  defaultBlockDelay?: number;
  style?: React.CSSProperties;
}

const SubCardItem: React.FC<SubCardItemProps> = ({
  card,
  isLight,
  animated,
  defaultBlockDelay = 10,
  style,
}) => {
  const cardAccent = card.accentColor || (isLight ? '#7c3aed' : '#8b5cf6');
  const cardBg = isLight
    ? 'rgba(255, 255, 255, 0.90)'
    : 'rgba(18, 18, 24, 0.85)';
  const cardBorder = isLight
    ? '1px solid rgba(0, 0, 0, 0.08)'
    : '1px solid rgba(255, 255, 255, 0.12)';
  const primaryTextColor = isLight ? '#0f172a' : '#ffffff';
  const descTextColor = isLight ? '#475569' : '#cbd5e1';

  const hasBlocks = card.blocksActive !== undefined || card.blocksTotal !== undefined;

  return (
    <div
      style={{
        flex: '1 1 0',
        minWidth: 0,
        backgroundColor: cardBg,
        border: cardBorder,
        borderRadius: 24,
        padding: '32px',
        boxShadow: isLight
          ? '0 20px 40px -15px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
          : '0 25px 50px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.16)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: 20,
        boxSizing: 'border-box',
        position: 'relative',
        ...style,
      }}
    >
      {/* 顶部标签行：左侧 tag / icon，右侧 pill 胶囊 */}
      {(card.tag || card.icon || card.pill) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            width: '100%',
          }}
        >
          {/* 左侧 Tag / Icon */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {card.icon && (
              <span
                style={{
                  fontSize: 22,
                  lineHeight: 1,
                  display: 'inline-flex',
                  alignItems: 'center',
                }}
              >
                {card.icon}
              </span>
            )}
            {card.tag && (
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: isLight ? '#64748b' : '#94a3b8',
                  backgroundColor: isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.08)',
                  padding: '4px 10px',
                  borderRadius: 6,
                  lineHeight: 1.2,
                }}
              >
                {card.tag}
              </span>
            )}
          </div>

          {/* 右侧醒目胶囊标签 (pill) */}
          {card.pill && (
            <div
              style={{
                background: 'linear-gradient(135deg, #8b5cf6, #a855f7)',
                color: '#ffffff',
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: '0.02em',
                padding: '4px 14px',
                borderRadius: 9999,
                boxShadow: '0 0 16px rgba(168, 85, 247, 0.45)',
                display: 'inline-flex',
                alignItems: 'center',
                whiteSpace: 'nowrap',
                lineHeight: 1.2,
              }}
            >
              {card.pill}
            </div>
          )}
        </div>
      )}

      {/* 核心内容区：标题与描述 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div
          style={{
            fontSize: 32,
            fontWeight: 800,
            color: primaryTextColor,
            letterSpacing: '-0.02em',
            lineHeight: 1.25,
            wordBreak: 'break-word',
          }}
        >
          {renderHighlightText(
            card.title,
            card.highlightWords,
            cardAccent,
            isLight ? 'rgba(124, 58, 237, 0.12)' : 'rgba(139, 92, 246, 0.20)'
          )}
        </div>

        {card.desc && (
          <div
            style={{
              fontSize: 22,
              color: descTextColor,
              lineHeight: 1.5,
              letterSpacing: '-0.01em',
              wordBreak: 'break-word',
              whiteSpace: 'pre-wrap',
            }}
          >
            {renderHighlightText(
              card.desc,
              card.highlightWords,
              cardAccent,
              isLight ? 'rgba(124, 58, 237, 0.12)' : 'rgba(139, 92, 246, 0.20)'
            )}
          </div>
        )}
      </div>

      {/* 底部进度槽区 */}
      {hasBlocks && (
        <div
          style={{
            marginTop: 'auto',
            paddingTop: 12,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <ProgressBlocks
            total={card.blocksTotal ?? 5}
            active={card.blocksActive ?? 3}
            activeColor={cardAccent}
            inactiveColor={isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.12)'}
            animated={animated}
            delay={card.blocksDelay ?? defaultBlockDelay}
          />
        </div>
      )}
    </div>
  );
};

/**
 * 极简科技短视频二选一对比 Bento 卡片组件 (BinaryBentoCard)
 * 适配 1080×1920 竖屏规格，具备像素级高质感黑白高对比、动态弹簧冲击波与进度槽点亮动效
 */
export const BinaryBentoCard: React.FC<BinaryBentoCardProps> = ({
  title,
  subtitle,
  leftCard,
  rightCard,
  dividerText = '或',
  theme = 'dark',
  style,
  className,
  animated = true,
}) => {
  const { frame, fps } = useSafeRemotion();

  const isLight =
    theme === 'light' ||
    (typeof theme === 'string' &&
      (theme.includes('#fff') || theme.includes('rgb(255')));

  // Remotion Spring 动效编排
  const headerSpring = animated
    ? spring({
        frame,
        fps,
        config: { damping: 14, stiffness: 120 },
      })
    : 1;

  const leftSpring = animated
    ? spring({
        frame: frame - 4,
        fps,
        config: { damping: 14, stiffness: 120 },
      })
    : 1;

  const rightSpring = animated
    ? spring({
        frame: frame - 10,
        fps,
        config: { damping: 14, stiffness: 120 },
      })
    : 1;

  const dividerSpring = animated
    ? spring({
        frame: frame - 14,
        fps,
        config: { damping: 12, stiffness: 160 },
      })
    : 1;

  // 变换插值（所有 opacity 与 scale 均严格配置 clamp 截断，防止弹簧超调过冲产生负透明度）
  const headerOpacity = animated
    ? interpolate(headerSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  const headerTranslateY = animated ? interpolate(headerSpring, [0, 1], [-16, 0]) : 0;

  const leftScale = animated ? interpolate(leftSpring, [0, 1], [0.92, 1.0]) : 1;
  const leftTranslateY = animated ? interpolate(leftSpring, [0, 1], [20, 0]) : 0;
  const leftOpacity = animated
    ? interpolate(leftSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  const rightScale = animated ? interpolate(rightSpring, [0, 1], [0.92, 1.0]) : 1;
  const rightTranslateY = animated ? interpolate(rightSpring, [0, 1], [20, 0]) : 0;
  const rightOpacity = animated
    ? interpolate(rightSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  const badgeScale = animated
    ? interpolate(dividerSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  const rippleScale = animated
    ? interpolate(dividerSpring, [0, 1], [0.8, 1.45], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  const rippleOpacity = animated
    ? interpolate(dividerSpring, [0, 0.4, 1], [0, 0.7, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  return (
    <div
      className={className}
      style={{
        width: '100%',
        maxWidth: 960,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 28,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        boxSizing: 'border-box',
        ...style,
      }}
    >
      {/* 1. 顶部大标题与副标题区域 */}
      {(title || subtitle) && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 10,
            width: '100%',
            opacity: headerOpacity,
            transform: `translateY(${headerTranslateY}px)`,
          }}
        >
          {title && (
            <h2
              style={{
                fontSize: 46,
                fontWeight: 800,
                color: isLight ? '#0f172a' : '#ffffff',
                letterSpacing: '-0.03em',
                margin: 0,
                lineHeight: 1.2,
              }}
            >
              {title}
            </h2>
          )}
          {subtitle && (
            <p
              style={{
                fontSize: 24,
                color: isLight ? '#64748b' : '#94a3b8',
                margin: 0,
                lineHeight: 1.4,
                maxWidth: 820,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* 2. 双卡横向排列与中央连接圆圈徽章 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          width: '100%',
          gap: 24,
          position: 'relative',
          alignItems: 'stretch',
          justifyContent: 'center',
        }}
      >
        {/* 左卡 */}
        <SubCardItem
          card={leftCard}
          isLight={isLight}
          animated={animated}
          defaultBlockDelay={10}
          style={{
            opacity: leftOpacity,
            transform: `scale(${leftScale}) translateY(${leftTranslateY}px)`,
            transformOrigin: 'center center',
          }}
        />

        {/* 右卡 */}
        <SubCardItem
          card={rightCard}
          isLight={isLight}
          animated={animated}
          defaultBlockDelay={14}
          style={{
            opacity: rightOpacity,
            transform: `scale(${rightScale}) translateY(${rightTranslateY}px)`,
            transformOrigin: 'center center',
          }}
        />

        {/* 中间浮动圆圈徽章 ("或" / "VS") */}
        {dividerText && (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: `translate(-50%, -50%) scale(${badgeScale})`,
              zIndex: 10,
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* 弹簧冲击波外扩散光环 */}
            {animated && (
              <div
                style={{
                  position: 'absolute',
                  inset: -6,
                  borderRadius: '50%',
                  border: '2px solid rgba(139, 92, 246, 0.65)',
                  transform: `scale(${rippleScale})`,
                  opacity: rippleOpacity,
                }}
              />
            )}

            {/* 徽章主体 */}
            <div
              style={{
                width: 48,
                height: 48,
                minWidth: 48,
                minHeight: 48,
                borderRadius: '50%',
                backgroundColor: isLight ? '#ffffff' : '#0f0f14',
                border: isLight
                  ? '1px solid rgba(0, 0, 0, 0.15)'
                  : '1px solid rgba(255, 255, 255, 0.25)',
                boxShadow: isLight
                  ? '0 6px 16px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
                  : '0 0 24px rgba(0, 0, 0, 0.9), 0 0 12px rgba(139, 92, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isLight ? '#0f172a' : '#ffffff',
                fontSize: 20,
                fontWeight: 800,
                letterSpacing: '-0.02em',
                userSelect: 'none',
              }}
            >
              {dividerText}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

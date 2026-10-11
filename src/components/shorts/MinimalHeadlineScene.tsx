import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export interface MinimalHeadlineSceneProps {
  title: string;
  subtitle?: string;
  category?: string; // 顶部小胶囊，例如 "CODEX DAY 6", "BREAKING"
  tag?: string; // 次级标签
  highlightWords?: string[]; // 需要高亮呈现的关键词列表
  inverted?: boolean; // 是否反转色彩：true 为白底黑字（视觉爆破冲击），false 为深黑底白字（默认）
  dateText?: string; // 日期或时间戳，例如 "2026.10.11"
  accentColor?: string; // 强调色，默认 '#8b5cf6' (紫色)
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
 * 渲染大字报文本，并为 highlightWords 关键词自动包裹高对比度胶囊高亮
 * 关键词优先按字符长度降序排序匹配，防止短词前缀吞噬长词
 */
export function renderHeadlineText(
  text: string,
  highlightWords?: string[],
  inverted = false,
  accentColor = '#8b5cf6',
  isSubtitle = false
): React.ReactNode {
  if (!text) return null;
  if (!highlightWords || highlightWords.length === 0) {
    return text;
  }

  // 1. 过滤空字符，并严格按长度降序排序（避免短词前缀吞噬长词）
  const validWords = highlightWords
    .filter((w) => Boolean(w && w.trim()))
    .sort((a, b) => b.length - a.length);

  if (validWords.length === 0) return text;

  // 2. 正则安全转义并创建分割正则表达式
  const escaped = validWords.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escaped.join('|')})`, 'gi');
  const parts = text.split(regex);

  // 3. 配色策略：常规模式为深黑底 + 浅紫霓虹发光胶囊；反转模式为纯白底 + 深紫高反差胶囊
  const capsuleBg = inverted
    ? 'rgba(139, 92, 246, 0.25)'
    : 'rgba(139, 92, 246, 0.22)';
  const capsuleColor = inverted
    ? '#6d28d9' // 白底下深紫清晰锐利
    : '#c084fc'; // 黑底下浅亮紫色霓虹发光
  const capsuleBorder = inverted
    ? '1.5px solid rgba(139, 92, 246, 0.40)'
    : '1px solid rgba(139, 92, 246, 0.45)';
  const capsuleShadow = inverted
    ? '0 2px 8px rgba(109, 40, 217, 0.15)'
    : '0 0 20px rgba(139, 92, 246, 0.35)';

  return parts.map((part, index) => {
    const isMatch = validWords.some((hw) => hw.toLowerCase() === part.toLowerCase());
    if (isMatch) {
      return (
        <span
          key={index}
          style={{
            backgroundColor: capsuleBg,
            color: capsuleColor,
            border: capsuleBorder,
            boxShadow: capsuleShadow,
            padding: isSubtitle ? '2px 8px' : '4px 14px',
            borderRadius: isSubtitle ? '8px' : '12px',
            fontWeight: isSubtitle ? 700 : 900,
            display: 'inline-block',
            margin: '0 4px',
            verticalAlign: 'baseline',
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
 * 极简大字报场景组件 (MinimalHeadlineScene)
 * 专为 1080×1920 竖屏短视频打造的高反差核心观点与视觉冲击开场
 */
export const MinimalHeadlineScene: React.FC<MinimalHeadlineSceneProps> = ({
  title,
  subtitle,
  category,
  tag,
  highlightWords,
  inverted = false,
  dateText,
  accentColor = '#8b5cf6',
  style,
  className,
}) => {
  const { frame, fps, isRemotion } = useSafeRemotion();

  // Remotion spring 入场缩放 (0.94 -> 1.0) 与淡入动效
  const entranceSpring = isRemotion
    ? spring({
        frame,
        fps,
        config: { damping: 16, stiffness: 120 },
      })
    : 1;

  const scale = isRemotion
    ? interpolate(entranceSpring, [0, 1], [0.94, 1.0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  const opacity = isRemotion
    ? interpolate(entranceSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  // 顶部胶囊从上方微移淡入
  const categorySpring = isRemotion
    ? spring({
        frame,
        fps,
        config: { damping: 18, stiffness: 140 },
      })
    : 1;

  const categoryTranslateY = isRemotion
    ? interpolate(categorySpring, [0, 1], [-18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  const categoryOpacity = isRemotion
    ? interpolate(categorySpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  // 副标题微延迟 4 帧上浮淡入
  const subtitleSpring = isRemotion
    ? spring({
        frame: Math.max(0, frame - 4),
        fps,
        config: { damping: 18, stiffness: 120 },
      })
    : 1;

  const subtitleTranslateY = isRemotion
    ? interpolate(subtitleSpring, [0, 1], [18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  const subtitleOpacity = isRemotion
    ? interpolate(subtitleSpring, [0, 1], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  return (
    <div
      className={className}
      style={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: style?.backgroundColor ?? (inverted ? '#ffffff' : '#000000'),
        color: inverted ? '#09090b' : '#ffffff',
        boxSizing: 'border-box',
        transform: `scale(${scale})`,
        opacity,
        textAlign: 'center',
        ...style,
      }}
    >
      {/* 1. 顶部 Category / Tag / Date 胶囊药丸区 */}
      {(category || tag || dateText) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: 12,
            marginBottom: 36,
            transform: `translateY(${categoryTranslateY}px)`,
            opacity: categoryOpacity,
          }}
        >
          {category && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '8px 24px',
                borderRadius: '9999px',
                fontSize: '22px',
                fontWeight: 700,
                letterSpacing: '2px',
                textTransform: 'uppercase',
                background: inverted
                  ? 'rgba(0, 0, 0, 0.04)'
                  : 'linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.25))',
                color: inverted ? '#09090b' : '#c4b5fd',
                border: inverted
                  ? '2px solid #09090b'
                  : '1.5px solid rgba(139, 92, 246, 0.45)',
                boxShadow: inverted
                  ? 'none'
                  : '0 0 20px rgba(139, 92, 246, 0.25)',
              }}
            >
              {category}
            </div>
          )}

          {tag && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '6px 18px',
                borderRadius: '9999px',
                fontSize: '18px',
                fontWeight: 600,
                letterSpacing: '1px',
                background: inverted ? 'rgba(0, 0, 0, 0.04)' : 'rgba(255, 255, 255, 0.08)',
                color: inverted ? '#52525b' : '#a1a1aa',
                border: inverted ? '1px solid rgba(0, 0, 0, 0.12)' : '1px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              {tag}
            </div>
          )}

          {dateText && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                fontSize: '18px',
                fontWeight: 600,
                letterSpacing: '1px',
                color: inverted ? '#71717a' : '#71717a',
                fontFamily: 'monospace, sans-serif',
              }}
            >
              {dateText}
            </div>
          )}
        </div>
      )}

      {/* 2. 居中极简大字报主标题 (64px ~ 76px 强张力排版) */}
      <h1
        style={{
          fontSize: '72px',
          fontWeight: 900,
          lineHeight: 1.35,
          textAlign: 'center',
          margin: 0,
          padding: '0 20px',
          maxWidth: '1000px',
          color: inverted ? '#09090b' : '#ffffff',
          letterSpacing: '-0.5px',
          whiteSpace: 'pre-line',
          wordBreak: 'break-word',
          textShadow: inverted ? 'none' : '0 4px 24px rgba(0, 0, 0, 0.8)',
        }}
      >
        {renderHeadlineText(title, highlightWords, inverted, accentColor, false)}
      </h1>

      {/* 3. 次级辅助解说或副标题 (若提供) */}
      {subtitle && (
        <p
          style={{
            fontSize: '30px',
            fontWeight: 500,
            lineHeight: 1.5,
            textAlign: 'center',
            marginTop: '28px',
            marginBottom: 0,
            padding: '0 30px',
            maxWidth: '920px',
            color: inverted ? '#4b5563' : '#a1a1aa',
            whiteSpace: 'pre-line',
            wordBreak: 'break-word',
            transform: `translateY(${subtitleTranslateY}px)`,
            opacity: subtitleOpacity,
          }}
        >
          {renderHeadlineText(subtitle, highlightWords, inverted, accentColor, true)}
        </p>
      )}
    </div>
  );
};

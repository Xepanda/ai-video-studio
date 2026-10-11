import React from 'react';
import { Img, staticFile } from 'remotion';
import { MessageCircle, Repeat2, Heart, BarChart2, Bookmark, Share } from 'lucide-react';
import { ThemeConfig } from '../../styles/theme';

export interface TweetMetrics {
  replies?: string | number;
  retweets?: string | number;
  likes?: string | number;
  views?: string | number;
}

export interface TweetEmbedCardProps {
  authorName: string;            // 如 "Tibo"
  authorHandle: string;          // 如 "@thdxllaux"
  avatarUrl?: string;            // 可选头像 URL 或本地路径，缺失时采用精致首字母渐变圆形兜底
  isVerified?: boolean;          // 是否显示官方蓝V图标（默认 true）
  timeAgo?: string;              // 如 "30m" 或 "14h"
  content: string;               // 推文正文，如 "Day 6: Reset"
  highlightWords?: string[];     // 正文中需要紫色胶囊包裹高亮的词汇
  subtitle?: string;             // 中文翻译或解读小字（可选）
  metrics?: TweetMetrics;        // 底部互动量：转推、点赞、浏览量
  theme?: ThemeConfig | Partial<ThemeConfig> | string;  // 当前主题配色
  maxWidth?: number;             // 最大宽度，默认 880px
  className?: string;
  style?: React.CSSProperties;
}

/**
 * 格式化推特互动量数值 (例如 3400 -> 3.4K, 1500000 -> 1.5M)
 */
export function formatMetric(val?: string | number): string {
  if (val === undefined || val === null || val === '') return '';
  if (typeof val === 'string') return val;
  if (val >= 1_000_000) {
    const formatted = (val / 1_000_000).toFixed(1);
    return formatted.endsWith('.0') ? formatted.slice(0, -2) + 'M' : formatted + 'M';
  }
  if (val >= 1_000) {
    const formatted = (val / 1_000).toFixed(1);
    return formatted.endsWith('.0') ? formatted.slice(0, -2) + 'K' : formatted + 'K';
  }
  return val.toString();
}

/**
 * 官方 Twitter / X 蓝 V 认证徽章 SVG
 */
const TwitterVerifiedBadge: React.FC<{ size?: number }> = ({ size = 22 }) => (
  <svg
    viewBox="0 0 24 24"
    aria-label="Verified account"
    style={{
      width: size,
      height: size,
      minWidth: size,
      minHeight: size,
      color: '#1d9bf0',
      display: 'inline-block',
      verticalAlign: 'middle',
    }}
  >
    <g fill="currentColor">
      <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z" />
    </g>
  </svg>
);

/**
 * 官方 X (Twitter) 极简图标
 */
const XLogo: React.FC<{ size?: number; color?: string }> = ({ size = 22, color = '#71767b' }) => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    style={{
      width: size,
      height: size,
      fill: color,
      display: 'inline-block',
    }}
  >
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
);

/**
 * 将文本中的重点高亮词用浅紫色胶囊包裹高亮呈现
 */
function renderContentWithHighlights(
  text: string,
  highlightWords?: string[],
  highlightColor = '#c084fc',
  highlightBg = 'rgba(139, 92, 246, 0.18)'
) {
  if (!highlightWords || highlightWords.length === 0) {
    return text;
  }

  const validWords = highlightWords.filter((w) => Boolean(w && w.trim()));
  if (validWords.length === 0) return text;
  validWords.sort((a, b) => b.length - a.length);

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
            padding: '2px 10px',
            borderRadius: '8px',
            fontWeight: 700,
            display: 'inline-block',
            margin: '0 2px',
            boxShadow: '0 0 16px rgba(139, 92, 246, 0.25)',
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
 * 极简科技资讯社交媒体推文拟态组件 (TweetEmbedCard)
 */
export const TweetEmbedCard: React.FC<TweetEmbedCardProps> = ({
  authorName,
  authorHandle,
  avatarUrl,
  isVerified = true,
  timeAgo,
  content,
  highlightWords,
  subtitle,
  metrics,
  theme,
  maxWidth = 880,
  className,
  style,
}) => {
  // 判断当前主题是浅色还是深色
  const themeObj: Partial<ThemeConfig> | undefined =
    theme && typeof theme === 'object' ? theme : undefined;

  const isLight =
    themeObj &&
    typeof themeObj.cardBg === 'string' &&
    (themeObj.cardBg.includes('#fff') || themeObj.cardBg.includes('rgb(255'));

  const cardBg = isLight ? '#ffffff' : (themeObj?.cardBg || '#000000');
  const cardBorder = isLight
    ? (themeObj?.cardBorder || '1px solid #e5e7eb')
    : (themeObj?.cardBorder || '1px solid rgba(255, 255, 255, 0.12)');
  const primaryTextColor = isLight ? '#0f1419' : '#ffffff';
  const secondaryTextColor = isLight ? '#536471' : '#71767b';
  const accentColor = themeObj?.accentColor || '#a855f7';
  const highlightColor = isLight ? '#7c3aed' : (themeObj?.subtitleHighlightColor || '#c084fc');
  const highlightBg = isLight ? 'rgba(124, 58, 237, 0.12)' : 'rgba(139, 92, 246, 0.20)';

  const resolvedAvatar = avatarUrl
    ? avatarUrl.startsWith('http://') ||
      avatarUrl.startsWith('https://') ||
      avatarUrl.startsWith('/') ||
      avatarUrl.startsWith('data:') ||
      avatarUrl.startsWith('blob:')
      ? avatarUrl
      : staticFile(avatarUrl)
    : undefined;

  const authorInitial = (authorName ? authorName.trim().charAt(0) : 'U').toUpperCase();

  // 格式化推特各互动量指标
  const replyText = formatMetric(metrics?.replies);
  const retweetText = formatMetric(metrics?.retweets);
  const likeText = formatMetric(metrics?.likes);
  const viewText = formatMetric(metrics?.views);

  return (
    <div
      className={className}
      style={{
        width: '100%',
        maxWidth,
        backgroundColor: cardBg,
        border: cardBorder,
        borderRadius: 24,
        padding: '32px 36px',
        boxShadow: isLight
          ? '0 20px 40px -15px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04)'
          : '0 25px 50px -12px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.08)',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: 22,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        position: 'relative',
        ...style,
      }}
    >
      {/* 1. 顶部用户身份与认证栏 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* 头像区域：图片或精致渐变首字母兜底 */}
          <div
            style={{
              width: 56,
              height: 56,
              minWidth: 56,
              minHeight: 56,
              borderRadius: '50%',
              overflow: 'hidden',
              backgroundColor: isLight ? '#f3f4f6' : '#1e293b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            }}
          >
            {resolvedAvatar ? (
              <Img
                src={resolvedAvatar}
                alt={authorName}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff',
                  fontSize: 26,
                  fontWeight: 700,
                  userSelect: 'none',
                }}
              >
                {authorInitial}
              </div>
            )}
          </div>

          {/* 昵称、蓝V认证与发布时间 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 700,
                  color: primaryTextColor,
                  letterSpacing: '-0.02em',
                  lineHeight: 1.2,
                }}
              >
                {authorName}
              </span>
              {isVerified && <TwitterVerifiedBadge size={22} />}
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 20,
                color: secondaryTextColor,
                lineHeight: 1.2,
              }}
            >
              <span>{authorHandle}</span>
              {timeAgo && (
                <>
                  <span style={{ opacity: 0.7 }}>·</span>
                  <span>{timeAgo}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* 顶部右侧官方 X (Twitter) Logo */}
        <div style={{ opacity: 0.85, paddingRight: 4 }}>
          <XLogo size={24} color={secondaryTextColor} />
        </div>
      </div>

      {/* 2. 推文正文排版区域 */}
      <div
        style={{
          fontSize: 34,
          lineHeight: 1.44,
          fontWeight: 400,
          color: primaryTextColor,
          letterSpacing: '-0.015em',
          wordBreak: 'break-word',
          whiteSpace: 'pre-wrap',
        }}
      >
        {renderContentWithHighlights(content, highlightWords, highlightColor, highlightBg)}
      </div>

      {/* 3. 中文解读/翻译小字 (可选) */}
      {subtitle && (
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 14,
            backgroundColor: isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.04)',
            borderLeft: `4px solid ${accentColor}`,
            fontSize: 24,
            lineHeight: 1.5,
            color: isLight ? '#475569' : '#cbd5e1',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            boxSizing: 'border-box',
          }}
        >
          <span style={{ fontSize: 22, lineHeight: 1 }}>💡</span>
          <span style={{ flex: 1 }}>{subtitle}</span>
        </div>
      )}

      {/* 4. 底部互动数据栏 (极简灰度图标与计数) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 16,
          borderTop: isLight ? '1px solid #f3f4f6' : '1px solid rgba(255, 255, 255, 0.08)',
          color: secondaryTextColor,
          fontSize: 20,
        }}
      >
        {/* 回复 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MessageCircle size={22} strokeWidth={1.8} />
          {replyText && <span>{replyText}</span>}
        </div>

        {/* 转推 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Repeat2 size={22} strokeWidth={1.8} />
          {retweetText && <span>{retweetText}</span>}
        </div>

        {/* 点赞 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Heart size={22} strokeWidth={1.8} />
          {likeText && <span>{likeText}</span>}
        </div>

        {/* 浏览量 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BarChart2 size={22} strokeWidth={1.8} />
          {viewText && <span>{viewText}</span>}
        </div>

        {/* 书签与分享 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <Bookmark size={20} strokeWidth={1.8} style={{ opacity: 0.8 }} />
          <Share size={20} strokeWidth={1.8} style={{ opacity: 0.8 }} />
        </div>
      </div>
    </div>
  );
};

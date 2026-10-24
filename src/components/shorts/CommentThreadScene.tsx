import React from 'react';
import { spring, interpolate } from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

/**
 * 热点快剪: 评论串场景 (W7-8 场景三)
 * 数据驱动的评论区 mockup: 头像 + 作者 + 正文 + 点赞数, 逐条弹簧入场。
 * 点赞数缺失时为 null (数据诚信: 严禁 0 填充伪装)。
 */

export interface CommentItem {
  author: string;
  content: string;
  likes?: number | null;
  timeAgo?: string;
  /** UP 主标记 (置顶高亮) */
  isAuthor?: boolean;
  /** 头像文字 (默认取作者首字符) */
  avatarText?: string;
}

export interface CommentThreadProps {
  comments?: CommentItem[];
  title?: string;
  category?: string;
}

const COMMENT_STAGGER = 14; // 帧: 每条评论入场间隔

export const CommentThreadScene: React.FC<CommentThreadProps & { theme?: ThemeConfig }> = ({
  comments = [],
  title,
  category,
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();
  const headerOpacity = Math.min(1, frame / (fps * 0.4));

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: '4% 7%',
        backgroundColor: '#0b1220',
        backgroundImage: 'radial-gradient(ellipse at 80% 10%, rgba(244,114,182,0.08), transparent 55%)',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}
    >
      {category ? (
        <div style={{ color: '#f9a8d4', fontSize: 19, fontWeight: 700, letterSpacing: '0.16em', opacity: headerOpacity }}>
          {category}
        </div>
      ) : null}
      {title ? (
        <div style={{ color: '#f8fafc', fontSize: 34, fontWeight: 800, margin: '8px 0 22px', opacity: headerOpacity }}>
          {title}
        </div>
      ) : null}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, justifyContent: 'center' }}>
        {comments.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 22 }}>未提供 comments 数据 (分镜嵌套配置缺失)</div>
        ) : (
          comments.map((c, idx) => {
            const appear = spring({
              frame: frame - idx * COMMENT_STAGGER,
              fps,
              config: { damping: 20, stiffness: 120 },
            });
            return (
              <div
                key={`${c.author}-${idx}`}
                style={{
                  display: 'flex',
                  gap: 14,
                  padding: '16px 20px',
                  borderRadius: 14,
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  border: c.isAuthor ? '1px solid rgba(56,189,248,0.5)' : '1px solid rgba(30,41,59,0.9)',
                  // 始终渲染 DOM (opacity 0 不可见), 保障 SSR 可观测契约
                  opacity: appear,
                  transform: `translateY(${interpolate(appear, [0, 1], [16, 0])}px)`,
                }}
              >
                {/* 头像 */}
                <div style={{
                  width: 46, height: 46, borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: 'linear-gradient(135deg, #38bdf8, #a855f7)',
                  color: '#fff', fontSize: 20, fontWeight: 800,
                }}>
                  {c.avatarText || (c.author || '?').slice(0, 1)}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ color: '#94a3b8', fontSize: 17, fontWeight: 700 }}>{c.author}</span>
                    {c.isAuthor ? (
                      <span style={{
                        fontSize: 12, fontWeight: 700, color: '#38bdf8',
                        border: '1px solid rgba(56,189,248,0.6)', borderRadius: 4, padding: '1px 6px',
                      }}>
                        UP主
                      </span>
                    ) : null}
                    {c.timeAgo ? (
                      <span style={{ color: '#475569', fontSize: 14 }}>{c.timeAgo}</span>
                    ) : null}
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: 21, lineHeight: 1.5 }}>{c.content}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, color: '#64748b', fontSize: 15 }}>
                    <span style={{ color: '#f472b6' }}>♥</span>
                    {typeof c.likes === 'number' ? c.likes.toLocaleString('zh-CN') : '赞数缺失'}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

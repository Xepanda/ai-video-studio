import React from 'react';
import { spring, interpolate } from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

/**
 * 热点快剪: 热点榜单卡片 + trending 动画 (W7-8 场景三)
 * 数据直接来自 hotspot_aggregator 聚合输出 (rank/title/heat/source/tag):
 * 火焰脉冲 + 排名徽章 + 热度值; heat 缺失显示"热度未知" (数据诚信, 禁 0 填充)。
 */

export interface TrendingRankProps {
  rank?: number;
  title?: string;
  /** 热度值; null/缺失 = 未知 (严禁 0 填充) */
  heat?: number | null;
  source?: string;
  tag?: string;
  category?: string;
}

const SOURCE_LABELS: Record<string, string> = {
  weibo: '微博热搜',
  douyin: '抖音热榜',
  bilibili: 'B站热榜',
  x_trends: 'X Trends',
};

export const TrendingRankCard: React.FC<TrendingRankProps & { theme?: ThemeConfig }> = ({
  rank = 1,
  title = '',
  heat = null,
  source = '',
  tag = '',
  category,
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const entry = spring({ frame, fps, config: { damping: 18, stiffness: 110 } });
  // 火焰脉冲: 持续呼吸 (与帧率无关的振荡)
  const flamePulse = 1 + 0.12 * Math.sin(frame / 5);
  const flameGlow = 0.55 + 0.35 * Math.sin(frame / 5 + 1);
  // 热度条宽度 (有热度才显示; 无热度不画假条)
  const heatRatio = typeof heat === 'number' && heat > 0 ? Math.min(1, heat / 5_000_000) : 0;

  const rankBadgeColor = rank <= 3 ? '#f43f5e' : '#64748b';

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '6% 8%',
        backgroundColor: '#0b1220',
        backgroundImage: 'radial-gradient(ellipse at 20% 20%, rgba(244,63,94,0.12), transparent 55%)',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}
    >
      {category ? (
        <div style={{ color: '#fda4af', fontSize: 19, fontWeight: 700, letterSpacing: '0.18em', marginBottom: 24, opacity: entry }}>
          {category}
        </div>
      ) : null}

      <div
        style={{
          width: '86%',
          padding: '34px 40px',
          borderRadius: 22,
          backgroundColor: 'rgba(15, 23, 42, 0.88)',
          border: '1px solid rgba(244, 63, 94, 0.35)',
          boxShadow: `0 0 ${Math.round(40 * flameGlow)}px rgba(244, 63, 94, ${(0.18 * flameGlow).toFixed(3)})`,
          opacity: entry,
          transform: `scale(${interpolate(entry, [0, 1], [0.94, 1.0])})`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
          {/* 排名徽章 */}
          <div
            style={{
              width: 64, height: 64, borderRadius: 16, flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'rgba(244,63,94,0.14)',
              border: `2px solid ${rankBadgeColor}`,
              color: rankBadgeColor, fontSize: 30, fontWeight: 900,
              fontFamily: 'monospace',
            }}
          >
            {rank}
          </div>

          {/* trending 火焰 (脉冲动画) */}
          <div
            style={{
              fontSize: 44,
              transform: `scale(${flamePulse})`,
              filter: `drop-shadow(0 0 ${Math.round(10 * flameGlow)}px rgba(251,146,60,${flameGlow.toFixed(2)}))`,
            }}
          >
            🔥
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: '#f8fafc', fontSize: 30, fontWeight: 800, lineHeight: 1.35 }}>
              {title || '未提供热点标题'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
              {source ? (
                <span style={{ color: '#7dd3fc', fontSize: 16, fontWeight: 700 }}>
                  {SOURCE_LABELS[source] || source}
                </span>
              ) : null}
              {tag ? (
                <span style={{
                  color: '#fda4af', fontSize: 14, fontWeight: 700,
                  border: '1px solid rgba(244,63,94,0.5)', borderRadius: 4, padding: '1px 8px',
                }}>
                  {tag}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        {/* 热度区 (有值才画条; 缺失如实标注) */}
        <div style={{ marginTop: 22 }}>
          {typeof heat === 'number' && heat > 0 ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: 16, marginBottom: 6 }}>
                <span>实时热度</span>
                <span style={{ color: '#f8fafc', fontWeight: 700, fontFamily: 'monospace' }}>
                  {heat.toLocaleString('zh-CN')}
                </span>
              </div>
              <div style={{ height: 8, borderRadius: 4, backgroundColor: 'rgba(30,41,59,0.9)', overflow: 'hidden' }}>
                <div style={{
                  width: `${Math.max(4, heatRatio * 100)}%`,
                  height: '100%',
                  borderRadius: 4,
                  background: 'linear-gradient(90deg, #f43f5e, #fb923c)',
                }} />
              </div>
            </>
          ) : (
            <div style={{ color: '#64748b', fontSize: 16 }}>热度值缺失 (信源未提供, 未做估值填充)</div>
          )}
        </div>
      </div>
    </div>
  );
};

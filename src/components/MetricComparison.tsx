import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

export interface MetricItem {
  name: string;
  value: number;
  maxValue?: number;
  unit?: string;
  color?: string;
  highlight?: boolean;
  subtext?: string;
}

export interface MetricCategory {
  title: string;
  badge?: string;
  pill?: string;
  items: MetricItem[];
}

export interface MetricComparisonProps {
  metrics?: MetricCategory[];
  title?: string;
}

const safeColorWithAlpha = (color: string | undefined, alphaHex: string, fallback: string = '#38bdf8') => {
  const base = color || fallback;
  if (base.startsWith('#') && (base.length === 7 || base.length === 4)) {
    return `${base}${alphaHex}`;
  }
  return base;
};

export const MetricComparison: React.FC<MetricComparisonProps> = ({
  metrics: customMetrics,
  title
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 默认三维工业化基准评测数据 (TTS 吞吐、ASR 打点、全流程成本)
  const defaultMetrics: MetricCategory[] = [
    {
      title: '实时率 RTF 对比 (越低越快)',
      badge: 'SPEED BENCHMARK',
      pill: '⚡ 12.8x 极速吞吐',
      items: [
        { name: '传统云端商业 API', value: 0.95, maxValue: 1.0, unit: 'RTF', color: '#64748b', subtext: '网络往返延迟高' },
        { name: '阿里 SenseVoice (CPU)', value: 0.05, maxValue: 1.0, unit: 'RTF', color: '#10b981', highlight: true, subtext: '纯 CPU 极速 20倍速' },
        { name: 'Paraformer 物理打点', value: 0.06, maxValue: 1.0, unit: 'RTF', color: '#38bdf8', highlight: true, subtext: '字级物理毫秒打点' }
      ]
    },
    {
      title: '单集生产成本 (元/分钟)',
      badge: 'COST EFFICIENCY',
      pill: '💰 0 元本地无版权',
      items: [
        { name: '外采音画混剪团队', value: 80, maxValue: 100, unit: '元/分', color: '#ef4444', subtext: '人力成本高昂' },
        { name: '商用 SaaS 商业订阅', value: 18, maxValue: 100, unit: '元/分', color: '#f59e0b', subtext: '按字计费上限受限' },
        { name: 'Remotion + ChatTTS (全开源)', value: 0, maxValue: 100, unit: '元/分', color: '#34d399', highlight: true, subtext: '100% 本地免费离线' }
      ]
    }
  ];

  const metrics = customMetrics && customMetrics.length > 0 ? customMetrics : defaultMetrics;

  return (
    <div style={{
      width: '100%',
      maxWidth: '1440px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      {/* 组件顶栏标题 (若调用方传入) */}
      {title && (
        <div style={{
          fontSize: '22px',
          fontWeight: 800,
          color: '#38bdf8',
          letterSpacing: '3px',
          textTransform: 'uppercase',
          marginBottom: '20px'
        }}>
          {title}
        </div>
      )}

      {/* 指标卡片网格 */}
      <div style={{
        width: '100%',
        display: 'flex',
        gap: '32px',
        justifyContent: 'center'
      }}>
        {metrics.map((cat, catIdx) => {
          const catSpring = spring({ frame: Math.max(0, frame - catIdx * 8), fps, config: { damping: 14 } });
          const items = cat.items || [];

          return (
            <div
              key={catIdx}
              style={{
                flex: 1,
                backgroundColor: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: '24px',
                padding: '36px 32px',
                boxShadow: '0 20px 45px rgba(0, 0, 0, 0.6)',
                backdropFilter: 'blur(16px)',
                transform: `scale(${interpolate(catSpring, [0, 1], [0.92, 1.0])})`,
                opacity: catSpring
              }}
            >
              {/* 顶栏徽标与对比药丸 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8', letterSpacing: '2px', textTransform: 'uppercase' }}>
                  {cat.badge || 'BENCHMARK'}
                </span>
                {cat.pill && (
                  <span style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    color: '#34d399',
                    border: '1px solid rgba(16, 185, 129, 0.35)',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontSize: '13px',
                    fontWeight: 800
                  }}>
                    {cat.pill}
                  </span>
                )}
              </div>

              {/* 分类标题 */}
              <div style={{ fontSize: '24px', fontWeight: 900, color: '#f8fafc', marginBottom: '28px' }}>
                {cat.title}
              </div>

              {/* 指标进度条列表 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
                {items.map((item, itemIdx) => {
                  const barSpring = spring({
                    frame: Math.max(0, frame - catIdx * 8 - 10 - itemIdx * 6),
                    fps,
                    config: { damping: 15, stiffness: 90 }
                  });

                  const maxV = item.maxValue || 100;
                  // 针对真正为 0 的数值保持 0%，非零数值保持适度可视长度
                  const ratio = item.value <= 0 ? 0 : Math.min(1.0, Math.max(0.04, item.value / maxV));
                  const barWidthPct = interpolate(barSpring, [0, 1], [0, ratio * 100]);
                  const itemColor = item.color || '#38bdf8';

                  return (
                    <div key={itemIdx}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{
                          fontSize: '16px',
                          fontWeight: item.highlight ? 800 : 600,
                          color: item.highlight ? '#f8fafc' : '#cbd5e1'
                        }}>
                          {item.name}
                        </span>
                        <span style={{
                          fontSize: '18px',
                          fontWeight: 900,
                          color: itemColor
                        }}>
                          {item.value} {item.unit || ''}
                        </span>
                      </div>

                      {/* 进度条轨道 */}
                      <div style={{
                        width: '100%',
                        height: '14px',
                        backgroundColor: 'rgba(2, 6, 23, 0.7)',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        padding: '2px',
                        border: item.highlight ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)'
                      }}>
                        <div style={{
                          width: `${barWidthPct}%`,
                          height: '100%',
                          borderRadius: '6px',
                          background: item.highlight
                            ? `linear-gradient(90deg, ${itemColor} 0%, #818cf8 100%)`
                            : itemColor,
                          boxShadow: item.highlight ? `0 0 12px ${safeColorWithAlpha(itemColor, '66')}` : 'none'
                        }} />
                      </div>

                      {item.subtext && (
                        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px' }}>
                          {item.subtext}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

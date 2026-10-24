import React from 'react';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

/**
 * 学科可视化: asciicast 终端播放场景 (W7-8 场景二)
 * 按帧回放 asciicast v2 事件流 ([time, 'o', data]), 还原真实终端会话:
 * 逐字符揭示 + 块状光标 + 终端窗口 chrome。
 * 事件数据来自真实录制 (github_demo_pipeline 等), 组件不做任何编造。
 */

export interface AsciicastEvent {
  /** 相对时间 (秒) */
  time: number;
  /** 事件类型: o=输出, i=输入 (r=resize 暂忽略) */
  type: string;
  /** 终端数据 (可含 ANSI 控制序列, 渲染前剥离) */
  data: string;
}

export interface AsciicastProps {
  events?: AsciicastEvent[];
  cols?: number;
  rows?: number;
  title?: string;
  category?: string;
  /** 回放速度倍率 (默认 1) */
  speed?: number;
}

// 剥离 ANSI CSI / OSC 序列 (颜色与光标控制码), 保留可读文本
// 数据诚信: 仅剥离控制序列, 不改写任何可见字符
const ANSI_RE = /\u001b\[[0-9;?]*[a-zA-Z]|\u001b\][^\u0007]*\u0007|\u001b[=>()][A-B0-9]?/g;

function stripAnsi(text: string): string {
  return text.replace(ANSI_RE, '');
}

export const AsciicastPlayer: React.FC<AsciicastProps & { theme?: ThemeConfig }> = ({
  events = [],
  cols = 100,
  rows = 24,
  title = 'terminal',
  category,
  speed = 1,
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();
  const nowSec = (frame / fps) * speed;

  // 累积揭示: 输出事件按时间序回放; 首事件 (通常是 shell 提示符) 始终可见,
  // 保障 SSR frame=0 快照的终端不为空 (可观测契约)
  let revealed = '';
  let cursorVisible = true;
  const sorted = [...events].sort((a, b) => a.time - b.time);
  for (let i = 0; i < sorted.length; i++) {
    const ev = sorted[i];
    if (ev.time <= nowSec || i === 0) {
      if (ev.type === 'o' || ev.type === 'i') revealed += stripAnsi(ev.data || '');
    } else {
      // 下一个事件的字符级部分揭示 (平滑打字感)
      const next = sorted[i];
      const prevTime = i > 0 ? sorted[i - 1].time : 0;
      const span = Math.max(0.001, next.time - prevTime);
      const progress = Math.min(1, Math.max(0, (nowSec - prevTime) / span));
      const chars = Math.floor(stripAnsi(next.data || '').length * progress);
      if (next.type === 'o' || next.type === 'i') {
        revealed += stripAnsi(next.data || '').slice(0, chars);
      }
      cursorVisible = progress > 0;
      break;
    }
  }

  const displayLines = revealed.replace(/\n$/, '').split('\n').slice(-rows);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#020617',
        fontFamily: '"JetBrains Mono", "Noto Sans SC", Consolas, monospace',
      }}
    >
      {category ? (
        <div style={{ color: '#7dd3fc', fontSize: 18, fontWeight: 700, letterSpacing: '0.16em', padding: '18px 28px 0', fontFamily: '"Noto Sans SC", sans-serif' }}>
          {category}
        </div>
      ) : null}

      <div
        style={{
          flex: 1,
          margin: '14px 28px 28px',
          borderRadius: 12,
          overflow: 'hidden',
          border: '1px solid #1e293b',
          backgroundColor: '#0f172a',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 24px 60px rgba(2,6,23,0.6)',
        }}
      >
        {/* 终端标题栏 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
          backgroundColor: '#1e293b', borderBottom: '1px solid #334155',
        }}>
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ef4444' }} />
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#f59e0b' }} />
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#22c55e' }} />
          <span style={{ marginLeft: 10, color: '#94a3b8', fontSize: 14 }}>{title}</span>
          <span style={{ marginLeft: 'auto', color: '#475569', fontSize: 12 }}>{cols}×{rows}</span>
        </div>

        {/* 终端输出区 (空事件流时显示等待占位, 不渲染空白行) */}
        <div style={{
          flex: 1, padding: '14px 18px', overflow: 'hidden',
          fontSize: 16, lineHeight: 1.5, color: '#e2e8f0', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
        }}>
          {revealed.length === 0 ? (
            <span style={{ color: '#475569' }}>等待终端事件流...</span>
          ) : (
            displayLines.map((line, idx) => <div key={idx}>{line || ' '}</div>)
          )}
          {cursorVisible ? (
            <span style={{
              display: 'inline-block', width: 10, height: 20, marginLeft: 2,
              backgroundColor: '#22d3ee', verticalAlign: 'text-bottom',
              opacity: Math.sin(frame / 8) > 0 ? 1 : 0.2,
            }} />
          ) : null}
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { interpolate, spring } from 'remotion';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

/**
 * 学科可视化: 时序图 / 状态机场景 (W7-8 场景一)
 * 两种数据驱动模式:
 *  - mode='sequence': participants (参与者列 + 生命线) + messages (带方向箭头的消息, 逐条入场)
 *  - mode='state':    states (状态节点) + transitions (转移箭头与标签)
 * 组件不持有任何硬编码学术内容, 全部来自分镜嵌套配置。
 */
export interface SequenceParticipant {
  id: string;
  name: string;
}

export interface SequenceMessage {
  from: string;
  to: string;
  label: string;
  dashed?: boolean;
}

export interface StateNode {
  id: string;
  label: string;
}

export interface StateTransition {
  from: string;
  to: string;
  label?: string;
}

export interface SequenceDiagramProps {
  mode?: 'sequence' | 'state';
  title?: string;
  category?: string;
  /** mode='sequence' */
  participants?: SequenceParticipant[];
  messages?: SequenceMessage[];
  /** mode='state' */
  states?: StateNode[];
  transitions?: StateTransition[];
}

const ACCENT = '#38bdf8';
const ACCENT_ALT = '#a855f7';
const NODE_FILL = 'rgba(30, 41, 59, 0.9)';

const MESSAGE_STAGGER = 18; // 帧: 每条消息的入场间隔

export const SequenceDiagramScene: React.FC<SequenceDiagramProps & { theme?: ThemeConfig }> = ({
  mode = 'sequence',
  title,
  category,
  participants = [],
  messages = [],
  states = [],
  transitions = [],
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const headerOpacity = spring({ frame, fps, config: { damping: 20, stiffness: 120 } });

  const renderSequence = () => {
    if (participants.length === 0) {
      return (
        <div style={{ color: '#64748b', fontSize: 24 }}>
          未提供 participants 数据 (分镜嵌套配置缺失)
        </div>
      );
    }
    const colWidth = 100 / participants.length;
    const colIndex = (id: string) => participants.findIndex((p) => p.id === id);

    return (
      <div style={{ position: 'relative', width: '100%', flex: 1 }}>
        {/* 参与者名称框 (列头) */}
        {participants.map((p, idx) => (
          <div
            key={`head-${p.id}`}
            style={{
              position: 'absolute',
              left: `calc(${colWidth * idx + colWidth / 2}% - 88px)`,
              top: 0,
              width: 176,
              padding: '10px 0',
              textAlign: 'center',
              borderRadius: 10,
              backgroundColor: 'rgba(30, 41, 59, 0.92)',
              border: `1px solid ${ACCENT}`,
              color: '#f1f5f9',
              fontSize: 22,
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            {p.name}
          </div>
        ))}

        {/* 生命线 (垂直虚线) */}
        {participants.map((p, idx) => (
          <div
            key={`line-${p.id}`}
            style={{
              position: 'absolute',
              left: `${colWidth * idx + colWidth / 2}%`,
              top: 84,
              bottom: 36,
              width: 0,
              borderLeft: '2px dashed rgba(148, 163, 184, 0.45)',
            }}
          />
        ))}

        {/* 消息箭头 (逐条入场; frame=0 时 opacity=0 不可见但保留 DOM, 保障 SSR 可观测契约) */}
        {messages.map((msg, idx) => {
          const fromIdx = colIndex(msg.from);
          const toIdx = colIndex(msg.to);
          if (fromIdx < 0 || toIdx < 0 || fromIdx === toIdx) return null;
          const appear = spring({
            frame: frame - idx * MESSAGE_STAGGER,
            fps,
            config: { damping: 22, stiffness: 130 },
          });
          const left = Math.min(fromIdx, toIdx) * colWidth + colWidth / 2;
          const width = Math.abs(toIdx - fromIdx) * colWidth;
          const forward = toIdx > fromIdx;
          const top = 120 + idx * 64;

          return (
            <div
              key={`msg-${idx}`}
              style={{
                position: 'absolute',
                left: `${left}%`,
                top,
                width: `${width}%`,
                opacity: appear,
                transform: `translateY(${interpolate(appear, [0, 1], [10, 0])}px)`,
              }}
            >
              <div
                style={{
                  position: 'relative',
                  height: 28,
                  borderTop: msg.dashed
                    ? `2px dashed ${ACCENT_ALT}`
                    : `2px solid ${ACCENT}`,
                }}
              >
                {/* 箭头头部 */}
                <div
                  style={{
                    position: 'absolute',
                    [forward ? 'right' : 'left']: -2,
                    top: -7,
                    width: 0,
                    height: 0,
                    borderTop: '7px solid transparent',
                    borderBottom: '7px solid transparent',
                    ...(forward
                      ? { borderLeft: `12px solid ${msg.dashed ? ACCENT_ALT : ACCENT}` }
                      : { borderRight: `12px solid ${msg.dashed ? ACCENT_ALT : ACCENT}` }),
                  }}
                />
              </div>
              <div
                style={{
                  position: 'absolute',
                  left: '50%',
                  top: -34,
                  transform: 'translateX(-50%)',
                  color: msg.dashed ? '#c4b5fd' : '#e2e8f0',
                  fontSize: 20,
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  textShadow: '0 2px 8px rgba(2,6,23,0.9)',
                }}
              >
                {msg.label}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderState = () => {
    if (states.length === 0) {
      return (
        <div style={{ color: '#64748b', fontSize: 24 }}>
          未提供 states 数据 (分镜嵌套配置缺失)
        </div>
      );
    }
    const nodeWidth = 100 / states.length;

    return (
      <div style={{ position: 'relative', width: '100%', flex: 1 }}>
        {/* 状态节点 */}
        {states.map((s, idx) => {
          const appear = spring({
            frame: frame - idx * MESSAGE_STAGGER,
            fps,
            config: { damping: 20, stiffness: 120 },
          });
          const incoming = transitions.filter((t) => t.to === s.id).length;
          return (
            <div
              key={s.id}
              style={{
                position: 'absolute',
                left: `calc(${nodeWidth * idx + nodeWidth / 2}% - 96px)`,
                top: '38%',
                width: 192,
                padding: '22px 0',
                textAlign: 'center',
                borderRadius: 999,
                backgroundColor: NODE_FILL,
                border: `2px solid ${incoming > 0 ? ACCENT : 'rgba(148,163,184,0.5)'}`,
                color: '#f1f5f9',
                fontSize: 24,
                fontWeight: 700,
                opacity: appear,
                transform: `scale(${interpolate(appear, [0, 1], [0.85, 1.0])})`,
                boxShadow: incoming > 0 ? '0 0 28px rgba(56,189,248,0.25)' : 'none',
              }}
            >
              {s.label}
            </div>
          );
        })}

        {/* 转移箭头与标签 (同上: opacity 0 保留 DOM) */}
        {transitions.map((t, idx) => {
          const fromIdx = states.findIndex((s) => s.id === t.from);
          const toIdx = states.findIndex((s) => s.id === t.to);
          if (fromIdx < 0 || toIdx < 0 || fromIdx === toIdx) return null;
          const appear = spring({
            frame: frame - (states.length + idx) * MESSAGE_STAGGER,
            fps,
            config: { damping: 22, stiffness: 130 },
          });
          const left = Math.min(fromIdx, toIdx) * nodeWidth + nodeWidth / 2;
          const width = Math.abs(toIdx - fromIdx) * nodeWidth;
          const forward = toIdx > fromIdx;

          return (
            <div
              key={`tr-${idx}`}
              style={{
                position: 'absolute',
                left: `${left}%`,
                top: 'calc(38% - 26px)',
                width: `${width}%`,
                opacity: appear,
              }}
            >
              <div
                style={{
                  position: 'relative',
                  height: 0,
                  borderTop: `2px solid ${ACCENT_ALT}`,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    [forward ? 'right' : 'left']: -2,
                    top: -7,
                    width: 0,
                    height: 0,
                    borderTop: '7px solid transparent',
                    borderBottom: '7px solid transparent',
                    ...(forward
                      ? { borderLeft: `12px solid ${ACCENT_ALT}` }
                      : { borderRight: `12px solid ${ACCENT_ALT}` }),
                  }}
                />
              </div>
              {t.label ? (
                <div
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: -36,
                    transform: 'translateX(-50%)',
                    color: '#c4b5fd',
                    fontSize: 19,
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {t.label}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: '4% 6%',
        backgroundColor: '#0b1220',
        backgroundImage: 'radial-gradient(ellipse at 50% 20%, rgba(168,85,247,0.10), transparent 60%)',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}
    >
      {category ? (
        <div style={{ color: '#c4b5fd', fontSize: 19, fontWeight: 700, letterSpacing: '0.16em', opacity: headerOpacity }}>
          {category}
        </div>
      ) : null}
      {title ? (
        <div style={{ color: '#f8fafc', fontSize: 36, fontWeight: 800, margin: '10px 0 20px', opacity: headerOpacity }}>
          {title}
        </div>
      ) : null}

      {mode === 'sequence' ? renderSequence() : renderState()}
    </div>
  );
};

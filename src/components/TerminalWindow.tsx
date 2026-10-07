import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

export interface TerminalWindowProps {
  title?: string;
  command?: string;
  content?: string;
  output?: string[];
  typingDurationFrames?: number;
  width?: number | string;
  height?: number | string;
}

/**
 * 极客终端代码打字机组件
 */
export const TerminalWindow: React.FC<TerminalWindowProps> = ({
  title = 'zsh - terminal',
  command,
  content,
  output = [],
  typingDurationFrames = 45,
  width = '100%',
  height = 'auto',
}) => {
  const frame = useCurrentFrame();
  const rawCode = command || content || '';
  const isMultiline = rawCode.includes('\n');

  // 打字进度
  const charsCount = Math.floor(
    interpolate(frame, [10, 10 + typingDurationFrames], [0, rawCode.length], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  const typedCommand = rawCode.slice(0, charsCount);
  const showOutput = frame > 10 + typingDurationFrames + 5;
  const cursorBlink = Math.floor(frame / 12) % 2 === 0;

  const lines = typedCommand.split('\n');

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: '#0d1117',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      }}
    >
      {/* 终端顶部标题栏 */}
      <div
        style={{
          height: '42px',
          backgroundColor: '#161b22',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ff5f56' }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ffbd2e' }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27c93f' }} />
        </div>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            textAlign: 'center',
            color: '#8b949e',
            fontSize: '14px',
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {title}
        </div>
      </div>

      {/* 终端控制台内容 */}
      <div
        style={{
          flex: 1,
          padding: '24px 28px',
          color: '#e6edf3',
          fontSize: isMultiline ? '20px' : '22px',
          lineHeight: 1.7,
          display: 'flex',
          flexDirection: 'column',
          gap: isMultiline ? '8px' : '12px',
        }}
      >
        {isMultiline ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {lines.map((line, idx) => {
              const isLastLine = idx === lines.length - 1;
              const isComment = line.trim().startsWith('#') || line.trim().startsWith('//');
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'baseline', gap: '16px' }}>
                  <span
                    style={{
                      color: '#4b5563',
                      fontSize: '15px',
                      userSelect: 'none',
                      minWidth: '24px',
                      textAlign: 'right',
                    }}
                  >
                    {idx + 1}
                  </span>
                  <div
                    style={{
                      flex: 1,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      color: isComment ? '#7dd3fc' : '#f1f5f9',
                    }}
                  >
                    <span>{line}</span>
                    {isLastLine && (!showOutput || cursorBlink) && (
                      <span
                        style={{
                          backgroundColor: '#38bdf8',
                          width: '10px',
                          height: '20px',
                          display: 'inline-block',
                          verticalAlign: 'text-bottom',
                          marginLeft: '4px',
                        }}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', whiteSpace: 'pre-wrap' }}>
            <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>➜</span>
            <span style={{ color: '#a78bfa' }}>projects</span>
            <span style={{ color: '#f43f5e' }}>git:(main)</span>
            <span>{typedCommand}</span>
            {(!showOutput || cursorBlink) && (
              <span style={{ backgroundColor: '#38bdf8', width: '12px', height: '24px', display: 'inline-block' }} />
            )}
          </div>
        )}

        {showOutput && output.length > 0 && (
          <div style={{ color: '#34d399', marginTop: '12px', whiteSpace: 'pre-wrap', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
            {output.map((line, idx) => (
              <div key={idx}>{line}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

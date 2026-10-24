import React from 'react';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

/**
 * 学科可视化: IDE 窗口场景 (W7-8 场景二)
 * 数据驱动的 IDE mockup: 文件树 + 标签页 + 语法高亮代码区 + 行号。
 * 语法高亮为内置轻量分词器 (无外部依赖), 以 React span 渲染
 * (不走 dangerouslySetInnerHTML, SSR 安全且无注入面)。
 */

export interface IdeFile {
  /** 文件名 (标签页显示) */
  name: string;
  /** 相对路径 (文件树分组显示; 省略时平铺) */
  path?: string;
  /** 语言: js/ts/py/c/go/bash/yaml/json (未知按纯文本) */
  lang?: string;
  /** 文件内容 */
  content: string;
  /** 是否为活动文件 (默认取第一个) */
  active?: boolean;
}

export interface IdeWindowProps {
  files?: IdeFile[];
  title?: string;
  category?: string;
}

const KEYWORDS: Record<string, string[]> = {
  js: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'from', 'export', 'default', 'class', 'extends', 'new', 'await', 'async', 'try', 'catch', 'throw', 'typeof', 'instanceof', 'null', 'undefined', 'true', 'false', 'this'],
  ts: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'from', 'export', 'default', 'class', 'extends', 'implements', 'interface', 'type', 'enum', 'new', 'await', 'async', 'try', 'catch', 'throw', 'typeof', 'instanceof', 'null', 'undefined', 'true', 'false', 'this', 'public', 'private', 'readonly', 'as'],
  py: ['def', 'return', 'if', 'elif', 'else', 'for', 'while', 'import', 'from', 'class', 'try', 'except', 'finally', 'raise', 'with', 'as', 'lambda', 'yield', 'pass', 'break', 'continue', 'None', 'True', 'False', 'self', 'and', 'or', 'not', 'in', 'is'],
  c: ['int', 'char', 'float', 'double', 'void', 'return', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'struct', 'typedef', 'static', 'const', 'unsigned', 'sizeof', 'NULL', 'include', 'define'],
  go: ['package', 'import', 'func', 'return', 'if', 'else', 'for', 'range', 'var', 'const', 'type', 'struct', 'interface', 'map', 'chan', 'go', 'defer', 'nil', 'true', 'false', 'string', 'int', 'error'],
  bash: ['if', 'then', 'else', 'fi', 'for', 'do', 'done', 'while', 'case', 'esac', 'function', 'return', 'export', 'echo', 'cd', 'sudo', 'apt', 'pip', 'npm', 'git'],
  yaml: ['true', 'false', 'null', 'yes', 'no', 'on', 'off'],
  json: ['true', 'false', 'null'],
};

const COMMENT_PREFIX: Record<string, string[]> = {
  js: ['//'], ts: ['//'], c: ['//'], go: ['//'], bash: ['#'], py: ['#'], yaml: ['#'],
};

type TokenKind = 'plain' | 'keyword' | 'string' | 'comment' | 'number' | 'fn';

const TOKEN_COLORS: Record<TokenKind, string> = {
  plain: '#e2e8f0',
  keyword: '#c084fc',
  string: '#86efac',
  comment: '#64748b',
  number: '#fbbf24',
  fn: '#38bdf8',
};

function highlightLine(line: string, lang: string): Array<{ kind: TokenKind; text: string }> {
  const keywords = new Set(KEYWORDS[lang] || []);
  const commentPrefixes = COMMENT_PREFIX[lang] || [];
  const tokens: Array<{ kind: TokenKind; text: string }> = [];

  // 注释整行
  for (const prefix of commentPrefixes) {
    if (line.trimStart().startsWith(prefix)) {
      return [{ kind: 'comment', text: line }];
    }
  }

  // 轻量分词: 字符串 / 注释尾随 / 标识符 / 数字 / 其他
  const tokenRe = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\/\/.*|#.*)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_$][\w$]*)|(\s+)|([^\sA-Za-z0-9_$]+)/g;
  let m: RegExpExecArray | null;
  let last = 0;
  const push = (kind: TokenKind, text: string) => {
    if (text) tokens.push({ kind, text });
  };
  while ((m = tokenRe.exec(line)) !== null) {
    if (m.index > last) push('plain', line.slice(last, m.index));
    if (m[1]) push('string', m[1]);
    else if (m[2]) push('comment', m[2]);
    else if (m[3]) push('number', m[3]);
    else if (m[4]) {
      const word = m[4];
      // 函数调用: 标识符后紧跟 (
      const after = line.slice(m.index + word.length, m.index + word.length + 1);
      if (after === '(') push('fn', word);
      else if (keywords.has(word)) push('keyword', word);
      else push('plain', word);
    } else if (m[5]) push('plain', m[5]);
    else if (m[6]) push('plain', m[6]);
    last = m.index + m[0].length;
  }
  if (last < line.length) push('plain', line.slice(last));
  return tokens;
}

export const IdeWindowScene: React.FC<IdeWindowProps & { theme?: ThemeConfig }> = ({
  files = [],
  title,
  category,
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  const activeFile = files.find((f) => f.active) || files[0];
  const entry = Math.min(1, frame / (fps * 0.5));
  const lines = activeFile ? activeFile.content.split('\n') : [];

  if (!activeFile) {
    return (
      <div style={{
        width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: '#0b1220', color: '#64748b', fontSize: 24,
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}>
        未提供 files 数据 (分镜 ide 嵌套配置缺失)
      </div>
    );
  }

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0b1220',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
        opacity: entry,
        transform: `scale(${0.97 + 0.03 * entry})`,
      }}
    >
      {category ? (
        <div style={{ color: '#7dd3fc', fontSize: 18, fontWeight: 700, letterSpacing: '0.16em', padding: '18px 28px 0' }}>
          {category}
        </div>
      ) : null}
      {title ? (
        <div style={{ color: '#f8fafc', fontSize: 32, fontWeight: 800, padding: '8px 28px 14px' }}>
          {title}
        </div>
      ) : null}

      <div
        style={{
          flex: 1,
          margin: '0 28px 28px',
          borderRadius: 14,
          overflow: 'hidden',
          border: '1px solid #1e293b',
          backgroundColor: '#0f172a',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 24px 60px rgba(2,6,23,0.6)',
        }}
      >
        {/* 窗口标题栏 (红黄绿 + 标题) */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
          backgroundColor: '#1e293b', borderBottom: '1px solid #334155',
        }}>
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ef4444' }} />
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#f59e0b' }} />
          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#22c55e' }} />
          <span style={{ marginLeft: 10, color: '#94a3b8', fontSize: 14 }}>{title || 'IDE'}</span>
        </div>

        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          {/* 文件树 */}
          <div style={{
            width: 220, borderRight: '1px solid #1e293b', padding: '12px 10px',
            backgroundColor: '#0c1322', overflow: 'hidden',
          }}>
            <div style={{ color: '#64748b', fontSize: 12, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 8 }}>
              EXPLORER
            </div>
            {files.map((f) => {
              const isActive = f === activeFile;
              return (
                <div
                  key={f.name + (f.path || '')}
                  style={{
                    color: isActive ? '#e2e8f0' : '#94a3b8',
                    backgroundColor: isActive ? 'rgba(56,189,248,0.12)' : 'transparent',
                    fontSize: 14,
                    padding: '4px 8px',
                    borderRadius: 6,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    fontFamily: 'monospace',
                  }}
                >
                  {isActive ? '▸ ' : '  '}
                  {f.path ? `${f.path}/` : ''}{f.name}
                </div>
              );
            })}
          </div>

          {/* 编辑区: 标签页 + 代码 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            {/* 标签页 */}
            <div style={{ display: 'flex', borderBottom: '1px solid #1e293b', backgroundColor: '#0c1322' }}>
              {files.map((f) => {
                const isActive = f === activeFile;
                return (
                  <div
                    key={`tab-${f.name}`}
                    style={{
                      padding: '8px 16px',
                      fontSize: 13,
                      fontFamily: 'monospace',
                      color: isActive ? '#38bdf8' : '#64748b',
                      borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                      borderRight: '1px solid #1e293b',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {f.name}
                  </div>
                );
              })}
            </div>

            {/* 代码区 (行号 + 高亮; 全量渲染保障 SSR 可观测契约) */}
            <div style={{ flex: 1, padding: '12px 0', overflow: 'hidden' }}>
              {lines.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', fontSize: 15, lineHeight: 1.55, fontFamily: '"JetBrains Mono", Consolas, monospace' }}>
                  <span style={{
                    width: 44, textAlign: 'right', paddingRight: 14, color: '#475569',
                    userSelect: 'none', flexShrink: 0,
                  }}>
                    {idx + 1}
                  </span>
                  <span style={{ whiteSpace: 'pre', color: TOKEN_COLORS.plain }}>
                    {highlightLine(line, activeFile.lang || '').map((tok, ti) => (
                      <span key={ti} style={{ color: TOKEN_COLORS[tok.kind] }}>{tok.text}</span>
                    ))}
                  </span>
                </div>
              ))}
              {/* 光标 */}
              <div style={{ display: 'flex', fontSize: 15, fontFamily: 'monospace' }}>
                <span style={{ width: 44, flexShrink: 0 }} />
                <span style={{
                  width: 9, height: 18, backgroundColor: '#38bdf8',
                  opacity: Math.sin(frame / 6) > 0 ? 1 : 0.15,
                }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

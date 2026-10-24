import React from 'react';
import { interpolate, spring } from 'remotion';
import katex from 'katex';
import { useSafeFrameConfig } from './useSafeFrameConfig';
import { ThemeConfig } from '../../styles/theme';

// KaTeX 排版样式表注入 (双环境兼容):
// - Remotion (webpack) 构建: require 字面量经 css-loader 静态处理, 样式进入 bundle;
// - 纯 Node 测试运行 (tsc->CJS, 无 CSS loader): require 失败静默跳过,
//   KaTeX HTML 输出自带内联结构样式, 契约断言不依赖外部 CSS 规则。
declare const require: (id: string) => unknown; // 局部声明: 不依赖 @types/node 全局注入
try {
  require('katex/dist/katex.min.css');
} catch {
  /* 测试环境无 CSS loader, 跳过样式注入 */
}

/**
 * 学科可视化: KaTeX 公式场景 (W7-8 场景一)
 * 将 LaTeX 公式渲染为高品质排版卡片, 支持逐词高亮说明与入场动效。
 * 公式内容完全由分镜数据驱动 (props.formula), 组件内绝不硬编码学术内容。
 */
export interface MathFormulaProps {
  /** LaTeX 公式字符串 (例如 "E = mc^2" 或 "\\frac{a}{b}") */
  formula: string;
  /** 行间公式模式 (独立成行, 默认 true) */
  displayMode?: boolean;
  title?: string;
  /** 公式下方的人话解读 */
  caption?: string;
  category?: string;
  /** 高亮描边 (强调核心公式时使用) */
  highlight?: boolean;
}

export const MathFormulaScene: React.FC<MathFormulaProps & { theme?: ThemeConfig }> = ({
  formula,
  displayMode = true,
  title,
  caption,
  category,
  highlight = false,
  theme: _theme,
}) => {
  const { frame, fps } = useSafeFrameConfig();

  // KaTeX 渲染 (throwOnError=false: 公式小错误降级为原文展示, 不炸渲染)
  let formulaHtml = '';
  try {
    formulaHtml = katex.renderToString(formula, {
      displayMode,
      throwOnError: false,
      strict: false,
      output: 'html',
      trust: false,
    });
  } catch {
    // 极端情况 (如 katex 内部异常): 回退纯文本, 绝不空白
    formulaHtml = `<span style="font-family: monospace">${formula.replace(/[<>&]/g, '')}</span>`;
  }

  const entry = spring({ frame, fps, config: { damping: 18, stiffness: 110 } });
  const captionOpacity = interpolate(frame, [fps * 0.8, fps * 1.6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
        backgroundImage: 'radial-gradient(ellipse at 50% 30%, rgba(56,189,248,0.10), transparent 60%)',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}
    >
      {category ? (
        <div
          style={{
            color: '#7dd3fc',
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: '0.18em',
            marginBottom: 28,
            opacity: entry,
          }}
        >
          {category}
        </div>
      ) : null}

      {title ? (
        <div
          style={{
            color: '#f8fafc',
            fontSize: 40,
            fontWeight: 800,
            marginBottom: 44,
            textAlign: 'center',
            opacity: entry,
          }}
        >
          {title}
        </div>
      ) : null}

      {/* 公式卡片: 入场弹性缩放 */}
      <div
        style={{
          transform: `scale(${interpolate(entry, [0, 1], [0.92, 1.0])})`,
          opacity: entry,
          maxWidth: '86%',
          padding: '44px 56px',
          borderRadius: 20,
          backgroundColor: 'rgba(15, 23, 42, 0.82)',
          border: highlight ? '2px solid #a855f7' : '1px solid rgba(56, 189, 248, 0.35)',
          boxShadow: highlight
            ? '0 0 44px rgba(168, 85, 247, 0.28)'
            : '0 18px 48px rgba(2, 6, 23, 0.55)',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          className="katex-formula-root"
          style={{ color: '#e2e8f0', fontSize: displayMode ? 40 : 32 }}
          dangerouslySetInnerHTML={{ __html: formulaHtml }}
        />
      </div>

      {caption ? (
        <div
          style={{
            marginTop: 40,
            maxWidth: '76%',
            color: '#94a3b8',
            fontSize: 26,
            lineHeight: 1.65,
            textAlign: 'center',
            opacity: captionOpacity,
          }}
        >
          {caption}
        </div>
      ) : null}
    </div>
  );
};

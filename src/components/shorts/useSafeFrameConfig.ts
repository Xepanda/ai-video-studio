import { useCurrentFrame, useVideoConfig } from 'remotion';

/**
 * useSafeFrameConfig
 * SSR / 单元测试 (ReactDOMServer.renderToStaticMarkup) 环境下不存在 Remotion
 * Composition 上下文, useCurrentFrame / useVideoConfig 会抛错或返回 undefined。
 * 统一安全回退 frame=0 / fps=30 / 1920x1080 (与 UniversalScene.useSafeRemotionConfig、
 * TechNewsShortsScene 的内联回退同一模式), 保证组件在无头渲染与契约测试中
 * 绝不抛异常, 同时防止 undefined 帧号污染 interpolate 产生 NaN。
 */
export function useSafeFrameConfig(): {
  frame: number;
  fps: number;
  width: number;
  height: number;
} {
  const fallback = { frame: 0, fps: 30, width: 1920, height: 1080 };
  try {
    const frame = useCurrentFrame();
    const { fps, width, height } = useVideoConfig();
    if (typeof frame !== 'number' || !Number.isFinite(frame)) {
      return { ...fallback, fps: safeNum(fps, 30), width: safeNum(width, 1920), height: safeNum(height, 1080) };
    }
    return {
      frame,
      fps: safeNum(fps, 30),
      width: safeNum(width, 1920),
      height: safeNum(height, 1080),
    };
  } catch {
    return fallback;
  }
}

function safeNum(value: unknown, fallbackValue: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallbackValue;
}

import { useCurrentFrame, useVideoConfig } from 'remotion';

/**
 * useSafeFrameConfig
 * SSR / 单元测试 (ReactDOMServer.renderToStaticMarkup) 环境下不存在 Remotion
 * Composition 上下文, useCurrentFrame / useVideoConfig 会抛错或返回 undefined。
 * 统一安全回退 frame=0 / fps=30 (与 UniversalScene.useSafeRemotionConfig、
 * TechNewsShortsScene 的内联回退同一模式), 保证组件在无头渲染与契约测试中
 * 绝不抛异常, 同时防止 undefined 帧号污染 interpolate 产生 NaN。
 */
export function useSafeFrameConfig(): { frame: number; fps: number } {
  try {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    if (typeof frame !== 'number' || !Number.isFinite(frame)) {
      return { frame: 0, fps: 30 };
    }
    if (typeof fps !== 'number' || !Number.isFinite(fps)) {
      return { frame, fps: 30 };
    }
    return { frame, fps };
  } catch {
    return { frame: 0, fps: 30 };
  }
}

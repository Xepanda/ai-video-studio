import React from 'react';
import { Img, useVideoConfig } from 'remotion';

export interface SafeImageProps {
  src: string;
  alt?: string;
  style?: React.CSSProperties;
  className?: string;
}

/**
 * 探测当前是否处于 Remotion Composition 上下文。
 * 裸 SSR / renderToStaticMarkup / Node 测试环境下 useVideoConfig 抛错
 * ("No video config found"), 此时 Remotion <Img> 内部
 * usePremounting -> useCurrentFrame 同样必抛, 图片无法渲染。
 */
export function useRemotionContext(): boolean {
  try {
    useVideoConfig();
    return true;
  } catch {
    return false;
  }
}

/**
 * SafeImage - 上下文自适应图片组件。
 *
 * - Remotion Composition 内 (真实渲染/预览): 使用 <Img>, 经 delayRender
 *   等待图片解码完成, 避免渲染黑帧 (Phase 0 B3 的既定收益);
 * - 裸 SSR / 契约测试环境: 回退原生 <img>, 保障无头渲染不抛错
 *   (与 useSafeFrameConfig 同一 SSR 安全哲学)。
 */
export const SafeImage: React.FC<SafeImageProps> = ({
  src,
  alt = '',
  style,
  className,
}) => {
  const inRemotion = useRemotionContext();
  if (inRemotion) {
    return <Img src={src} alt={alt} style={style} className={className} />;
  }
  return <img src={src} alt={alt} style={style} className={className} />;
};

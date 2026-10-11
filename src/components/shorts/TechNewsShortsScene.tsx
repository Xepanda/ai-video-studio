import React from 'react';
import { SceneMeta } from '../UniversalScene';
import { ThemeConfig } from '../../styles/theme';
import { TweetEmbedCard, TweetEmbedCardProps, TweetMetrics } from './TweetEmbedCard';
import { BinaryBentoCard, BinaryBentoCardProps, BentoSubCard } from './BinaryBentoCard';
import { MinimalHeadlineScene, MinimalHeadlineSceneProps } from './MinimalHeadlineScene';

/**
 * 竖屏科技短视频分镜元数据接口，提供严格类型定义消除内部 any 类型转换
 */
export interface ShortsSceneMeta extends SceneMeta {
  tag?: string;
  dateText?: string;
  date?: string;
  metrics?: TweetMetrics | any;
}

export interface TechNewsShortsSceneProps {
  scene: ShortsSceneMeta;
  activeTheme?: ThemeConfig;
  style?: React.CSSProperties;
}

/**
 * 渲染深色模式下的主题网格/点阵背景覆盖层，同时支持 dots 与 grid 类型
 */
function renderBackgroundOverlay(theme?: ThemeConfig): React.ReactNode {
  if (!theme || !theme.gridOverlay || theme.gridOverlay.type === 'none') {
    return null;
  }

  const overlay = theme.gridOverlay;
  const size = overlay.size && overlay.size > 0 ? overlay.size : 36;
  const color = overlay.color || 'rgba(255, 255, 255, 0.08)';
  const opacity = overlay.opacity ?? 0.7;

  if (overlay.type === 'dots') {
    return (
      <div
        className="technews-overlay-dots"
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(${color} 1.5px, transparent 1.5px)`,
          backgroundSize: `${size}px ${size}px`,
          opacity,
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />
    );
  }

  if (overlay.type === 'grid') {
    return (
      <div
        className="technews-overlay-grid"
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, ${color} 1px, transparent 1px),
            linear-gradient(to bottom, ${color} 1px, transparent 1px)
          `,
          backgroundSize: `${size}px ${size}px`,
          opacity,
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />
    );
  }

  return null;
}

/**
 * 竖屏科技短视频统一调度中心 (TechNewsShortsScene)
 * 接收 ShortsSceneMeta，多态分发至 TweetEmbedCard / BinaryBentoCard / MinimalHeadlineScene，
 * 显式 scene.type 拥有绝对最高路由优先级，并统一保障 1080×1920 竖屏画布比例与底部 220px 交互安全区。
 */
export const TechNewsShortsScene: React.FC<TechNewsShortsSceneProps> = ({
  scene,
  activeTheme,
  style,
}) => {
  // 1. 判断是否反转色彩模式（白底黑字视觉爆破）
  const isInverted = Boolean(
    scene.inverted ||
      (scene.binaryBento && scene.binaryBento.theme === 'light')
  );

  // 2. 映射推文卡片属性 (TweetEmbedCard)
  const renderTweetCard = () => {
    const tweet = scene.tweet || {};
    const tweetProps: TweetEmbedCardProps = {
      authorName: tweet.authorName || 'Tech Insider',
      authorHandle: tweet.authorHandle || '@techinsider',
      avatarUrl: tweet.avatarUrl,
      isVerified: tweet.isVerified !== undefined ? tweet.isVerified : true,
      timeAgo: tweet.timeAgo || 'Just now',
      content: tweet.content || scene.text || scene.title || '',
      highlightWords: tweet.highlightWords || scene.highlightWords,
      subtitle: tweet.subtitle || scene.desc || scene.subtitle,
      metrics: tweet.metrics || scene.metrics,
      theme: activeTheme,
      maxWidth: tweet.maxWidth || 920,
      style: tweet.style,
      className: tweet.className,
    };
    return <TweetEmbedCard {...tweetProps} />;
  };

  // 3. 映射二选一对比卡片属性 (BinaryBentoCard)
  const renderBentoCard = () => {
    const bento = scene.binaryBento || {};
    const leftRaw = bento.leftCard;
    const rightRaw = bento.rightCard;

    const leftCard: BentoSubCard = {
      title: leftRaw?.title || (scene.cards && scene.cards[0]?.title) || '方案 A',
      desc: leftRaw?.desc || (scene.cards && scene.cards[0]?.desc),
      tag: leftRaw?.tag || (scene.cards && scene.cards[0]?.tag),
      pill: leftRaw?.pill,
      icon: leftRaw?.icon || (scene.cards && scene.cards[0]?.icon),
      blocksTotal: leftRaw?.blocksTotal ?? scene.blocksTotal ?? 5,
      blocksActive: leftRaw?.blocksActive ?? scene.blocksActive ?? 2,
      blocksDelay: leftRaw?.blocksDelay,
      highlightWords: leftRaw?.highlightWords || scene.highlightWords,
      accentColor: leftRaw?.accentColor || activeTheme?.accentColor,
    };

    const rightCard: BentoSubCard = {
      title: rightRaw?.title || (scene.cards && scene.cards[1]?.title) || '方案 B',
      desc: rightRaw?.desc || (scene.cards && scene.cards[1]?.desc),
      tag: rightRaw?.tag || (scene.cards && scene.cards[1]?.tag),
      pill: rightRaw?.pill,
      icon: rightRaw?.icon || (scene.cards && scene.cards[1]?.icon),
      blocksTotal: rightRaw?.blocksTotal ?? scene.blocksTotal ?? 5,
      blocksActive: rightRaw?.blocksActive ?? (scene.blocksActive !== undefined ? scene.blocksActive : 5),
      blocksDelay: rightRaw?.blocksDelay,
      highlightWords: rightRaw?.highlightWords || scene.highlightWords,
      accentColor: rightRaw?.accentColor || activeTheme?.accentColor,
    };

    const bentoProps: BinaryBentoCardProps = {
      title: bento.title || scene.title,
      subtitle: bento.subtitle || scene.desc || scene.subtitle,
      leftCard,
      rightCard,
      dividerText: bento.dividerText || '或',
      theme: bento.theme || (isInverted ? 'light' : 'dark'),
      animated: bento.animated !== undefined ? bento.animated : true,
      style: bento.style,
      className: bento.className,
    };
    return <BinaryBentoCard {...bentoProps} />;
  };

  // 4. 映射极简大字报属性 (MinimalHeadlineScene)
  const renderHeadlineCard = () => {
    const headlineProps: MinimalHeadlineSceneProps = {
      title: scene.title || scene.text || '',
      subtitle: scene.subtitle || scene.desc,
      category: scene.category || scene.pill || scene.badge,
      tag: scene.tag || scene.systemTag,
      highlightWords: scene.highlightWords,
      inverted: isInverted,
      dateText: scene.dateText || scene.date,
      accentColor: activeTheme?.accentColor || '#8b5cf6',
      style: {
        backgroundColor: 'transparent',
      },
    };
    return <MinimalHeadlineScene {...headlineProps} />;
  };

  // 5. 显式 scene.type 拥有绝对最高路由优先级，随后回退至数据属性推断
  const sceneType = scene.type || '';
  let contentElement: React.ReactNode = null;

  if (sceneType === 'TweetEmbed') {
    contentElement = renderTweetCard();
  } else if (sceneType === 'BinaryBento') {
    contentElement = renderBentoCard();
  } else if (sceneType === 'MinimalHeadline') {
    contentElement = renderHeadlineCard();
  } else if (scene.tweet) {
    contentElement = renderTweetCard();
  } else if (scene.binaryBento) {
    contentElement = renderBentoCard();
  } else {
    contentElement = renderHeadlineCard();
  }

  // 6. 容器背景与样式设置
  const defaultDarkBg =
    'radial-gradient(ellipse 90% 70% at 50% 25%, #181825 0%, #0c0d14 60%, #050508 100%)';
  const containerBg = isInverted ? '#ffffff' : (activeTheme?.background || defaultDarkBg);

  return (
    <div
      className="technews-shorts-scene"
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box',
        overflow: 'hidden',
        backgroundColor: isInverted ? '#ffffff' : '#09090b',
        background: containerBg,
        color: isInverted ? '#09090b' : '#ffffff',
        ...style,
      }}
    >
      {/* 7. 深色模式下的可选工科网格/点阵覆盖装饰 (支持 dots 与 grid) */}
      {!isInverted && renderBackgroundOverlay(activeTheme)}

      {/* 8. 深色模式下的可选环境顶光 (Spotlight) */}
      {!isInverted && activeTheme?.spotlight && (
        <div
          style={{
            position: 'absolute',
            top: activeTheme.spotlight.position || '-10%',
            left: '50%',
            transform: 'translateX(-50%)',
            width: activeTheme.spotlight.size || '800px',
            height: '600px',
            background: `radial-gradient(ellipse at center, ${activeTheme.spotlight.color} 0%, transparent 70%)`,
            opacity: activeTheme.spotlight.opacity ?? 0.6,
            pointerEvents: 'none',
            zIndex: 1,
          }}
        />
      )}

      {/* 9. 竖屏黄金视觉中心与底部安全区避让容器 (y: 45%~50%，避开抖音右侧互动栏与底部标题) */}
      <div
        className="technews-shorts-content"
        style={{
          flex: 1,
          width: '100%',
          maxWidth: 1000,
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          paddingLeft: 40,
          paddingRight: 40,
          paddingBottom: 220, // 底部 220px 预留交互安全区
          boxSizing: 'border-box',
          zIndex: 2,
        }}
      >
        {contentElement}
      </div>
    </div>
  );
};

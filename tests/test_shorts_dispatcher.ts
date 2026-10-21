import React from 'react';
import ReactDOMServer from 'react-dom/server';
import {
  MinimalHeadlineScene,
  renderHeadlineText,
  TechNewsShortsScene,
} from '../src/components/shorts';
import type {
  MinimalHeadlineSceneProps,
  TechNewsShortsSceneProps,
  ShortsSceneMeta,
} from '../src/components/shorts';
import { THEMES } from '../src/styles/theme';

/**
 * 1. 验证 MinimalHeadlineScene 接口契约与渲染特性
 */
function testMinimalHeadlineScene() {
  console.log('Testing MinimalHeadlineScene interface & rendering features...');

  // 1.1 极简入参契约
  const minimalProps: MinimalHeadlineSceneProps = {
    title: 'Codex 第六天',
  };
  const minimalElem = React.createElement(MinimalHeadlineScene, minimalProps);
  const minimalHtml = ReactDOMServer.renderToStaticMarkup(minimalElem);

  if (!minimalHtml.includes('Codex 第六天')) {
    throw new Error('MinimalHeadlineScene HTML missing title');
  }
  // 默认模式应为黑色背景
  if (!minimalHtml.includes('background-color:#000000')) {
    throw new Error('MinimalHeadlineScene default mode should have black background');
  }

  // 1.2 反转色彩模式 (inverted: true, 白底黑字冲击)
  const invertedProps: MinimalHeadlineSceneProps = {
    title: 'Codex 第六天，迎来最大规则重置！',
    subtitle: '所有配额策略重新洗牌，高频开发者需立即关注。',
    category: 'BREAKING NEWS',
    tag: 'DAY 6 SPECIAL',
    dateText: '2026.10.11',
    highlightWords: ['规则重置', 'Codex'],
    inverted: true,
  };
  const invertedElem = React.createElement(MinimalHeadlineScene, invertedProps);
  const invertedHtml = ReactDOMServer.renderToStaticMarkup(invertedElem);

  // 验证反转模式背景白底与黑字
  if (!invertedHtml.includes('background-color:#ffffff')) {
    throw new Error('Inverted MinimalHeadlineScene should have white background');
  }
  if (!invertedHtml.includes('color:#09090b')) {
    throw new Error('Inverted MinimalHeadlineScene should have black text (#09090b)');
  }
  if (!invertedHtml.includes('BREAKING NEWS')) {
    throw new Error('Inverted MinimalHeadlineScene missing category pill text');
  }
  if (!invertedHtml.includes('DAY 6 SPECIAL')) {
    throw new Error('Inverted MinimalHeadlineScene missing tag');
  }
  if (!invertedHtml.includes('2026.10.11')) {
    throw new Error('Inverted MinimalHeadlineScene missing dateText');
  }
  // 验证关键词胶囊包裹（反转模式使用深紫与高反差边框）
  if (!invertedHtml.includes('规则重置') || !invertedHtml.includes('color:#6d28d9')) {
    throw new Error('Inverted MinimalHeadlineScene missing high-contrast keyword capsules');
  }

  // 1.3 自定义 accentColor 动态计算验证
  const customAccentProps: MinimalHeadlineSceneProps = {
    title: '全新架构跃迁',
    highlightWords: ['架构跃迁'],
    accentColor: '#38bdf8', // 天蓝色
    inverted: false,
  };
  const customAccentHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MinimalHeadlineScene, customAccentProps)
  );

  // 应该动态生成 rgba(56, 189, 248, ...)
  if (!customAccentHtml.includes('rgba(56, 189, 248, 0.22)')) {
    throw new Error('renderHeadlineText failed to calculate dynamic rgba from custom accentColor');
  }
  if (!customAccentHtml.includes('#38bdf8')) {
    throw new Error('renderHeadlineText failed to apply custom accentColor to capsule text');
  }

  // 1.4 关键词降序排序匹配验证（防止短词前缀吞噬长词）
  const overlapText = 'OpenAI 规则重置方案与规则调整细节';
  const overlapNodes = renderHeadlineText(overlapText, ['规则', '规则重置'], false);
  const overlapHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement('div', null, overlapNodes)
  );

  // '规则重置' 必须作为完整胶囊渲染，而不是被 '规则' 拆散
  if (!overlapHtml.includes('>规则重置</span>')) {
    throw new Error('renderHeadlineText failed to prioritize longer keyword over shorter prefix');
  }

  console.log('✓ MinimalHeadlineScene tests passed.');
}

/**
 * 2. 验证 TechNewsShortsScene 多态路由分发与安全区控制
 */
function testTechNewsShortsSceneDispatcher() {
  console.log('Testing TechNewsShortsScene polymorphic routing & safe-area controls...');

  const activeTheme = THEMES['linear-graphite'];

  // 2.1 路由分支 1：TweetEmbed 多态分发
  const tweetScene: ShortsSceneMeta = {
    id: 'scene_tweet_01',
    type: 'TweetEmbed',
    durationInFrames: 120,
    tweet: {
      authorName: 'Guillermo Rauch',
      authorHandle: '@rauchg',
      content: 'Shipping the new Next.js compiler update today.',
      highlightWords: ['Next.js', 'compiler'],
      subtitle: 'Next.js 编译器重大更新今日正式发布。',
      metrics: {
        likes: 4200,
        retweets: 512,
        replies: 88,
        views: 240000,
      },
    },
  };

  const tweetElem = React.createElement(TechNewsShortsScene, {
    scene: tweetScene,
    activeTheme,
  });
  const tweetHtml = ReactDOMServer.renderToStaticMarkup(tweetElem);

  // 验证容器满填充画布与底部安全区避让:
  // 1080x1920 竖屏尺寸由 Remotion Composition 提供, 组件以 width/height:100% + inset:0 满填充承接;
  // SSR (renderToStaticMarkup) 环境下 useVideoConfig 回退横屏 1920x1080,
  // 故安全区走横屏分支 padding-bottom:100px (竖屏 220px 由 Composition 竖屏尺寸驱动, 此处无法构造)。
  if (!tweetHtml.includes('width:100%') || !tweetHtml.includes('height:100%')) {
    throw new Error('TechNewsShortsScene container missing full-fill canvas constraints');
  }
  if (!tweetHtml.includes('padding-bottom:100px')) {
    throw new Error('TechNewsShortsScene missing bottom safe-area padding (SSR landscape fallback)');
  }
  if (!tweetHtml.includes('Guillermo Rauch') || !tweetHtml.includes('@rauchg')) {
    throw new Error('TechNewsShortsScene failed to route TweetEmbedCard');
  }
  if (!tweetHtml.includes('4.2K') || !tweetHtml.includes('240K')) {
    throw new Error('TechNewsShortsScene TweetEmbedCard metrics formatting missing');
  }

  // 2.2 路由分支 2：BinaryBento 多态分发
  const bentoScene: ShortsSceneMeta = {
    id: 'scene_bento_01',
    type: 'BinaryBento',
    durationInFrames: 150,
    binaryBento: {
      title: '配额机制二选一',
      subtitle: '选择最契合开发流的工作模式',
      leftCard: {
        title: '每日自然刷新',
        desc: '每早 4 点释放 1 格配额',
        blocksTotal: 5,
        blocksActive: 2,
        accentColor: '#38bdf8',
      },
      rightCard: {
        title: '重置卡即时补满',
        desc: '一次性回满全部 5 格配额',
        blocksTotal: 5,
        blocksActive: 5,
        pill: '即刻生效',
        accentColor: '#8b5cf6',
      },
      dividerText: '或',
    },
  };

  const bentoElem = React.createElement(TechNewsShortsScene, {
    scene: bentoScene,
    activeTheme,
  });
  const bentoHtml = ReactDOMServer.renderToStaticMarkup(bentoElem);

  if (!bentoHtml.includes('配额机制二选一')) {
    throw new Error('TechNewsShortsScene failed to route BinaryBentoCard title');
  }
  if (!bentoHtml.includes('每日自然刷新') || !bentoHtml.includes('重置卡即时补满')) {
    throw new Error('TechNewsShortsScene failed to render BinaryBento sub-cards');
  }
  if (!bentoHtml.includes('或')) {
    throw new Error('TechNewsShortsScene BinaryBentoCard missing divider text "或"');
  }

  // 2.3 路由分支 3：MinimalHeadline 多态分发 (常规深色模式)
  const headlineScene: ShortsSceneMeta = {
    id: 'scene_headline_01',
    type: 'MinimalHeadline',
    durationInFrames: 90,
    title: 'AI 编程助手\n进入全新分水岭',
    desc: '底层大模型与本地 IDE 的深度协同，正在彻底重塑代码开发范式。',
    pill: 'SPECIAL REPORT',
    highlightWords: ['分水岭', '彻底重塑'],
    inverted: false,
  };

  const headlineElem = React.createElement(TechNewsShortsScene, {
    scene: headlineScene,
    activeTheme,
  });
  const headlineHtml = ReactDOMServer.renderToStaticMarkup(headlineElem);

  if (!headlineHtml.includes('AI 编程助手') || !headlineHtml.includes('SPECIAL REPORT')) {
    throw new Error('TechNewsShortsScene failed to route MinimalHeadlineScene');
  }
  if (!headlineHtml.includes('分水岭')) {
    throw new Error('TechNewsShortsScene MinimalHeadlineScene missing highlighted keyword');
  }

  // 2.4 路由分支 4：MinimalHeadline 反转色彩模式 (inverted: true, 全屏白色冲击)
  const invertedHeadlineScene: ShortsSceneMeta = {
    id: 'scene_headline_inverted',
    type: 'MinimalHeadline',
    durationInFrames: 60,
    title: 'Codex 极限重置！',
    category: 'BREAKING',
    highlightWords: ['极限重置'],
    inverted: true,
  };

  const invertedHeadlineElem = React.createElement(TechNewsShortsScene, {
    scene: invertedHeadlineScene,
    activeTheme,
  });
  const invertedHeadlineHtml = ReactDOMServer.renderToStaticMarkup(invertedHeadlineElem);

  // 深色主题 (linear-graphite) + inverted: 容器为高亮纯白底爆破 (#fbf8f1), 文本深岩黑 (#0f172a)
  if (!invertedHeadlineHtml.includes('background-color:#fbf8f1')) {
    throw new Error('Inverted TechNewsShortsScene container must be white paper background (#fbf8f1)');
  }
  if (!invertedHeadlineHtml.includes('color:#0f172a')) {
    throw new Error('Inverted TechNewsShortsScene text must be dark slate (#0f172a)');
  }
  if (!invertedHeadlineHtml.includes('BREAKING')) {
    throw new Error('Inverted TechNewsShortsScene missing category');
  }

  // 2.5 核心审查点验证：显式 scene.type 拥有绝对最高优先级
  // 即使附带了 scene.tweet 对象，但显式声明 type: 'MinimalHeadline' 时，必须严格渲染大字报
  const explicitPriorityScene: ShortsSceneMeta = {
    id: 'scene_explicit_priority',
    type: 'MinimalHeadline',
    durationInFrames: 90,
    title: '显式类型最高优先级',
    tweet: {
      authorName: 'Ghost Tweet',
      authorHandle: '@ghost',
      content: 'This should not be rendered because type is MinimalHeadline',
    },
  };

  const priorityHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TechNewsShortsScene, {
      scene: explicitPriorityScene,
      activeTheme,
    })
  );

  if (!priorityHtml.includes('显式类型最高优先级')) {
    throw new Error('Explicit scene.type MinimalHeadline was not rendered');
  }
  if (priorityHtml.includes('Ghost Tweet')) {
    throw new Error('Explicit scene.type did not take precedence over implicit scene.tweet detection');
  }

  // 2.6 隐式属性推断回退验证 (未显式指定 scene.type，但含有 scene.tweet 或 scene.binaryBento)
  const implicitTweetScene: ShortsSceneMeta = {
    id: 'scene_implicit_tweet',
    durationInFrames: 90,
    tweet: {
      authorName: 'Implicit Author',
      authorHandle: '@implicit',
      content: 'Implicitly dispatched tweet content',
    },
  };
  const implicitTweetHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TechNewsShortsScene, {
      scene: implicitTweetScene,
      activeTheme,
    })
  );
  if (!implicitTweetHtml.includes('Implicit Author')) {
    throw new Error('Implicit tweet detection fallback failed');
  }

  // 2.7 主题网格覆盖层支持验证 (dots 与 grid)
  const gridTheme = {
    ...activeTheme,
    gridOverlay: {
      type: 'grid' as const,
      color: 'rgba(56, 189, 248, 0.1)',
      size: 40,
      opacity: 0.8,
    },
  };
  const gridSceneHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TechNewsShortsScene, {
      scene: headlineScene,
      activeTheme: gridTheme,
    })
  );
  if (!gridSceneHtml.includes('technews-overlay-grid')) {
    throw new Error('TechNewsShortsScene failed to render linear grid overlay');
  }

  // 2.8 容错与兜底：传入空属性或未知类型的 scene，确保平稳降级绝不抛出异常
  const emptyScene: ShortsSceneMeta = {
    id: 'scene_empty_fallback',
    durationInFrames: 30,
  };

  const emptyElem = React.createElement(TechNewsShortsScene, {
    scene: emptyScene,
  });
  const emptyHtml = ReactDOMServer.renderToStaticMarkup(emptyElem);

  if (!emptyHtml || !emptyHtml.includes('technews-shorts-scene')) {
    throw new Error('TechNewsShortsScene failed graceful fallback for empty SceneMeta');
  }

  console.log('✓ TechNewsShortsScene dispatcher tests passed.');
}

/**
 * 执行全量验证测试
 */
function runAllShortsDispatcherTests() {
  console.log('====================================================');
  console.log('Running TechNews Shorts Dispatcher & Headline Tests');
  console.log('====================================================');

  testMinimalHeadlineScene();
  testTechNewsShortsSceneDispatcher();

  console.log('====================================================');
  console.log('✓ All TechNews Shorts Dispatcher & Headline tests passed cleanly!');
  console.log('====================================================');
}

runAllShortsDispatcherTests();

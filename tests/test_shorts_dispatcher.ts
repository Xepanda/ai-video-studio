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
} from '../src/components/shorts';
import type { SceneMeta } from '../src/components/UniversalScene';
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

  // 1.3 关键词降序排序匹配验证（防止短词前缀吞噬长词）
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
  const tweetScene: SceneMeta = {
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

  // 验证 1080x1920 容器尺寸、220px 底部安全区与推文内容渲染
  if (!tweetHtml.includes('width:1080px') || !tweetHtml.includes('height:1920px')) {
    throw new Error('TechNewsShortsScene container missing 1080x1920 vertical canvas constraints');
  }
  if (!tweetHtml.includes('padding-bottom:220px')) {
    throw new Error('TechNewsShortsScene missing 220px bottom safe-area padding');
  }
  if (!tweetHtml.includes('Guillermo Rauch') || !tweetHtml.includes('@rauchg')) {
    throw new Error('TechNewsShortsScene failed to route TweetEmbedCard');
  }
  if (!tweetHtml.includes('4.2K') || !tweetHtml.includes('240K')) {
    throw new Error('TechNewsShortsScene TweetEmbedCard metrics formatting missing');
  }

  // 2.2 路由分支 2：BinaryBento 多态分发
  const bentoScene: SceneMeta = {
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
  const headlineScene: SceneMeta = {
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
  const invertedHeadlineScene: SceneMeta = {
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

  if (!invertedHeadlineHtml.includes('background-color:#ffffff')) {
    throw new Error('Inverted TechNewsShortsScene container must be white background (#ffffff)');
  }
  if (!invertedHeadlineHtml.includes('color:#09090b')) {
    throw new Error('Inverted TechNewsShortsScene text must be dark (#09090b)');
  }
  if (!invertedHeadlineHtml.includes('BREAKING')) {
    throw new Error('Inverted TechNewsShortsScene missing category');
  }

  // 2.5 容错与兜底：传入空属性或未知类型的 scene，确保平稳降级绝不抛出异常
  const emptyScene: SceneMeta = {
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

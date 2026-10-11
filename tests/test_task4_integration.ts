import React from 'react';
import ReactDOMServer from 'react-dom/server';
import { UniversalScene, SceneMeta } from '../src/components/UniversalScene';
import { RemotionRoot, MainComposition, MasterVideo } from '../src/Root';

function testUniversalSceneRouting() {
  console.log('Testing UniversalScene shorts routing conditions...');

  // 1. scene.type === 'TechNewsShorts'
  const sceneTechNewsShorts: SceneMeta = {
    id: 's1',
    type: 'TechNewsShorts',
    title: '科技快讯头条',
    durationInFrames: 90,
  };
  const html1 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneTechNewsShorts })
  );
  if (!html1.includes('technews-shorts-scene')) {
    throw new Error('UniversalScene did not route TechNewsShorts to TechNewsShortsScene');
  }

  // 2. scene.type === 'TechNews'
  const sceneTechNews: SceneMeta = {
    id: 's2',
    type: 'TechNews',
    title: 'AI 资讯简报',
    durationInFrames: 90,
  };
  const html2 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneTechNews })
  );
  if (!html2.includes('technews-shorts-scene')) {
    throw new Error('UniversalScene did not route TechNews to TechNewsShortsScene');
  }

  // 3. scene.type === 'TweetEmbed'
  const sceneTweetEmbed: SceneMeta = {
    id: 's3',
    type: 'TweetEmbed',
    durationInFrames: 90,
    tweet: {
      authorName: 'Alex River',
      authorHandle: '@ariver',
      content: 'Codex 6.0 drops today with zero latency streaming.',
    },
  };
  const html3 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneTweetEmbed })
  );
  if (!html3.includes('technews-shorts-scene') || !html3.includes('@ariver')) {
    throw new Error('UniversalScene did not route TweetEmbed to TechNewsShortsScene');
  }

  // 4. scene.type === 'BinaryBento'
  const sceneBinaryBento: SceneMeta = {
    id: 's4',
    type: 'BinaryBento',
    durationInFrames: 90,
    title: '新旧方案对比',
    binaryBento: {
      leftCard: { title: '旧版本方案', desc: '每月手动刷新额度' },
      rightCard: { title: '新版本重置卡', desc: '即用即充灵活生效' },
    },
  };
  const html4 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneBinaryBento })
  );
  if (!html4.includes('technews-shorts-scene') || !html4.includes('新版本重置卡')) {
    throw new Error('UniversalScene did not route BinaryBento to TechNewsShortsScene');
  }

  // 5. scene.type === 'MinimalHeadline'
  const sceneMinimalHeadline: SceneMeta = {
    id: 's5',
    type: 'MinimalHeadline',
    title: '规则大重置！',
    category: 'BREAKING',
    durationInFrames: 90,
    inverted: true,
  };
  const html5 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneMinimalHeadline })
  );
  if (!html5.includes('technews-shorts-scene') || !html5.includes('规则大重置！')) {
    throw new Error('UniversalScene did not route MinimalHeadline to TechNewsShortsScene');
  }

  // 6. scene.tweet is present without explicit type
  const sceneWithTweetData: SceneMeta = {
    id: 's6',
    durationInFrames: 90,
    tweet: {
      authorName: 'Sam Altman',
      authorHandle: '@sama',
      content: 'AGI is getting closer every day.',
    },
  };
  const html6 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneWithTweetData })
  );
  if (!html6.includes('technews-shorts-scene') || !html6.includes('@sama')) {
    throw new Error('UniversalScene did not route scene with tweet property to TechNewsShortsScene');
  }

  // 7. scene.binaryBento is present without explicit type
  const sceneWithBentoData: SceneMeta = {
    id: 's7',
    durationInFrames: 90,
    title: '架构二选一',
    binaryBento: {
      leftCard: { title: 'REST API' },
      rightCard: { title: 'gRPC Stream' },
    },
  };
  const html7 = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: sceneWithBentoData })
  );
  if (!html7.includes('technews-shorts-scene') || !html7.includes('gRPC Stream')) {
    throw new Error('UniversalScene did not route scene with binaryBento property to TechNewsShortsScene');
  }

  console.log('✓ UniversalScene routing checks passed cleanly.');
}

function testRootCompositionRegistration() {
  console.log('Testing Root.tsx RemotionRoot and Composition registration...');

  if (MainComposition !== MasterVideo) {
    throw new Error('MainComposition should reference MasterVideo');
  }

  const rootElem = React.createElement(RemotionRoot);
  // RemotionRoot returns a React Fragment with Compositions
  const children = (rootElem.type as any)().props.children;
  const compositions = React.Children.toArray(children) as React.ReactElement<any>[];

  const techNewsComp = compositions.find((c) => c.props.id === 'TechNewsShorts');
  if (!techNewsComp) {
    throw new Error('Root.tsx RemotionRoot does not have TechNewsShorts Composition');
  }

  if (techNewsComp.props.width !== 1080) {
    throw new Error(`Expected TechNewsShorts width 1080, got ${techNewsComp.props.width}`);
  }
  if (techNewsComp.props.height !== 1920) {
    throw new Error(`Expected TechNewsShorts height 1920, got ${techNewsComp.props.height}`);
  }
  if (techNewsComp.props.fps !== 30) {
    throw new Error(`Expected TechNewsShorts fps 30, got ${techNewsComp.props.fps}`);
  }
  if (techNewsComp.props.component !== MainComposition) {
    throw new Error('Expected TechNewsShorts component to be MainComposition');
  }

  console.log('✓ Root.tsx Composition registration checks passed cleanly.');
}

function runAll() {
  testUniversalSceneRouting();
  testRootCompositionRegistration();
  console.log('====================================================');
  console.log('✓ Task 4 Integration tests passed 100% cleanly!');
  console.log('====================================================');
}

runAll();

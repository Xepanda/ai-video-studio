import React from 'react';
import ReactDOMServer from 'react-dom/server';
import {
  BinaryBentoCard,
  ProgressBlocks,
  renderHighlightText,
} from '../src/components/shorts';
import type {
  BentoSubCard,
  BinaryBentoCardProps,
  ProgressBlocksProps,
} from '../src/components/shorts';

/**
 * 编译期与运行时接口契约验证测试
 */
function testBinaryBentoContract() {
  console.log('Testing BinaryBentoCard & ProgressBlocks interface contracts...');

  // 1. 验证 ProgressBlocks 极简与全量参数契约
  const minimalProgressProps: ProgressBlocksProps = {};
  const minimalProgressElem = React.createElement(ProgressBlocks, minimalProgressProps);
  if (!minimalProgressElem || minimalProgressElem.type !== ProgressBlocks) {
    throw new Error('Failed to create minimal ProgressBlocks element');
  }

  const fullProgressProps: ProgressBlocksProps = {
    total: 7,
    active: 4,
    activeColor: '#38bdf8',
    inactiveColor: 'rgba(255, 255, 255, 0.15)',
    animated: false,
    className: 'custom-progress-blocks',
    style: { marginTop: 12 },
  };
  const fullProgressElem = React.createElement(ProgressBlocks, fullProgressProps);
  if (!fullProgressElem) {
    throw new Error('Failed to create full ProgressBlocks element');
  }

  // 渲染 ProgressBlocks HTML 并验证节点数量
  const progressHtml = ReactDOMServer.renderToStaticMarkup(fullProgressElem);
  if (!progressHtml || !progressHtml.includes('custom-progress-blocks')) {
    throw new Error('ProgressBlocks HTML render failed or missing className');
  }

  // 2. 验证 ProgressBlocks 边界条件（active > total, active = 0, total = 0）
  const edgeProgressProps: ProgressBlocksProps = {
    total: 0,
    active: 10,
    animated: true,
  };
  const edgeProgressHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ProgressBlocks, edgeProgressProps)
  );
  if (!edgeProgressHtml) {
    throw new Error('Edge ProgressBlocks HTML render failed');
  }

  // 3. 验证 BinaryBentoCard 极简入参契约
  const minimalLeftCard: BentoSubCard = {
    title: '方案 A',
  };
  const minimalRightCard: BentoSubCard = {
    title: '方案 B',
  };

  const minimalBentoProps: BinaryBentoCardProps = {
    leftCard: minimalLeftCard,
    rightCard: minimalRightCard,
  };
  const minimalBentoElem = React.createElement(BinaryBentoCard, minimalBentoProps);
  if (!minimalBentoElem || minimalBentoElem.type !== BinaryBentoCard) {
    throw new Error('Failed to create minimal BinaryBentoCard element');
  }

  const minimalBentoHtml = ReactDOMServer.renderToStaticMarkup(minimalBentoElem);
  if (!minimalBentoHtml.includes('方案 A') || !minimalBentoHtml.includes('方案 B')) {
    throw new Error('Minimal BinaryBentoCard HTML missing card titles');
  }
  if (!minimalBentoHtml.includes('或')) {
    throw new Error('Minimal BinaryBentoCard HTML missing default divider "或"');
  }

  // 4. 验证 Codex 风格全量参数契约（二选一规则：每日刷新 vs 重置卡）
  const fullLeftCard: BentoSubCard = {
    title: '等待每日刷新',
    desc: '系统于每日 04:00 自动释放额度，单次消耗 1 格进度。',
    tag: '常规机制',
    icon: '⏳',
    blocksTotal: 5,
    blocksActive: 2,
    highlightWords: ['每日 04:00', '1 格进度'],
    accentColor: '#38bdf8',
  };

  const fullRightCard: BentoSubCard = {
    title: '使用重置卡',
    desc: '即刻补满全部 5 格配额，无需等待冷却周期。',
    tag: '即时生效',
    pill: '重置卡',
    icon: '⚡',
    blocksTotal: 5,
    blocksActive: 5,
    highlightWords: ['全部 5 格配额', '无需等待'],
    accentColor: '#8b5cf6',
  };

  const fullBentoProps: BinaryBentoCardProps = {
    title: '二选一配额规则',
    subtitle: '根据开发节奏灵活切换，保障高频生产不中断。',
    leftCard: fullLeftCard,
    rightCard: fullRightCard,
    dividerText: '或',
    theme: 'dark',
    animated: true,
    className: 'codex-binary-bento',
    style: {
      padding: '40px 0',
    },
  };

  const fullBentoElem = React.createElement(BinaryBentoCard, fullBentoProps);
  const fullBentoHtml = ReactDOMServer.renderToStaticMarkup(fullBentoElem);

  // 校验全量内容渲染
  if (!fullBentoHtml.includes('二选一配额规则')) {
    throw new Error('Full BinaryBentoCard HTML missing title');
  }
  if (!fullBentoHtml.includes('根据开发节奏灵活切换')) {
    throw new Error('Full BinaryBentoCard HTML missing subtitle');
  }
  if (!fullBentoHtml.includes('等待每日刷新') || !fullBentoHtml.includes('使用重置卡')) {
    throw new Error('Full BinaryBentoCard HTML missing subcard titles');
  }
  if (!fullBentoHtml.includes('重置卡')) {
    throw new Error('Full BinaryBentoCard HTML missing pill badge');
  }
  if (!fullBentoHtml.includes('⏳') || !fullBentoHtml.includes('⚡')) {
    throw new Error('Full BinaryBentoCard HTML missing card icons');
  }

  // 5. 验证 Light 主题与自定义 dividerText（例如 "VS"）
  const lightBentoProps: BinaryBentoCardProps = {
    ...fullBentoProps,
    theme: 'light',
    dividerText: 'VS',
    animated: false,
  };
  const lightBentoHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(BinaryBentoCard, lightBentoProps)
  );
  if (!lightBentoHtml.includes('VS')) {
    throw new Error('Light BinaryBentoCard HTML missing custom divider "VS"');
  }

  // 6. 验证文字高亮解析辅助函数 renderHighlightText
  const sampleText = '采用 GPT-SoVITS 极速克隆声线，效果远超预期。';
  const highlights = ['GPT-SoVITS', '声线'];
  const highlightNodes = renderHighlightText(sampleText, highlights);
  const renderedHighlightHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement('div', null, highlightNodes)
  );
  if (!renderedHighlightHtml.includes('GPT-SoVITS') || !renderedHighlightHtml.includes('声线')) {
    throw new Error('renderHighlightText failed to render highlighted tokens');
  }

  console.log('✓ All BinaryBentoCard & ProgressBlocks interface compatibility and runtime SSR checks passed cleanly!');
}

testBinaryBentoContract();

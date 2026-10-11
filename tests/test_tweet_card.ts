import React from 'react';
import { TweetEmbedCard, formatMetric } from '../src/components/shorts';
import type { TweetEmbedCardProps, TweetMetrics } from '../src/components/shorts';

/**
 * 编译期与运行时接口契约验证测试
 */
function testTweetEmbedCardContract() {
  console.log('Testing TweetEmbedCard interface contract...');

  // 1. 验证极简入参契约
  const minimalProps: TweetEmbedCardProps = {
    authorName: 'Tibo',
    authorHandle: '@thdxllaux',
    content: 'Day 6: Reset',
  };

  const minimalElement = React.createElement(TweetEmbedCard, minimalProps);
  if (!minimalElement || minimalElement.type !== TweetEmbedCard) {
    throw new Error('Failed to create minimal TweetEmbedCard element');
  }

  // 2. 验证全量参数契约 (包括数字格式 metrics)
  const fullNumericMetrics: TweetMetrics = {
    replies: 42,
    retweets: 128,
    likes: 3400,
    views: 150000,
  };

  const fullPropsWithNumericMetrics: TweetEmbedCardProps = {
    authorName: 'Tibo',
    authorHandle: '@thdxllaux',
    avatarUrl: 'https://pbs.twimg.com/profile_images/tibo.jpg',
    isVerified: true,
    timeAgo: '14h',
    content: 'Day 6: Reset\nCodex has completely surpassed my expectations.',
    highlightWords: ['Reset', 'Codex'],
    subtitle: '第6天：全面重置，Codex 性能远超预期。',
    metrics: fullNumericMetrics,
    theme: {
      cardBg: '#000000',
      cardBorder: '1px solid rgba(255, 255, 255, 0.12)',
      accentColor: '#8b5cf6',
      subtitleHighlightColor: '#c084fc',
    },
    maxWidth: 880,
    className: 'custom-tweet-card',
    style: {
      marginTop: 40,
      opacity: 1,
    },
  };

  const fullElement = React.createElement(TweetEmbedCard, fullPropsWithNumericMetrics);
  if (!fullElement || fullElement.props.authorName !== 'Tibo') {
    throw new Error('Failed to create full TweetEmbedCard element with numeric metrics');
  }

  // 3. 验证字符串格式 metrics 契约
  const stringMetrics: TweetMetrics = {
    replies: '42',
    retweets: '128',
    likes: '3.4K',
    views: '150K',
  };

  const fullPropsWithStringMetrics: TweetEmbedCardProps = {
    ...minimalProps,
    isVerified: false,
    metrics: stringMetrics,
  };

  const stringMetricsElement = React.createElement(TweetEmbedCard, fullPropsWithStringMetrics);
  if (!stringMetricsElement) {
    throw new Error('Failed to create TweetEmbedCard element with string metrics');
  }

  // 4. 验证数值格式化工具函数 formatMetric
  const tests: Array<[string | number | undefined, string]> = [
    [undefined, ''],
    ['', ''],
    ['12.5K', '12.5K'],
    [500, '500'],
    [1000, '1K'],
    [3400, '3.4K'],
    [150000, '150K'],
    [1000000, '1M'],
    [2500000, '2.5M'],
  ];

  for (const [input, expected] of tests) {
    const output = formatMetric(input);
    if (output !== expected) {
      throw new Error(`formatMetric(${input}) returned "${output}", expected "${expected}"`);
    }
  }

  console.log('✓ All TweetEmbedCard interface compatibility checks passed cleanly!');
}

testTweetEmbedCardContract();

import React from 'react';
import ReactDOMServer from 'react-dom/server';
import {
  IdeWindowScene,
  AsciicastPlayer,
  CommentThreadScene,
  TrendingRankCard,
} from '../src/components/shorts';
import type {
  IdeWindowProps,
  AsciicastProps,
  CommentThreadProps,
  TrendingRankProps,
} from '../src/components/shorts';
import { TweetEmbedCard } from '../src/components/shorts';
import { SafeImage } from '../src/components/shorts/SafeImage';
import { safeLoadDemoTimeline } from '../src/utils/safeDemoTimeline';
import { UniversalScene } from '../src/components/UniversalScene';
import type { SceneMeta } from '../src/components/UniversalScene';

/**
 * W7-8 场景二/三: 工程演示与热点组件族契约测试
 * 覆盖: IdeWindowScene (IDE) / AsciicastPlayer (终端回放) /
 *       CommentThreadScene (评论串) / TrendingRankCard (热点榜+trending动画) /
 *       TweetEmbedCard 长文截断 及 UniversalScene 路由注册
 */

/**
 * 1. IdeWindowScene: 文件树 + 标签页 + 语法高亮
 */
function testIdeWindowScene() {
  console.log('Testing IdeWindowScene (IDE mockup)...');

  const props: IdeWindowProps = {
    title: '看内核里的三次握手',
    category: 'CODE DEEP DIVE',
    files: [
      {
        name: 'tcp_connect.c',
        path: 'net/ipv4',
        lang: 'c',
        content: 'int tcp_v4_connect(struct sock *sk) {\n  tcp_set_state(sk, TCP_SYN_SENT);\n}',
        active: true,
      },
      { name: 'main.py', lang: 'py', content: 'print("hello")' },
    ],
  };
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(IdeWindowScene, props));

  // 文件树: 路径 + 双文件
  if (!html.includes('net/ipv4/') || !html.includes('tcp_connect.c') || !html.includes('main.py')) {
    throw new Error('IdeWindowScene file tree contract broken');
  }
  // 标签页 (活动标签下边框强调色)
  if (!html.includes('border-bottom:2px solid #38bdf8')) {
    throw new Error('IdeWindowScene missing tab bar');
  }
  // 语法高亮: C 关键字 (keyword 紫色)
  if (!html.includes('#c084fc') || !html.includes('TCP_SYN_SENT')) {
    throw new Error('IdeWindowScene syntax highlight contract broken');
  }
  // 窗口 chrome + 行号
  if (!html.includes('#ef4444')) {
    throw new Error('IdeWindowScene missing window chrome dots');
  }
  if (!html.includes('CODE DEEP DIVE')) {
    throw new Error('IdeWindowScene missing category');
  }

  // 缺失数据兜底
  const emptyHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IdeWindowScene, { files: [] })
  );
  if (!emptyHtml.includes('files')) {
    throw new Error('IdeWindowScene missing-data fallback broken');
  }

  console.log('✓ IdeWindowScene tests passed.');
}

/**
 * 2. AsciicastPlayer: 事件流回放与 ANSI 剥离
 */
function testAsciicastPlayer() {
  console.log('Testing AsciicastPlayer (asciicast playback)...');

  const props: AsciicastProps = {
    title: 'yt-dlp --version',
    category: 'REAL TERMINAL SESSION',
    events: [
      { time: 0, type: 'o', data: '$ yt-dlp --version\r\n' },
      { time: 0.5, type: 'o', data: '2026.10.24\r\n' },
    ],
  };
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(AsciicastPlayer, props));

  // 首事件 (shell 提示符) 在 SSR frame=0 始终可见 (可观测契约)
  if (!html.includes('$ yt-dlp --version')) {
    throw new Error('AsciicastPlayer first-event visibility contract broken');
  }
  if (!html.includes('REAL TERMINAL SESSION')) {
    throw new Error('AsciicastPlayer missing category');
  }
  if (!html.includes('100×24')) {
    throw new Error('AsciicastPlayer missing cols/rows chrome');
  }

  // ANSI 控制序列被剥离 (可见字符保留)
  const ansiHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(AsciicastPlayer, {
      events: [{ time: 0, type: 'o', data: '\u001b[32mgreen text\u001b[0m' }],
    })
  );
  if (ansiHtml.includes('\u001b[')) {
    throw new Error('AsciicastPlayer failed to strip ANSI control sequences');
  }
  if (!ansiHtml.includes('green text')) {
    throw new Error('AsciicastPlayer stripped visible characters');
  }

  // 空事件流兜底
  const emptyHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(AsciicastPlayer, { events: [] })
  );
  if (!emptyHtml.includes('等待终端事件流')) {
    throw new Error('AsciicastPlayer empty-events fallback broken');
  }

  console.log('✓ AsciicastPlayer tests passed.');
}

/**
 * 3. CommentThreadScene: 评论串契约
 */
function testCommentThreadScene() {
  console.log('Testing CommentThreadScene (comment thread)...');

  const props: CommentThreadProps = {
    title: '评论区怎么看',
    category: 'COMMUNITY REACTION',
    comments: [
      { author: '硬件宅小明', content: '原来如此，讲得太清楚了', likes: 1520, timeAgo: '2小时前' },
      { author: 'UP主', content: '置顶: 下期讲 DMA', likes: null, isAuthor: true },
    ],
  };
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(CommentThreadScene, props));

  if (!html.includes('硬件宅小明') || !html.includes('原来如此')) {
    throw new Error('CommentThreadScene missing comment content');
  }
  // 点赞数: 有值格式化, null 诚实标注 (禁 0 填充)
  if (!html.includes('1,520')) {
    throw new Error('CommentThreadScene likes formatting broken');
  }
  if (!html.includes('赞数缺失')) {
    throw new Error('CommentThreadScene must honestly mark missing likes');
  }
  // UP 主标记
  if (!html.includes('UP主')) {
    throw new Error('CommentThreadScene missing author badge');
  }

  // 空数据兜底
  const emptyHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(CommentThreadScene, { comments: [] })
  );
  if (!emptyHtml.includes('comments')) {
    throw new Error('CommentThreadScene missing-data fallback broken');
  }

  console.log('✓ CommentThreadScene tests passed.');
}

/**
 * 4. TrendingRankCard: 热点榜 + trending 动画契约
 */
function testTrendingRankCard() {
  console.log('Testing TrendingRankCard (trending rank + animation)...');

  const props: TrendingRankProps = {
    rank: 1,
    title: '某发布会公布新一代芯片工艺',
    heat: 4800000,
    source: 'weibo',
    tag: '沸',
    category: 'REALTIME HOTSPOT',
  };
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(TrendingRankCard, props));

  if (!html.includes('某发布会公布新一代芯片工艺')) {
    throw new Error('TrendingRankCard missing title');
  }
  // 排名徽章 + Top3 红色
  if (!html.includes('#f43f5e')) {
    throw new Error('TrendingRankCard top-rank badge accent broken');
  }
  // 热度值千分位 + 来源中文映射
  if (!html.includes('4,800,000') || !html.includes('微博热搜')) {
    throw new Error('TrendingRankCard heat/source contract broken');
  }
  // trending 火焰
  if (!html.includes('🔥')) {
    throw new Error('TrendingRankCard missing trending flame');
  }

  // heat 缺失: 诚实标注, 不画假热度条 (数据诚信)
  const nullHeatHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TrendingRankCard, { rank: 5, title: '无热度话题', heat: null, source: 'bilibili' })
  );
  if (!nullHeatHtml.includes('热度值缺失')) {
    throw new Error('TrendingRankCard must honestly mark missing heat');
  }
  if (nullHeatHtml.includes('实时热度')) {
    throw new Error('TrendingRankCard must not render heat bar when heat is null');
  }

  console.log('✓ TrendingRankCard tests passed.');
}

/**
 * 5. TweetEmbedCard: 长文截断契约 (W7-8 场景三)
 */
function testTweetTruncation() {
  console.log('Testing TweetEmbedCard long-content truncation...');

  const baseProps = {
    authorName: 'Tibo',
    authorHandle: '@thdxllaux',
    content: '',
  };

  // 默认不截断: 长文完整渲染, 无截断标记
  const longContent = '第一行内容。\n第二行内容。\n第三行内容。\n第四行内容。';
  const fullHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TweetEmbedCard, { ...baseProps, content: longContent })
  );
  if (fullHtml.includes('长文已截断')) {
    throw new Error('TweetEmbedCard must not truncate by default');
  }
  if (!fullHtml.includes('第四行内容')) {
    throw new Error('TweetEmbedCard default render missing content');
  }

  // maxLines 截断: line-clamp 样式 + 截断标记
  const clampedHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TweetEmbedCard, { ...baseProps, content: longContent, maxLines: 2 })
  );
  if (!clampedHtml.includes('-webkit-line-clamp')) {
    throw new Error('TweetEmbedCard maxLines clamp style broken');
  }
  if (!clampedHtml.includes('长文已截断') || !clampedHtml.includes('仅展示前 2 行')) {
    throw new Error('TweetEmbedCard missing truncation marker');
  }

  // 短内容不触发截断标记
  const shortHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(TweetEmbedCard, { ...baseProps, content: '单行短推文', maxLines: 3 })
  );
  if (shortHtml.includes('长文已截断')) {
    throw new Error('TweetEmbedCard must not mark short content as truncated');
  }

  console.log('✓ TweetEmbedCard truncation tests passed.');
}

/**
 * 6. UniversalScene 路由注册 (W7-8 B/C 四类型 + 隐式推断)
 */
function testUniversalSceneBcRouting() {
  console.log('Testing UniversalScene routing for W7-8 B/C family...');

  const makeScene = (extra: Partial<SceneMeta>): SceneMeta => ({
    id: 'scene_test',
    durationInFrames: 90,
    text: '测试旁白',
    ...extra,
  } as SceneMeta);

  // IdeWindow 显式 type
  const ideHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        type: 'IdeWindow',
        ide: { files: [{ name: 'a.c', lang: 'c', content: 'int x;' }] },
      }),
    })
  );
  if (!ideHtml.includes('a.c') || !ideHtml.includes('EXPLORER')) {
    throw new Error('UniversalScene IdeWindow routing broken');
  }

  // Asciicast 隐式推断
  const asciicastHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        asciicast: { events: [{ time: 0, type: 'o', data: '$ echo hi' }], title: 't' },
      }),
    })
  );
  if (!asciicastHtml.includes('$ echo hi')) {
    throw new Error('UniversalScene Asciicast implicit routing broken');
  }

  // CommentThread 显式 type
  const commentHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        type: 'CommentThread',
        commentThread: { comments: [{ author: '路人甲', content: '说得好' }] },
      }),
    })
  );
  if (!commentHtml.includes('路人甲') || !commentHtml.includes('说得好')) {
    throw new Error('UniversalScene CommentThread routing broken');
  }

  // TrendingRank 隐式推断
  const trendingHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        trending: { rank: 2, title: '热点话题乙', heat: 100 },
      }),
    })
  );
  if (!trendingHtml.includes('热点话题乙')) {
    throw new Error('UniversalScene TrendingRank implicit routing broken');
  }

  console.log('✓ UniversalScene B/C routing tests passed.');
}

/**
 * 7. SSR 安全基建回归 (CI 曝光缺陷的防复发测试)
 *    - SafeImage: 裸 SSR 无 Remotion 上下文时回退原生 <img> (Remotion <Img>
 *      内部 usePremounting->useCurrentFrame 必抛, 曾导致 task4 集成测试在
 *      干净检出下崩溃)
 *    - safeDemoTimeline: 无 require.context (Node 测试) 或文件缺失时降级
 *      空时间轴不抛错 (public/projects 被 gitignore, 静态 import 曾使
 *      tsc --noEmit 在干净检出下 TS2307 失败)
 */
function testSsrSafetyInfrastructure() {
  console.log('Testing SSR safety infrastructure (SafeImage / safeDemoTimeline)...');

  // 7.1 SafeImage 裸 SSR 回退原生 img (不抛错)
  const imgHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SafeImage, { src: 'images/demo_capture/x.png', alt: '回归测试' })
  );
  if (!imgHtml.includes('<img')) {
    throw new Error('SafeImage must fall back to native img in bare SSR');
  }
  if (!imgHtml.includes('images/demo_capture/x.png')) {
    throw new Error('SafeImage lost src');
  }

  // 7.2 safeDemoTimeline 在 Node 测试环境降级为空时间轴 (不抛错)
  const timeline = safeLoadDemoTimeline('demo_style_apple');
  if (!Array.isArray(timeline.scenes) || timeline.scenes.length !== 0) {
    throw new Error('safeDemoTimeline must degrade to empty scenes without require.context');
  }

  // 7.3 WebBrowserMockup 场景经 UniversalScene 渲染不抛 (曾因裸 useCurrentFrame 崩)
  const browserHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: {
        id: 'scene_browser',
        type: 'WebBrowserMockup',
        durationInFrames: 90,
        text: '浏览器场景回归',
        browser: { url: 'https://example.com', image: 'images/x.png' },
      } as SceneMeta,
    })
  );
  if (!browserHtml.includes('浏览器场景回归') && !browserHtml.includes('example.com')) {
    throw new Error('UniversalScene WebBrowserMockup SSR regression');
  }

  console.log('✓ SSR safety infrastructure tests passed.');
}

/**
 * 执行全量验证测试
 */
function runAllBcComponentTests() {
  console.log('====================================================');
  console.log('Running W7-8 B/C Component Family & Routing Tests');
  console.log('====================================================');

  testIdeWindowScene();
  testAsciicastPlayer();
  testCommentThreadScene();
  testTrendingRankCard();
  testTweetTruncation();
  testUniversalSceneBcRouting();
  testSsrSafetyInfrastructure();

  console.log('====================================================');
  console.log('✓ All W7-8 B/C Component & Routing tests passed cleanly!');
  console.log('====================================================');
}

runAllBcComponentTests();

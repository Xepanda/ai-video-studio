import React from 'react';
import ReactDOMServer from 'react-dom/server';
import {
  MathFormulaScene,
  SequenceDiagramScene,
} from '../src/components/shorts';
import type {
  MathFormulaProps,
  SequenceDiagramProps,
} from '../src/components/shorts';
import { PinoutStream } from '../src/components/PinoutStream';
import { UniversalScene } from '../src/components/UniversalScene';
import type { SceneMeta } from '../src/components/UniversalScene';

/**
 * W7-8 场景一: 学科可视化组件族契约测试
 * 覆盖: MathFormulaScene (KaTeX) / SequenceDiagramScene (时序图+状态机) /
 *       PinoutStream (数据驱动化) 及 UniversalScene 路由注册
 * 说明: renderToStaticMarkup 会将 '>' 转义为 '&gt;' (React SSR 行为);
 *       组件动效在 frame=0 的 SSR 快照下仅渲染首帧, 断言均基于可观测契约。
 */

/**
 * 1. MathFormulaScene: KaTeX 公式渲染与 props 契约
 */
function testMathFormulaScene() {
  console.log('Testing MathFormulaScene (KaTeX) interface & rendering...');

  // 1.1 公式经 KaTeX 真实渲染 (katex 容器 + 数学字母 span)
  // 注: KaTeX HTML 将字母拆为独立 span (>E< / >m< / >c<), 不断言连续字符串
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MathFormulaScene, { formula: 'E = mc^2' })
  );
  if (!defaultHtml.includes('class="katex"')) {
    throw new Error('MathFormulaScene missing katex container');
  }
  if (!defaultHtml.includes('>E<') || !defaultHtml.includes('>m<') || !defaultHtml.includes('>c<')) {
    throw new Error('MathFormulaScene missing rendered formula letter spans');
  }

  // 1.2 自定义契约: title/category/caption 全部进入画面
  const customProps: MathFormulaProps = {
    formula: '\\frac{a}{b}',
    title: ' Shannon 极限的审美',
    category: 'INFORMATION THEORY',
    caption: '信道容量决定了通信的物理天花板。',
    highlight: true,
  };
  const customHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MathFormulaScene, customProps)
  );
  if (!customHtml.includes('INFORMATION THEORY')) {
    throw new Error('MathFormulaScene failed to render category');
  }
  if (!customHtml.includes('信道容量决定了通信的物理天花板。')) {
    throw new Error('MathFormulaScene failed to render caption');
  }
  // highlight 走紫色描边契约 (与 ProtocolStackTower 聚焦态一致的视觉语言)
  if (!customHtml.includes('#a855f7')) {
    throw new Error('MathFormulaScene missing highlight border accent');
  }

  // 1.3 分数公式的 KaTeX 结构 (frac 脚手架类名)
  const fracHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MathFormulaScene, { formula: '\\frac{a}{b}', displayMode: false })
  );
  if (!fracHtml.includes('frac-line')) {
    throw new Error('MathFormulaScene failed to render fraction structure');
  }

  // 1.4 公式缺省兜底: 空 formula 不炸渲染 (降级为原文 span)
  const emptyHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MathFormulaScene, { formula: '' })
  );
  if (emptyHtml.length === 0) {
    throw new Error('MathFormulaScene crashed on empty formula');
  }

  console.log('✓ MathFormulaScene tests passed.');
}

/**
 * 2. SequenceDiagramScene: 时序图与状态机双模式契约
 */
function testSequenceDiagramScene() {
  console.log('Testing SequenceDiagramScene (sequence & state modes)...');

  // 2.1 时序图模式: 参与者 + 消息标签进入 SSR 首帧
  const seqProps: SequenceDiagramProps = {
    mode: 'sequence',
    title: 'TCP 三次握手时序',
    category: 'NETWORKING 101',
    participants: [
      { id: 'client', name: '客户端' },
      { id: 'server', name: '服务端' },
    ],
    messages: [
      { from: 'client', to: 'server', label: 'SYN' },
      { from: 'server', to: 'client', label: 'SYN + ACK' },
      { from: 'client', to: 'server', label: 'ACK' },
    ],
  };
  const seqHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SequenceDiagramScene, seqProps)
  );
  if (!seqHtml.includes('客户端') || !seqHtml.includes('服务端')) {
    throw new Error('SequenceDiagram (sequence) missing participants');
  }
  if (!seqHtml.includes('SYN')) {
    throw new Error('SequenceDiagram (sequence) missing message labels');
  }
  // 消息箭头强调色 (青色实线 / 紫色虚线)
  if (!seqHtml.includes('#38bdf8')) {
    throw new Error('SequenceDiagram (sequence) missing arrow accent color');
  }

  // 2.2 虚线消息 (dashed) 走紫色系
  const dashedHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SequenceDiagramScene, {
      mode: 'sequence',
      participants: [
        { id: 'a', name: 'A' },
        { id: 'b', name: 'B' },
      ],
      messages: [{ from: 'a', to: 'b', label: '重传', dashed: true }],
    })
  );
  if (!dashedHtml.includes('dashed') || !dashedHtml.includes('#a855f7')) {
    throw new Error('SequenceDiagram dashed message contract broken');
  }

  // 2.3 状态机模式: 状态节点 + 转移标签
  const stateProps: SequenceDiagramProps = {
    mode: 'state',
    title: 'TCP 状态跃迁',
    states: [
      { id: 'closed', label: 'CLOSED' },
      { id: 'syn_sent', label: 'SYN_SENT' },
      { id: 'established', label: 'ESTABLISHED' },
    ],
    transitions: [
      { from: 'closed', to: 'syn_sent', label: '主动打开' },
      { from: 'syn_sent', to: 'established', label: '收到 ACK' },
    ],
  };
  const stateHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SequenceDiagramScene, stateProps)
  );
  for (const label of ['CLOSED', 'SYN_SENT', 'ESTABLISHED', '主动打开', '收到 ACK']) {
    if (!stateHtml.includes(label)) {
      throw new Error(`SequenceDiagram (state) missing ${label}`);
    }
  }

  // 2.4 空数据兜底: 无 participants/states 时不炸, 输出缺失提示
  const emptySeqHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SequenceDiagramScene, { mode: 'sequence', participants: [] })
  );
  if (!emptySeqHtml.includes('participants')) {
    throw new Error('SequenceDiagram missing-data fallback broken (sequence)');
  }
  const emptyStateHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(SequenceDiagramScene, { mode: 'state', states: [] })
  );
  if (!emptyStateHtml.includes('states')) {
    throw new Error('SequenceDiagram missing-data fallback broken (state)');
  }

  console.log('✓ SequenceDiagramScene tests passed.');
}

/**
 * 3. PinoutStream: 数据驱动化契约 (W7-8 重构)
 */
function testPinoutStream() {
  console.log('Testing PinoutStream data-driven contract...');

  // 3.1 无 props 回退内置演示数据 (Root.tsx 零配置用法兼容)
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(PinoutStream, {})
  );
  if (!defaultHtml.includes('GPIO 18 (SCLK)')) {
    throw new Error('PinoutStream lost default demo pins');
  }
  if (!defaultHtml.includes('GPIO 脉冲走线信号波形')) {
    throw new Error('PinoutStream lost default title');
  }

  // 3.2 数据驱动: 自定义引脚列表覆盖默认, 自定义标题生效
  const customHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(PinoutStream, {
      title: '自定义波形标题',
      pins: [
        { pin: 'PA0 (TIM2_CH1)', freq: 0.3, color: '#f43f5e' },
        { pin: 'PB7 (I2C1_SDA)', freq: 0.12, color: '#22d3ee' },
      ],
    })
  );
  if (!customHtml.includes('自定义波形标题')) {
    throw new Error('PinoutStream failed to apply custom title');
  }
  if (!customHtml.includes('PA0 (TIM2_CH1)') || !customHtml.includes('PB7 (I2C1_SDA)')) {
    throw new Error('PinoutStream failed to render custom pins');
  }
  if (customHtml.includes('GPIO 18 (SCLK)')) {
    throw new Error('PinoutStream must override default pins when custom pins provided');
  }
  if (!customHtml.includes('#f43f5e')) {
    throw new Error('PinoutStream missing custom pin color');
  }

  console.log('✓ PinoutStream tests passed.');
}

/**
 * 4. UniversalScene 路由注册 (显式 type 优先 + 嵌套配置隐式推断)
 */
function testUniversalSceneVisualRouting() {
  console.log('Testing UniversalScene routing for W7-8 visual family...');

  const makeScene = (extra: Partial<SceneMeta>): SceneMeta => ({
    id: 'scene_test',
    durationInFrames: 90,
    text: '测试旁白',
    ...extra,
  } as SceneMeta);

  // 4.1 MathFormula: 显式 type
  const mathHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        type: 'MathFormula',
        mathFormula: { formula: 'E = mc^2', title: '显式路由标题' },
      }),
    })
  );
  if (!mathHtml.includes('class="katex"') || !mathHtml.includes('显式路由标题')) {
    throw new Error('UniversalScene MathFormula explicit-type routing broken');
  }

  // 4.2 MathFormula: 嵌套配置隐式推断 (无显式 type)
  const implicitMathHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        mathFormula: { formula: 'F = ma', title: '隐式路由标题' },
      }),
    })
  );
  if (!implicitMathHtml.includes('class="katex"') || !implicitMathHtml.includes('隐式路由标题')) {
    throw new Error('UniversalScene MathFormula implicit-inference routing broken');
  }

  // 4.3 SequenceDiagram: 显式 type (状态机模式)
  const seqHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        type: 'SequenceDiagram',
        sequenceDiagram: {
          mode: 'state',
          states: [{ id: 'a', label: 'STATE_A' }],
          transitions: [],
        },
      }),
    })
  );
  if (!seqHtml.includes('STATE_A')) {
    throw new Error('UniversalScene SequenceDiagram routing broken');
  }

  // 4.4 PinoutStream: 嵌套配置隐式推断
  const pinoutHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, {
      scene: makeScene({
        pinoutStream: { title: '路由注入的引脚流', pins: [{ pin: 'PC13', freq: 0.2, color: '#fff' }] },
      }),
    })
  );
  if (!pinoutHtml.includes('路由注入的引脚流') || !pinoutHtml.includes('PC13')) {
    throw new Error('UniversalScene PinoutStream routing broken');
  }

  console.log('✓ UniversalScene visual routing tests passed.');
}

/**
 * 执行全量验证测试
 */
function runAllVisualComponentTests() {
  console.log('====================================================');
  console.log('Running W7-8 Visual Component Family & Routing Tests');
  console.log('====================================================');

  testMathFormulaScene();
  testSequenceDiagramScene();
  testPinoutStream();
  testUniversalSceneVisualRouting();

  console.log('====================================================');
  console.log('✓ All W7-8 Visual Component & Routing tests passed cleanly!');
  console.log('====================================================');
}

runAllVisualComponentTests();

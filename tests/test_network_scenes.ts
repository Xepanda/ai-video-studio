import React from 'react';
import ReactDOMServer from 'react-dom/server';
import {
  ProtocolStackTower,
  PacketAssemblyPipeline,
  RouterPacketInspection,
  WeChatMobileMockup,
} from '../src/components/shorts';
import type {
  ProtocolTowerProps,
  PacketAssemblyProps,
  RouterInspectionProps,
  WeChatMobileProps,
} from '../src/components/shorts';
import { UniversalScene } from '../src/components/UniversalScene';
import type { SceneMeta } from '../src/components/UniversalScene';

/**
 * 1. 验证 ProtocolStackTower 接口契约与渲染特性
 */
function testProtocolStackTower() {
  console.log('Testing ProtocolStackTower interface & rendering features...');

  // 1.1 默认契约: 标题回退 towerTitle, category 回退默认胶囊, 五层全部渲染
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ProtocolStackTower, {})
  );
  if (!defaultHtml.includes('TCP/IP 五层协议大厦')) {
    throw new Error('ProtocolStackTower missing default tower title fallback');
  }
  if (!defaultHtml.includes('NETWORK ARCHITECTURE · 5 LAYERS')) {
    throw new Error('ProtocolStackTower missing default category pill');
  }
  for (const layerName of ['应用层', '传输层', '网络层', '数据链路层', '物理层']) {
    if (!defaultHtml.includes(layerName)) {
      throw new Error(`ProtocolStackTower missing layer ${layerName} in full-stack render`);
    }
  }
  if (!defaultHtml.includes('HTTP/3') || !defaultHtml.includes('Ethernet')) {
    throw new Error('ProtocolStackTower missing protocol entries');
  }

  // 1.2 自定义契约: sceneTitle 覆盖 towerTitle, category 覆盖默认胶囊
  const customProps: { protocolTower: ProtocolTowerProps; title: string; category: string } = {
    protocolTower: { activeLayer: 3, showAllLayers: false, title: '内部塔标题不应胜出' },
    title: '微信发一句在吗，底层经历了什么？',
    category: 'TCP/IP STACK',
  };
  const customHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ProtocolStackTower, customProps)
  );
  if (!customHtml.includes('微信发一句在吗，底层经历了什么？')) {
    throw new Error('ProtocolStackTower failed to apply scene title override');
  }
  if (!customHtml.includes('TCP/IP STACK')) {
    throw new Error('ProtocolStackTower failed to apply custom category');
  }
  if (customHtml.includes('内部塔标题不应胜出')) {
    throw new Error('ProtocolStackTower scene title must take precedence over protocolTower.title');
  }

  // 1.3 activeLayer=3 (L3 网络层): 聚焦层边框 2px solid #a855f7, 其余层弱化
  if (!customHtml.includes('2px solid #a855f7')) {
    throw new Error('ProtocolStackTower activeLayer=3 did not focus L3 Network layer border');
  }

  // 1.4 activeLayer=0 (全部激活): 不存在任何聚焦层边框
  if (defaultHtml.includes('2px solid #a855f7')) {
    throw new Error('ProtocolStackTower activeLayer=0 should not focus any single layer');
  }

  console.log('✓ ProtocolStackTower tests passed.');
}

/**
 * 2. 验证 PacketAssemblyPipeline 接口契约与分 stage 渲染
 */
function testPacketAssemblyPipeline() {
  console.log('Testing PacketAssemblyPipeline interface & stage rendering...');

  // 2.1 默认契约: payload 阶段, 默认徽标与载荷文本
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(PacketAssemblyPipeline, {})
  );
  if (!defaultHtml.includes('数据装配流水线')) {
    throw new Error('PacketAssemblyPipeline missing default header badge');
  }
  if (!defaultHtml.includes('L5 应用层')) {
    throw new Error('PacketAssemblyPipeline missing default layer name');
  }
  if (!defaultHtml.includes('在吗')) {
    throw new Error('PacketAssemblyPipeline missing default payload text');
  }
  if (!defaultHtml.includes('e5 9c a8 e5 90 97')) {
    throw new Error('PacketAssemblyPipeline missing default payload hex');
  }

  // 2.2 自定义契约: tcp 阶段, 自定义报头与主题色注入
  const tcpProps: { packetAssembly: PacketAssemblyProps; title: string; category: string } = {
    packetAssembly: {
      stage: 'tcp',
      layerName: 'L4 传输层 (TCP)',
      payloadText: '在吗',
      tcpHeader: 'Src: 52144 -> Dst: 443 | SEQ=1001 ACK=0',
      headerBadge: 'TCP 443',
      color: '#38bdf8',
    },
    title: '传输层：TCP 报头封装',
    category: 'LAYER 4 · TRANSPORT',
  };
  const tcpHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(PacketAssemblyPipeline, tcpProps)
  );
  // 注意: React renderToStaticMarkup 会将 '>' 转义为 '&gt;', 断言使用转义后的 DOM 真实输出
  if (!tcpHtml.includes('Src: 52144 -&gt; Dst: 443 | SEQ=1001 ACK=0')) {
    throw new Error('PacketAssemblyPipeline failed to render custom TCP header');
  }
  if (!tcpHtml.includes('L4 传输层 (TCP)')) {
    throw new Error('PacketAssemblyPipeline failed to render custom layer name');
  }
  if (!tcpHtml.includes('传输层：TCP 报头封装')) {
    throw new Error('PacketAssemblyPipeline failed to apply scene title');
  }
  if (!tcpHtml.includes('#38bdf8')) {
    throw new Error('PacketAssemblyPipeline failed to apply custom theme color');
  }

  // 2.3 bits 阶段: 默认比特流字符串契约
  const bitsHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(PacketAssemblyPipeline, {
      packetAssembly: { stage: 'bits', bitstream: '01101001 01101110 01100101 01110100' },
    })
  );
  if (!bitsHtml.includes('01101001 01101110 01100101 01110100')) {
    throw new Error('PacketAssemblyPipeline failed to render bitstream payload');
  }

  console.log('✓ PacketAssemblyPipeline tests passed.');
}

/**
 * 3. 验证 RouterPacketInspection 接口契约与 switch/router 双模式
 */
function testRouterPacketInspection() {
  console.log('Testing RouterPacketInspection interface & dual-mode rendering...');

  // 3.1 默认契约: switch 模式设备名/动作/默认胶囊/副标题
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(RouterPacketInspection, {})
  );
  if (!defaultHtml.includes('二层以太网交换机')) {
    throw new Error('RouterPacketInspection missing default switch device name');
  }
  if (!defaultHtml.includes('只读取最外层 MAC 帧头，不拆包秒级转发')) {
    throw new Error('RouterPacketInspection missing default switch action');
  }
  if (!defaultHtml.includes('L2 SWITCHING · HARDWARE ACCELERATED')) {
    throw new Error('RouterPacketInspection missing default switch category pill');
  }
  if (!defaultHtml.includes('「只看外壳」的极速检票闸机')) {
    throw new Error('RouterPacketInspection missing switch subtitle');
  }
  // switch 模式强调色为琥珀 #f59e0b
  if (!defaultHtml.includes('#f59e0b')) {
    throw new Error('RouterPacketInspection switch mode should use amber accent');
  }

  // 3.2 自定义契约: router 模式, 自定义设备/动作/匹配状态
  const routerProps: { routerInspection: RouterInspectionProps; title: string; category: string } = {
    routerInspection: {
      mode: 'router',
      deviceName: '三层骨干路由器',
      action: '剥除旧 MAC 外壳 -> 查路由表匹配 IP -> 套上新 MAC 封箱',
      macMatch: '替换 MAC: B4:2E -> 00:1A:E8',
      ipStatus: '路由表命中默认网关',
    },
    title: '路由器：拆壳换装的跨网枢纽',
    category: 'HOP 2 · L3 ROUTER',
  };
  const routerHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(RouterPacketInspection, routerProps)
  );
  if (!routerHtml.includes('三层骨干路由器')) {
    throw new Error('RouterPacketInspection failed to render custom router device name');
  }
  // 注意: React renderToStaticMarkup 会将 '>' 转义为 '&gt;', 断言使用转义后的 DOM 真实输出
  if (!routerHtml.includes('剥除旧 MAC 外壳 -&gt; 查路由表匹配 IP -&gt; 套上新 MAC 封箱')) {
    throw new Error('RouterPacketInspection failed to render custom router action');
  }
  if (!routerHtml.includes('替换 MAC: B4:2E -&gt; 00:1A:E8')) {
    throw new Error('RouterPacketInspection failed to render custom macMatch');
  }
  if (!routerHtml.includes('「开箱换壳」的跨网导航枢纽')) {
    throw new Error('RouterPacketInspection missing router subtitle');
  }
  // router 模式强调色为紫 #a855f7
  if (!routerHtml.includes('#a855f7')) {
    throw new Error('RouterPacketInspection router mode should use purple accent');
  }

  console.log('✓ RouterPacketInspection tests passed.');
}

/**
 * 4. 验证 WeChatMobileMockup 接口契约与 send/receive 双模式
 */
function testWeChatMobileMockup() {
  console.log('Testing WeChatMobileMockup interface & dual-mode rendering...');

  // 4.1 默认契约: send 模式, 默认好友/消息/胶囊
  const defaultHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(WeChatMobileMockup, {})
  );
  if (!defaultHtml.includes('好友')) {
    throw new Error('WeChatMobileMockup missing default sender name');
  }
  if (!defaultHtml.includes('在吗')) {
    throw new Error('WeChatMobileMockup missing default message text');
  }
  if (!defaultHtml.includes('ORIGIN · WECHAT CLIENT')) {
    throw new Error('WeChatMobileMockup missing default send-mode category pill');
  }
  if (!defaultHtml.includes('21:30')) {
    throw new Error('WeChatMobileMockup missing default sent time');
  }

  // 4.2 自定义契约: receive 模式, 自定义消息与时间戳
  // 注意: 时延徽章 (latencyText) 受 `frame > 30` 动效门控, SSR 环境 frame=0 不可见,
  // 属有意的入场动画设计 (不为可测性改动生产行为); 此处验证 SSR 可观测契约。
  const receiveProps: { wechat: WeChatMobileProps; title: string; category: string } = {
    wechat: {
      mode: 'receive',
      senderName: '好友',
      messageText: '在吗',
      sentTime: '21:30:00.080',
      latencyText: '耗时: 80ms · 跨越 1200km',
    },
    title: '消息跨越一千二百公里抵达',
    category: 'DELIVERY COMPLETE · 0.08s',
  };
  const receiveHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(WeChatMobileMockup, receiveProps)
  );
  if (!receiveHtml.includes('21:30:00.080')) {
    throw new Error('WeChatMobileMockup failed to render custom sent time');
  }
  if (!receiveHtml.includes('DELIVERY COMPLETE · 0.08s')) {
    throw new Error('WeChatMobileMockup failed to apply custom category');
  }
  if (!receiveHtml.includes('消息跨越一千二百公里抵达')) {
    throw new Error('WeChatMobileMockup failed to apply scene title');
  }

  console.log('✓ WeChatMobileMockup tests passed.');
}

/**
 * 5. 验证 UniversalScene 路由注册表对四组件的分发契约
 */
function testUniversalSceneNetworkRouting() {
  console.log('Testing UniversalScene routing registry for network scene family...');

  // 5.1 显式 type: ProtocolStackTower
  const towerScene: SceneMeta = {
    id: 'scene_tower_01',
    type: 'ProtocolStackTower',
    durationInFrames: 150,
    category: 'TCP/IP STACK',
    protocolTower: { activeLayer: 0, showAllLayers: true, title: 'TCP/IP 五层协议大厦' },
  };
  const towerHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: towerScene })
  );
  if (!towerHtml.includes('TCP/IP 五层协议大厦')) {
    throw new Error('UniversalScene failed to route ProtocolStackTower by explicit type');
  }

  // 5.2 显式 type: PacketAssemblyPipeline
  const packetScene: SceneMeta = {
    id: 'scene_packet_01',
    type: 'PacketAssemblyPipeline',
    durationInFrames: 120,
    category: 'LAYER 5 · APPLICATION',
    packetAssembly: { stage: 'payload', layerName: 'L5 应用层 (Application)', payloadText: '在吗' },
  };
  const packetHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: packetScene })
  );
  if (!packetHtml.includes('数据装配流水线')) {
    throw new Error('UniversalScene failed to route PacketAssemblyPipeline by explicit type');
  }
  if (!packetHtml.includes('L5 应用层 (Application)')) {
    throw new Error('UniversalScene did not forward packetAssembly props to component');
  }

  // 5.3 显式 type: RouterPacketInspection
  const routerScene: SceneMeta = {
    id: 'scene_router_01',
    type: 'RouterPacketInspection',
    durationInFrames: 120,
    category: 'HOP 1 · L2 SWITCH',
    routerInspection: { mode: 'switch', deviceName: '二层以太网交换机' },
  };
  const routerHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: routerScene })
  );
  if (!routerHtml.includes('二层以太网交换机')) {
    throw new Error('UniversalScene failed to route RouterPacketInspection by explicit type');
  }

  // 5.4 显式 type: WeChatMobileMockup
  const wechatScene: SceneMeta = {
    id: 'scene_wechat_01',
    type: 'WeChatMobileMockup',
    durationInFrames: 90,
    category: 'NETWORKING 101',
    wechat: { mode: 'send', senderName: '好友', messageText: '在吗' },
  };
  const wechatHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: wechatScene })
  );
  if (!wechatHtml.includes('在吗') || !wechatHtml.includes('好友')) {
    throw new Error('UniversalScene failed to route WeChatMobileMockup by explicit type');
  }

  // 5.5 隐式推断: 无显式 type 但携带 protocolTower 嵌套对象
  const implicitTowerScene: SceneMeta = {
    id: 'scene_implicit_tower',
    durationInFrames: 90,
    protocolTower: { activeLayer: 3, title: '隐式路由协议栈' },
  };
  const implicitTowerHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: implicitTowerScene })
  );
  if (!implicitTowerHtml.includes('隐式路由协议栈')) {
    throw new Error('UniversalScene implicit protocolTower detection failed');
  }

  // 5.6 优先级: 显式 type=ProtocolStackTower 必须压过同时携带的 wechat 隐式对象
  const priorityScene: SceneMeta = {
    id: 'scene_type_priority',
    type: 'ProtocolStackTower',
    durationInFrames: 90,
    protocolTower: { title: '显式类型优先' },
    wechat: { messageText: '此消息不应渲染' },
  };
  const priorityHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: priorityScene })
  );
  if (!priorityHtml.includes('显式类型优先')) {
    throw new Error('UniversalScene explicit type ProtocolStackTower was not rendered');
  }
  if (priorityHtml.includes('此消息不应渲染')) {
    throw new Error('UniversalScene explicit type must take precedence over implicit wechat detection');
  }

  // 5.7 未知类型容错: 落入默认卡片分支, 不抛异常
  // 注意: 默认分支的 SFX 层使用 Remotion <Sequence>, 其内部 useVideoConfig 在 SSR 下必然抛错
  // (Remotion 框架限制, 非组件缺陷); 通过 scene.enableSfx=false 跳过音效层, 验证卡片兜底契约。
  const unknownScene: SceneMeta = {
    id: 'scene_unknown_fallback',
    type: 'SomeFutureUnknownType',
    durationInFrames: 60,
    enableSfx: false,
  };
  const unknownHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(UniversalScene, { scene: unknownScene })
  );
  if (!unknownHtml.includes('高性能计算底座')) {
    throw new Error('UniversalScene unknown type should fall back to default cards branch');
  }

  console.log('✓ UniversalScene network routing tests passed.');
}

/**
 * 执行全量验证测试
 */
function runAllNetworkSceneTests() {
  console.log('====================================================');
  console.log('Running Network Scene Family & UniversalScene Routing Tests');
  console.log('====================================================');

  testProtocolStackTower();
  testPacketAssemblyPipeline();
  testRouterPacketInspection();
  testWeChatMobileMockup();
  testUniversalSceneNetworkRouting();

  console.log('====================================================');
  console.log('✓ All Network Scene Family & Routing tests passed cleanly!');
  console.log('====================================================');
}

runAllNetworkSceneTests();

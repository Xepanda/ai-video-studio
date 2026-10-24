# 计算机网络五层模型与数据包套娃深度科普短视频设计规范

> ⚠️ **历史存档标注（2026-10-21，Phase 0 C4）**：本文档为历史设计规格留档。文中「-11.0 LUFS / ≤ -0.5 dBFS」母带标准已被 `scripts/audio_mastering.py` 的 `PLATFORM_LOUDNESS_PRESETS` 平台适配表取代（横屏科普默认 `web` -14.0 LUFS / TP ≤ -1.5 dBTP），验收时以代码单一事实源为准。

## 1. 概述与背景

在前期原型中，科普短视频存在视觉表现偏向文本静态排版、缺乏微观具象化动效、转场音效过于突兀刺耳等问题，导致观众完播欲望不足。
本设计规范旨在对标国内外顶流科技科普（如 ByteByteGo、3Blue1Brown、Fireship、柴知道微观动效），重新打造一部约 75 秒、11 幕高视觉信息密度、极具观赏性的 1080×1920 竖屏深度科普视频：《微信发一句“在吗”，底层经历了什么？计算机网络五层分工与数据包套娃》。

---

## 2. 全局技术约束与设计原则

1. **画幅与规格**：严格锁定 1080 × 1920 (9:16 竖屏)，CFR 30.000 FPS。
2. **移动端安全区**：画面底部预留 220px 抖音/小红书/视频号原生交互安全区，确保动态大字幕与关键组件不被遮挡。
3. **零转场杂音（Zero Transition SFX）**：彻底关闭分镜间的切换音效（`enableSfx: false`），杜绝廉价突兀听感。
4. **广播级人声与背景音乐**：
   - 配音：本地 ChatTTS 4444 科技随和男声音色。
   - 对齐：FunASR / Paraformer 毫秒级字词物理时间戳对齐。
   - 垫乐：`bgm_cyber_ambient.wav`，音量基础值 0.035，人声说话时自动闪避至 0.007（-43 dBFS）。
   - 母带：双遍 EBU R128 标准化压制，严格锁定 **-11.0 LUFS**，真峰值 ≤ -0.5 dBFS。
5. **纯代码驱动**：100% 依赖 React/SVG/CSS 与 GSAP 确定性动画，零外部 AI 视频生成，无画风畸变或模糊。
6. **双轨渲染出口**：
   - 主轨：Remotion React 多核光栅化。
   - 副轨：HyperFrames 确定性 HTML/GSAP 光栅化。

---

## 3. 核心定制动效组件体系

为构建高密度的微观世界探索感，在 `src/components/shorts/` 目录下新增 4 大专用核心动效组件：

### 3.1 `WeChatMobileMockup.tsx`（拟真移动端聊天组件）
- **职责**：开场（分镜 01）抛出生活化悬念，收尾（分镜 11）闭环送达。
- **视觉要素**：
  - iPhone 钛金属深色圆角外壳、灵动岛、顶部网络状态栏（Wi-Fi/5G/电量）。
  - 微信顶栏（返回箭头、联系人“好友”、更多按钮）。
  - 对话流：对方发送时间戳，用户敲击键盘光标，绿色气泡（`#07c160`）带微弹簧（damping: 14）弹入。
  - 微距下潜模式（Zoom-in Transition）：相机镜头向绿色气泡核心推进（scale 1.0 ➔ 3.2，opacity 渐变），文字裂变为十六进制发光晶体。

### 3.2 `ProtocolStackTower.tsx`（5 层立体水晶协议塔组件）
- **职责**：全局鸟瞰（分镜 02）以及后续每一层深度拆解时的常驻导航仪。
- **视觉要素**：
  - 5 阶晶体立柱（L5 应用层 绿、L4 传输层 蓝、L3 网络层 紫、L2 链路层 橙、L1 物理层 青）。
  - 支持 `activeLayer?: 1 | 2 | 3 | 4 | 5` 属性：当前活跃层向前浮动并释放柔和外发光（`box-shadow: 0 0 30px`），非活跃层半透明弱化。
  - 右侧悬浮各层专职协议标签（HTTP/TCP/IP/Ethernet/光纤脉冲）与参数胶囊。

### 3.3 `PacketAssemblyPipeline.tsx`（机械套娃装配流水线组件）
- **职责**：L5~L1 各层的数据包物理嵌套组装（分镜 03~07）与反向拆包（分镜 10）。
- **视觉要素**：
  - **组件阶段模式**：支持 `stage: 'payload' | 'tcp' | 'ip' | 'mac' | 'bits' | 'unpack'`。
  - **装配动效**：
    1. 中心：绿色 `[ Payload: "在吗" ]`。
    2. TCP 阶段：左右两侧机械滑轨合上蓝色 `[ TCP 报头 | 端口 52144 -> 443 | SEQ=100 ]`。
    3. IP 阶段：外层上下滑块嵌套紫色 `[ IP 报头 | 192.168.1.100 -> 120.232.145.88 ]`。
    4. MAC 阶段：最外层咬合橙色 `[ MAC 帧头 | 下一跳网卡 ]` 与尾部 `[ FCS 校验码 ]`。
    5. 比特流阶段：套娃整体转化为光电扫描线，逐字节转化为 `01011001...` 粒子流射出。

### 3.4 `RouterPacketInspection.tsx`（路由器与交换机微观透视组件）
- **职责**：展现网络设备行为（分镜 08、09）。
- **视觉要素**：
  - **交换机模式（L2 Switch）**：安检机扫描线仅扫过数据包最外层橙色 MAC 帧头，内部 IP 和 TCP 保持闭合，绿灯亮起，0.01ms 直通转发。
  - **路由器模式（L3 Router）**：机械臂将外层橙色旧 MAC 帧头瞬间切开剥离，露出发光紫色 IP 报头；动态路由表矩阵高亮匹配网段，重新贴上新目的 MAC 帧头，封箱发出。

---

## 4. 11 幕全景分镜文稿与时钟规划（约 75 秒 / 2250 帧）

| 幕次 | 分镜 ID | 组件选择 | 台词原稿 | 视觉核心 |
| :---: | :---: | :---: | :--- | :--- |
| 1 | `scene_01` | `WeChatMobileMockup` | 在微信发一句在吗，这句短短两个字的消息，底层究竟经历了怎样惊心动魄的星际航行？ | 微信真机，绿色气泡弹出，微距下潜文字裂变晶体 |
| 2 | `scene_02` | `ProtocolStackTower` | 计算机网络通过五层分工模型，将庞大的系统解耦为五道精密工序。 | 5层立体水晶塔完整拔地而起，各层光流贯通 |
| 3 | `scene_03` | `PacketAssemblyPipeline` | 第一步，应用层。微信 App 将文字编码为数据载荷，准备向下移交给操作系统内核。 | L5 激活，绿色 Payload 晶体生成（`UTF-8: "在吗"`） |
| 4 | `scene_04` | `PacketAssemblyPipeline` | 第二步，传输层。操作系统给它套上 TCP 报头，贴上端口号与序列号，保证消息绝不丢包。 | L4 激活，机械臂咬合蓝色 TCP 报头（52144 -> 443） |
| 5 | `scene_05` | `PacketAssemblyPipeline` | 第三步，网络层。贴上 IP 地址作为跨网身份证，告诉沿途路由器目标机房的具体坐标。 | L3 激活，嵌套紫色 IP 报头（局域网 IP -> 腾讯机房） |
| 6 | `scene_06` | `PacketAssemblyPipeline` | 第四步，数据链路层。套上下一站路由器的 MAC 物理地址，并在尾部加上校验码防止路上损坏。 | L2 激活，套上橙色 MAC 帧头与 FCS 循环校验尾 |
| 7 | `scene_07` | `PacketAssemblyPipeline` | 第五步，物理层。调制解调器将数据包轰击为高频光电脉冲，顺着光纤网线激射而出！ | L1 激活，整块套娃被激光扫描，化为 `0101` 比特光流 |
| 8 | `scene_08` | `RouterPacketInspection` | 抵达交换机，它像高速检票闸机，只看最外层 MAC 地址，直接精准推向出口。 | 二层交换机模式，安检线扫描 MAC，不拆包秒放行 |
| 9 | `scene_09` | `RouterPacketInspection` | 而跨网路由器则会拆掉旧外壳，读取 IP 重新规划路线，套上新 MAC 重新打包发往骨干光纤。 | 三层路由器模式，剥掉旧 MAC，查路由表，贴新 MAC |
| 10 | `scene_10` | `PacketAssemblyPipeline` | 穿过数千公里，好友手机收到电信号，自底向上层层撕开报头拆箱还原，提取出纯净的文字。 | 拆包模式，自底向上像拆快递盒一样依次剥离报头 |
| 11 | `scene_11` | `WeChatMobileMockup` | 仅耗时零点零八秒！每一层只做一件事，却让全世界数以亿计的设备紧密相连。 | 对方微信聊天窗口弹出“在吗”，计时器定格 0.08s |

---

## 5. 架构与路由设计（Polymorphic Dispatching）

在 `src/components/shorts/TechNewsShortsScene.tsx` 与 `src/components/UniversalScene.tsx` 中集成新组件分发：
- 若 `scene.type === 'WeChatMobileMockup'` 或 `scene.wechat` 存在 ➔ 渲染 `<WeChatMobileMockup />`
- 若 `scene.type === 'ProtocolStackTower'` 或 `scene.protocolTower` 存在 ➔ 渲染 `<ProtocolStackTower />`
- 若 `scene.type === 'PacketAssemblyPipeline'` 或 `scene.packetAssembly` 存在 ➔ 渲染 `<PacketAssemblyPipeline />`
- 若 `scene.type === 'RouterPacketInspection'` 或 `scene.routerInspection` 存在 ➔ 渲染 `<RouterPacketInspection />`

`scripts/sensevoice_aligner.py` 需将 `wechat`、`protocolTower`、`packetAssembly`、`routerInspection` 纳入属性白名单，自动透传至 `timeline.json`。

---

## 6. 验证与门禁标准

1. **类型安全**：`npx tsc --noEmit` 0 报错。
2. **时钟契约**：`python scripts/validator.py --project network_layers_deepdive` 100% 通过。
3. **声学无杂音**：分镜切换无任何过渡 Whoosh/SFX 音效；语音段 BGM 自动闪避。
4. **母带指标**：`audio_mastering.py --video` 输出综合响度严格稳定在 **-11.0 LUFS (±0.2)**。
5. **双轨可渲染**：Remotion 与 HyperFrames 均能正常光栅化输出完整 MP4。

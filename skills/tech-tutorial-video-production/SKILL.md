---
name: tech-tutorial-video-production
description: Use when producing high-retention technical explainer videos, coding tutorials, network protocol walkthroughs, or computer science educational shorts using Code-as-Video, Remotion/HyperFrames, dynamic syntax-highlighted code blocks, terminal typing animations, and conceptual diagram layers.
---

# Tech Tutorial Video Production (自媒体技术教学与硬核科普短视频制作)

## Overview
本 Skill 总结了制作顶流科技科普（对标 3Blue1Brown、ByteByteGo、Fireship）与自媒体硬核技术教学视频的核心经验、镜头节拍与参数规范。
全片基于 **Code-as-Video（代码即视频）** 确定性驱动，彻底告别画面模糊与画风畸变。

---

## 1. 核心制作原则 (Core Tenets)

1. **绝对时钟对齐（Audio as Absolute Clock）**：
   - 视频帧率锁定 30 FPS 或 60 FPS；
   - 动画进度、字幕弹跳、激光指针移动均是 `(currentFrame, fps, timeline)` 的纯数学确定性函数。
2. **字符权重等比分配（Character-Weighted Subtitle Allocation）**：
   - 严禁将场景总时长平均切片；
   - 分配公式：$\text{frames}_i = \text{total\_frames} \times \frac{\text{len}(\text{chunk}_i)}{\sum \text{len}(\text{chunk}_k)}$，确保短字不拖沓、长句有充足阅读时间。
3. **零转场杂音法则（Zero Transition SFX）**：
   - 禁用廉价刺耳的咻咻转场音效（设置 `enableSfx: false`）；
   - 背景音乐选用低频律动氛围垫乐（`bgm_cyber_ambient`），音量平时 0.035，人声说话时自动闪避（Audio Ducking）至 0.007（-43 dBFS）。

---

## 2. 核心定制动效组件规范

### 2.1 拟真移动端交互组件 (`WeChatMobileMockup.tsx`)
- **适用场景**：开场抛出生活化悬念（如“微信发一句在吗，底层发生了什么？”）。
- **动效细节**：
  - 钛金属深色圆角外壳 + 灵动岛；
  - 键盘输入光标跳动，微信绿底气泡（`#07c160`）以弹簧阻尼（`damping: 14, stiffness: 120`）弹入；
  - 微距下潜转场（Scale 1.0 ➔ 3.2），气泡文字裂变为十六进制发光网格。

### 2.2 立体协议水晶塔组件 (`ProtocolStackTower.tsx`)
- **适用场景**：5 层/7 层协议分工总览与常驻导航。
- **动效细节**：
  - 晶体立柱（L5 应用层绿、L4 传输层蓝、L3 网络层紫、L2 链路层橙、L1 物理层青）；
  - 当前活跃层向前浮动并释放柔和外发光（`box-shadow: 0 0 30px`），非活跃层半透明弱化。

### 2.3 机械套娃装配流水线 (`PacketAssemblyPipeline.tsx`)
- **适用场景**：展现协议数据包在各层的封装与拆解（Header + Payload）。
- **阶段模式**：`payload` ➔ `tcp` 报头 ➔ `ip` 报头 ➔ `mac` 帧头与 FCS 校验 ➔ 比特光流粒子流。

---

## 3. 配音与音色推荐
- **主力引擎**：本地 ChatTTS，锁定 **Seed 4444（随和生活男声）** 或 **Seed 2222（极客男声）**；
- **声音母带**：双遍 EBU R128 标准化压制，综合响度 **-11.0 LUFS ~ -14.0 LUFS**，真峰值 $\le -0.5\text{ dBFS}$。

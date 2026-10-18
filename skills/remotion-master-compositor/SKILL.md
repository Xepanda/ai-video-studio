---
name: remotion-master-compositor
description: Use when orchestrating the master timeline in Remotion (React 19 + TypeScript), assembling multi-layer video tracks, implementing SenseVoice word-level animated subtitles, applying EBU R128 loudness normalization, managing timeline snapshots, and rendering final 1080p videos.
---

# Remotion Master Compositor Skill (代码级总装合成与音频母带规范)

## Overview
Remotion 是整个 `ai-video-studio` 流水线的**核心总装底座与渲染引擎**。
通过 React 19 + TypeScript 的声明式纯函数组件模型，将配音、音效、SenseVoice 词级跳动字幕、HyperFrames B-Roll 以及终端动效按时间线组装为像素级精确的成片。

---

## 1. 核心时钟与组件规范

### 1.1 纯数学时钟法则
所有动画和位移必须基于 `useCurrentFrame()` 和 `useVideoConfig()` 计算，绝不能产生异步副作用：
```tsx
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// 平滑阻尼弹入
const scale = spring({
  frame,
  fps,
  config: { damping: 12, stiffness: 100 }
});
```

### 1.2 SenseVoice 词级动态高亮字幕 (`DynamicSubtitles.tsx`)
每个字词自带 `[startMs, endMs]` 毫秒级时间戳。Remotion 根据当前帧换算的毫秒数动态施加发光或变色样式：
```tsx
const currentMs = (frame / fps) * 1000;
const isCurrentWord = currentMs >= word.startMs && currentMs <= word.endMs;

<span style={{
  color: isCurrentWord ? "#00f2fe" : "#ffffff",
  transform: isCurrentWord ? "scale(1.15)" : "scale(1.0)",
  textShadow: isCurrentWord ? "0 0 16px rgba(0, 242, 254, 0.8)" : "none",
  display: "inline-block",
  transition: "all 0.08s ease"
}}>
  {word.text}
</span>
```

---

## 2. 国际广播级音频母带标准 (EBU R128)

所有配音和背景音乐必须经过 [`scripts/utils/audio_normalizer.py`](file:///C:/Users/ePanda/WorkBuddy/Worktrees/ai-video-studio/master-0d8c5b2f/scripts/utils/audio_normalizer.py) 进行标准化规整：

| 音轨类型 | 目标综合响度 (Integrated Loudness) | 真峰值上限 (True Peak) | 响度范围 (LRA) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **主配音轨 (Voiceover)** | **-16.0 LUFS** | $\le -1.0\text{ dBFS}$ | $\le 7.0\text{ LU}$ | 保证人声饱满清晰、音量恒定 |
| **背景音乐轨 (BGM)** | **-28.0 LUFS** | $\le -3.0\text{ dBFS}$ | — | 弱化为氛围底垫，避免喧宾夺主 |
| **音效轨 (SFX)** | **-20.0 LUFS** | $\le -2.0\text{ dBFS}$ | — | 短促打击感，禁用过高频刺耳音 |

---

## 3. 防灾快照管理 (Safety Snapshot)

在进行任何重大分镜重构或调用 Agent 进行修剪时，必须通过快照系统备份安全网：

```bash
# 创建时间戳快照
npm run snapshot:create -- --label "pre-major-refactor"

# 列出历史快照
npm run snapshot:list

# 一键回滚到最近快照
npm run snapshot:rollback
```

---

## 4. AMD 5800H 硬件资源调度准则
- **并发渲染控制**：渲染 1080p 60fps 视频时，建议设置 Remotion 并发数为 4~6（`--concurrency=4`），避免 16 线程满载导致 16GB 物理内存 OOM。
- **阶段性流水线执行**：配音生成、动效编译、主工程渲染应当按步骤流转，不要在后台并行运行多个重度 Python 模型进程。

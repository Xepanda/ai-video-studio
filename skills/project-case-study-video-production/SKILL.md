---
name: project-case-study-video-production
description: Use when producing technical project deep-dives, architectural breakdown videos, engineering case studies, or software post-mortems using interactive system topology graphs, B-roll cinematic mix, and code walkthroughs.
---

# Project Case Study Video Production (项目复盘与架构深度解析视频制作)

## Overview
本 Skill 总结了将开源项目、商业工程落地、技术踩坑排障以及架构重构制作成**高逼格商业级/极客级工程案例分析视频**的完整经验体系。

---

## 1. 经典五段式工程叙事结构 (5-Stage Narrative)

```
[1. 业务痛点与危机] ➔ [2. 经典架构的瓶颈] ➔ [3. 破局之道与重构设计] ➔ [4. 核心代码与算法透视] ➔ [5. 压测指标与量化成效]
```

1. **第 1 幕：痛点与危机（The Crisis Hook）**：
   - 抛出具体事故或性能瓶颈（如“QPS 翻倍直接打爆 Redis”、“长文本推理 OOM 内存崩溃”）；
   - 配合红色告警指示灯与系统吞吐量断崖式下跌折线图。
2. **第 2 幕：架构瓶颈拆解（Architecture Bottleneck）**：
   - 展现旧系统拓扑架构，用红色流光粒子标出阻塞瓶颈节点（如单点写入、锁竞争、过度深层嵌套）。
3. **第 3 幕：破局与核心方案（The Paradigm Shift）**：
   - 引入全新解法（如零拷贝、无锁队列、注意力机制优化、分片集群）；
   - 水晶卡片逐层展开新架构设计。
4. **第 4 幕：代码走读（Code Walkthrough）**：
   - 使用 TerminalWindow 或 CodeBlock 组件，关键字高亮逐行推入，避免一整屏贴代码。
5. **第 5 幕：收益交付与商业价值（Impact Metrics）**：
   - 动态数字增长翻牌器（Counter），直观展示延时降低 85%、成本节约 60%、吞吐量提升 10 倍。

---

## 2. 视觉组件与电影级 B-Roll 混剪
- **Google Flow B-Roll 融入**：在讲解宏观概念、服务器机房、城市数据流时，调用 `scripts/flow_automation/browser_flow_automation.js` 生成 1080p 电影级运镜空镜，通过 `<BrollVideoPlayer />` 无缝淡入。
- **动态终端仿真 (`TerminalWindow.tsx`)**：
  - 支持命令敲击打字效果、ANSI 颜色高亮、真实编译进度条动画；
  - 窗口右上角红黄绿三色控制按钮。
- **拟真浏览器视窗组件 (`WebBrowserMockupScene.tsx`)**：
  - 呈现真实 GitHub 仓库看板、Star 历史折线、官方技术文档或本地运行的 UI 页面；
  - 自带安全锁真实 URL 地址栏、平滑运镜微推拉与底部核心实证指标胶囊。
- **无头截屏与证据链抓取 (`scripts/generate_evidence_screenshots.py`)**：
  - 支持直接截取任意本地/线上服务页面并输出 1080p 超清无畸变图像。

---

## 3. 色彩与听觉工程规范
- **主题风格选择**：
  - 极客工程案例可选用 `linear-graphite` 或 `cyber-blueprint`；
  - 开源指南、技术白皮书、架构规范类推荐采用 `editorial-paper-light` 浅色暖纸底，阅读舒适、护眼自然。
- **音效清理**：
  - 严禁在分镜切换处添加尖锐刺耳的科技扫频音效；
  - 纯净叙事人声配合双遍 EBU R128 (-11.0 LUFS) 广播级母带，保证小音量字字清晰。


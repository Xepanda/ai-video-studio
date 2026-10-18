---
name: hyperframes-motion
description: Use when creating, customizing, or rendering deterministic HTML5/CSS/GSAP motion graphics B-roll according to the HyperFrames (HeyGen) specification, and compiling them to 1080p 60fps MP4s using Playwright and hf_builder.py.
---

# HyperFrames Motion Graphics Skill (网页动效代码化 B-Roll 生成)

## Overview
HyperFrames 是由 HeyGen 提出并开源的前端动效代码化规范。
它基于 **HTML5 + CSS3 + GSAP 3** 编写，通过无头浏览器 Playwright 进行确定性逐帧捕获，以 100% 确定性生成无任何 AI 畸变、画质极致锐利的 1080p 60fps 科技 B-Roll 视频。

---

## 1. 模板体系与规范约束

所有 HyperFrames 动效模板集中存放于 `projects_hf/templates/<template_name>/`：

```
projects_hf/templates/
├── architecture_flow/        # 网络拓扑/微服务数据包流转动效
│   ├── index.html            # 入口页面与 GSAP 时间轴绑定
│   ├── style.css             # 响应式布局与赛博霓虹质感样式
│   └── main.js               # 暴露 window.setFrame(n) 与 window.totalFrames
└── code_spotlight/           # 黑客终端代码打字与高亮聚光灯
    ├── index.html
    ├── style.css
    └── main.js
```

### 1.1 必须遵循的代码规范
1. **绝对时间轴绑定（Deterministic Frame Hook）**：
   页面中必须挂载全局时间轴函数，供 Playwright 自动化驱动逐帧步进：
   ```javascript
   window.totalFrames = 180; // 3 秒 @ 60fps
   window.setFrame = function(frameIndex) {
     const progress = frameIndex / window.totalFrames;
     masterTimeline.progress(progress); // GSAP 进度定位
   };
   ```
2. **双画幅支持（Dual Aspect Ratio）**：
   - 默认支持 **16:9 横屏**（`1920x1080`）与 **9:16 竖屏**（`1080x1920`）；
   - 通过 CSS Media Query 或容器自适应类名（`.portrait` / `.landscape`）自动切换，关键图表与文字始终保持在中心安全区（80% 视野范围内）。
3. **禁用随机与环境扰动**：
   禁止使用未经受控种子的 `Math.random()`，禁止依赖系统实际流逝时间（`Date.now()` / `performance.now()`），所有粒子流均需基于伪随机或固定初相位。

---

## 2. CLI 自动化构建与编译

使用项目内置的 [`scripts/hf_builder.py`](file:///C:/Users/ePanda/WorkBuddy/Worktrees/ai-video-studio/master-0d8c5b2f/scripts/hf_builder.py) 进行管理与渲染：

### 常用命令
```bash
# 1. 列出当前可用动效模板
python scripts/hf_builder.py list

# 2. 渲染指定模板为 60fps MP4
python scripts/hf_builder.py render architecture_flow --aspect 16:9 --fps 60 --duration 3.0 --out public/footage/broll_arch.mp4

# 3. 渲染为 9:16 竖屏短视频素材
python scripts/hf_builder.py render code_spotlight --aspect 9:16 --fps 60 --duration 4.0 --out public/footage/broll_code_vertical.mp4

# 4. 在 Chrome 中启动实时交互预览（热调试 GSAP 动画）
python scripts/hf_builder.py preview architecture_flow
```

---

## 3. 在主工程 Remotion 中的调用方式

渲染生成的 `.mp4` 文件保存在 `public/footage/` 下，在 Remotion 组件树中通过 `<OffthreadVideo />` 或 `<Video />` 无缝接入：

```tsx
import { OffthreadVideo, staticFile } from "remotion";

export const HyperFrameScene: React.FC<{ durationInFrames: number }> = () => {
  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <OffthreadVideo
        src={staticFile("footage/broll_arch.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </div>
  );
};
```

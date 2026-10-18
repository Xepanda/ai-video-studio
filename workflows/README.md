# 视频工程类型与工作流一览 (Video Workflows Matrix)

本项目沉淀了针对不同内容形态的 **4 套标准化制作工作流（SOP）**：

---

## 1. 🛍️ 抖音/快手直播带货短视频工作流
- **文件路径**：[`docs/LIVE_ECOMMERCE_SOP.md`](../docs/LIVE_ECOMMERCE_SOP.md)
- **对应技能**：[`skills/live-ecommerce-video-editor/SKILL.md`](../skills/live-ecommerce-video-editor/SKILL.md)
- **核心逻辑**：几小时原素材 ➔ Faster-Whisper 转录定位 ➔ 黄金3秒重组 + Boom音效 ➔ 细节推镜特写 + 镜像防反贴纸 + 50:50等比双色对比 ➔ ASS发光字幕 ➔ Option 1 爆款大促封面。
- **执行命令**：
  ```bash
  python scripts/live_ecommerce_pipeline.py --project "D:/dy-video-projects/project1_jacket"
  ```
- **⭐ 数据驱动批量化升级（多 SKU 一键成片）**：[`scripts/live_ecommerce_batch_pipeline.py`](../scripts/live_ecommerce_batch_pipeline.py)
  - 每个 SKU 一份「剪辑计划 JSON」（`02_scripts_and_docs/plans/<sku>.plan.json`），声明切片/推镜/镜像/分屏/贴纸/字幕/封面全要素；
  - 所有时间点**锚定到切片**（`{clip, off, dur}`），按渲染后实测时长解析，彻底消除累积漂移；
  - 自动产出：黄金3秒钩子卡（胸前带避脸位）、6 款利益点挂角徽章（低位 y=1400 安全带）、50:50 对称双色分屏（居中发光分割线 + 左右胶囊标签）、ASS 发光字幕（关键词亮黄）、Sub-Bass Boom、尾部 CTA 气泡、Option 1 爆款封面；
  - 执行命令：
  ```bash
  python scripts/live_ecommerce_batch_pipeline.py --project "D:/dy-video-projects/dy_live_20261014" --sku sku09_thinsulate
  ```

---

## 2. 💻 自媒体技术教学与硬核科普工作流
- **文件路径**：[`WORKFLOW.md`](../WORKFLOW.md)
- **对应技能**：[`skills/tech-tutorial-video-production/SKILL.md`](../skills/tech-tutorial-video-production/SKILL.md)
- **核心逻辑**：`PROJECT_SPEC.md` 脚本撰写 ➔ 本地 ChatTTS (Seed 4444) ➔ SenseVoice 毫秒级打点 ➔ 质量门禁校验 (`validator.py`) ➔ Remotion Studio 所见即所得排版 ➔ 多核并发光栅化渲染。
- **执行命令**：
  ```bash
  python scripts/pipeline.py --project my_project
  npm run dev
  npm run render
  ```

---

## 3. 🏗️ 项目复盘与架构案例深度剖析工作流
- **对应技能**：[`skills/project-case-study-video-production/SKILL.md`](../skills/project-case-study-video-production/SKILL.md)
- **核心逻辑**：五段式叙事（危机 ➔ 瓶颈 ➔ 破局 ➔ 代码 ➔ 交付）➔ 动态系统拓扑图 ➔ 终端打字模拟 ➔ Google Flow 电影级 B-Roll 混剪。

---

## 4. 🌐 Google Flow (flow.google.com) 电影级 AI 镜头生成流
- **核心工具**：[`scripts/flow_automation/browser_flow_automation.js`](../scripts/flow_automation/browser_flow_automation.js)
- **核心逻辑**：以 `--remote-debugging-port=9222` 启动本地真实 Chrome 保持 2FA 登录态 ➔ Playwright CDP 自动接管 ➔ 上传首帧、填入运镜 Prompt ➔ 轮询状态并自动下载 1080p MP4。

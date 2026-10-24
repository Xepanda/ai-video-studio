# HyperFrames 动效引擎与 yt-dlp 素材采集中枢工作流集成设计规范

> ⚠️ **历史存档标注（2026-10-21，Phase 0 C4）**：本文档为历史设计规格留档。文中「-11.0 LUFS / -0.5 dBFS」母带标准已被 `scripts/audio_mastering.py` 的 `PLATFORM_LOUDNESS_PRESETS` 平台适配表取代（默认 `web` -14.0 LUFS / TP ≤ -1.5 dBTP；短视频 `--platform short_video` -11.0 LUFS），验收时以代码单一事实源为准。

## 1. 概述与背景

随着全链路视频自动化生产系统（`ai-video-studio`）的持续演进，现有管线在以下两个维度迎来了关键升级契机：
1. **上游素材与灵感采集瓶颈**：当前视频素材主要依赖本地静态图表或代码组件，缺乏自动从主流视频平台（YouTube、Bilibili、Twitter/X 等）定向切取高质量 B-roll、提取原视频原声音频或抓取原文字幕做反向拆解的自动化工具链；
2. **轻量化动效渲染诉求**：当前主力渲染引擎 Remotion 依赖完整的 React 19 运行时与 TSX 编译打包，对于高频次、图文排版、短资讯类的视频，构建门槛与大模型代码生成开销偏高。引入 HeyGen 官方开源的 **HyperFrames**（原生 HTML5/CSS3/GSAP 声明式时钟引擎）作为第二渲染引擎，可以实现“大模型生成极简稳定、渲染极速轻量、与 Remotion 各取所长”的渐进式双轨架构。

本设计规范明确了如何将 **yt-dlp** 与 **HyperFrames** 深度融入现有 `ai-video-studio` 工程，实现从素材定向采集、音频字幕对齐、双引擎自由切换渲染，到 EBU R128 广播级母带压制的完整生产流水线。

---

## 2. 系统全局架构与数据流向

整个视频自动化工作室采用**“单一时间源契约 + 双轨渲染出口”**的解耦设计：

```
                    ┌────────────────────────────────────────┐
                    │  1. 智能素材收集 (yt-dlp Ingestion)      │
                    │  · 目标链接 / B-Roll 关键词切片采集      │
                    │  · 提取高保真干声 / 参考音色 / 原文字幕  │
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼
                    ┌────────────────────────────────────────┐
                    │  2. 脚本大模型编排 (Scripting Engine)    │
                    │  · 提炼结构 ➔ 输出 content/scripts/*.json│
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼
                    ┌────────────────────────────────────────┐
                    │  3. 专属声纹与对齐 (TTS + ASR Aligner)   │
                    │  · ChatTTS (Seed 2222 等) ➔ Paraformer │
                    │  · 锁定标准契约: public/.../timeline.json│
                    └───────────────────┬────────────────────┘
                                        │
                  ┌─────────────────────┴─────────────────────┐
                  ▼                                           ▼
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│ 4A. 旗舰视觉渲染 (Remotion 引擎)   │       │ 4B. 极速动效渲染 (HyperFrames 引擎)│
│ · React 3D/2.5D 复杂交互动效      │       │ · 声明式 HTML/CSS/GSAP 轻量化排版 │
│ · npx remotion render             │       │ · hyperframes render              │
└─────────────────┬─────────────────┘       └─────────────────┬─────────────────┘
                  │                                           │
                  └─────────────────────┬─────────────────────┘
                                        │
                                        ▼
                    ┌────────────────────────────────────────┐
                    │  5. 商业广播级母带压制 (Audio Mastering) │
                    │  · EBU R128 (-11.0 LUFS / -0.5 dB Peak)│
                    │  · 动态 BGM Ducking 闪避 ➔ 成品 MP4 交付│
                    └────────────────────────────────────────┘
```

---

## 3. 子系统 1：yt-dlp 素材与音频智能采集中枢 (`scripts/ingest_material.py`)

### 3.1 职责定义
作为上游资产输入中枢，封装 `yt-dlp` 与本地 `ffmpeg`，提供高精度视频切片下载、干声音频提取与字幕元数据抓取能力，杜绝人工手动下载与转换格式的繁琐流程。

### 3.2 CLI 命令参数接口规范
```bash
python scripts/ingest_material.py [OPTIONS]
```

- `--url <URL>`：目标视频/流媒体地址（必填）。
- `--project <PROJECT_NAME>`：归属项目名称，用于资产隔离存储（默认 `common`）。
- `--name <FILE_NAME>`：输出素材基准文件名（可选，未指定时默认使用视频 title slug）。
- `--section "<START>-<END>"`：时间段切片，例如 `"00:01:15-00:01:30"` 或 `"01:15-01:30"`。
- `--audio-only`：仅提取高质量音频（默认输出 24kHz/48kHz WAV）。
- `--subtitles`：抓取中英文原文字幕（输出 `.vtt` / `.srt` / `.json`）。
- `--extract-info`：仅提取并导出视频元数据（标题、描述、标签、章节打点）。
- `--resolution <RES>`：目标分辨率上限（默认 `1080`，可选 `720` / `1080` / `2160`）。
- `--fps <FPS>`：输出视频帧率锁定（默认 `30`）。

### 3.3 关键技术与转码规范
1. **精确时间切片与按需下载**：通过 `yt-dlp --download-sections "*<START>-<END>"` 避免下载整段冗余视频，节约磁盘与网络开销；
2. **CFR 30.000 FPS 恒定帧率标准化**：流媒体平台下载的视频常为可变帧率（VFR），极易引发 Remotion / HyperFrames 逐帧光栅化时的音画跑偏。本脚本在下载后自动执行 `ffmpeg` 滤镜转码：
   ```bash
   ffmpeg -i raw.mp4 -vf "fps=30,scale=1080:-2" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k out.mp4
   ```
3. **资产存储路径规范**：
   - 视频切片：`public/projects/{project}/footage/{name}.mp4`（或 `public/footage/{project}/`）
   - 干声音频：`public/projects/{project}/audio/reference_voice.wav`
   - 字幕与元数据：`inputs/transcripts/{project}_metadata.json`

---

## 4. 子系统 2：HyperFrames 动效转译与渲染中枢 (`scripts/timeline_to_hyperframes.py`)

### 4.1 职责定义
读取阿里 Paraformer 毫秒打点生成的物理时钟文件 `timeline.json`，将其自动转译为完全自包含、符合 HeyGen 规范的 HyperFrames 原生 Web 动效项目目录（`projects_hf/{project}/`）。

### 4.2 独立项目目录结构
```text
projects_hf/{project}/
├── hyperframes.json        # 项目画幅与时钟元数据
├── index.html              # 声明式语义 HTML 视觉主体
├── styles.css              # 高对比度极简排版、Bento 网格、毛玻璃与动态胶囊样式
├── script.js               # GSAP 物理缓动与卡拉OK逐词高亮时间轴
└── assets/
    ├── audio/              # 分镜配音 scene_*.wav 与背景音乐
    └── footage/            # 引入自 yt-dlp 的 B-Roll 视频或外部截图
```

### 4.3 核心组件的 Web 标准映射契约
1. **MinimalHeadline（震撼大字头条）**：
   - 采用 Flex 居中布局，支持正常暗黑模式与黑底白字高反差 Inverted 反转模式；
   - 动态关键词胶囊（Capsule Badge）采用 CSS 渐变高光与微弹性缩放。
2. **TweetEmbed（原生推文卡片）**：
   - 1:1 还原 X/Twitter 平台质感，包含头像、认证蓝标、@账号名、推文正文与互动指标（Likes/Retweets）。
3. **BinaryBento（双拼对比 Bento 网格）**：
   - 左右双卡对比，配合 `ProgressBlocks` 发光进度点阵，由 GSAP 在卡片落定后逐个平滑点亮。
4. **B-Roll 视频视窗（与 yt-dlp 深度联动）**：
   - 标签声明 `<video data-in="start" data-out="end" src="assets/footage/...">`；
   - 支持圆角画中画、外发光边框或全屏暗角背景，完美承接 `ingest_material.py` 采集的高清切片。
5. **底部安全区卡拉OK字幕（DynamicSubtitles）**：
   - 严格固定在屏幕底部 220px 安全区上方，避开短视频平台原生 UI；
   - 根据 `timeline.json` 中的词级物理起止时间，通过 GSAP 绑定精准的高亮渐变，实现无延迟逐词跳动。

### 4.4 确定性渲染与质量审查
- **预览**：`npx hyperframes preview projects_hf/{project}`（毫秒级热加载）；
- **门禁**：`npx hyperframes check projects_hf/{project}`（静态检查时序重叠与资产有效性）；
- **渲染**：`npx hyperframes render projects_hf/{project} -o out/{project}_hf.mp4`（Puppeteer 无头逐帧渲染）。

---

## 5. 子系统 3：总控流水线双轨调度与工程规范 (`scripts/pipeline.py`)

### 5.1 调度参数扩展
在 `scripts/pipeline.py` 中新增 `--engine_render` 参数：
- `--engine_render remotion`（默认）：走经典 React/TSX Remotion 渲染链路；
- `--engine_render hyperframes`：自动执行转译、门禁检查，并调用 HyperFrames 渲染出 MP4；
- `--engine_render both`：双引擎同时渲染，分别输出 `out/{project}_remotion.mp4` 与 `out/{project}_hf.mp4`，便于画质与动效横评。

### 5.2 统一广播级音频母带
无论底层是由 Remotion 还是 HyperFrames 输出视频画面，最终均自动流转至统一的步骤 4：
```bash
python scripts/audio_mastering.py --video out/{project}.mp4
```
严格锁定 ITU-R BS.1770 / EBU R128 标准（综合响度 **-11.0 LUFS**，真峰值 **-0.5 dBFS**），保证全平台发布的听觉一致性。

### 5.3 package.json 便捷指令补充
```json
{
  "scripts": {
    "ingest": "python scripts/ingest_material.py",
    "dev:hf": "hyperframes preview",
    "render:hf": "hyperframes render",
    "pipeline:hf": "python scripts/pipeline.py --render --engine_render hyperframes"
  }
}
```

---

## 6. 自动化测试与质量保障

1. **素材采集中枢测试 (`tests/test_ingest_material.py`)**：
   - 测试切片参数解析（`hh:mm:ss` 正则提取）；
   - Mock 模式下验证 `yt-dlp` CLI 命令构建合法性；
   - 验证音频提取与字幕提取的输出路径与文件规整。
2. **HyperFrames 转译测试 (`tests/test_timeline_to_hyperframes.py`)**：
   - 校验生成的 `index.html` 包含正确的 `data-in` 与 `data-out` 时钟标记；
   - 校验 `hyperframes.json` 中画幅（1080x1920 / 1920x1080）与帧率（30 FPS）符合规范；
   - 校验包含 B-roll 视窗与 Bento 卡片的完整结构。
3. **端到端集成验证**：
   - 构建包含 B-roll 视频切片分镜的示例短片；
   - 分别通过 Remotion 与 HyperFrames 执行渲染并母带压制，验证两端输出均符合 1080p CFR 30fps 及 -11.0 LUFS 标准。

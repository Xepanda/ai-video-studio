# 🎬 AI Video Studio (全链路 AI 视频自动化生产工作室)

> **基于代码即视频 (Code-as-Video) 理念打造的工业级视频自动化流水线**  
> 融合 **自声音克隆 (TTS)**、**阿里 SenseVoice 毫秒级时钟打点**、**Google Flow (Veo) 电影级 AI 镜头** 与 **Remotion 物理无头光栅化渲染**。

---

## 🌟 核心特色与架构

* **声音先行 (Audio-First)**：以音频的物理毫秒长度决定画面生命周期，彻底杜绝音画错位与抽卡不可控性。
* **专属真声音色克隆 (GPT-SoVITS)**：支持使用真实个人录音训练出的专属声音模型 (`epanda_voice`)，实现带个人音色与语调节奏的数字分身配音，并支持本地离线与双轨高可用自动降级。
* **时钟契约 (`timeline.json`)**：Python 极速提取词级时间戳与情绪标签，声明式注入 React 状态机。
* **Google Flow (Veo) 协同**：内置标准提示词工程模板与 `<BrollVideoPlayer />` 组件，无缝混合电影级 AI 视频。
* **五重审查门禁 (`AUDIT_CHECKLIST.md`)**：分镜审查 ➔ 声音对齐 ➔ 视觉动效 ➔ 自动化契约校验 (`validator.py`) ➔ 成品验收。
* **针对 AMD 5800H 物理深度优化**：纯 CPU 极速 ASR 推理 (RTF 0.16) + 6 进程并发 Chrome 光栅化。

---

## 📂 工程全景目录

```text
ai-video-studio/
├── WORKFLOW.md                    # 🎬 Master SOP：串联所有工具与 Skills 的全流程
├── AUDIT_CHECKLIST.md             # 🔍 五重审查审核机制与交付门禁
├── templates/
│   └── PROJECT_SPEC_TEMPLATE.md   # 📋 创作者需求填写模板（只需填此文档即可出片）
│
├── skills/                        # 🧠 8+1 大专业 Skills 知识库与规范
│   ├── live-ecommerce-video-editor/ # 🛍️ 抖音/快手直播带货短视频工业化剪辑（黄金3s/镜像贴纸/双色对比/封面）
│   ├── google-flow-broll/         # Google Flow 镜头提示词与 Web 协同规范
│   ├── remotion/                  # Remotion 底座规范
│   ├── motion-design/             # 阻尼动效法则
│   ├── video-shotcraft/           # 镜头语言与特效
│   ├── handdrawn/                 # 白板手绘擦除
│   ├── pixel2motion/              # 矢量动态 SVG
│   └── gsap/                      # 复杂路径补间
│
├── docs/                          # 📚 深度文档与模型知识库
│   ├── LIVE_ECOMMERCE_SOP.md      # 🛍️ 抖音带货短视频 6 步标准 SOP
│   ├── tools_setup.md             # 各种工具下载、安装与环境配置指南
│   └── knowledge_base/
│       └── ai_video_engines_playbook.md # 📖 ASR/TTS/Google Flow/确定性渲染全模型实测与排坑宝典
│
├── models/                        # 🧠 AI 模型与核心声音资产库
│   ├── gpt_sovits/                # 专属微调导出的声音权重 (.pth / .ckpt)
│   └── reference_audio/           # 提示音频 (5s) 与训练切片数据集
│
├── scripts/                       # 🛠️ 自动化 Python 工具中枢
│   ├── live_ecommerce_pipeline.py # 🛍️ 直播带货短视频全自动切片、打点、大卡合成流水线
│   ├── generate_audio.py          # 多服务商配音生成中枢 (ChatTTS / GPT-SoVITS / Edge-TTS)
│   ├── sensevoice_aligner.py      # SenseVoice 毫秒打点与情绪提取
│   ├── browser_flow_automation.js # 🌐 Google Flow (flow.google.com) 浏览器 CDP 全自动接管引擎
│   ├── validator.py               # 数据契约自动化审查脚本 (Quality Gate)
│   └── pipeline.py                # 一键端到端总控流水线
│
├── public/                        # 📂 静态媒体资产库 (Remotion staticFile 根目录)
│   ├── audio/                     # 生成的克隆 WAV 音频
│   ├── footage/                   # 实拍素材 & Google Flow 生成的 MP4 B-Roll
│   ├── svg/                       # 矢量资产
│   └── timeline.json              # 核心时间轴数据契约
│
├── src/                           # ⚛️ Remotion 视频源码
│   ├── components/                # BrollVideoPlayer / TerminalWindow / DynamicSubtitles
│   ├── templates/                 # 四大形态实现 (科普/自媒体/实战/实拍混剪)
│   ├── Root.tsx                   # 16:9 与 9:16 Composition 注册
│   └── index.ts                   # 渲染入口
│
├── package.json                   # Remotion 与 React 依赖
└── tsconfig.json
```

---

## 🚀 极速起步 (Quick Start)

### 1. 创作者日常做视频只需 3 步：
1. **填表**：复制 `templates/PROJECT_SPEC_TEMPLATE.md` 为 `my_project.md`，填入分镜文案与素材需求。
2. **跑流水线**：
   ```bash
   python scripts/pipeline.py --project my_project
   ```
   自动完成配音生成、SenseVoice 毫秒打点与数据契约自动审查。
3. **预览与出片**：
   ```bash
   # 网页端交互预览
   npm run dev

   # 1080p 多核并发导出
   npm run render
   ```

### 2. 静态数据契约校验：
任何时候均可运行：
```bash
python scripts/validator.py
```
快速检测所有音频、视频文件是否存在，帧数是否无损闭环。

---

## 🎙️ 双轨声音引擎：高保真商业音色与专属真声克隆

本项目内置**双轨可切换的配音引擎架构**，兼顾日常敏捷制作的极速体验与专属个人 IP 的沉淀：

### 1. 默认引擎：微软 Edge-TTS（推荐日常快速出片）
* **音色**：`zh-CN-YunxiNeural`（云希，沉稳大气的科普自媒体专业男声）。
* **优势**：免启动任何本地大模型服务、毫秒级即时合成、零内存占用，适合日常快速迭代与分镜调试。
* **配置方式**：在 `.env` 中设置 `TTS_PROVIDER=edge_tts`（默认即此模式）。

### 2. 专属声音：GPT-SoVITS 个人真声微调模型（保留并随时激活）
* **音色**：基于创作者 3m42s 真实录音微调的专属声纹 (`epanda_voice`)。
* **资产**：
  * `models/gpt_sovits/epanda_voice_e8_s120.pth` (SoVITS 音色模型)
  * `models/gpt_sovits/epanda_voice-e15.ckpt` (GPT 节奏模型)
  * `models/reference_audio/my_voice_ref_5s.wav` (5s 提示基准音频)
* **激活方法**：
  1. 双击运行 `scripts/start_local_sovits.bat`（启动本地 9880 端口 CPU 推理引擎）；
  2. 在 `.env` 中修改为 `TTS_PROVIDER=gpt_sovits`；
  3. 重新运行 `python scripts/pipeline.py ...` 即刻全自动切换为个人专属音色！
* **详细训练与本地推理 SOP**：
  参见知识库 Wiki：[专属音色克隆与全自动微调训练指南 (GPT-SoVITS + Colab 混合云实战)](../wiki/docs/02-projects/ai-video-automation/06-personal-voice-cloning-gpt-sovits.mdx)。


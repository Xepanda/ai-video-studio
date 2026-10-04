# 🎬 AI Video Studio (全链路 AI 视频自动化生产工作室)

> **基于代码即视频 (Code-as-Video) 理念打造的工业级视频自动化流水线**  
> 融合 **自声音克隆 (TTS)**、**阿里 SenseVoice 毫秒级时钟打点**、**Google Flow (Veo) 电影级 AI 镜头** 与 **Remotion 物理无头光栅化渲染**。

---

## 🌟 核心特色与架构

* **声音先行 (Audio-First)**：以音频的物理毫秒长度决定画面生命周期，彻底杜绝音画错位与抽卡不可控性。
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
├── skills/                        # 🧠 7+1 大专业 Skills 知识库与规范
│   ├── google-flow-broll/         # Google Flow 镜头提示词与 Web 协同规范
│   ├── remotion/                  # Remotion 底座规范
│   ├── motion-design/             # 阻尼动效法则
│   ├── video-shotcraft/           # 镜头语言与特效
│   ├── handdrawn/                 # 白板手绘擦除
│   ├── pixel2motion/              # 矢量动态 SVG
│   └── gsap/                      # 复杂路径补间
│
├── scripts/                       # 🛠️ 自动化 Python 工具中枢
│   ├── sensevoice_aligner.py      # SenseVoice 毫秒打点与情绪提取
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

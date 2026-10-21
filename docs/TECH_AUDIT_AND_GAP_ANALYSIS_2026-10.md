# AI Video Studio 全面技术审计与能力差距分析报告

> **审计对象**：`ai-video-studio`（Xepanda/ai-video-studio，master @ f6b166c，2026-10-18）
> **审计视角**：自媒体专家 + 资深视频工作者 + 软件工程
> **审计基线**：本地 master 落后远端 4 个提交（OpenChatCut/HyperFrames 集成、visual QC、增量缓存、技能同步）。因 GitHub 直连被网络阻断（TLS 握手失败），已通过本地已缓存的远端对象检出 `origin/master` 干净工作区完成审计；本地工作区另有一批未提交 WIP（`video_production_engine.py`、`run_all_products.py`、`content/scripts/network_layers_*.json`、`src/components/shorts/{ProtocolStackTower,PacketAssemblyPipeline,RouterPacketInspection,WeChatMobileMockup}.tsx`、`projects_hf/hf_tech_demo/` 等），一并纳入评估。
> **报告日期**：2026-10-21

---

## 0. 执行摘要（结论先行）

**总体判断：这是一条「剪辑车间」世界级、「编辑部」与「运营部」尚未成立的半自动生产线。**

1. **中段生产能力（配音→打点→渲染→质检）达到可商用工程水准**，多项指标超过多数人工团队：音频先行架构从根上消除音画错位；SenseVoice 词级毫秒打点 + 帧守恒校验；EBU R128 双遍母带；黑帧/冻结帧/安全区自动化检测；快照回滚与资产缓存。
2. **但项目存在 2 个 P0 级阻断缺陷**：三个 demo 组件静态导入不存在的 JSON 导致**整个工程无法编译**；`watch_chatcut.js` 守护进程输出路径与渲染层读取路径不一致，OpenChatCut 热同步链路**整体断裂**。
3. **三大目标场景能力呈「一强、一半、一弱」**：知识科普有组件与样片但脚本生成仍是模板拼接；GitHub 演示的「证据截图」实为**本地渲染的仿造页面**（非真实抓取），端到端演示流水线不存在；热点快剪仅覆盖 X 单源且**失败兜底会编造推文数据**（假蓝标、假互动量——已在成品脚本 `network_layers_shorts.json` 中实际使用，构成内容合规风险）。
4. **全链路八大环节中，选题、发布、复盘三个环节完全空白**，平台标准覆盖度约 25% 且集中于抖音带货单点。对标行业（OpusClip/Descript/ultrademo/demo-machine 等 2026 创作者工具栈），差距不在单点工具，而在**流水线的闭环与自动化深度**。
5. **工程化存在系统性欠债**：无 Python 依赖声明（复现性归零）、无 CI、核心 subprocess 全部无超时、质量门禁组件零测试、三套互相矛盾的响度标准并存。

**建议投入顺序**：P0 止血（2 周）→ 三大场景流水线补齐（6-8 周）→ 选题/发布/复盘闭环（8 周）→ 工程化与规模化（持续）。

---

## 1. 现有能力与问题清单

### 1.1 能力资产盘点（按生产环节）

| 环节 | 已有能力 | 成熟度 | 关键证据 |
|---|---|---|---|
| **选题** | 仅关键词五域分类器 | ★ 原型 | `scripts/create_script_from_topic.py`（正则分类→模板字典，无 LLM、无热点源） |
| **素材获取** | yt-dlp 精准切片采集+标准化转码；X 推文抓取；Playwright 通用截屏；Google Flow CDP 半自动 | ★★ 可用 | `scripts/ingest_material.py`（335 行）；`scripts/x_fetcher.py`；`scripts/generate_evidence_screenshots.py` |
| **脚本生成** | PROJECT_SPEC 模板 + 分镜 JSON 契约 + 科技新闻 Shorts 脚手架 | ★★ 可用 | `templates/PROJECT_SPEC_TEMPLATE.md`；`scripts/create_tech_news_shorts.py`（schema 自校验+时长估算） |
| **配音** | 8 提供商 TTS 分层（Edge-TTS 默认/GPT-SoVITS 个人克隆/ChatTTS/Kokoro/F5 等）+ MD5 缓存 + 技术术语 G2P 多音字引擎 | ★★★ 生产级 | `scripts/generate_audio.py`（423 行）；`scripts/tech_phonetic_dict.py`（行→航/调→钓/重→虫） |
| **时钟对齐** | SenseVoice/Paraformer 双引擎 ASR 词级毫秒打点 + 情绪标签，产出 `timeline.json` 唯一契约 | ★★★ 生产级 | `scripts/sensevoice_aligner.py`（392 行，RTF 0.16） |
| **质量门禁** | validator：帧守恒/音频 3 帧容差/words 单调性/组件 Schema/BGM-SFX 强校验；visual_qc：BT.709 黑帧/冻结帧/安全区 | ★★★ 生产级 | `scripts/validator.py`（395 行）；`scripts/utils/visual_qc.py` |
| **渲染** | Remotion（React 声明式）+ HyperFrames（HTML/GSAP）双引擎调度；5800H 6 进程并发光栅化 | ★★★ 生产级 | `scripts/pipeline.py:44-99` 双引擎分流；`scripts/timeline_to_hyperframes.py`（942 行） |
| **母带** | 7 段 DSP 链（HPF→Mud Notch→Presence→压缩→VAD RMS→限幅）+ FFmpeg loudnorm 双遍 EBU R128 + 算法合成 BGM/SFX（无版权风险） | ★★★ 生产级 | `scripts/audio_mastering.py`；`scripts/utils/audio_normalizer.py` |
| **剪辑协同** | OpenChatCut 双向桥（timeline↔project）+ ≤3 帧间隙消毒 + 快照回滚 + 实时 watcher | ★★ 可用（链路断裂，见 1.3） | `scripts/bridge/*.js`；`scripts/utils/snapshot_manager.py` |
| **包装** | 电商封面矩阵（三卡封面/挂角徽标/CTA）；ASS 发光字幕；词级高亮字幕 | ★★ 可用（仅电商场景） | `scripts/video_production_engine.py`（WIP）；`live_ecommerce_batch_pipeline.py` |
| **发布** | **无** | — | 全仓库无发布 SOP、无元数据模板、无多平台分发 |
| **复盘** | **无** | — | 无指标收集/看板/A-B 测试/迭代机制 |

### 1.2 代码质量

| 维度 | 数据 | 评价 |
|---|---|---|
| 规模 | Python 41 文件 11,251 行；TS/TSX 22 文件 6,308 行 | 个人项目中偏大，模块化程度尚可 |
| 异常处理 | 58 处 `except Exception`，其中 **22 处吞异常**（仅 pass/打印） | 降级设计合理处与掩盖故障处混杂 |
| 日志 | 仅 `asset_cache_manager.py` 用标准 logging，其余 40 个文件 `print()` + emoji | 无人值守/CI 场景无法分级采集 |
| 硬编码个人路径 | `pipeline.py:19`、`ingest_material.py:22`、`batch_render_all.py:18` 硬编码 `C:\Users\ePanda\...\liveclip\python.exe`；`create_video_cover.py:16` 指向 `.gemini/antigravity/brain/...`；`live_ecommerce_pipeline.py:137` 模块级 `LiveVideoPipeline("D:/dy-video/project1")` | **可移植性归零**，换机即行为漂移 |
| 死代码 | TTS 回退导入链引用不存在的 `scripts/tts_*.py`（实际在 `scripts/audio_engines/`）；`pipeline.py:115` 无效 flag；`Root.tsx:381,388` 计算后未使用 | 回退路径一旦触发即 ImportError 崩溃 |
| 类型安全 | Root.tsx / UniversalScene.tsx 约 30 处 `any`，timeline 契约编译期无类型（`SceneMeta` 未声明 `startFrame/words/audioPath`） | 类型债务集中在数据入口 |
| 重复逻辑 | ffmpeg 探测 2 份、音频时长探测 3 份、`cmd.exe /c` 包装 3 份、高亮算法 4 份（3 TS + 1 Python）、"安全获取 Remotion 上下文" 8 份 | 重构空间大 |
| 文案硬编码 | Root.tsx Scene01-05 演示分镜全文案、demos/* 三视图、WebBrowserMockupScene 默认 URL 写死个人仓库 | 数据驱动不彻底 |

### 1.3 架构设计

**优点**：
- 音频先行（Audio-First）：以音频物理毫秒长度决定画面生命周期，`timeline.json` 作为唯一时钟契约，由 SenseVoice 生产、validator 校验、双引擎消费，设计理念先进。
- 双引擎调度（Remotion + HyperFrames）与 OpenChatCut 桥接具备工业化雏形；snapshot_manager（先解析源路径再改状态、原子恢复）是全仓设计最稳健的组件。
- 多项目资产隔离（`public/projects/{project}/`）+ 全局镜像预览。

**缺陷**：
1. **P0：工程无法编译**。`src/components/demos/{FireshipKineticView,AppleKeynoteView,MotionCanvasView}.tsx:14` 静态导入 `public/projects/demo_style_*/timeline.json`，文件不存在 → Root.tsx 导入即失败 → dev/render/测试全挂。
2. **P0：watcher 链路断裂**。`scripts/bridge/watch_chatcut.js:20` 写入 `inputs/timeline.json`，而渲染层消费 `public/timeline.json` / `public/projects/{project}/timeline.json`——"OpenChatCut 保存即刷新"的核心卖点不成立，同步产物无消费方。
3. **双引擎契约实质分裂**：HyperFrames 仅支持 Broll/TweetEmbed/BinaryBento，默认时间轴 3/7 幕 WebBrowserMockup 降级为纯大字报；tweet metrics `retweets/views` vs `reposts` 字段不一致；blocksTotal 5 vs 8；dividerText "或" vs 硬编码 "VS"；HF 完全无主题系统。
4. **动态 timeline 路径下静态兜底**：`UniversalScene.tsx:65-71` 从静态默认 timeline 推导 theme/sceneIndex/totalScenes，自定义项目场景编号全部错乱（恒 "SCENE 01/07"）。
5. **安全区体系形同虚设**：唯一成体系的 `ResponsiveSafeArea` Context 全库零使用；同一语义三套数值（组件 220/100 vs SafeArea 280/120 vs AUDIT_CHECKLIST 320/140），竖屏右侧 120px 交互列避让在生效组件中全部缺失。
6. **文档-代码契约断裂**：README 宣称 `<BrollVideoPlayer/>` 为 Google Flow B-roll 唯一入口，实际全库零引用（生效的是 CinematicHeroScene）；README 宣称 10+ Skills，实际 8 个；WORKFLOW.md "7+1 矩阵"中 4 个技能为悬空引用。

### 1.4 功能完整性（对照三大场景）

- **知识科普**：组件资产较丰富（TechNewsShorts 分发器、MinimalHeadline、BinaryBento、ArchitectureTopology、MetricComparison、WhiteboardHanddrawn、PinoutStream、PhoneFrame/CalloutPointer），WIP 中新增协议栈塔/数据包装配/路由器检测/微信拟态四组件（**未提交、未接入路由、无测试**）。但**脚本生成无 LLM**（纯模板拼接），无数学公式/时序图/状态机等学科可视化引擎，无嵌入式专用素材体系（ datasheet 图/原理图/示波器波形）。
- **GitHub 演示**：**端到端能力不存在**。`generate_evidence_screenshots.py:24-347` 的 `GITHUB_HTML`/`NEJM_HTML` 是本地渲染的**仿造页面**（非真实抓取 GitHub/期刊），唯一真实浏览器能力是通用 `capture_url()`（且 `channel="msedge"` 硬编码）。全仓无 `git clone`、无依赖安装、无 dev server 启动、无 asciinema 类终端录制。TerminalWindow 按终端渲染代码场景（无语法高亮、无文件树）。
- **热点快剪**：仅 X 单源（fxtwitter/oEmbed）+ 3 条预设；**`x_fetcher.py:228-243` 四级降链最终兜底编造数据**（`isVerified: True`、假 timeAgo/互动量、content 回显用户输入），且该编造数据已实际进入成品脚本（`network_layers_shorts.json` 的 Vint Cerf 推文：2.4K 回复/15.8K 转推/1.2M 浏览均为虚构）。无热榜监测、无 LLM 解说生成、无平台热门音轨体系、无时效性工作流。

### 1.5 稳定性

| 问题 | 证据 | 影响 |
|---|---|---|
| 核心 subprocess 全部无超时 | 仅 `hf_builder.py:198-260` 有 180s timeout；`pipeline.py:29`（shell=True 字符串命令）、`ingest_material.py:184`、`audio_mastering.py:248`、`batch_render_all.py:142-151` 均无 | 任一子进程挂起无限阻塞整条流水线 |
| 无重试机制 | 除 edge_tts 3 次重试外，渲染/转码/下载一次定生死 | 网络波动即整批失败 |
| 命令注入面 | `pipeline.py:69,83`、`batch_render_all.py:250` 项目名/路径拼 shell 字符串 | 含引号路径即注入风险 |
| 文件存在性无检查 | `batch_render_all.py:239-240` 直接 `open(tl_path)`；`create_video_cover.py` import 时即执行复制 | 错误信息不可读 / import 即崩 |
| 多项目全局状态竞态 | `sensevoice_aligner.py:330-337` 并发覆盖全局 timeline.json；`generate_audio.py:304-313` 孤儿清理跨项目误删 | 并行生产互相污染 |
| 缺失资产零降级 | 全部场景 mp3/BGM/SFX/real_sample.mp4 在本 checkout 不存在且无检查；默认 MasterVideo 无法出片 | clean checkout 不可渲染 |
| 原生 `<img>` 加载截图 | `WebBrowserMockupScene.tsx:239` 未用 Remotion `<Img>`（无 delayRender） | 无头渲染截图未加载完即抓帧，空白/闪烁 |
| 字体无加载机制 | 全库无 `loadFont`/`@remotion/google-fonts`，直接引用系统字体名 | Linux 渲染容器字形漂移/中文 tofu |
| 零/负时长击穿 | `timeline_sanitizer.js:109-112` 吸附分支无 `Math.max(0,…)` | `<Sequence durationInFrames={0}>` 渲染崩溃 |
| TS 测试与实现脱节 | `test_shorts_dispatcher.ts:139-144,237-241` 三处断言必 FAIL，且未接入任何 npm script | 质量门禁形同虚设 |

### 1.6 工程化程度

| 项 | 状态 |
|---|---|
| Python 依赖声明 | **无**（无 requirements.txt / pyproject.toml）——funasr/misaki/f5-tts 等冷门包无版本锁定，复现完全依赖个人 liveclip 环境 |
| CI/CD | **无**（无 .github/workflows） |
| 测试接入 | `npm run test:all` 仅跑 bridge + 3 个 Python 测试文件；9 个 Python 测试文件未接入；4 个 TS 测试未接入且断言脱节 |
| 测试覆盖 | 97 个 Python 用例集中于纯函数；**validator.py（最该测的质量门禁）零覆盖**；`test_aligner_whitelist.py` 为同义反复测试（断言源码含字符串） |
| 技能仓库治理 | `skills/` 与 `.agents/skills/` 双副本已漂移（project-case-study 技能内容不一致）；f6b166c 声称 "synchronize all 8 skills" 实际未同步；`.skills/ai-video-production` 未登记 |
| 标准一致性 | 响度三套矛盾：-16 LUFS（remotion 技能）vs -11~-14（tech-tutorial/playbook）vs -10.0~-11.5（audio_mastering.py）；底部安全区三套数值 |

---

## 2. 对标差距分析（三类核心场景）

### 2.1 行业基准（2026）

**平台算法与运营标准**（综合抖音/B站/小红书/YouTube 公开方法论）：
- 黄金 3 秒决定约 70% 完播率；开场四模板（悬念/利益/冲突/结果前置）；每 5-8 秒一个小高潮；结尾引导互动。
- 抖音：完播率>30%、互动率>8% 进下一级流量池；热门 BGM 加成 20-30%；封面大字标题。
- B站：完播率+投币权重高；横屏 16:9、5-15 分钟、章节标记、三连引导。
- 小红书：搜索+推荐双驱动，重收藏；标题埋关键词；3:4 封面；发布时间 20:00-23:00。
- YouTube：thumbnail CTR、retention 曲线、chapters、说明区 SEO、双语字幕。
- 全平台：1080P+、字幕清晰重点标色、禁带别平台水印、错峰发布（间隔 30 分钟-2 小时）。

**技术科普标杆工作流**（3Blue1Brown/Fireship/Hyperplexed）：
- 3B1B：问题→张力→解决的"发现之旅"叙事；Manim 程序化动画（代码即视觉，精确可复现）；视觉服务直觉而非装饰；Peer Review 事实校验。
- Fireship：高密度信息交付、5-10 秒 hook、快节奏剪辑、强观点。

**工具链基准**（2026 创作者栈）：OpusClip（长→短自动切片+动态字幕）、Descript（文本剪辑）、CapCut（终修）、ultrademo/demo-machine（demo 视频即代码：flow/spec 文件→Playwright 捕获→TTS→Remotion 渲染）、asciinema（终端录制）、Buffer/Hypefury（多平台排期发布）、ThumbnailAI（封面 A/B）。

### 2.2 场景一：知识科普类（STM32 原理、计算机网络 → 短视频）

| 能力项 | 行业标准 | studio 现状 | 差距 |
|---|---|---|---|
| 叙事结构 | 问题-张力-解决；hook 5-10s；每 5-8s 小高潮 | 五段式循证叙事（仅 science-pop 技能）；无钩子公式库 | **中**：科普技能缺 hook 方法论与认知张力设计 |
| 脚本生成 | LLM 辅助 + 人工审校；对标视频拆解学习 | 纯本地模板拼接（`create_script_from_topic.py` 五域字典，440 行大函数） | **大**：无 LLM 接入、无对标拆解、无事实核查 |
| 学科可视化 | Manim 类程序化动画；时序图/状态机/公式/波形 | 协议栈塔/数据包装配（WIP 未接入）；WhiteboardHanddrawn；PinoutStream（仅 3 pin 硬编码） | **大**：无公式渲染（KaTeX）、无时序图/状态机组件、无示波器/波形、无 datasheet/原理图素材体系 |
| 音画同步 | — | 毫秒级词级打点，全行业领先 | **无差距（核心优势）** |
| 字幕 | 动态字幕、静音可看懂 | 词级高亮 + 防闪烁桥接（质量最高细节之一） | 小：单时间源单行显示，快语速"逐词跳字" |
| 双引擎一致性 | — | HF 丢 WebBrowserMockup 等 5 类场景 | 中：需场景能力矩阵对齐 |
| 科普样片验证 | — | `network_layers_*`（WIP）+ 11 支长视频矩阵 + 循证科普 ep01 | 已有基础，但未提交/未测试 |

**场景一小结**：组件方向正确（协议栈/数据包/路由器拟态正是计算机网络科普的刚需），但「脚本智能生成」与「学科可视化深度」两处断层明显；WIP 四组件处于"未提交、未接路由、无测试"的悬空状态，需立即纳入主干并补契约测试。

### 2.3 场景二：GitHub 项目深度演示类（输入链接→自动拉取/运行/截图/录屏→演示视频）

| 能力项 | 行业标准（ultrademo/demo-machine/asciinema） | studio 现状 | 差距 |
|---|---|---|---|
| 端到端流水线 | spec/flow 文件驱动：clone→install→run→Playwright 捕获→storyboard→TTS→Remotion | **不存在**；无 clone/install/run 任何代码路径 | **极大（场景核心能力缺失）** |
| 真实截图 | 真实浏览器会话捕获 + trace + events.json | `generate_evidence_screenshots.py` 是**本地 mock HTML**（仿 GitHub/NEJM 页面）；唯一真实能力是通用 capture_url（msedge 硬编码、networkidle 30s） | **极大**：mock 页面用于公开内容有误导风险；需建真实捕获管线 |
| 终端/代码呈现 | asciinema 终端录制；IDE 组件（语法高亮/文件树/选区） | TerminalWindow 打字机（匀速、无语法高亮、output 整块出现）；codeSnippet 场景按终端渲染 | **大**：需 IDE 组件 + asciicast 解析播放 |
| 演示叙事 | 60-90s 单一用例跑通为主，忌架构大全景 | project-case-study 技能有五段式工程叙事 | 小：叙事规范已有，缺自动化串联 |
| 质量验证 | capture verification + quality.json + trace 复盘 | visual_qc 黑帧/冻结/安全区 | 中：缺捕获级验证（截图证据链） |
| 版本联动 | release 时自动重生成 demo，README 嵌入 | 无 | 中 |

**场景二小结**：这是三大场景中差距最大的。名称带有误导性的 `generate_evidence_screenshots.py`（宣称"高质量真实证据链截图"实为仿造页面）必须整改——要么补真实 URL 抓取路径，要么更名并显式标注"示意图"。建议以 demo-machine 的 spec 驱动架构为蓝本，复用已有 Playwright 基础与 TerminalWindow/WebBrowserMockupScene 组件。

### 2.4 场景三：热点快剪类（社交媒体热点→分钟级解说视频）

| 能力项 | 行业标准 | studio 现状 | 差距 |
|---|---|---|---|
| 热点监测 | 微博热搜/抖音热榜/X Trends/B站热榜多源 + 选题评估（时效/受众/差异化） | 仅 X 单源 + 3 条预设推文；无热榜 | **大** |
| 抓取可靠性 | 多通道 + 显式失败 | fxtwitter/oEmbed/预设/**编造数据**四级降链 | **极大（合规风险）**：假蓝标+假互动量已进入成品脚本 |
| 脚本生成 | LLM 快稿 + 事实核查 + 信源标注 | 无 LLM；无核查流程 | **大** |
| 快剪组件 | 推文卡/大字报/二元对比/评论串/trending 数字动画 | TweetEmbedCard（拟态质量高）+ MinimalHeadline + BinaryBento；38s codex 样片跑通 | 中：缺评论串组件、缺 trending 动画、超长推文无截断 |
| 音轨/贴纸 | 平台热门 BGM/贴纸/特效模板（流量加成 20-30%） | 算法合成 BGM（版权安全但非热门音轨） | 中 |
| 时效工作流 | 小时级产出；发布节奏/冷启动运营 | 无 | **大** |
| 合规 | AI 生成内容显著标注（2025《人工智能生成合成内容标识办法》+ 平台强制）；极限词审查 | 仓库零覆盖 | **大（监管硬性要求）** |

**场景三小结**：组件层已具备快剪形态（38 秒样片证明管线可跑通），但**数据源真实性是最大隐患**——`x_fetcher.py:228-243` 的编造兜底与 `network_layers_shorts.json` 中虚构的 Vint Cerf 推文指标组合，意味着按当前代码持续生产会系统性产出"看似真实的虚假证据"，必须优先修复。

---

## 3. 缺失的能力、工具、素材与专业技能明细

### 3.1 能力（软件功能）

| # | 缺失能力 | 对应场景 | 优先级 |
|---|---|---|---|
| C1 | LLM 脚本/分镜生成引擎（接入本地或云端 LLM，输出分镜 JSON 契约） | 全部 | P0 |
| C2 | GitHub demo 端到端流水线（clone→env→run→capture→narrate→render，spec 驱动） | 场景二 | P0 |
| C3 | 真实证据截图管线（Playwright 真实会话 + 截图台账 + 版本快照） | 场景二 | P0 |
| C4 | 多源热点聚合（微博/抖音/X/B站热榜 + RSS + 去重 + 选题评分） | 场景三 | P1 |
| C5 | IDE/代码编辑器组件（语法高亮/文件树/标签页/选区动画） | 场景二 | P1 |
| C6 | 学科可视化组件库（公式 KaTeX、时序图、状态机、波形、协议交互图） | 场景一 | P1 |
| C7 | 终端录制播放（asciicast 解析 + 播放器组件） | 场景二 | P1 |
| C8 | 长视频→ shorts 自动切片（对标 OpusClip：精彩度评分+自动裁切+动态字幕） | 场景三/全场景 | P1 |
| C9 | 多平台多规格批量导出（16:9/9:16/3:4/1:1 派生 + 平台元数据模板） | 全场景 | P1 |
| C10 | 发布与排期（多平台元数据/封面 A/B/定时发布/错峰） | 全场景 | P1 |
| C11 | 数据复盘闭环（指标收集/看板/完播率诊断/A-B 测试/反哺选题） | 全场景 | P2 |
| C12 | 选题库与对标拆解（爆款要素结构化、选题通过率标准） | 全场景 | P2 |
| C13 | 事实核查 SOP 工具化（参数/版本/数据三源核查、引用快照存档） | 场景一/二/三 | P1 |
| C14 | 版权与合规工具（素材授权台账、AI 标注、极限词审查、字体/音乐授权矩阵） | 全场景 | P1 |
| C15 | 评论/私域运营辅助（置顶评论模板、预埋提问、应对话术） | 场景三 | P2 |

### 3.2 工具（工程基础设施）

| # | 缺失工具 | 现状 | 优先级 |
|---|---|---|---|
| T1 | `requirements.txt`/`pyproject.toml` + 版本锁定（funasr/misaki/f5-tts/edge-tts） | 无 | P0 |
| T2 | CI（GitHub Actions：eslint + tsc --noEmit + pytest + 契约测试 + 编译门禁） | 无 | P0 |
| T3 | 统一日志（logging 模块 + 级别 + 结构化） | print+emoji | P1 |
| T4 | subprocess 统一封装（timeout + 有限重试 + 可读错误） | 仅 hf_builder 有 | P0 |
| T5 | 环境变量化配置（`AVS_PYTHON` 等替代硬编码路径） | 硬编码 | P0 |
| T6 | timeline JSON-Schema + 契约测试（合法/非法 fixture 各一组） | validator 零测试 | P0 |
| T7 | TS 测试接入 `npm test` 并修正脱节断言 | 未接入且必 FAIL | P0 |
| T8 | 任务队列/断点恢复（长渲染可恢复、失败可续跑） | 无 | P2 |
| T9 | 素材库资产化管理（DAM：标签/检索/授权状态） | 散落 public/ | P2 |
| T10 | 演示服务器沙箱（项目 clone 后隔离 run，防依赖污染主机） | 无 | P1 |

### 3.3 素材（内容资产）

| # | 缺失素材体系 | 说明 | 优先级 |
|---|---|---|---|
| M1 | 嵌入式学科素材库 | STM32/ESP32 数据手册图、原理图、寄存器表、示波器波形、时钟时序图 | P1 |
| M2 | 网络协议素材库 | 协议交互图（三次握手/HTTP/TLS）、封包格式图、Wireshark 截图模板 | P1 |
| M3 | 代码高亮主题与 IDE 皮肤 | VS Code Dark+ 等 3-5 套，配合 IDE 组件 | P1 |
| M4 | 平台热门音轨库（商用授权） | 抖音热门 BGM 白名单/版权音乐源 | P1 |
| M5 | 封面模板矩阵 | 分平台（B站 16:9/小红书 3:4/YouTube 1280x720）分风格（大字报/三卡/极简） | P1 |
| M6 | 钩子开场模板库 | 悬念/反常识/数据冲击/冲突对峙四类 × 分场景 | P1 |
| M7 | 品牌资产（Logo/片头片尾/转场音效/水印） | 个人 IP 一致性 | P2 |

### 3.4 专业技能（团队知识沉淀）

| # | 缺失技能 | 现状 | 优先级 |
|---|---|---|---|
| S1 | 热点快剪 SKILL（模板已建成但未登记，`workflows/README.md` 未收录） | 能力已建成、规范未沉淀 | P0 |
| S2 | GitHub 项目演示 SKILL | 无 | P0 |
| S3 | 选题方法论 SKILL（热榜→评估→立项） | 无 | P1 |
| S4 | 发布与运营 SKILL（分平台元数据/发布时间/冷启动） | 无 | P1 |
| S5 | 数据复盘 SKILL（24h/72h/7d 指标模板/完播诊断/A-B） | 无 | P1 |
| S6 | 合规审查 SKILL（AI 标注/极限词/版权/事实核查清单） | 无 | P1 |
| S7 | 学科可视化 SKILL（Manim 思想 + 组件选型指南） | 无 | P2 |
| S8 | 技能仓库治理（README 悬空引用清理、skills/ 与 .agents/skills/ 同步、登记 .skills/ai-video-production） | 已漂移 | P0 |

---

## 4. 分阶段可落地的流水线建设路线图

> 目标：完整跑通「选题 → 素材获取 → 内容生成 → 剪辑包装 → 发布」全流程。每阶段给出交付物与验收标准。

### Phase 0：止血与可复现（第 1-2 周）

**目标**：消除 P0 缺陷，让任何人在干净环境跑通编译与测试。

| # | 任务 | 验收标准 |
|---|---|---|
| 0.1 | 新增 `requirements.txt`（锁定 funasr/edge-tts/misaki/chattts 等），`LIVECLIP_PYTHON` 改 `AVS_PYTHON` 环境变量（保留回退） | 新克隆仓库 `pip install -r` 后 `python scripts/validator.py` 可运行 |
| 0.2 | 修复三个 demo 组件缺失 JSON（随管线生成并纳入资产清单，或改 props 注入） | `npx tsc --noEmit` 与 `npm run dev` 编译通过 |
| 0.3 | 统一 watcher 输出路径（`public/timeline.json`）或让 pipeline 消费 `inputs/`，更新文档 | OpenChatCut 保存→Remotion 预览刷新链路实测通过 |
| 0.4 | `x_fetcher.py:228-243` 编造兜底改为显式失败或 `isSynthetic: true` 标记（渲染层同步标注） | 断网状态下不再产出"真实外观"假推文 |
| 0.5 | subprocess 统一封装：timeout（渲染 30min/转码 10min/下载 15min）+ 有限重试 + 可读错误 | 全仓无裸 `subprocess.run` 无超时调用 |
| 0.6 | 接入 CI（GitHub Actions：lint + tsc + pytest + test:bridge），TS 测试修正断言后接入 `npm test` | PR 合并前门禁全绿 |
| 0.7 | 统一响度标准（建议：平台适配表——抖音/Reels -14 LUFS / YouTube -14 / B站 -14，TP≤-1.5），清理三套矛盾文档 | AUDIT_CHECKLIST/技能/代码注释数字一致 |
| 0.8 | 修复 sanitizer 负 duration、`<img>`→`<Img>`、batch_render 存在性检查 | 已知 P1 清单清零 |

### Phase 1：三大场景流水线补齐（第 3-10 周）

**场景一（知识科普）**：
- 1.1 将 WIP 四组件（ProtocolStackTower/PacketAssemblyPipeline/RouterPacketInspection/WeChatMobileMockup）提交主干，接入 UniversalScene 路由注册表，补 dispatcher 契约测试（对齐 test_shorts_dispatcher 模式）。
- 1.2 新建 `scripts/llm_scriptgen.py`：LLM（本地 Qwen/DeepSeek 或云端 API）将主题/大纲转为分镜 JSON 契约，保留人工审校门；`create_script_from_topic.py` 模板降级为离线兜底。
- 1.3 学科可视化：接入 KaTeX 公式组件；补时序图/状态机组件（数据驱动）；PinoutStream 改为 pin 配置数据驱动。
- 1.4 沉淀「知识科普」SKILL：钩子公式库（悬念/反常识/数据冲击）、认知张力叙事模板、事实核查清单（技术参数三源核查+引用快照）。

**场景二（GitHub 演示）**：
- 2.1 新建 `scripts/github_demo_pipeline.py`（对标 demo-machine 的 spec 驱动）：`.demo.yaml`（clone URL/安装命令/启动命令/步骤流）→ 沙箱 clone+install+run → Playwright 捕获（截图+录屏+events）→ storyboard.json → TTS 配音 → 双引擎渲染。
- 2.2 `generate_evidence_screenshots.py` 整改：保留 `capture_url()` 真实抓取能力为默认路径，mock HTML 更名 `mock_pages.py` 并强制 `isMock: true` 标注；补截图台账（URL/时间/哈希）。
- 2.3 IDE 组件（语法高亮+文件树+标签页）+ asciicast 终端播放组件。
- 2.4 沉淀「GitHub 项目演示」SKILL：60-90s 单一用例叙事规范、demo 与 repo release 联动重生成流程。

**场景三（热点快剪）**：
- 3.1 多源热点聚合器（微博热搜/抖音热榜/X Trends/B站热榜 API+RSS）→ 选题评分（时效/受众匹配/差异化/风险）→ 选题库。
- 3.2 LLM 快稿 + 事实核查门（信源链接必填、AI 生成标注自动附加）。
- 3.3 补评论串组件、trending 数字动画、长推文截断策略。
- 3.4 沉淀「热点快剪」SKILL 并登记入 workflows 矩阵（含小时级时效 SOP）。
- 3.5 平台热门音轨白名单 + 版权音乐源接入（BGM 层与算法合成并存，热门音轨需授权核查）。

### Phase 2：全链路闭环（第 11-18 周）

- 4.1 **选题系统**：选题库结构、评估维度、通过率标准、对标账号拆解方法（SKILL + 工具）。
- 4.2 **发布系统**：多平台元数据模板（标题公式/话题标签/简介 SEO/封面尺寸矩阵：B站 16:9、小红书 3:4、YouTube 1280×720）；定时发布与错峰排期；水印规范（禁外平台水印）。
- 4.3 **数据复盘闭环**：发布后指标收集（播放/完播/互动/转化）→ 24h/72h/7d 复盘模板 → 完播率曲线诊断（前 3 秒流失/中段流失对策）→ 封面标题 A/B 测试 → 反哺选题。
- 4.4 **合规体系**：AI 生成内容标注操作手册（平台合规硬性要求）；素材授权台账；字体/音乐授权矩阵；极限词审查清单；技术内容免责声明。
- 4.5 **多规格派生导出**：一母版自动派生横竖屏版本（含 ResponsiveSafeArea 真正上岗，统一安全区数值）。
- 4.6 **长→短切片**：基于 ASR 精彩度评分的长视频自动切片（对标 OpusClip），喂给场景三与 shorts 矩阵。

### Phase 3：工程化与规模化（第 19 周起，持续）

- 5.1 可移植渲染（Docker/Linux 容器 + 字体锁定 + ffmpeg 版本锁定）。
- 5.2 任务队列与断点恢复（渲染可恢复、失败续跑、WIP 版本化）。
- 5.3 素材资产化管理（DAM：标签/检索/授权状态/复用率）。
- 5.4 性能与成本（渲染并发优化、缓存命中率监控、TTS 配额管理）。
- 5.5 技能仓库治理常态化（双副本同步脚本、SKILL.md 校验 CI）。

### 路线图总览

```
Phase 0 (W1-2)   止血与可复现     P0 缺陷清零 / CI 绿 / 依赖可复现
Phase 1 (W3-10)  三大场景流水线    科普 LLM 化 / GitHub demo 端到端 / 热点多源+合规
Phase 2 (W11-18) 全链路闭环       选题→发布→复盘 / 合规体系 / 多规格派生
Phase 3 (W19+)   工程化规模化      容器化 / 队列恢复 / DAM / 成本优化
```

---

## 5. 全链路覆盖矩阵（现状 vs 目标）

| 环节 | 现状 | Phase 0 后 | Phase 1 后 | Phase 2 后 |
|---|---|---|---|---|
| 选题 | ❌ | ❌ | ⚠️（热点聚合+评分） | ✅（选题库+方法论） |
| 素材获取 | ⚠️（X 单源/mock 截图） | ⚠️ | ✅（多源+真实捕获） | ✅（DAM） |
| 内容生成（脚本） | ⚠️（模板拼接） | ⚠️ | ✅（LLM+审校） | ✅（对标拆解） |
| 配音 | ✅ | ✅ | ✅ | ✅ |
| 渲染/剪辑 | ✅（双引擎） | ✅ | ✅（三场景组件齐备） | ✅（多规格派生） |
| 包装 | ⚠️（仅电商） | ⚠️ | ✅（分平台封面/音轨） | ✅（A/B 测试） |
| 发布 | ❌ | ❌ | ⚠️（元数据模板） | ✅（排期+分发） |
| 复盘 | ❌ | ❌ | ❌ | ✅（指标闭环） |
| 合规 | ❌ | ⚠️（AI 标注/极限词） | ✅（核查 SOP） | ✅（授权台账） |

---

## 6. 风险提示

1. **内容合规风险（最高优先级）**：`x_fetcher.py` 编造数据兜底 + 已用于成品的虚构推文指标，若持续生产公开发布，构成虚假信息传播风险；AI 生成内容未按《人工智能生成合成内容标识办法》及平台规则标注，有限流/下架风险。
2. **误导性组件**：`generate_evidence_screenshots.py` 名不副实（仿造页面充当证据截图），用于 GitHub 演示场景会损害账号专业可信度。
3. **可复现性风险**：无 Python 依赖声明 + 个人路径硬编码，项目无法移交/协作/上云。
4. **迭代失同步风险**：README/WORKFLOW 与代码实体大面积脱节（悬空技能引用、零引用组件宣称为核心入口、TS 测试必 FAIL），团队认知成本极高。
5. **网络依赖**：GitHub 直连不稳定（本次审计即受阻），素材抓取/Flow 自动化/模型下载均需可降级的多通道设计。

---

## 附录 A：关键证据索引

| 问题 | 位置 |
|---|---|
| demo 组件导入缺失 JSON（P0） | `src/components/demos/FireshipKineticView.tsx:14`、`AppleKeynoteView.tsx:14`、`MotionCanvasView.tsx:14` |
| watcher 路径断裂（P0） | `scripts/bridge/watch_chatcut.js:20` vs `src/Root.tsx:3` |
| 编造推文数据兜底（P0） | `scripts/x_fetcher.py:228-243` |
| 仿造 GitHub 页面（P0） | `scripts/generate_evidence_screenshots.py:24-347` |
| 硬编码个人 Python 环境 | `scripts/pipeline.py:19`、`ingest_material.py:22`、`batch_render_all.py:18` |
| 无超时 subprocess | `scripts/pipeline.py:29`、`ingest_material.py:184`、`audio_mastering.py:248` |
| TTS 回退导入断裂 | `scripts/generate_audio.py:152,175,185,195` |
| 多项目竞态 | `scripts/sensevoice_aligner.py:330-337`、`generate_audio.py:304-313` |
| 双引擎契约分裂 | `scripts/timeline_to_hyperframes.py:247-256,87-89,143,159` |
| 安全区三套数值 | `TechNewsShortsScene.tsx:272` / `ResponsiveSafeArea.tsx:48-66` / `AUDIT_CHECKLIST.md:50-54` |
| 虚构推文指标进入成品 | `content/scripts/network_layers_shorts.json` scene_02 |
| 响度三套矛盾 | remotion 技能 -16 LUFS / tech-tutorial -11~-14 / `audio_mastering.py` -10.0~-11.5 |
| TS 测试脱节未接入 | `tests/test_shorts_dispatcher.ts:139-144,237-241`、`package.json:26-30` |
| 无 Python 依赖声明 | 仓库根无 requirements.txt/pyproject.toml |
| 无 CI | 无 .github/workflows |

## 附录 B：审计方法与范围

- 代码基线：`origin/master` f6b166c（2026-10-18）干净检出 + 本地工作区未提交 WIP。
- 范围：`scripts/`（41 Python 文件，11,251 行）、`src/`（22 TS/TSX，6,308 行）、`scripts/bridge/*.js`、`tests/`（97 Python 用例 + 6 bridge + 4 TS）、`skills/`（8+1）、`docs/`、`workflows/`、`templates/`、`content/scripts/`（21 剧本）、`projects_hf/`。
- 行业基准：2026-10-21 检索的平台运营方法论、3Blue1Brown/Fireship 创作流程、2026 创作者 AI 工具栈（OpusClip/Descript/ultrademo/demo-machine 等）。
- 局限：`out/` 目录为空（成品 MP4 未入库），成片观感质量无法直接验证，仅能验证工程链路；WIP 组件未提交主干，其集成度按悬空状态评估。

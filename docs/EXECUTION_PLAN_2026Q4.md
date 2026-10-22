# AI Video Studio 完善方案执行计划（2026 Q4）

> **依据**：《TECH_AUDIT_AND_GAP_ANALYSIS_2026-10.md》（2026-10-21 全面技术审计报告）
> **当前分支**：`feature/phase0-stabilization`（Phase 0 已提交 `2d84559`）；Phase 1 W3-4 进行中（分支 `feature/phase1-w3-4-scenario-pipelines`）
> **目标**：修复 P0 缺陷、补齐工程化基建，为三大场景流水线（知识科普 / GitHub 演示 / 热点快剪）与全链路闭环（选题→发布→复盘）奠定可落地基础。
> **本计划状态**：Phase 0（任务组 A/B/C）已实施完成并通过全量验证；Phase 1 W3-4（四组件入主干 + 路由注册表 / GitHub demo 流水线立项 / 多源热点聚合器 v1）已实施完成并通过全量验证（Python 129/129、bridge 6/6、TS 5 文件全过、tsc 0 错误）；W5-10 待用户确认启动（见文末实施记录）。

---

## 一、总体路线图

| 阶段 | 周期 | 主题 | 核心目标 | 出口验收标准 |
|---|---|---|---|---|
| **Phase 0** | 第 1-2 周 | 止血与可复现 | P0 缺陷清零、依赖可复现、CI 门禁建立 | 干净环境 `pip install -r requirements.txt` 后可跑通 validator；`tsc --noEmit` 与全部测试通过；PR 合并前门禁全绿 |
| **Phase 1** | 第 3-10 周 | 三大场景流水线 | 知识科普 LLM 化 / GitHub demo 端到端 / 热点多源+合规 | 三个场景各跑通 1 条完整样例视频并入库 |
| **Phase 2** | 第 11-18 周 | 全链路闭环 | 选题→发布→复盘/AI 标注合规/多规格派生 | 一条视频从选题到发布到复盘全流程留痕 |
| **Phase 3** | 第 19 周起 | 工程化与规模化 | 容器化/队列恢复/DAM/成本优化 | 渲染可移植、可恢复、可度量 |

---

## 二、Phase 0 详细任务分解（本次实施范围）

### 任务组 A：P0 缺陷修复（优先级最高）

| # | 任务 | 具体步骤 | 负责角色 | 工时 | 预期成果 | 验收标准 |
|---|---|---|---|---|---|---|
| A1 | demo 组件编译失败修复 | 三个 demo 视图的静态 JSON 导入改为运行时安全加载（`src/utils/safeDemoTimeline.ts` + context require + 降级空时间轴） | 前端 | 2h | `tsc --noEmit` 与 webpack 构建通过 | `npm run dev` 可启动；demo 组合降级渲染不崩溃 |
| A2 | watcher 路径断裂修复 | `watch_chatcut.js` 输出改 `public/timeline.json`；写文件改临时文件+原子替换；`fs.watch` 增加 error 处理 | 前端 | 1.5h | OpenChatCut 保存→Remotion 预览刷新链路打通 | `node scripts/bridge/watch_chatcut.js --once` 退出码 0 且 public/timeline.json 更新 |
| A3 | x_fetcher 编造数据整改 | 删除"高保真生成式推文契约"兜底，改显式 `XFetchError`；`convert_to_scene` 的 metrics/isVerified 假默认值改为诚实默认（0/False）；CLI 捕获并给出可读错误 | 后端 | 2h | 断网/失效输入不再产出"真实外观"假推文 | 单测覆盖：全部通道失败时抛错；preset 通道仍可用 |
| A4 | 硬编码路径环境变量化 | 新增 `scripts/utils/runtime.py`（`AVS_PYTHON` 解析 + `run_command` 统一封装）；pipeline/ingest/batch_render 三处 `LIVECLIP_PYTHON` 改调用 runtime；`create_video_cover.py` 的 SRC_IMAGE 改 `AVS_COVER_SRC` 环境变量并加 main 守卫 | 后端 | 3h | 换机不再锁定个人 conda 环境 | 无 AVS_PYTHON 时回退 `sys.executable` 且行为一致 |

### 任务组 B：稳定性加固

| # | 任务 | 具体步骤 | 工时 | 预期成果 | 验收标准 |
|---|---|---|---|---|---|
| B1 | subprocess 超时与重试 | runtime.run_command 增加 timeout（默认 1800s）+ 有限重试（默认 1 次）；pipeline.py run_step、ingest_material.py、audio_mastering.py、batch_render_all.py run_cmd 全部切换 | 3h | 子进程挂起不再无限阻塞 | 全仓无裸 `subprocess.run` 无超时调用（脚本化核查） |
| B2 | sanitizer 负时长修复 | `timeline_sanitizer.js:111` 吸附分支补 `Math.max(0, …)` 保护 | 0.5h | 极短分镜不再产生 0/负 duration | `test_bridge.js` 增加吸附边界用例并通过 |
| B3 | 证据截图延迟加载 | `WebBrowserMockupScene.tsx` 原生 `<img>` 改 Remotion `<Img>` | 0.5h | 无头渲染等待截图解码完成 | tsc 通过；组件快照测试（如有）通过 |
| B4 | 批量渲染存在性检查 | `batch_render_all.py:239` open 前检查文件存在并给出可读错误 | 0.5h | 缺失时间轴时错误信息可读 | 构造缺失场景手动验证 |

### 任务组 C：工程化基建

| # | 任务 | 具体步骤 | 工时 | 预期成果 | 验收标准 |
|---|---|---|---|---|---|
| C1 | Python 依赖声明 | 新建 `requirements.txt`：核心依赖（edge-tts/requests/numpy/scipy/soundfile/pillow/pypinyin/pyyaml/playwright/yt-dlp）+ 可选重依赖分组注释（funasr/torch/torchaudio/ChatTTS/f5-tts/faster-whisper/onnxruntime/misaki/gradio_client） | 1h | 新环境可复现 | 干净 venv 安装核心组后 `python -m py_compile scripts/*.py` 通过 |
| C2 | CI 工作流 | `.github/workflows/ci.yml`：Python 语法检查 + unittest 发现式测试 + `node --check` 全部 JS + `tsc --noEmit` + bridge 测试 | 1.5h | PR 门禁 | 本地模拟 CI 步骤全部通过 |
| C3 | 测试接线 | package.json 增加 `test:py`（unittest discover）、`test:ts`（tsc 编译+node 运行）；修正 `test_shorts_dispatcher.ts` 三处脱节断言 | 3h | `npm run test:all` 覆盖 11 个 Python 文件 + bridge + TS | 全部通过；CI 可调用同一命令 |
| C4 | 响度标准统一 | 统一为平台适配表：抖音/YouTube/B站/Reels **-14 LUFS / TP ≤ -1.5 dBTP**；`audio_mastering.py` 默认值调整 + 环境变量 `AVS_LOUDNESS_LUFS` 覆盖；AUDIT_CHECKLIST、remotion 技能、tech-tutorial 技能、pipeline docstring 同步 | 1.5h | 三套矛盾数字归一 | 全仓检索无 -16/-11.0 旧标准残留（文档注释除外的历史说明需标注） |

**Phase 0 总工时估算**：约 20 小时（1 人 × 2.5 个工作日，含验证）。

---

## 三、Phase 1-3 概要（后续排期）

### Phase 1（第 3-10 周）：三大场景流水线

| 周次 | 场景一：知识科普 | 场景二：GitHub 演示 | 场景三：热点快剪 |
|---|---|---|---|
| W3-4 | WIP 四组件（ProtocolStackTower/PacketAssemblyPipeline/RouterPacketInspection/WeChatMobileMockup）提交主干并接入 UniversalScene 路由注册表 + dispatcher 契约测试 | `scripts/github_demo_pipeline.py` 立项：`.demo.yaml` spec 格式设计（clone/install/run/steps） | 多源热点聚合器 v1（微博热搜/抖音热榜/X Trends/B站热榜） |
| W5-6 | `scripts/llm_scriptgen.py`：LLM 主题→分镜 JSON 契约 + 人工审校门 | 沙箱 clone+install+run + Playwright 真实捕获（截图+录屏+events）→ storyboard.json | LLM 快稿 + 事实核查门（信源必填+AI 标注自动附加） |
| W7-8 | 学科可视化：KaTeX 公式组件、时序图/状态机组件、PinoutStream 数据驱动化 | IDE 组件（语法高亮/文件树/标签页）+ asciicast 终端播放组件 | 评论串组件、trending 动画、长推文截断；热点快剪 SKILL 登记入 workflows 矩阵 |
| W9-10 | 知识科普 SKILL：钩子公式库+认知张力叙事+事实核查清单 | `generate_evidence_screenshots.py` 整改：真实抓取为默认路径，mock 更名并强制标注；沉淀 GitHub 演示 SKILL | 平台热门音轨白名单+版权音乐源；小时级时效 SOP |
| **出口** | 1 条计算机网络/STM32 科普短视频全自动产出 | 1 条真实 GitHub 项目演示视频（clone→run→截图→配音→渲染） | 1 条热点解说视频（多源热点→LLM 稿→成片≤2h） |

### Phase 2（第 11-18 周）：全链路闭环
- 选题系统（选题库/评估维度/对标拆解 SKILL）
- 发布系统（多平台元数据模板/封面矩阵分平台/定时排期/水印规范）
- 数据复盘闭环（24h/72h/7d 指标模板/完播率诊断/封面标题 A/B）
- 合规体系（AI 生成标注操作手册/素材授权台账/极限词审查）
- 多规格派生导出（ResponsiveSafeArea 上岗，统一安全区数值）
- 长→短自动切片（ASR 精彩度评分，对标 OpusClip）

### Phase 3（第 19 周起）：工程化与规模化
Docker/Linux 可移植渲染（字体锁定）、任务队列与断点恢复、素材 DAM、性能与成本监控、技能仓库治理常态化（双副本同步脚本 + SKILL.md 校验 CI）。

---

## 四、资源需求

| 类别 | 项目 | 说明 |
|---|---|---|
| 算力 | 本地 AMD 5800H（现有） | ASR/TTS/渲染；Phase 1 起 LLM 脚本生成建议本地 Qwen-7B 或云端 API（DeepSeek/通义） |
| 存储 | ≥ 50GB 可用 | 素材库 + 成品 + 快照；`out/` 建议 Git LFS 或对象存储 |
| 账号/密钥 | LLM API Key；各平台创作者账号 | Phase 2 发布联调用 |
| 软件 | Node 20+ / Python 3.10+ / FFmpeg / Playwright Chromium | CI 同款锁定 |
| 人力 | 1 名主力（用户本人）+ AI Agent 协作 | Phase 0 可独立完成；Phase 1 起建议每场景配 1 个验收人 |

---

## 五、风险管理

| 风险 | 影响 | 缓解 |
|---|---|---|
| LLM 脚本质量不稳定 | 科普事实错误 | 人工审校门 + 事实核查 SOP（三源核查+引用快照） |
| GitHub 项目依赖安装失败率高 | demo 流水线中断 | 沙箱隔离 + 安装失败显式降级（仅截图 README/官网）+ 超时重试 |
| 热点内容时效与合规冲突 | 限流/违规 | 信源必填 + AI 标注 + 极限词审查门禁 |
| 网络不稳定（GitHub/模型下载） | 交付延期 | 多通道下载 + 缓存 + 离线兜底（显式标注） |
| 需求蔓延 | Phase 0 拖期 | 严格出口验收标准，未完成不进入下一阶段 |

---

## 六、实施记录（滚动更新）

| 日期 | 事项 | 状态 |
|---|---|---|
| 2026-10-21 | 仓库同步至 f6b166c，创建 `feature/phase0-stabilization` 分支 | ✅ |
| 2026-10-21 | 执行计划文档建立 | ✅ |
| 2026-10-21 | A4: 新增 `scripts/utils/runtime.py`（AVS_PYTHON 解析 + run_command 超时/重试统一封装）；pipeline/ingest_material/batch_render 三处硬编码解释器路径移除 | ✅ |
| 2026-10-21 | B1: pipeline.run_step / ingest yt-dlp+ffmpeg / audio_mastering loudnorm 双遍 / batch_render run_cmd 全部切换 runtime.run_command（超时可配，失败保留真实退出码） | ✅ |
| 2026-10-21 | A3: x_fetcher 删除编造推文兜底，改显式 XFetchError；metrics/isVerified/timeAgo 一律诚实默认；关键词预设兜底加醒目告警；preset 互动量清空 | ✅ |
| 2026-10-21 | A2: watch_chatcut.js 输出改 `public/timeline.json`（Remotion 真实消费路径）+ 原子写 + fs.watch error 处理与自动重启 + 优雅退出 + `--timeline` 参数 | ✅ |
| 2026-10-21 | B2: timeline_sanitizer.js 两处吸附分支补 `Math.max(0, …)` 负时长防护（含 leading-gap 分支） | ✅ |
| 2026-10-21 | B3: WebBrowserMockupScene.tsx 原生 `<img>` → Remotion `<Img>`（delayRender 安全） | ✅ |
| 2026-10-21 | B4: batch_render_all.py 时间轴读取前存在性/可读性检查，缺失时返回 FAILED_TL 可读状态 | ✅ |
| 2026-10-21 | A4-cover: create_video_cover.py 重写——SRC_IMAGE 改 AVS_COVER_SRC、import 副作用移除（main 守卫）、字体候选探测、失败显式报错 | ✅ |
| 2026-10-21 | C4: audio_mastering.py 新增 PLATFORM_LOUDNESS_PRESETS 单一事实源（web=-14/short_video=-11/broadcast=-23，TP≤-1.5）+ AVS_LOUDNESS_LUFS/TP 环境变量 + `--platform`；默认值 -11.0/-0.5 → -14.0/-1.5；pipeline docstring/步骤说明同步 | ✅ |
| 2026-10-21 | C1: 新建分层 requirements.txt（核心层 + 引擎层按需注释） | ✅ |
| 2026-10-21 | C2: 新建 `.github/workflows/ci.yml`（Python unittest + compileall / tsc --noEmit / test:ts / node --check / bridge） | ✅ |
| 2026-10-21 | C3: package.json 接线 `test:ts`/`test:py`/`test:all`；新增 `tests/tsconfig.test.json`（tsc→CJS 编译 + node 运行）；修正 test_shorts_dispatcher.ts 三处脱节断言；修复 TechNewsShortsScene 深色主题 inverted 背景逻辑（组件真 bug） | ✅ |
| 2026-10-21 | 数据诚信延伸：清理 12 个内容/时间轴文件中编造的推文互动量与 timeAgo；Vint Cerf 场景替换为 FCC FIRSTS 访谈可验证引述并标注 source；create_tech_news_shorts.py 预设生成器同步去编造 + 测试断言更新 | ✅ |
| 2026-10-21 | 验证：Python unittest 82/82 ✅；bridge 6/6 ✅；TS 4/4 ✅；tsc --noEmit 0 错误 ✅；compileall ✅；watcher --once 冒烟（原子写 + 无负时长）✅ | ✅ |
| 2026-10-21 | C4 文档同步收尾：science-pop/tech-tutorial（含 .agents 副本）、project-case-study、ai_video_engines_playbook、remotion-master-compositor（重构为"分轨混音规整→成品母带"两阶段架构，顺带修复泄漏的个人绝对路径）、AUDIT_CHECKLIST（阶段 5 新增成品响度门禁）全部改引 PLATFORM_LOUDNESS_PRESETS；4 份 superpowers 历史 plans/specs 加注存档说明；audio_normalizer voice/bgm 分轨值（-16/-28）确认保留（混音阶段用途不同） | ✅ |
| 2026-10-21 | Phase 0 提交 `2d84559`（42 文件：7 新增 + 35 修改）于 `feature/phase0-stabilization`；排除早期会话未跟踪产物与 WIP 四组件（留给 W3-4） | ✅ |
| 2026-10-22 | W3-4 场景一：ProtocolStackTower/PacketAssemblyPipeline/RouterPacketInspection/WeChatMobileMockup 四组件提交入主干；新增 `src/components/shorts/useSafeFrameConfig.ts` 共享 SSR 安全 hook（四组件 + ProceduralBackground 接入，修复裸 hook 在无 Composition 上下文抛错）；index.ts barrel 导出；UniversalScene 注册四条路由（显式 type 优先 + 嵌套对象隐式推断，与 tweet/binaryBento 同模式）并扩充 SceneMeta 契约；修复 WeChatMobileMockup 的 title prop 被解构但从未渲染的真缺陷；新增 `tests/test_network_scenes.ts`（30 断言：默认/自定义契约、activeLayer 聚焦、双模式、路由优先级、未知类型兜底）并接线 test:ts | ✅ |
| 2026-10-22 | W3-4 场景二：`scripts/github_demo_pipeline.py` 立项——`.demo.yaml` spec 六段契约（spec_version/project/setup/run/capture/output）+ 完整校验器（可读错误）；幂等 clone（--force 重建）/ install（显式降级不编造）/ run steps（expect_exit 契约校验 + 真实退出码记录）；storyboard.json 输出（开场 MinimalHeadline + 每步 TerminalWindow + 收尾，执行事实元数据进 demoRun 字段）；示例 `inputs/yt-dlp.demo.yaml`；`tests/test_github_demo_pipeline.py` 25 例（含 dry-run CLI 冒烟）；修复跨盘符 relpath 崩溃真 bug | ✅ |
| 2026-10-22 | W3-4 场景三：`scripts/hotspot_aggregator.py` 多源热点聚合器 v1——微博热搜/抖音热榜/B站热榜/X Trends 四源归一化（rank/title/heat/url/source/tag）；数据诚信延续：单源失败显式记录零编造、heat 缺失一律 null、X Trends 未配置 AVS_X_BEARER_TOKEN 显式跳过；`tests/test_hotspot_aggregator.py` 22 例（伪 session 离线注入） | ✅ |
| 2026-10-22 | W3-4 验证：Python unittest **129/129** ✅；bridge 6/6 ✅；TS 5 文件全过（15 组断言）✅；tsc --noEmit 0 错误 ✅；compileall ✅ | ✅ |

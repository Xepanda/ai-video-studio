---
name: github-demo-video-production
description: Use when creating deep-dive demo videos for GitHub open-source projects, requiring .demo.yaml spec contracts, idempotent clone/install/run orchestration with explicit degradation, Playwright real capture (screenshots + recording + events, never fabricated), and storyboard compilation with honest execution metadata.
---

# GitHub Demo Video Production (GitHub 开源项目深度演示制作体系)

## Overview

本技能沉淀自 GitHub 演示流水线 (W3-4 立项 + W5-6 真实捕获接入) 的完整生产经验, 核心命题是**让视频里出现的每一条命令、每一个画面都来自真实执行, 失败如实标注而非编造**。

**行业反模式 (本技能的整治对象):**
1. **假终端**: 手工 PS 的命令输出, 观众照着敲跑不通, 信任破产;
2. **假截图**: 用 HTML 模板冒充仓库真实页面 (W9-10 已整改: mock 强制 `mock_` 前缀 + manifest 标注);
3. **安装失败装没事**: 环境装崩了还演一出"完美运行", 翻车在评论区;
4. **只念 README**: 无真实运行证据的纯介绍, 信息增量趋近于零。

---

## 1. `.demo.yaml` 六段契约 (spec_version 1.0)

```yaml
spec_version: "1.0"
project:  { name, repo, ref, title, subtitle, tags }   # repo 必须 http(s)/ssh 地址
setup:    { clone_dir, install[], env{} }              # install 失败 -> 显式降级
run:      { steps[] }                                  # 每步 id/title/cmd/expect_exit/capture/narration/duration
capture:  { enabled, targets[] }                       # W5-6: 真实捕获目标 (id/url/wait_until/full_page/record_video)
output:   { storyboard, fps }
```

- `run.steps[].capture`: `terminal` (默认) | `screenshot` | `none`;
- `run.steps[].expect_exit`: 退出码契约, 偏离如实标注 `status=failed`, **不篡改为成功**;
- `capture.targets[].id`: 产物文件名标识, 唯一; 仅 http(s) 真实网页。

---

## 2. 失败策略分级 (数据诚信的工程化)

| 失败 | 策略 | storyboard 表现 |
|---|---|---|
| clone 失败 | **硬错误** (无仓库即无演示) | 流水线终止, 退出码 3 |
| install 失败 | **显式降级** (不阻断) | `source.degraded=true`, 仅介绍分镜, 步骤标 `skipped_degraded_install` |
| run step 退出码偏离 | 如实记录 | 步骤 `status=failed` + 真实退出码入 `demoRun` 元数据 |
| 捕获失败 | 证据留空 | 该目标 `status=failed` 且 screenshot/video 为 null, **不入画面** |

---

## 3. 执行事实与画面分离

- **入画面**: 真实命令 (`$ cmd`)、真实输出节选 (`output_excerpt` 前 2000 字符首行)、真实截图 (`BrowserScreenshot` 场景, `browser.image` 走 `screenshotStatic` public 相对路径);
- **只入元数据**: 退出码、expect_exit、capture 状态、install 失败清单、捕获 events (console/pageerror/failedRequests) —— 供质检与人工审校, 不进观众视野。

---

## 4. 组件族与叙事结构

```
scene_01        MinimalHeadline      项目标题 + 副标题钩子
scene_cap_*     BrowserScreenshot    真实捕获的仓库主页/文档 (仅 ok 捕获)
scene_02..N     TerminalWindow       每个演示步骤 (codeSnippet=真实命令)
scene_last      MinimalHeadline      收尾 (star 引导 / 降级时如实说明)
```

W7-8 扩展: 代码深度剖析用 `IdeWindowScene` (语法高亮+文件树+标签页); 真实终端会话回放用 `AsciicastPlayer` (asciicast v2 事件流, ANSI 剥离只剥控制序列不改写可见字符)。

---

## 5. 环境与依赖

- Playwright: `pip install playwright && playwright install chromium` (未安装时捕获目标记 failed 并附安装指引, 不静默);
- clone 幂等: 已存在目录复用, `--force` 重建; clone_dir 支持 `{name}`/`{repo}` 占位符;
- 超时可配: `AVS_DEMO_CLONE_TIMEOUT` / `AVS_DEMO_INSTALL_TIMEOUT` / `AVS_DEMO_STEP_TIMEOUT`。

---

## 6. 质量门禁清单 (审校人逐项签字)

- [ ] spec 契约校验通过 (`load_spec` 无 DemoPipelineError)
- [ ] clone/install/run 阶段状态与 storyboard 元数据一致 (无意外降级)
- [ ] 画面中的每条命令都真实执行过 (demoRun.status 可追溯)
- [ ] 截图全部来自真实捕获 (captureResult.records 无 failed 入画)
- [ ] 退出码偏离契约的步骤已在口播中如实说明或剪裁
- [ ] 无 mock 产物冒充真实证据 (evidence_manifest.json 核对)
- [ ] 收尾文案与 degraded 状态匹配 (降级时明确告知观众)

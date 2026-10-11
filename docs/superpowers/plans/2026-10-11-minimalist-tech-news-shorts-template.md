# 极简科技资讯竖屏短视频模板 (Minimalist Tech News Shorts) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于抖音/Twitter 头部科技自媒体（如 `@小猫AI`）爆款风格，在 `ai-video-studio` 中构建一套 30~45 秒纯代码驱动的「极简科技资讯竖屏短视频（Minimalist Tech News Shorts）」生成模板与工业化脚手架，实现零 AI 视频生成依赖、秒级 Remotion 渲染、黑白高对比 Bento 排版与推特截图真实感背书。

**Architecture:** 
1. 新建 `src/components/shorts/` 专用竖屏组件库，包含 `TweetEmbedCard`（X/Twitter 推文原生拟态）、`BinaryBentoCard`（二元对比 Bento）、`MinimalHeadlineScene`（黑白撞色大字报加高亮胶囊）与 `ProgressBlocks`（动态微进度槽）；
2. 扩展 `UniversalScene.tsx` 与 `Root.tsx`，注册 `TechNewsShorts` 1080×1920 竖屏专属 Composition 与安全区避让布局；
3. 构建 `scripts/create_tech_news_shorts.py` 自动化脚手架，一键从简短科技资讯/推特文本生成符合 Schema 的剧本契约；
4. 复刻一份完整的 38 秒 Codex 更新示范样片（`codex_day6_reset_demo.json`），跑通 TTS、Paraformer 声学打点、Remotion 渲染与 -11 LUFS 商业母带全链路。

**Tech Stack:** React 19, TypeScript, Remotion 4.0, Tailwind/Inline CSS, Python 3.10+, ChatTTS (Seed 4444), FunASR Paraformer, FFmpeg.

**Spec:** `Screenrecorder-2026-10-10-15-26-02-635.mp4` 视觉逆向工程规范。

## Global Constraints

- 画幅规格严格锁定为 1080 × 1920 (9:16 竖屏)，CFR 30.000 FPS；
- 底部预留 220px 抖音/视频号/Reels 原生交互安全区，确保字幕与卡片不被遮挡；
- 零外部 AI 视频生成依赖，100% 依赖纯代码 CSS/SVG 与静态截图渲染；
- 所有组件需兼容 TypeScript 严格类型检查，无 `any` 泛滥；
- 音频遵循 ITU-R BS.1770 / EBU R128 -11.0 LUFS 广播级商业母带标准。

---

### Task 1: 打造社交媒体推文拟态组件 (TweetEmbedCard)

**Files:**
- Create: `src/components/shorts/TweetEmbedCard.tsx`
- Test: `tests/test_tweet_card.tsx` 或在 Remotion Preview 中验证

**Interfaces:**
- Produces: `TweetEmbedCardProps` & `TweetEmbedCard: React.FC<TweetEmbedCardProps>`
- Props: `authorName`, `authorHandle`, `avatarUrl`, `isVerified`, `timeAgo`, `content`, `highlightWords`, `metrics?: { replies, retweets, likes, views }`, `theme`

- [ ] **Step 1: 编写推特卡片组件实现**

创建 `src/components/shorts/TweetEmbedCard.tsx`，实现仿 X (Twitter) 官方的现代极简卡片：
- 顶部头像（支持图片或首字母渐变兜底）、昵称、Handle、蓝 V 图标与发布时间；
- 正文区域支持换行、中英双语混排与重点词高亮；
- 底部轻量灰度统计数据（转推、点赞、浏览量）；
- 容器支持暗黑模式与明亮模式自适应。

- [ ] **Step 2: 验证组件类型与编译**

运行 `npx tsc --noEmit` 确保无类型错误。

- [ ] **Step 3: 提交代码**

```bash
git add src/components/shorts/TweetEmbedCard.tsx
git commit -m "feat(shorts): add TweetEmbedCard for native social media proof"
```

---

### Task 2: 打造二选一对比 Bento 与进度槽组件 (BinaryBentoCard)

**Files:**
- Create: `src/components/shorts/BinaryBentoCard.tsx`
- Modify: `src/components/shorts/index.ts`

**Interfaces:**
- Produces: `BinaryBentoCardProps` & `BinaryBentoCard: React.FC<BinaryBentoCardProps>`
- Props: `title: string`, `leftCard: { title, desc, tag, blocksActive?: number }`, `rightCard: { title, desc, pill, tag }`, `dividerText?: string`

- [ ] **Step 1: 编写二选一对比 Bento 容器与微动效**

创建 `src/components/shorts/BinaryBentoCard.tsx`：
- 支持“标题 + 双列并列卡片 + 中间圆圈‘或/VS’”结构；
- 左卡支持可配置的 `ProgressBlocks` 逐格点亮动画；
- 右卡支持醒目的紫色药丸/胶囊标签（如“重置卡”）；
- 采用 Remotion `spring` 实现顺滑的入场与高亮动效。

- [ ] **Step 2: 验证组件渲染与编译**

运行 `npx tsc --noEmit` 确保无编译错误。

- [ ] **Step 3: 提交代码**

```bash
git add src/components/shorts/BinaryBentoCard.tsx
git commit -m "feat(shorts): add BinaryBentoCard and ProgressBlocks for comparison scenes"
```

---

### Task 3: 打造极简大字报与竖屏综合调度中心 (MinimalHeadlineScene & TechNewsShortsScene)

**Files:**
- Create: `src/components/shorts/MinimalHeadlineScene.tsx`
- Create: `src/components/shorts/TechNewsShortsScene.tsx`
- Create: `src/components/shorts/index.ts`

**Interfaces:**
- Produces: `TechNewsShortsScene: React.FC<{ scene: SceneMeta, activeTheme: ThemeConfig }>`
- Polymorphic routing:
  - `scene.type === 'TweetEmbed'` -> `TweetEmbedCard`
  - `scene.type === 'BinaryBento'` -> `BinaryBentoCard`
  - `scene.type === 'MinimalHeadline'` 或默认 -> `MinimalHeadlineScene`

- [ ] **Step 1: 编写极简大字报场景组件 (MinimalHeadlineScene)**

实现黑白高对比大字报：
- 支持 `inverted?: boolean`（黑底白字 vs 白底黑字快速反转）；
- 顶部醒目 episode/category pill 胶囊标签；
- 超大主标题居中排版，支持 `keywords` 自动使用紫色胶囊背景高亮包裹；
- 底部次级辅助说明或时间节点。

- [ ] **Step 2: 编写竖屏综合调度组件 (TechNewsShortsScene)**

创建统一分发入口 `TechNewsShortsScene.tsx`，将大字报、推文卡片、对比卡片以及底部安全区自适应字幕紧密整合。

- [ ] **Step 3: 提交代码**

```bash
git add src/components/shorts/
git commit -m "feat(shorts): add MinimalHeadlineScene and TechNewsShortsScene dispatcher"
```

---

### Task 4: 注册 TechNewsShorts 专属竖屏合成并在 UniversalScene 中接入

**Files:**
- Modify: `src/Root.tsx`
- Modify: `src/components/UniversalScene.tsx`

- [ ] **Step 1: 更新 UniversalScene.tsx 支持 shorts 类型分发**

当 `scene.type === 'TweetEmbed' | 'BinaryBento' | 'MinimalHeadline' | 'TechNews'` 时，直接委托给 `TechNewsShortsScene` 渲染。

- [ ] **Step 2: 在 Root.tsx 中注册 TechNewsShorts 竖屏合成**

添加：
```tsx
<Composition
  id="TechNewsShorts"
  component={MainComposition}
  durationInFrames={timelineData.totalDurationFrames || 1140}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{ timeline: 'public/timeline.json' }}
/>
```

- [ ] **Step 3: 验证 TypeScript 编译**

运行 `npx tsc --noEmit`。

- [ ] **Step 4: 提交代码**

```bash
git add src/Root.tsx src/components/UniversalScene.tsx
git commit -m "feat(shorts): register TechNewsShorts 1080x1920 composition and scene routing"
```

---

### Task 5: 编写一键脚手架 CLI 与 Codex Day 6 参考示范样片

**Files:**
- Create: `scripts/create_tech_news_shorts.py`
- Create: `content/scripts/codex_day6_reset_demo.json`
- Test: `tests/test_create_tech_news_shorts.py`

- [ ] **Step 1: 编写单元测试 test_create_tech_news_shorts.py**

验证 CLI 参数解析、推文卡片元数据填充、分镜时长估算与 Schema 合规性。

- [ ] **Step 2: 运行测试确保失败**

运行 `pytest tests/test_create_tech_news_shorts.py` 确保测试未通过。

- [ ] **Step 3: 实现 create_tech_news_shorts.py**

实现 CLI 工具：
`python scripts/create_tech_news_shorts.py --topic "OpenAI Codex 第六天更新" --project codex_day6_reset_demo ...`

- [ ] **Step 4: 运行测试确保通过**

运行 `pytest tests/test_create_tech_news_shorts.py` 确保全部 PASS。

- [ ] **Step 5: 生成高保真复刻示范剧本 codex_day6_reset_demo.json**

严格复刻参考视频的 8 个段落（38 秒总长）：
1. 悬念大字：没有新功能，只有重置
2. 推特实锤：Tibo 的推文 "Day 6: Reset"
3. 二元对比：直接刷新额度 vs 给重置卡
4. 悬念过渡：帖子没说，等落地才知道
5. 背景回溯：上一次全员重置是第二天
6. 推特前兆：前一天 Tibo 发推 "一眨眼都周六了"
7. 因果推导：功能没影子，这是要重置啊
8. 结尾互动：第七天会有什么功能？明天接着看

- [ ] **Step 6: 提交代码**

```bash
git add scripts/create_tech_news_shorts.py content/scripts/codex_day6_reset_demo.json tests/test_create_tech_news_shorts.py
git commit -m "feat(shorts): add create_tech_news_shorts generator and codex demo script"
```

---

### Task 6: 运行端到端流水线并验证成片与性能

**Files:**
- Output: `out/codex_day6_reset_demo.mp4`
- Output: `public/projects/codex_day6_reset_demo/`

- [ ] **Step 1: 运行 TTS 生成与 Paraformer 物理声学毫秒对齐**

执行：
```bash
python scripts/generate_audio.py --project codex_day6_reset_demo --engine chattts --voice 4444
python scripts/sensevoice_aligner.py --project codex_day6_reset_demo
```

- [ ] **Step 2: 运行 Quality Gate 审查**

执行：
```bash
python scripts/validator.py --project codex_day6_reset_demo
```

- [ ] **Step 3: 渲染 1080×1920 竖屏成片并执行 -11 LUFS 商业母带处理**

执行：
```bash
npx remotion render src/index.ts TechNewsShorts out/codex_day6_reset_demo.mp4 --props '{"timeline": "public/projects/codex_day6_reset_demo/timeline.json"}'
python scripts/audio_mastering.py --video out/codex_day6_reset_demo.mp4
```

- [ ] **Step 4: 导出多张关键分镜高清预览图并做全套校验**

验证：推特卡片、二选一卡片、大字报排版、手机安全区避让、渲染耗时与视听效果。

- [ ] **Step 5: 提交最终工程代码**

```bash
git add .
git commit -m "feat(shorts): complete 38s codex tech news vertical shorts production"
```

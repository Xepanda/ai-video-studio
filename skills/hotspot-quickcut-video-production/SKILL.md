---
name: hotspot-quickcut-video-production
description: Use when creating quick-cut commentary videos on trending topics (Weibo/Douyin/Bilibili/X Trends hotspots) within a 2-hour window, requiring multi-source aggregation, LLM fast drafting with a mandatory fact-check gate (sources required + AI disclosure auto-attached), and human review before production.
---

# Hotspot Quick-Cut Video Production (热点快剪短视频制作体系)

## Overview

本技能沉淀自热点快剪流水线 (W3-4 聚合器 + W5-6 LLM 快稿与事实核查门) 的完整生产经验, 核心命题是**在小时级时效窗口内, 用工程门禁守住内容可信度**。

**行业反模式 (本技能的整治对象):**
1. **时效造假**: 热点已过窗口仍伪装"刚刚发生", 或把旧闻当新闻讲;
2. **编造信源**: LLM 快稿张口就来, 数字/引述无出处, 评论区打脸;
3. **零标注蹭AI**: 用 LLM 量产同质化快稿却不按平台规范标注 AI 生成;
4. **单源依赖**: 只刷一个平台的热榜, 错过交叉验证与选题差异。

---

## 1. 时效 SOP (小时级窗口管理)

```
T+0min   聚合: hotspot_aggregator.py 抓取多源热榜 (单源失败零编造, 如实记录)
T+10min  选题: 按 rank/热度选话题; 无真实输入拒绝进入下一步
T+20min  快稿: hotspot_scriptgen.py 生成分镜 (事实核查门内建)
T+40min  审校: 人工审校门 --approve (事实核查清单逐项过)
T+90min  成片: pipeline TTS/打点/渲染 + 平台母带
────────────────────────────────────────────
超过 T+6h 的热点: 降级为"复盘解读"形态 (明确说明时间线), 严禁伪装时效
```

---

## 2. 事实核查门 (硬性门禁, 无人工Override)

`hotspot_scriptgen.py` 内建的四条规则, 违规即打回 LLM 重写 (默认 2 次), 耗尽拒绝放行:

1. **信源必填**: 每一幕必须携带非空 `sources` [{title, url}], 且整片必须引用热点话题自身的 URL (来自聚合输入, 非 LLM 编造);
2. **AI 标注自动附加**: `aiDisclosure` 块由门禁自动补全 (autoFix 留痕), 成片按平台规范标注;
3. **数量声明审查**: 旁白出现百分比/万/亿/美元等声明 -> 标记待人工核实 (不阻断, 但审校人必须逐项核对);
4. **话题绑定**: 草稿必须回链选定话题 (title/url/heat 记入 source 元数据)。

---

## 3. 数据诚信红线 (延续审计 A3)

- 无真实热点输入 (聚合文件缺失/全源失败) -> 拒绝生成, 不凭空编造话题;
- 单源抓取失败 -> 该源状态 failed, 聚合结果零该源编造条目;
- 热度值缺失 -> 一律 null, **严禁 0 填充或估值**;
- X Trends 未配置 `AVS_X_BEARER_TOKEN` -> 显式跳过并说明;
- 抖音热榜通常需要登录态 cookie, 失败属预期内, 不阻塞其他源。

---

## 4. 平台热门音轨白名单与版权音乐源

**原则: 快剪的音乐是版权雷区, 只用以下三类来源, 用前必查授权范围:**

1. **平台官方曲库**: 抖音/小红书/B站创作者后台的热门音轨 (平台内使用随账号授权, 跨平台搬运无效);
2. **CC0/公共领域**: Free Music Archive (CC0 筛选)、YouTube Audio Library (免版税库);
3. **自制/免授权订阅**: 已订阅的免版税曲库 (按订阅条款使用, 保留订阅凭证)。

**禁忌**: 直接抓取榜单视频的 BGM 复用 (侵权高风险); 无授权商用曲; 未标注出处的"网抑云"导出。

---

## 5. 组件族与节奏

- 开场: `TrendingRankCard` (真实热点数据: rank/heat/source/tag, 热度缺失诚实标注);
- 主体: 内容场景 (BinaryBento 对比 / MinimalHeadline 观点 / MetricComparison 数据);
- 互动: `CommentThreadScene` (评论串, 点赞数缺失标"赞数缺失"禁 0 填充);
- 收尾: MinimalHeadline + 观点闭环 + 三连引导。

节奏铁律: 单镜头 ≤5s, 信息密度靠组件不靠语速; 热度数据只原样引用不得改写。

---

## 6. 质量门禁清单 (审校人逐项签字)

- [ ] 热点为真 (聚合输入可追溯, 非记忆/编造)
- [ ] 每幕信源可点击验证, 且包含话题原链
- [ ] 数量声明逐项核对 (factCheck.warnings 清空或确认)
- [ ] AI 标注已附加且符合目标平台规范
- [ ] 时效形态正确 (窗口内=快评 / 过窗口=复盘)
- [ ] 音轨来自白名单三类来源之一
- [ ] 无极限词/绝对化用语
- [ ] `llm_scriptgen.py --status` 确认 approved 后才进渲染

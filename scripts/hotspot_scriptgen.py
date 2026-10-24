#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hotspot_scriptgen.py
热点快剪类视频: LLM 快稿生成 + 事实核查门 (Phase 1 W5-6 场景三)

功能特性:
  1. 消费 scripts/hotspot_aggregator.py 的聚合输出 (topics + 每源状态),
     选定热点话题后调用 LLM 生成竖屏快剪分镜草稿 (复用 llm_scriptgen 的契约校验);
  2. 事实核查门 (执行计划风险表"热点内容时效与合规冲突 -> 信源必填 + AI 标注"缓解策略):
     - 信源必填: 每一幕必须携带非空 sources [{title, url}], 且整片必须引用热点话题
       自身的 URL (来自聚合输入, 非 LLM 编造); 缺失即违规, 拒绝放行;
     - AI 标注自动附加: aiDisclosure 块由门禁自动补全 (autoFix 留痕);
     - 数字声明审查: 旁白中出现百分比/万/亿等数量声明 -> 标记待人工核实 (warning);
     - 话题绑定: 草稿必须回链选定话题 (topicTitle/topicUrl 记入 source 元数据);
  3. 违规反馈重试: 门禁不过时将违规清单反馈给 LLM 修复 (默认最多 2 次尝试),
     仍不过则显式 ScriptgenError 并附带完整门禁报告 (绝不带病放行);
  4. 审校门衔接: 草稿同样挂起 review.status=pending, 须经 llm_scriptgen --approve 批准。

数据诚信承诺 (延续审计 A3):
  - 热点话题必须来自真实聚合输入; 无 --hotspots 输入时拒绝生成 (不凭空编造热点);
  - LLM 失败显式 LLMError; 门禁违规显式报告, 不静默放行。

用法:
  python scripts/hotspot_aggregator.py --top 10 --output inputs/hotspots/latest.json
  python scripts/hotspot_scriptgen.py --hotspots inputs/hotspots/latest.json \\
      --rank 1 --project hotspot_demo --scenes 4
"""

import os
import sys
import re
import json
import argparse
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 保障 utils 包可导入
from utils.llm_client import LLMClient, LLMError, now_iso

from llm_scriptgen import (
    SCENE_TYPE_REGISTRY,
    validate_storyboard_payload,
    build_review_block,
    attach_ai_disclosure,
    ScriptgenError,
    save_storyboard,
    _rel_or_abs,
)
from create_script_from_topic import slugify

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "content", "scripts")

DEFAULT_FPS = 30
DEFAULT_MAX_RETRIES = 2

# 数量声明模式 (百分比 / 万 / 亿 / 美元等) -> 命中即标记待人工核实
_NUMBER_CLAIM_RE = re.compile(
    r"\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*[万亿]|\d+(?:\.\d+)?\s*(?:美元|美金|元|人次|人)"
)


class FactCheckError(Exception):
    """事实核查门未通过且重试耗尽 (携带完整门禁报告)。"""


# ---------------------------------------------------------------------------
# 热点输入加载与话题选择
# ---------------------------------------------------------------------------

def load_hotspots(path: str) -> Dict[str, Any]:
    """加载 hotspot_aggregator 聚合输出并做基本结构检查。"""
    if not os.path.exists(path):
        raise ScriptgenError(
            f"热点聚合文件不存在: {path}\n"
            "  请先执行: python scripts/hotspot_aggregator.py --output <path> "
            "(按数据诚信原则, 无真实热点输入不生成快稿)"
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except ValueError as e:
        raise ScriptgenError(f"热点聚合文件 JSON 解析失败: {path}\n{e}")

    if not isinstance(payload, dict) or not isinstance(payload.get("topics"), list):
        raise ScriptgenError(f"热点聚合文件结构不符预期 (缺少 topics 列表): {path}")
    return payload


def select_topic(hotspots: Dict[str, Any], rank: int = 1,
                 topic_title: str = "") -> Dict[str, Any]:
    """从聚合结果选择话题: --topic-title 精确匹配优先, 否则按 rank (热度序)。

    注意: topics 按抓取顺序拼接 (非全局热度序), rank 为源内排名 + 偏移后的展示位;
    选择逻辑只做确定性挑选, 不重新排序编造。
    """
    topics = hotspots.get("topics") or []
    if not topics:
        raise ScriptgenError("热点聚合输入中没有任何话题 (所有源均失败?); 无热点不生成快稿")

    if topic_title.strip():
        for t in topics:
            if str(t.get("title", "")).strip() == topic_title.strip():
                return t
        raise ScriptgenError(
            f"未在聚合输入中找到标题为 {topic_title!r} 的话题 (可用 --rank 按位置选择)"
        )

    idx = max(1, int(rank)) - 1
    if idx >= len(topics):
        raise ScriptgenError(f"--rank {rank} 超出话题总数 ({len(topics)})")
    return topics[idx]


# ---------------------------------------------------------------------------
# 事实核查门
# ---------------------------------------------------------------------------

def fact_check_storyboard(
    payload: Any,
    topic: Dict[str, Any],
    hotspot_path: str = "",
) -> Dict[str, Any]:
    """对 LLM 快稿执行事实核查门, 返回报告 dict。

    Report 结构:
      passed     是否放行 (无 violations)
      violations 硬违规 (信源缺失/格式非法/未回链热点话题) -> 阻断
      warnings   软警告 (数量声明待人工核实/嵌套配置缺失等) -> 不阻断但需人工关注
      autoFixes  门禁自动修复留痕 (AI 标注附加)
    """
    violations: List[str] = []
    warnings: List[str] = []
    auto_fixes: List[str] = []

    topic_url = str(topic.get("url") or "").strip()
    topic_title = str(topic.get("title") or "").strip()

    if not isinstance(payload, dict):
        return {
            "passed": False,
            "violations": [f"根对象必须是 JSON 对象, 实际为: {type(payload).__name__}"],
            "warnings": warnings,
            "autoFixes": auto_fixes,
            "checkedAt": now_iso(),
        }

    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        violations.append("分镜 'scenes' 必须为非空列表")
        scenes = []

    referenced_topic_url = False
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{idx + 1}") if isinstance(scene, dict) else f"scene_{idx + 1}"
        if not isinstance(scene, dict):
            violations.append(f"分镜 [{scene_id}] 必须是 JSON 对象")
            continue

        # 1. 信源必填: 每幕 sources 非空且格式合法
        sources = scene.get("sources")
        if not isinstance(sources, list) or len(sources) == 0:
            violations.append(f"分镜 [{scene_id}] 缺少信源 (sources 必须为非空列表, 信源必填)")
        else:
            for sidx, src in enumerate(sources):
                if not isinstance(src, dict):
                    violations.append(f"分镜 [{scene_id}] sources[{sidx}] 必须是 {{title, url}} 对象")
                    continue
                url = str(src.get("url") or "").strip()
                title = str(src.get("title") or "").strip()
                if not url.startswith("http://") and not url.startswith("https://"):
                    violations.append(f"分镜 [{scene_id}] sources[{sidx}].url 非法: {url!r}")
                if not title:
                    violations.append(f"分镜 [{scene_id}] sources[{sidx}] 缺少 title")
                if topic_url and url == topic_url:
                    referenced_topic_url = True

        # 2. 数量声明审查 (不阻断, 标记人工核实)
        text = scene.get("text") or ""
        if isinstance(text, str) and _NUMBER_CLAIM_RE.search(text):
            warnings.append(
                f"分镜 [{scene_id}] 旁白含数量声明, 需人工核实信源: "
                f"{_NUMBER_CLAIM_RE.search(text).group(0)!r}"
            )

    # 3. 热点话题回链 (整片必须引用聚合输入中的话题 URL)
    if topic_url and not referenced_topic_url:
        violations.append(
            f"整片未引用热点话题自身的信源 URL ({topic_url}); "
            "信源必填: 至少一幕的 sources 必须包含该热点链接"
        )

    # 4. AI 标注自动附加 (autoFix 语义: 门禁主动补全而非阻断)
    disclosure = payload.get("aiDisclosure")
    if not (isinstance(disclosure, dict) and disclosure.get("isAiGenerated")):
        payload["aiDisclosure"] = {
            "isAiGenerated": True,
            "notice": "本视频基于真实热点话题由 AI 辅助生成解说文案, 已经人工审校门审核; "
                      "成片需按平台规范标注 AI 生成内容。",
        }
        auto_fixes.append("已自动附加 aiDisclosure AI 生成标注 (平台合规)")

    # 5. 话题绑定元数据
    source_meta = payload.get("source")
    if not isinstance(source_meta, dict):
        source_meta = {}
        payload["source"] = source_meta
    source_meta.setdefault("hotspot", {
        "title": topic_title,
        "url": topic_url,
        "source": topic.get("source"),
        "heat": topic.get("heat"),
        "aggregatedFrom": os.path.basename(hotspot_path) if hotspot_path else None,
    })

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "autoFixes": auto_fixes,
        "topic": {"title": topic_title, "url": topic_url},
        "checkedAt": now_iso(),
    }


# ---------------------------------------------------------------------------
# 提示词工程
# ---------------------------------------------------------------------------

def build_hotspot_messages(topic: Dict[str, Any], scene_count: int,
                            feedback: str = "") -> List[Dict[str, str]]:
    """构造 LLM 消息: system 定义快照契约 + 信源必填规则, user 给出热点话题。

    feedback: 上一轮门禁违规清单 (重试时注入, 要求 LLM 修复)。
    """
    registry_lines = "\n".join(
        f"  - {name}: {meta['desc']}" for name, meta in SCENE_TYPE_REGISTRY.items()
    )
    system = f"""你是一位资深热点解读短视频编导, 擅长把热点事件转化为 30-60 秒竖屏快剪解说。
请严格输出一个 JSON 对象 (不要输出任何额外文字, 不要使用 markdown 代码围栏), 契约如下:

{{
  "project": "<项目标识>",
  "title": "<带悬念的短视频标题, 20字以内>",
  "theme": "linear-graphite",
  "engine": "chattts",
  "voice": "4444",
  "fps": 30,
  "scenes": [
    {{
      "id": "scene_01",
      "type": "<场景类型, 见注册表>",
      "title": "<本幕标题>",
      "text": "<本幕旁白, 口语化, 40-100字>",
      "highlightWords": ["关键词"],
      "estimatedDuration": <秒数, 正数, 3-8>,
      "sources": [{{"title": "<信源名称>", "url": "<信源URL>"}}]
    }}
  ]
}}

可用场景类型注册表:
{registry_lines}

硬性规则 (事实核查门会自动审查, 违规将打回重写):
1. scenes 数量必须精确等于 {scene_count} 幕; 第一幕必须是 MinimalHeadline 开场钩子;
2. 每一幕必须提供非空 sources 列表, 且至少一幕的 sources 必须包含下面的【热点信源URL】;
3. 旁白只陈述热点相关事实, 禁止编造具体数字/比例; 无可靠信源时用定性描述;
4. 语气克制, 不做煽动性结论, 不做未经证实的因果推断;
5. 除 JSON 对象外不要输出任何内容。"""

    user = (
        f"【热点话题】{topic.get('title', '')}\n"
        f"【热点信源URL】{topic.get('url', '')}\n"
        f"【话题来源】{topic.get('source', '')}"
    )
    heat = topic.get("heat")
    if isinstance(heat, int):
        user += f"\n【热度值】{heat} (仅可原样引用, 不得改写)"
    user += f"\n请生成 {scene_count} 幕竖屏快剪分镜。"
    if feedback:
        user += (
            "\n\n【上一轮被事实核查门打回, 请修复以下违规项后重新输出】\n"
            + "\n".join(f"- {v}" for v in feedback)
        )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# 生成主流程 (门禁 + 反馈重试)
# ---------------------------------------------------------------------------

def generate_hotspot_script(
    topic: Dict[str, Any],
    client: LLMClient,
    hotspot_path: str = "",
    scene_count: int = 4,
    theme: str = "linear-graphite",
    project_name: str = "",
    engine: str = "chattts",
    voice: str = "4444",
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """LLM 快稿 + 事实核查门 (带违规反馈重试)。

    Returns:
        (storyboard, fact_check_report)

    Raises:
        ScriptgenError: LLM 调用/解析失败, 或契约校验失败
        FactCheckError: 重试耗尽后事实核查门仍未通过 (报告随异常携带)
    """
    feedback = ""
    last_report: Dict[str, Any] = {}
    payload: Any = None

    for attempt in range(1, max_retries + 2):  # 首次 + max_retries 次反馈重试
        messages = build_hotspot_messages(topic, scene_count, feedback=feedback)
        print(f"🤖 [Hotspot ScriptGen] 第 {attempt} 次生成尝试 (模型: {client.model})")
        try:
            payload = client.chat_json(messages, temperature=0.5, max_tokens=6144)
        except LLMError as e:
            raise ScriptgenError(f"LLM 快稿生成失败: {e}")

        errors, warnings = validate_storyboard_payload(payload)
        if errors:
            if attempt <= max_retries:
                feedback = [f"契约校验: {e}" for e in errors]
                print(f"⚠️ [Hotspot ScriptGen] 契约校验未过 ({len(errors)} 项), 反馈重试...")
                continue
            raise ScriptgenError(
                "LLM 快稿未通过分镜契约校验 (重试耗尽, 已拒绝写入):\n"
                + "\n".join(f"   ✖ {e}" for e in errors)
            )

        # 归一化 (CLI 参数优先; 帧数确定性计算)
        fps = payload.get("fps") if isinstance(payload.get("fps"), int) and payload.get("fps", 0) > 0 else DEFAULT_FPS
        payload["project"] = project_name.strip() or slugify(str(topic.get("title", "hotspot")))
        payload["title"] = payload.get("title") or str(topic.get("title", "热点快评"))
        payload["theme"] = theme
        payload["engine"] = engine
        payload["voice"] = voice
        payload["fps"] = fps
        total_frames = 0
        for idx, scene in enumerate(payload["scenes"]):
            scene.setdefault("id", f"scene_{idx + 1:02d}")
            duration = scene.get("estimatedDuration")
            if not isinstance(duration, (int, float)) or duration <= 0:
                duration = 4.0
                scene["estimatedDuration"] = duration
            frames = int(round(duration * fps))
            scene["estimatedFrames"] = frames
            scene["durationInFrames"] = frames
            total_frames += frames
        payload["totalDurationInFrames"] = total_frames

        # 事实核查门
        report = fact_check_storyboard(payload, topic, hotspot_path=hotspot_path)
        last_report = report
        if report["passed"]:
            print(f"✅ [FactCheck] 门禁通过 (attempt {attempt}): "
                  f"{len(report['warnings'])} 项待人工核实警告")
            payload["factCheck"] = report
            payload["review"] = build_review_block()
            attach_ai_disclosure(payload, client.model)
            payload["source"]["generatedBy"] = "hotspot_scriptgen.py"
            payload["source"]["model"] = client.model
            payload["source"]["generatedAt"] = now_iso()
            return payload, report

        print(f"⚠️ [FactCheck] 门禁未过 (attempt {attempt}/{max_retries + 1}): "
              f"{len(report['violations'])} 项违规")
        for v in report["violations"]:
            print(f"   ✖ {v}")
        if attempt <= max_retries:
            feedback = report["violations"]
        else:
            payload["factCheck"] = report
            raise FactCheckError(
                "事实核查门未通过且重试耗尽 (已拒绝写入, 绝不带病放行):\n"
                + "\n".join(f"   ✖ {v}" for v in report["violations"])
                + f"\n完整报告: {json.dumps(report, ensure_ascii=False)}"
            )

    # 不可达: 循环内必定 return 或 raise
    raise FactCheckError(f"热点快稿生成流程异常终止; 最后门禁报告: {last_report}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_parser() -> argparse.ArgumentParser:
    """定义并返回热点快稿生成器命令行解析器"""
    parser = argparse.ArgumentParser(
        description="热点快剪: LLM 快稿生成 + 事实核查门 (信源必填 + AI 标注自动附加, W5-6)"
    )
    parser.add_argument("--hotspots", type=str, required=True,
                        help="hotspot_aggregator.py 的聚合输出 JSON 路径")
    parser.add_argument("--rank", type=int, default=1, help="选择第几条热点 (默认 1)")
    parser.add_argument("--topic-title", type=str, default="", help="按标题精确选择热点 (优先于 --rank)")
    parser.add_argument("--project", type=str, default="", help="项目标识 (默认由话题标题生成)")
    parser.add_argument("--scenes", type=int, default=4, choices=range(2, 9),
                        help="分镜数量 (2 ~ 8, 默认 4; 首幕固定 MinimalHeadline)")
    parser.add_argument("--theme", type=str, default="linear-graphite", help="视觉主题")
    parser.add_argument("--engine", type=str, default="chattts", help="TTS 引擎 (默认 chattts)")
    parser.add_argument("--voice", type=str, default="4444", help="TTS 音色 (默认 4444)")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                        help="门禁违规后的反馈重试次数 (默认 2)")
    parser.add_argument("--output", type=str, default="",
                        help="输出路径 (默认 content/scripts/{project}_hotspot.json)")
    parser.add_argument("--dry-run", action="store_true", help="仅打印至控制台, 不写入磁盘")
    return parser


def main():
    args = get_parser().parse_args()

    try:
        hotspots = load_hotspots(args.hotspots)
        topic = select_topic(hotspots, rank=args.rank, topic_title=args.topic_title)
    except ScriptgenError as e:
        print(f"\n❌ [Hotspot ScriptGen] {e}")
        sys.exit(2)

    print(f"🔥 [Hotspot ScriptGen] 选定热点: {topic.get('title')} "
          f"(来源: {topic.get('source')}, 热度: {topic.get('heat')})")

    client = LLMClient()
    try:
        storyboard, report = generate_hotspot_script(
            topic=topic,
            client=client,
            hotspot_path=args.hotspots,
            scene_count=args.scenes,
            theme=args.theme,
            project_name=args.project,
            engine=args.engine,
            voice=args.voice,
            max_retries=args.max_retries,
        )
    except (ScriptgenError, FactCheckError) as e:
        print(f"\n❌ [Hotspot ScriptGen] {e}")
        sys.exit(4)

    output_path = args.output.strip() or os.path.join(
        SCRIPTS_DIR, f"{storyboard['project']}_hotspot.json"
    )
    formatted = json.dumps(storyboard, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(formatted)
        return

    out_abs = save_storyboard(storyboard, output_path)
    print(f"\n=======================================================")
    print(f"✅ [Hotspot ScriptGen] 快稿已生成并通过事实核查门 "
          f"({len(storyboard['scenes'])} 幕 / {storyboard['totalDurationInFrames']} 帧)")
    print(f"   输出: {out_abs}")
    if report["warnings"]:
        print(f"   ⚠️ {len(report['warnings'])} 项数量声明待人工核实 (见 factCheck.warnings)")
    print(f"   ⏸️  审校门状态: pending (须经 llm_scriptgen --approve 批准后进入生产)")
    print(f"=======================================================\n")
    print("💡 审校批准命令: python scripts/llm_scriptgen.py --approve "
          f"--input {_rel_or_abs(out_abs)} --reviewer <你的名字>")


if __name__ == "__main__":
    main()

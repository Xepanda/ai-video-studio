#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/llm_scriptgen.py
知识科普类视频: LLM 主题 -> 分镜 JSON 契约生成器 + 人工审校门 (Phase 1 W5-6)

功能特性:
  1. 调用 OpenAI 兼容 LLM (utils.llm_client.LLMClient) 将主题转化为生产级分镜契约:
     project / title / theme / voice / engine / fps / scenes / totalDurationInFrames
  2. 严格场景类型注册表 (与 src/components/UniversalScene.tsx 路由一一对应),
     提示词内嵌嵌套配置契约 (protocolTower / packetAssembly / tweet / binaryBento ...);
  3. 契约校验 validate_storyboard_payload (蓝本 scripts/validator.py 的 schema 审查),
     不合法即显式 ScriptgenError, 绝不把坏契约写入 content/scripts/;
  4. 人工审校门 (执行计划风险表"LLM 脚本质量不稳定 -> 人工审校门"缓解策略):
     - 生成的草稿一律标记 review.status = pending, 附事实核查清单;
     - 必须经 --approve --reviewer 显式批准才能进入 TTS/渲染 (assert_review_approved);
  5. AI 标注自动附加 (aiDisclosure 块): 平台合规要求 AI 生成内容显式声明;
  6. 数据诚信承诺 (延续审计 A3): LLM 调用失败显式 LLMError, 无模板兜底编造分镜。

用法:
  python scripts/llm_scriptgen.py --topic "TCP 三次握手为什么是三次而不是两次" \\
      --project tcp_handshake --scenes 6
  python scripts/llm_scriptgen.py --status --input content/scripts/tcp_handshake.json
  python scripts/llm_scriptgen.py --approve --input content/scripts/tcp_handshake.json --reviewer 庖丁
"""

import os
import sys
import json
import argparse
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 保障 utils 包可导入
from utils.llm_client import LLMClient, LLMError, now_iso

# slugify 复用 create_script_from_topic (保证项目标识生成规则全仓一致)
from create_script_from_topic import slugify

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "content", "scripts")

DEFAULT_FPS = 30
DEFAULT_SCENE_DURATION = 5.0  # 秒 (LLM 未给出 estimatedDuration 时的兜底, 并记 warning)

# ---------------------------------------------------------------------------
# 场景类型注册表 (与 UniversalScene 路由对齐; 描述供 LLM 提示词使用)
# ---------------------------------------------------------------------------

SCENE_TYPE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "MinimalHeadline": {"nested": None, "desc": "极简大字标题场景, 适合开场钩子与收尾总结"},
    "TerminalWindow": {"nested": None, "desc": "极客终端窗口, 展示真实命令与输出 (codeSnippet)"},
    "TerminalCodeDemo": {"nested": None, "desc": "终端代码演示, 展示源码片段 (codeTitle/codeLang/codeSnippet)"},
    "ArchitectureTopology": {"nested": ("topologyNodes", "topologyLinks"), "desc": "架构拓扑图 (nodes + links)"},
    "TopologyFlow": {"nested": ("topologyNodes", "topologyLinks"), "desc": "拓扑流程图 (nodes + links)"},
    "MetricComparison": {"nested": ("metrics",), "desc": "性能指标对照卡片 (MetricCategory[])"},
    "MetricChart": {"nested": ("metrics",), "desc": "指标图表 (MetricCategory[])"},
    "TweetEmbed": {"nested": ("tweet",), "desc": "推文嵌入卡片 (tweet: authorName/authorHandle/content)"},
    "BinaryBento": {"nested": ("binaryBento",), "desc": "二进制便当卡片 (binaryBento: leftCard/rightCard)"},
    "ProtocolStackTower": {"nested": ("protocolTower",), "desc": "协议栈塔 (protocolTower: activeLayer/showAllLayers/title)"},
    "PacketAssemblyPipeline": {"nested": ("packetAssembly",), "desc": "数据包组装流水线 (packetAssembly: stage/layerName/payloadText)"},
    "RouterPacketInspection": {"nested": ("routerInspection",), "desc": "路由器查表转发表 (routerInspection: 查表动作)"},
    "WeChatMobileMockup": {"nested": ("wechat",), "desc": "微信手机 mockup (wechat: mode/senderName/messageText/sentTime)"},
    "WebBrowserMockup": {"nested": ("browser",), "desc": "网页浏览器 mockup (browser: url/image)"},
    "BrowserScreenshot": {"nested": ("browser",), "desc": "浏览器真实截图视窗 (browser: url/image)"},
    "CinematicHero": {"nested": None, "desc": "电影级 Hero 大场景 (heroImage/heroVideo)"},
}

# 人工审校门核查清单 (执行计划: 事实核查 SOP 三源核查 + 引用快照)
REVIEW_CHECKLIST: List[str] = [
    "事实核查: 所有技术声明均有可靠信源支撑 (三源核查 + 引用快照)",
    "数字审计: 性能数字/比例均有出处, 无估值伪装精确值",
    "口播文案: 语句通顺符合口语播报, 无语病与歧义",
    "分镜节奏: 每幕信息密度适中, 无大段文字墙",
    "合规检查: 无极限词/绝对化用语, AI 生成标注已附加",
]


class ScriptgenError(Exception):
    """LLM 分镜生成或契约校验失败 (显式报错, 由调用方决定降级/重试)。"""


class ReviewGateError(Exception):
    """人工审校门未通过: LLM 草稿未经批准不得进入生产环节。"""


# ---------------------------------------------------------------------------
# 契约校验 (蓝本 scripts/validator.py validate_script_file 的 schema 审查)
# ---------------------------------------------------------------------------

def validate_storyboard_payload(payload: Any) -> Tuple[List[str], List[str]]:
    """校验 LLM 产出的分镜契约, 返回 (errors, warnings)。

    检查项:
      - 根对象: project / title / scenes 必填且非空
      - fps: 正整数 (缺失记 warning 并按 30 归一化)
      - 每幕: id 唯一非空 / text 非空 / type 合法 (未知类型记 warning, 按默认卡片渲染)
      - 嵌套配置: 注册表声明 nested 的 type 必须提供对应字段 (缺失记 error)
      - estimatedDuration: 正数 (缺失记 warning)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(payload, dict):
        return ([f"根对象必须是 JSON 对象 (mapping)，实际为: {type(payload).__name__}"], warnings)

    for field in ("project", "title"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"根对象缺少必填字段或为空: '{field}'")

    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or len(scenes) == 0:
        errors.append("'scenes' 必须为非空列表 (至少 1 幕分镜)")
        return (errors, warnings)

    fps = payload.get("fps", DEFAULT_FPS)
    if not isinstance(fps, int) or fps <= 0:
        warnings.append(f"fps 缺失或非法 ({fps!r})，将按 {DEFAULT_FPS} 归一化")

    seen_ids = set()
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{idx + 1}") if isinstance(scene, dict) else f"scene_{idx + 1}"
        if not isinstance(scene, dict):
            errors.append(f"分镜 [{scene_id}] 必须是 JSON 对象，实际为: {type(scene).__name__}")
            continue

        sid = scene.get("id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"分镜 #{idx + 1} 缺少非空字符串 'id'")
        elif sid in seen_ids:
            errors.append(f"分镜 id 重复: {sid!r}")
        else:
            seen_ids.add(sid)

        text = scene.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"分镜 [{scene_id}] 缺少有效旁白文案 (text 为空)")

        scene_type = scene.get("type", "Default")
        if scene_type in SCENE_TYPE_REGISTRY:
            nested_fields = SCENE_TYPE_REGISTRY[scene_type]["nested"]
            if nested_fields:
                for nf in nested_fields:
                    value = scene.get(nf)
                    if value is None or (isinstance(value, (list, dict, str)) and len(value) == 0):
                        errors.append(
                            f"分镜 [{scene_id}] 声明类型 {scene_type}，但缺少嵌套配置字段 '{nf}'"
                        )
        else:
            warnings.append(
                f"分镜 [{scene_id}] 类型 {scene_type!r} 不在注册表中, 将按默认卡片渲染 (建议修正)"
            )

        duration = scene.get("estimatedDuration")
        if duration is None:
            warnings.append(f"分镜 [{scene_id}] 缺少 estimatedDuration，将按 {DEFAULT_SCENE_DURATION}s 兜底")
        elif not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"分镜 [{scene_id}] estimatedDuration 必须为正数，实际为: {duration!r}")

    return (errors, warnings)


# ---------------------------------------------------------------------------
# 人工审校门
# ---------------------------------------------------------------------------

def build_review_block() -> Dict[str, Any]:
    """构造待审校状态的 review 元数据块 (LLM 草稿的默认状态)。"""
    return {
        "status": "pending",
        "required": True,
        "reviewer": None,
        "reviewedAt": None,
        "checklist": list(REVIEW_CHECKLIST),
    }


def approve_storyboard(payload: Dict[str, Any], reviewer: str) -> Dict[str, Any]:
    """批准分镜 (人工审校门放行); reviewer 必填, 留痕审计。"""
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ReviewGateError("审校人 (reviewer) 不能为空: 审校门必须留下可追溯的审批人")
    review = payload.get("review")
    if not isinstance(review, dict):
        review = build_review_block()
        payload["review"] = review
    review["status"] = "approved"
    review["reviewer"] = reviewer.strip()
    review["reviewedAt"] = now_iso()
    return payload


def assert_review_approved(payload: Dict[str, Any], context: str = "") -> None:
    """审校门断言: 未批准的分镜禁止进入下游生产 (TTS/渲染)。"""
    review = payload.get("review") if isinstance(payload, dict) else None
    status = review.get("status") if isinstance(review, dict) else None
    if status != "approved":
        raise ReviewGateError(
            f"{context}分镜未通过人工审校门 (review.status={status!r})；"
            "按生产规范，LLM 生成的草稿必须经人工审校批准后才能进入 TTS/渲染环节。"
        )


# ---------------------------------------------------------------------------
# AI 标注 (平台合规: AI 生成内容显式声明)
# ---------------------------------------------------------------------------

def attach_ai_disclosure(payload: Dict[str, Any], model: str) -> Dict[str, Any]:
    """自动附加 AI 生成标注块 (执行计划场景三"AI 标注自动附加"的共享实现)。"""
    payload["aiDisclosure"] = {
        "isAiGenerated": True,
        "model": model,
        "generatedAt": now_iso(),
        "notice": "本视频分镜文案由 AI 辅助生成并经过人工审校门审核; 成片需按平台规范标注 AI 生成内容。",
    }
    return payload


# ---------------------------------------------------------------------------
# 提示词工程
# ---------------------------------------------------------------------------

def _registry_prompt_lines() -> str:
    lines = []
    for name, meta in SCENE_TYPE_REGISTRY.items():
        nested = f" (必须提供嵌套字段: {', '.join(meta['nested'])})" if meta["nested"] else ""
        lines.append(f"  - {name}: {meta['desc']}{nested}")
    return "\n".join(lines)


def build_scriptgen_messages(topic: str, scene_count: int, domain: str = "") -> List[Dict[str, str]]:
    """构造 LLM 消息: system 定义契约与规则, user 给出主题。"""
    system = f"""你是一位资深技术科普视频编导, 擅长把硬核技术主题转化为高信息密度、有认知张力的短视频分镜。
请严格输出一个 JSON 对象 (不要输出任何额外文字, 不要使用 markdown 代码围栏), 契约如下:

{{
  "project": "<英文或拼音项目标识>",
  "title": "<视频标题, 带悬念或反差>",
  "theme": "linear-graphite",
  "engine": "chattts",
  "voice": "4444",
  "fps": 30,
  "scenes": [
    {{
      "id": "scene_01",
      "type": "<场景类型, 见下方注册表>",
      "title": "<本幕标题>",
      "text": "<本幕旁白文案, 口语化, 60-140字>",
      "category": "<场景分类标签>",
      "highlightWords": ["关键词1", "关键词2"],
      "estimatedDuration": <秒数, 正数, 3-12>
      // 如 type 需要嵌套配置, 必须提供对应字段
    }}
  ]
}}

可用场景类型注册表 (与渲染组件一一对应):
{_registry_prompt_lines()}

硬性规则 (数据诚信):
1. scenes 数量必须精确等于 {scene_count} 幕; 第一幕必须是 MinimalHeadline 开场钩子, 最后一幕必须是 MinimalHeadline 收尾总结;
2. 旁白文案必须是口语化中文, 禁止书面语长难句; 禁止编造具体性能数字, 如无可靠信源, 用定性描述代替;
3. 嵌套配置字段必须与 type 匹配, 字段名严格遵循注册表;
4. estimatedDuration 为正数 (秒);
5. 除 JSON 对象外不要输出任何内容。"""

    user = f"视频主题: {topic}"
    if domain:
        user += f"\n技术领域提示: {domain}"
    user += f"\n请生成 {scene_count} 幕分镜。"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# 生成与归一化
# ---------------------------------------------------------------------------

def generate_storyboard(
    topic: str,
    client: LLMClient,
    scene_count: int = 5,
    theme: str = "linear-graphite",
    domain: str = "",
    project_name: str = "",
    engine: str = "chattts",
    voice: str = "4444",
) -> Dict[str, Any]:
    """LLM 主题 -> 分镜契约 (校验 + 归一化 + 审校门挂起 + AI 标注)。

    失败策略: LLM 调用/解析/契约校验失败一律显式抛错, 无模板兜底 (数据诚信)。
    """
    messages = build_scriptgen_messages(topic, scene_count, domain)
    print(f"🤖 [LLM ScriptGen] 正在调用模型生成分镜: {client.model} (主题: {topic})")
    try:
        payload = client.chat_json(messages, temperature=0.5, max_tokens=8192)
    except LLMError as e:
        raise ScriptgenError(f"LLM 分镜生成失败: {e}")

    errors, warnings = validate_storyboard_payload(payload)
    if warnings:
        print(f"⚠️ [LLM ScriptGen] 契约校验警告 {len(warnings)} 项:")
        for w in warnings:
            print(f"   • {w}")
    if errors:
        raise ScriptgenError(
            "LLM 产出未通过分镜契约校验 (已拒绝写入, 不降级不编造):\n"
            + "\n".join(f"   ✖ {e}" for e in errors)
        )

    # 归一化: CLI 显式参数优先, LLM 缺失字段兜底
    fps = payload.get("fps") if isinstance(payload.get("fps"), int) and payload.get("fps", 0) > 0 else DEFAULT_FPS
    payload["project"] = project_name.strip() or slugify(topic)
    payload["title"] = payload.get("title") or topic
    payload["theme"] = theme
    payload["engine"] = engine
    payload["voice"] = voice
    payload["fps"] = fps

    total_frames = 0
    for idx, scene in enumerate(payload["scenes"]):
        scene.setdefault("id", f"scene_{idx + 1:02d}")
        duration = scene.get("estimatedDuration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            duration = DEFAULT_SCENE_DURATION
            scene["estimatedDuration"] = duration
        frames = int(round(duration * fps))
        scene["estimatedFrames"] = frames
        scene["durationInFrames"] = frames
        total_frames += frames
    payload["totalDurationInFrames"] = total_frames

    payload["source"] = {
        "generatedBy": "llm_scriptgen.py",
        "topic": topic,
        "domain": domain or "auto",
        "model": client.model,
        "generatedAt": now_iso(),
    }

    # 审校门挂起 + AI 标注 (草稿默认 pending, 必须人工批准)
    payload["review"] = build_review_block()
    attach_ai_disclosure(payload, client.model)
    return payload


def load_storyboard(path: str) -> Dict[str, Any]:
    """读取分镜 JSON (--status / --approve 模式的输入)。"""
    if not os.path.exists(path):
        raise ScriptgenError(f"分镜文件不存在: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError as e:
        raise ScriptgenError(f"分镜文件 JSON 解析失败: {path}\n{e}")


def save_storyboard(payload: Dict[str, Any], output_path: str) -> str:
    """落盘分镜契约 (相对路径基于 PROJECT_ROOT 解析)。"""
    out_abs = output_path if os.path.isabs(output_path) else os.path.join(PROJECT_ROOT, output_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_abs


def _rel_or_abs(path: str) -> str:
    """跨盘符时 relpath 不可用 (Windows ValueError), 回退绝对路径 (绝不因此中断收尾)。"""
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_parser() -> argparse.ArgumentParser:
    """定义并返回 LLM 分镜生成器命令行解析器"""
    parser = argparse.ArgumentParser(
        description="知识科普类: LLM 主题 -> 分镜 JSON 契约生成器 + 人工审校门 (W5-6)"
    )
    # 生成模式
    parser.add_argument("--topic", type=str, default="", help="视频核心主题 (生成模式必填)")
    parser.add_argument("--project", type=str, default="", help="项目标识 (默认由 topic 自动生成)")
    parser.add_argument("--scenes", type=int, default=5, choices=range(2, 13),
                        help="分镜数量 (2 ~ 12, 默认 5; 首尾两幕固定为 MinimalHeadline)")
    parser.add_argument(
        "--theme",
        type=str,
        choices=[
            "linear-graphite", "vercel-geist", "motion-canvas-warm", "cyber-blueprint",
            "obsidian-minimal", "blueprint-engineering", "cinema-editorial",
        ],
        default="linear-graphite",
        help="视觉主题 (默认 linear-graphite)",
    )
    parser.add_argument("--domain", type=str, default="", help="技术领域提示 (可选, 写入提示词)")
    parser.add_argument("--engine", type=str, default="chattts", help="TTS 引擎 (默认 chattts)")
    parser.add_argument("--voice", type=str, default="4444", help="TTS 音色 (默认 4444)")
    parser.add_argument("--output", type=str, default="",
                        help="输出路径 (默认 content/scripts/{project}.json)")
    parser.add_argument("--dry-run", action="store_true", help="仅打印至控制台, 不写入磁盘")
    # 审校门模式
    parser.add_argument("--approve", action="store_true", help="审校门批准模式 (需配合 --input/--reviewer)")
    parser.add_argument("--status", action="store_true", help="查询分镜审校门状态 (需配合 --input)")
    parser.add_argument("--input", type=str, default="", help="审校门模式操作的既有分镜文件路径")
    parser.add_argument("--reviewer", type=str, default="", help="审校人署名 (批准模式必填, 留痕审计)")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # -- 审校门: 状态查询模式 ------------------------------------------------
    if args.status:
        if not args.input:
            parser.error("--status 需要配合 --input 指定分镜文件")
        try:
            payload = load_storyboard(args.input)
        except ScriptgenError as e:
            print(f"\n❌ [LLM ScriptGen] {e}")
            sys.exit(2)
        review = payload.get("review") or {}
        print(f"\n=======================================================")
        print(f"🔍 [Review Gate] 分镜审校状态: {args.input}")
        print(f"   状态: {review.get('status', '<未标记, 视为 pending>')}")
        print(f"   审校人: {review.get('reviewer') or '<未审校>'}")
        print(f"   审校时间: {review.get('reviewedAt') or '<未审校>'}")
        print(f"=======================================================\n")
        sys.exit(0 if review.get("status") == "approved" else 1)

    # -- 审校门: 批准模式 ----------------------------------------------------
    if args.approve:
        if not args.input:
            parser.error("--approve 需要配合 --input 指定分镜文件")
        try:
            payload = load_storyboard(args.input)
            approve_storyboard(payload, args.reviewer)
            out_abs = save_storyboard(payload, args.input)
        except (ScriptgenError, ReviewGateError) as e:
            print(f"\n❌ [Review Gate] 批准失败: {e}")
            sys.exit(5)
        print(f"\n=======================================================")
        print(f"✅ [Review Gate] 分镜已通过人工审校门: {args.input}")
        print(f"   审校人: {payload['review']['reviewer']} | 时间: {payload['review']['reviewedAt']}")
        print(f"=======================================================\n")
        print("💡 后续可执行: python scripts/pipeline.py --script "
              f"{_rel_or_abs(out_abs)} --project {payload.get('project', 'unknown')} --render")
        return

    # -- 生成模式 ------------------------------------------------------------
    if not args.topic.strip():
        parser.error("生成模式必须提供 --topic (非空); 审校门模式请使用 --approve/--status")

    client = LLMClient()
    try:
        storyboard = generate_storyboard(
            topic=args.topic,
            client=client,
            scene_count=args.scenes,
            theme=args.theme,
            domain=args.domain,
            project_name=args.project,
            engine=args.engine,
            voice=args.voice,
        )
    except ScriptgenError as e:
        print(f"\n❌ [LLM ScriptGen] {e}")
        sys.exit(4)

    output_path = args.output.strip() or os.path.join(SCRIPTS_DIR, f"{storyboard['project']}.json")
    formatted = json.dumps(storyboard, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(formatted)
        return

    out_abs = save_storyboard(storyboard, output_path)
    print(f"\n=======================================================")
    print(f"✅ [LLM ScriptGen] 分镜草稿已生成 ({len(storyboard['scenes'])} 幕 / "
          f"{storyboard['totalDurationInFrames']} 帧 @ {storyboard['fps']}fps)")
    print(f"   输出: {out_abs}")
    print(f"   ⏸️  审校门状态: pending (必须经人工审校批准后才能进入生产)")
    print(f"=======================================================\n")
    print("💡 审校批准命令: python scripts/llm_scriptgen.py --approve "
          f"--input {_rel_or_abs(out_abs)} --reviewer <你的名字>")


if __name__ == "__main__":
    main()

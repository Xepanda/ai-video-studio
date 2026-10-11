#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/create_tech_news_shorts.py
极简竖屏科技资讯短视频脚手架生成器 (Tech News Vertical Shorts Generator)

功能特性：
1. 生产级竖屏短视频 (1080x1920 @ 30FPS) 剧本脚手架生成
2. 自动化 Slugification (拼音 / 英文智能转换与特殊字符清洗)
3. 语速与分镜时长自动化估算 (按中英文及标点停顿精准预测)
4. 内置 Codex Day 6 参考示范样片预设 (--preset codex_day6)，1:1 像素级复刻 8 幕高保真结构
5. 严格契合 TechNewsShortsScene、TweetEmbedCard、BinaryBentoCard 与 MinimalHeadline 契约
6. 支持 CLI 灵活参数定制与 Schema 完整性自动化校验
"""

import os
import sys
import re
import json
import time
import argparse
from typing import Dict, Any, List, Tuple, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "content", "scripts")


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def slugify(text: str) -> str:
    """
    生成规范且可读的文件名 Slug：
    1. 中文字符尝试转换为拼音 (优先使用 pypinyin)
    2. 转换为小写并消除多余空格与特殊标点
    3. 合并连续下划线并去除首尾下划线
    4. 若为空则提供稳妥回退标识
    """
    if not text or not text.strip():
        return f"shorts_{int(time.time()) % 100000:05d}"

    cleaned = text.strip()

    # 尝试将中文转为拼音
    try:
        import pypinyin
        pinyin_list = pypinyin.lazy_pinyin(cleaned)
        cleaned = " ".join(pinyin_list)
    except Exception:
        pass

    cleaned = cleaned.lower()
    # 替换非字母数字字符为下划线
    cleaned = re.sub(r'[^a-z0-9]+', '_', cleaned)
    # 合并多个下划线
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')

    if cleaned:
        return cleaned
    return f"project_{int(time.time()) % 100000:05d}"


def estimate_duration_seconds(text: str, chars_per_sec: float = 4.5, min_sec: float = 2.0) -> float:
    """
    估算分镜旁白文本所需的朗读时长（秒）。
    考虑中文字符数量、英文词汇数量以及标点停顿加权。
    """
    if not text or not text.strip():
        return min_sec

    # 中文字符计数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    # 英文单词计数
    english_words = len(re.findall(r'[a-zA-Z0-9]+', text))
    # 标点符号停顿时间：逗号/分号约 0.2s，句号/感叹号/换行约 0.4s
    short_pauses = len(re.findall(r'[,，、;；]', text)) * 0.2
    long_pauses = len(re.findall(r'[。！？!\?\n]', text)) * 0.4

    base_duration = (chinese_chars / chars_per_sec) + (english_words / 2.5) + short_pauses + long_pauses
    return max(min_sec, round(base_duration, 2))


def estimate_duration_frames(text: str, fps: int = 30, chars_per_sec: float = 4.5, min_sec: float = 2.0) -> int:
    """
    根据估算秒数计算分镜帧数
    """
    sec = estimate_duration_seconds(text, chars_per_sec=chars_per_sec, min_sec=min_sec)
    return int(round(sec * fps))


def build_codex_day6_preset(
    project: str = "codex_day6_reset_demo",
    theme: str = "linear-graphite",
    voice: str = "4444",
    engine: str = "chattts",
    fps: int = 30
) -> Dict[str, Any]:
    """
    构建精准 1:1 像素级复刻参考视频（38 秒）的 Codex Day 6 8 幕高保真剧本契约
    """
    scenes = [
        # Scene 1: MinimalHeadline (inverted: false)
        {
            "id": "scene_01",
            "type": "MinimalHeadline",
            "title": "没有新功能，只有重置！",
            "text": "没有新功能，只有重置！",
            "category": "CODEX DAY 6",
            "highlightWords": ["没有新功能", "重置"],
            "inverted": False,
            "estimatedDuration": 3.5,
            "estimatedFrames": int(round(3.5 * fps))
        },
        # Scene 2: TweetEmbed
        {
            "id": "scene_02",
            "type": "TweetEmbed",
            "title": "Tibo 官方推文确认第 6 天重置",
            "text": "Tibo 发推表示，第六天只做 Reset。",
            "tweet": {
                "authorName": "Tibo",
                "authorHandle": "@tibo_maker",
                "avatarUrl": "",
                "isVerified": True,
                "timeAgo": "14h",
                "content": "Day 6: Reset\n\nNo new features today, just resetting quotas for everyone.",
                "highlightWords": ["Reset", "No new features"],
                "metrics": {
                    "replies": "128",
                    "retweets": "450",
                    "likes": "3.4K",
                    "views": "150K"
                },
                "subtitle": "官方确认：第六天无新功能发布，仅执行全局重置"
            },
            "estimatedDuration": 4.5,
            "estimatedFrames": int(round(4.5 * fps))
        },
        # Scene 3: BinaryBento
        {
            "id": "scene_03",
            "type": "BinaryBento",
            "title": "配额重置机制与规则",
            "text": "二选一规则：要么直接刷新额度，要么给重置卡。",
            "binaryBento": {
                "title": "配额重置机制",
                "subtitle": "二选一规则",
                "dividerText": "或",
                "leftCard": {
                    "title": "消耗每日配额",
                    "desc": "等待每日零点自动刷新",
                    "tag": "方案 A",
                    "blocksTotal": 5,
                    "blocksActive": 3
                },
                "rightCard": {
                    "title": "使用月度重置卡",
                    "desc": "即时恢复全部对话算力",
                    "pill": "重置卡",
                    "tag": "方案 B"
                }
            },
            "estimatedDuration": 6.0,
            "estimatedFrames": int(round(6.0 * fps))
        },
        # Scene 4: MinimalHeadline (inverted: true - 纯白底黑字反转)
        {
            "id": "scene_04",
            "type": "MinimalHeadline",
            "title": "具体怎么重置帖子没细说，等落地才知道！",
            "text": "具体怎么重置帖子没细说，等落地才知道！",
            "category": "UNCONFIRMED",
            "highlightWords": ["没细说", "等落地才知道"],
            "inverted": True,
            "estimatedDuration": 4.5,
            "estimatedFrames": int(round(4.5 * fps))
        },
        # Scene 5: MinimalHeadline (inverted: false)
        {
            "id": "scene_05",
            "type": "MinimalHeadline",
            "title": "上一次全员重置还是在第二天。",
            "text": "上一次全员重置还是在第二天。",
            "category": "TIMELINE",
            "highlightWords": ["第二天", "全员重置"],
            "inverted": False,
            "estimatedDuration": 4.0,
            "estimatedFrames": int(round(4.0 * fps))
        },
        # Scene 6: TweetEmbed
        {
            "id": "scene_06",
            "type": "TweetEmbed",
            "title": "前一天 Tibo 预热发推",
            "text": "前一天 Tibo 就发推说：一眨眼都周六了。",
            "tweet": {
                "authorName": "Tibo",
                "authorHandle": "@tibo_maker",
                "avatarUrl": "",
                "isVerified": True,
                "timeAgo": "1d",
                "content": "Can't believe it's already Saturday. Time flies when building in public.",
                "highlightWords": ["Saturday", "Time flies"],
                "metrics": {
                    "replies": "86",
                    "retweets": "190",
                    "likes": "1.8K",
                    "views": "82K"
                },
                "subtitle": "此前周五晚间的微妙预热"
            },
            "estimatedDuration": 4.5,
            "estimatedFrames": int(round(4.5 * fps))
        },
        # Scene 7: MinimalHeadline (inverted: false)
        {
            "id": "scene_07",
            "type": "MinimalHeadline",
            "title": "合着功能没影子，这是又要重置啊！",
            "text": "合着功能没影子，这是又要重置啊！",
            "category": "INSIGHT",
            "highlightWords": ["没影子", "又要重置"],
            "inverted": False,
            "estimatedDuration": 4.5,
            "estimatedFrames": int(round(4.5 * fps))
        },
        # Scene 8: MinimalHeadline (inverted: true - 纯白底黑字反转)
        {
            "id": "scene_08",
            "type": "MinimalHeadline",
            "title": "第七天到底会有什么新功能？明天接着看！",
            "text": "第七天到底会有什么新功能？明天接着看！",
            "category": "STAY TUNED",
            "highlightWords": ["第七天", "明天接着看"],
            "inverted": True,
            "estimatedDuration": 5.5,
            "estimatedFrames": int(round(5.5 * fps))
        }
    ]

    total_frames = sum(s.get("estimatedFrames", int(round(4.5 * fps))) for s in scenes)

    return {
        "project": project,
        "title": "OpenAI Codex 第六天更新：没有新功能，只有重置",
        "theme": theme,
        "voice": voice,
        "engine": engine,
        "fps": fps,
        "bgm": "bgm_cyber_ambient.wav",
        "bgmPath": "audio/bgm_cyber_ambient.wav",
        "bgmVolume": 0.035,
        "bgmDuckRatio": 0.20,
        "voiceVolume": 1.0,
        "enableBgm": True,
        "enableSfx": True,
        "totalDurationInFrames": total_frames,
        "scenes": scenes
    }


def generate_tech_news_script(
    topic: str,
    project: Optional[str] = None,
    theme: str = "linear-graphite",
    voice: str = "4444",
    engine: str = "chattts",
    preset: Optional[str] = None,
    fps: int = 30
) -> Dict[str, Any]:
    """
    根据主题或预设自动构建短视频剧本
    """
    if preset == "codex_day6":
        p_name = project or "codex_day6_reset_demo"
        return build_codex_day6_preset(project=p_name, theme=theme, voice=voice, engine=engine, fps=fps)

    project_slug = project or slugify(topic)

    # 提取高频关键词作为高亮词
    clean_topic = topic.replace("：", ":").replace("，", ",")
    words_pool = [w for w in re.split(r'[:,\s\-]+', clean_topic) if len(w) >= 2]
    hl_words = words_pool[:3] if words_pool else ["重磅更新", "核心特性"]

    scenes = [
        # 1. 悬念钩子 (大字报)
        {
            "id": "scene_01",
            "type": "MinimalHeadline",
            "title": topic,
            "text": f"重磅消息！{topic}！",
            "category": "BREAKING NEWS",
            "highlightWords": hl_words,
            "inverted": False,
            "estimatedDuration": estimate_duration_seconds(f"重磅消息！{topic}！"),
            "estimatedFrames": estimate_duration_frames(f"重磅消息！{topic}！", fps=fps)
        },
        # 2. 官方推特实锤
        {
            "id": "scene_02",
            "type": "TweetEmbed",
            "title": f"官方关于 {topic} 的最新公告",
            "text": f"官方刚刚在推特发布了最新公告，引发全网热议。",
            "tweet": {
                "authorName": "Tech Insider",
                "authorHandle": "@tech_insider",
                "avatarUrl": "",
                "isVerified": True,
                "timeAgo": "2h",
                "content": f"Official Announcement: {topic}\n\nHere is everything you need to know about this major update.",
                "highlightWords": hl_words,
                "metrics": {
                    "replies": "156",
                    "retweets": "420",
                    "likes": "3.8K",
                    "views": "180K"
                },
                "subtitle": "官方权威发布，全网关注"
            },
            "estimatedDuration": estimate_duration_seconds("官方刚刚在推特发布了最新公告，引发全网热议。"),
            "estimatedFrames": estimate_duration_frames("官方刚刚在推特发布了最新公告，引发全网热议。", fps=fps)
        },
        # 3. 核心机制对比 (二选一 Bento)
        {
            "id": "scene_03",
            "type": "BinaryBento",
            "title": "新旧方案核心对比",
            "text": "究竟是颠覆性创新，还是换汤不换药？我们对比了两种方案。",
            "binaryBento": {
                "title": "技术方案路线比对",
                "subtitle": "二选一关键决策",
                "dividerText": "对比",
                "leftCard": {
                    "title": "原有传统路径",
                    "desc": "依赖传统堆叠，延迟与成本居高不下",
                    "tag": "旧模式",
                    "blocksTotal": 5,
                    "blocksActive": 2
                },
                "rightCard": {
                    "title": "最新原生机制",
                    "desc": "极低推理时延与动态算力调度",
                    "pill": "推荐方案",
                    "tag": "新架构"
                }
            },
            "estimatedDuration": estimate_duration_seconds("究竟是颠覆性创新，还是换汤不换药？我们对比了两种方案。"),
            "estimatedFrames": estimate_duration_frames("究竟是颠覆性创新，还是换汤不换药？我们对比了两种方案。", fps=fps)
        },
        # 4. 深度洞察 (反转白底大字报)
        {
            "id": "scene_04",
            "type": "MinimalHeadline",
            "title": "底层逻辑与潜在影响",
            "text": "看似只是小步迭代，背后其实藏着大模型落地的新趋势！",
            "category": "DEEP DIVE",
            "highlightWords": ["小步迭代", "新趋势"],
            "inverted": True,
            "estimatedDuration": estimate_duration_seconds("看似只是小步迭代，背后其实藏着大模型落地的新趋势！"),
            "estimatedFrames": estimate_duration_frames("看似只是小步迭代，背后其实藏着大模型落地的新趋势！", fps=fps)
        },
        # 5. 结尾互动与预告
        {
            "id": "scene_05",
            "type": "MinimalHeadline",
            "title": "关注进展，持续深潜",
            "text": "你觉得这次更新能解决痛点吗？评论区聊聊，明天接着看！",
            "category": "STAY TUNED",
            "highlightWords": ["评论区聊聊", "明天接着看"],
            "inverted": False,
            "estimatedDuration": estimate_duration_seconds("你觉得这次更新能解决痛点吗？评论区聊聊，明天接着看！"),
            "estimatedFrames": estimate_duration_frames("你觉得这次更新能解决痛点吗？评论区聊聊，明天接着看！", fps=fps)
        }
    ]

    total_frames = sum(s.get("estimatedFrames", int(round(4.0 * fps))) for s in scenes)

    return {
        "project": project_slug,
        "title": topic,
        "theme": theme,
        "voice": voice,
        "engine": engine,
        "fps": fps,
        "bgm": "bgm_cyber_ambient.wav",
        "bgmPath": "audio/bgm_cyber_ambient.wav",
        "bgmVolume": 0.035,
        "bgmDuckRatio": 0.20,
        "voiceVolume": 1.0,
        "enableBgm": True,
        "enableSfx": True,
        "totalDurationInFrames": total_frames,
        "scenes": scenes
    }


def validate_script_schema(script_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    审查短视频剧本 Schema 规范性与必要元数据完整性
    """
    errors = []
    warnings = []

    # 1. 核心根属性校验
    for field in ["project", "theme", "voice", "engine", "scenes"]:
        if field not in script_data:
            errors.append(f"剧本根对象缺失必填字段: '{field}'")

    scenes = script_data.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) == 0:
        errors.append("剧本 'scenes' 列表为空或不是合法列表！")
        return errors, warnings

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{idx+1}")
        s_type = scene.get("type")

        # 检查旁白文案
        text = scene.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            errors.append(f"分镜 [{scene_id}] 缺少有效旁白文本 (text)！")

        # 组件特化校验
        if s_type == "TweetEmbed":
            tweet = scene.get("tweet")
            if not isinstance(tweet, dict):
                errors.append(f"分镜 [{scene_id}] 类型为 TweetEmbed，但 tweet 属性不是字典！")
            else:
                for tf in ["authorName", "authorHandle", "content"]:
                    if not tweet.get(tf):
                        errors.append(f"分镜 [{scene_id}] tweet 对象缺少核心字段: '{tf}'")
        elif s_type == "BinaryBento":
            bento = scene.get("binaryBento")
            if not isinstance(bento, dict):
                errors.append(f"分镜 [{scene_id}] 类型为 BinaryBento，但 binaryBento 属性不是字典！")
            else:
                left_card = bento.get("leftCard")
                right_card = bento.get("rightCard")
                if not isinstance(left_card, dict) or not isinstance(right_card, dict):
                    errors.append(f"分镜 [{scene_id}] binaryBento 必须同时包含 leftCard 与 rightCard 对象！")
                else:
                    if not left_card.get("title") or not right_card.get("title"):
                        errors.append(f"分镜 [{scene_id}] binaryBento 卡片缺少 title 字段！")
        elif s_type == "MinimalHeadline":
            if not scene.get("title") and not scene.get("text"):
                errors.append(f"分镜 [{scene_id}] MinimalHeadline 缺少 title 或 text！")

    return errors, warnings


def save_script_to_file(script_data: Dict[str, Any], output_path: str) -> str:
    """
    格式化保存剧本至 JSON 文件
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output), exist_ok=True)
    with open(abs_output, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    return abs_output


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    CLI 参数解析
    """
    parser = argparse.ArgumentParser(
        description="极简竖屏科技资讯短视频剧本生成器 (Tech News Vertical Shorts Generator)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="核心资讯主题标题（必填，若指定 --preset codex_day6 则可缺省）"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="项目唯一标识 slug（默认由 topic 自动生成拼音/英文 slug）"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="linear-graphite",
        help="视觉设计主题（默认 linear-graphite）"
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="4444",
        help="TTS 音色配置（默认 4444, ChatTTS 随和男声）"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="chattts",
        help="TTS 合成引擎（默认 chattts）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="剧本输出文件路径（默认 content/scripts/{project}.json）"
    )
    parser.add_argument(
        "--preset",
        type=str,
        default=None,
        choices=["codex_day6"],
        help="预设高保真模板（支持 codex_day6 官方示范样片）"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="视频帧率（默认 30 FPS）"
    )

    args = parser.parse_args(argv)

    # 若未指定 topic 且为 codex_day6 预设，补齐默认 topic
    if not args.topic:
        if args.preset == "codex_day6":
            args.topic = "OpenAI Codex 第六天更新：没有新功能，只有重置"
        else:
            parser.error("缺少必填参数: --topic")

    if not args.project:
        if args.preset == "codex_day6":
            args.project = "codex_day6_reset_demo"
        else:
            args.project = slugify(args.topic)

    if not args.output:
        args.output = os.path.join(SCRIPTS_DIR, f"{args.project}.json")

    return args


def main():
    args = parse_args()

    print(f"\n{BColors.HEADER}===================================================={BColors.ENDC}")
    print(f"{BColors.BOLD}⚡ [TechNewsShorts] 启动竖屏科技资讯短视频剧本生成器...{BColors.ENDC}")
    print(f"{BColors.HEADER}===================================================={BColors.ENDC}\n")

    print(f"🎯 主题: {BColors.OKCYAN}{args.topic}{BColors.ENDC}")
    print(f"📁 项目 Slug: {BColors.OKBLUE}{args.project}{BColors.ENDC}")
    print(f"🎨 主题样式: {args.theme} | 配音引擎: {args.engine} (音色: {args.voice})")
    if args.preset:
        print(f"🚀 激活预设: {BColors.OKGREEN}{args.preset}{BColors.ENDC}")
    print("-" * 52)

    script_data = generate_tech_news_script(
        topic=args.topic,
        project=args.project,
        theme=args.theme,
        voice=args.voice,
        engine=args.engine,
        preset=args.preset,
        fps=args.fps
    )

    # 校验 Schema
    errors, warnings = validate_script_schema(script_data)
    if warnings:
        for w in warnings:
            print(f"{BColors.WARNING}⚠️ [WARN] {w}{BColors.ENDC}")
    if errors:
        for e in errors:
            print(f"{BColors.FAIL}❌ [ERROR] {e}{BColors.ENDC}")
        sys.exit(1)

    # 输出文件
    saved_path = save_script_to_file(script_data, args.output)
    total_scenes = len(script_data.get("scenes", []))
    total_est_frames = script_data.get("totalDurationInFrames", 0)

    print(f"✅ 剧本成功生成！分镜段落: {total_scenes} 幕 | 预估总帧数: {total_est_frames} 帧 (~{total_est_frames/args.fps:.1f}s)")
    print(f"💾 存储文件: {BColors.OKGREEN}{saved_path}{BColors.ENDC}\n")


if __name__ == "__main__":
    main()

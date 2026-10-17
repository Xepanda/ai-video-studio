#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/validator.py
视频工程数据契约与资产完整性自动化审查工具 (Quality Gate Validator)
严格校验：
  1. timeline.json 契约合法性
  2. 分镜帧数连续性与全局总帧数守恒
  3. 静态音视频资产存在性与时长容差
  4. 字幕短句 (words) 声学打点单调性、起止有效性与持续时间门禁
"""

import os
import sys
import json
import wave
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TIMELINE_PATH = os.path.join(PROJECT_ROOT, "public", "timeline.json")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_audio_duration_seconds(audio_full_path: str) -> float:
    """计算音频真实时长 (多后端容错: soundfile -> torchaudio -> wave)"""
    try:
        import soundfile as sf
        info = sf.info(audio_full_path)
        return float(info.duration)
    except Exception:
        pass

    try:
        import torchaudio
        info = torchaudio.info(audio_full_path)
        if info.sample_rate > 0:
            return float(info.num_frames) / float(info.sample_rate)
    except Exception:
        pass

    try:
        with wave.open(audio_full_path, 'rb') as wf:
            framerate = wf.getframerate()
            if framerate > 0:
                return wf.getnframes() / float(framerate)
    except Exception:
        pass

    return None

def validate_words(scene_id: str, scene: dict, duration: int, real_sec: float, fps: int, errors: list, warnings: list):
    """严格审查分镜内字幕短句 (words) 打点数据契约"""
    words = scene.get("words", [])
    if not words:
        warnings.append(f"分镜 [{scene_id}] 未配置任何字幕打点短句 (words 列表为空)。")
        return

    prev_start_frame = -1
    prev_start_ms = -1
    max_allowed_ms = int(real_sec * 1000) + 200 if real_sec is not None else int((duration / fps) * 1000) + 200

    for idx, w in enumerate(words):
        w_text = w.get("text", "")
        start_f = w.get("startFrame")
        end_f = w.get("endFrame")
        start_ms = w.get("startMs")
        end_ms = w.get("endMs")

        if start_f is None or end_f is None:
            errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 缺少 startFrame 或 endFrame！")
            continue

        # 1. 严格非负与起止区间
        if start_f < 0:
            errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 起始帧小于0: {start_f}")
        if start_f >= end_f:
            errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 帧数区间倒置或为零: [{start_f} ~ {end_f}]")
        if end_f > duration:
            errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 结束帧 ({end_f}) 超出分镜总时长 ({duration}帧)！")

        # 2. 单调性检查
        if start_f < prev_start_frame:
            errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 起始帧出现逆向回跳 (前句: {prev_start_frame}, 当前: {start_f})")
        prev_start_frame = start_f

        # 3. 毫秒打点检查
        if start_ms is not None and end_ms is not None:
            if start_ms >= end_ms:
                errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 毫秒区间倒置或为零: [{start_ms}ms ~ {end_ms}ms]")
            if end_ms > max_allowed_ms:
                warnings.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 结束毫秒 ({end_ms}ms) 超出音频总时长 ({max_allowed_ms}ms)！")
            if start_ms < prev_start_ms:
                errors.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 起始毫秒逆向回跳: {start_ms}ms < {prev_start_ms}ms")
            prev_start_ms = start_ms

        # 4. 短句极短闪现预警 (< 5 帧，约 166ms)
        chunk_dur = end_f - start_f
        if chunk_dur < 5:
            warnings.append(f"分镜 [{scene_id}] 短句 #{idx+1} '{w_text}' 持续时间仅 {chunk_dur} 帧 ({chunk_dur/fps*1000:.0f}ms)，可能导致字幕闪烁。")

def validate(timeline_path: str = None):
    print(f"\n{BColors.HEADER}===================================================={BColors.ENDC}")
    print(f"{BColors.BOLD}🔍 [Quality Gate] 启动视频数据契约与静态资产审查...{BColors.ENDC}")
    print(f"{BColors.HEADER}===================================================={BColors.ENDC}\n")

    errors = []
    warnings = []

    target_timeline = timeline_path or DEFAULT_TIMELINE_PATH
    # 1. 检查 timeline.json 存在性
    if not os.path.exists(target_timeline):
        print(f"{BColors.FAIL}[ERROR] 关键契约缺失: 找不到 {target_timeline}{BColors.ENDC}")
        print("请先运行 scripts/pipeline.py 或 scripts/sensevoice_aligner.py 生成时间轴！")
        sys.exit(1)

    with open(target_timeline, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"{BColors.FAIL}[ERROR] {target_timeline} JSON 解析失败: {e}{BColors.ENDC}")
            sys.exit(1)

    fps = data.get("fps", 30)
    scenes = data.get("scenes", [])
    total_frames = data.get("totalDurationInFrames", 0)

    print(f"📊 项目名称: {BColors.OKCYAN}{data.get('project', 'unknown')}{BColors.ENDC}")
    print(f"🎯 帧率配置: {fps} FPS | 分镜总数: {len(scenes)} | 宣称总帧数: {total_frames}")
    print("-" * 52)

    if not scenes:
        errors.append("timeline.json 中未定义任何分镜 scenes 列表！")

    current_expected_frame = 0
    calculated_total_frames = 0

    for i, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{i+1}")
        start_frame = scene.get("startFrame", 0)
        duration = scene.get("durationInFrames", 0)
        audio_rel_path = scene.get("audioPath")
        video_rel_path = scene.get("videoSrc")
        real_sec = None

        # 检查时间轴连续性
        if start_frame != current_expected_frame:
            errors.append(
                f"分镜 [{scene_id}] 起始帧不连续! 预期: {current_expected_frame}, 实际: {start_frame}"
            )

        current_expected_frame += duration
        calculated_total_frames += duration

        # 检查音频文件存在性与时长
        if audio_rel_path:
            audio_full_path = os.path.join(PUBLIC_DIR, audio_rel_path)
            if not os.path.exists(audio_full_path):
                errors.append(f"分镜 [{scene_id}] 音频文件不存在: {audio_rel_path}")
            else:
                real_sec = get_audio_duration_seconds(audio_full_path)
                if real_sec is not None:
                    ideal_frames = int(round(real_sec * fps))
                    diff = abs(ideal_frames - duration)
                    if diff > 3:  # 允许 3 帧以内的舍入缓冲
                        warnings.append(
                            f"分镜 [{scene_id}] 帧数设置({duration}帧)与真实音频时长({real_sec:.2f}s -> {ideal_frames}帧)存在 {diff} 帧偏差！"
                        )
        else:
            warnings.append(f"分镜 [{scene_id}] 未配置 audioPath 音频文件。")

        # 检查视频素材存在性 (实拍或 Google Flow B-Roll)
        if video_rel_path:
            video_full_path = os.path.join(PUBLIC_DIR, video_rel_path)
            if not os.path.exists(video_full_path):
                errors.append(f"分镜 [{scene_id}] 视频素材不存在: {video_rel_path}")

        # 深度校验字幕打点数据契约 (words)
        validate_words(scene_id, scene, duration, real_sec, fps, errors, warnings)

        # 视效组件契约深度审查 (Visual Component Schema Gate)
        scene_type = scene.get("type", "Default")
        if scene_type == "TweetEmbed" or scene.get("tweet"):
            tweet = scene.get("tweet")
            if not isinstance(tweet, dict):
                errors.append(f"分镜 [{scene_id}] 声明为 TweetEmbed，但 tweet 不是合法字典对象！")
            else:
                if not (tweet.get("authorName") or tweet.get("author")):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'authorName'！")
                if not (tweet.get("authorHandle") or tweet.get("handle")):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'authorHandle'！")
                if not tweet.get("content"):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'content'！")
        elif scene_type == "BinaryBento" or scene.get("binaryBento"):
            bento = scene.get("binaryBento")
            if not isinstance(bento, dict):
                errors.append(f"分镜 [{scene_id}] 声明为 BinaryBento，但 binaryBento 不是合法字典对象！")
            else:
                left_card = bento.get("leftCard")
                right_card = bento.get("rightCard")
                if not isinstance(left_card, dict) or not isinstance(right_card, dict):
                    errors.append(f"分镜 [{scene_id}] binaryBento 必须同时包含 leftCard 与 rightCard 对象！")
                else:
                    if not left_card.get("title") or not right_card.get("title"):
                        errors.append(f"分镜 [{scene_id}] binaryBento 卡片缺少 title 字段！")
        elif scene_type == "MinimalHeadline":
            title = scene.get("title") or (scene.get("words") and len(scene.get("words")) > 0)
            if not title:
                errors.append(f"分镜 [{scene_id}] MinimalHeadline 缺少 title 或字幕！")
        elif scene_type in ["MetricComparison", "MetricChart"]:
            metrics = scene.get("metrics", [])
            if not metrics:
                errors.append(f"分镜 [{scene_id}] 声明类型为 {scene_type}，但未提供 metrics 数据数组！")
            for m_idx, cat in enumerate(metrics):
                if not isinstance(cat, dict):
                    errors.append(f"分镜 [{scene_id}] 指标项 #{m_idx+1} 不是合法字典对象！")
                elif not cat.get("items") and not cat.get("value") and not cat.get("label") and not cat.get("title"):
                    errors.append(f"分镜 [{scene_id}] 指标项 #{m_idx+1} 缺少 items 或 value/label 核心字段！")
        elif scene_type in ["ArchitectureTopology", "TopologyFlow"]:
            nodes = scene.get("topologyNodes", [])
            if not nodes:
                errors.append(f"分镜 [{scene_id}] 声明类型为 {scene_type}，但未提供 topologyNodes 节点列表！")
        elif scene_type == "CinematicHero" or scene.get("heroImage") or scene.get("heroVideo"):
            hero_img = scene.get("heroImage")
            hero_vid = scene.get("heroVideo") or scene.get("videoPath")
            if not hero_img and not hero_vid:
                errors.append(f"分镜 [{scene_id}] 声明为 CinematicHero，但未配置 heroImage 或 heroVideo 素材路径！")
            if hero_img and not hero_img.startswith("http://") and not hero_img.startswith("https://"):
                full_img_path = os.path.join(PUBLIC_DIR, hero_img)
                if not os.path.exists(full_img_path):
                    errors.append(f"分镜 [{scene_id}] heroImage 原画素材不存在: {hero_img}")
            if hero_vid and not hero_vid.startswith("http://") and not hero_vid.startswith("https://"):
                full_vid_path = os.path.join(PUBLIC_DIR, hero_vid)
                if not os.path.exists(full_vid_path):
                    errors.append(f"分镜 [{scene_id}] heroVideo 视频素材不存在: {hero_vid}")

    # 检查总帧数一致性
    if total_frames != calculated_total_frames:
        errors.append(
            f"全局 totalDurationInFrames ({total_frames}) 与各分镜累计帧数 ({calculated_total_frames}) 不匹配！"
        )

    # 检查全局背景音乐 (BGM) 与转场音效 (SFX) 资产 (若开启则作为阻断性资产强校验)
    enable_bgm = data.get("enableBgm", True)
    bgm_path = data.get("bgmPath", "audio/bgm_cyber_ambient.wav")
    if enable_bgm and bgm_path:
        full_bgm = os.path.join(PUBLIC_DIR, bgm_path)
        if not os.path.exists(full_bgm):
            errors.append(f"全局 BGM 文件不存在: {bgm_path} (请运行 python scripts/generate_sfx_bgm.py 自动生成)")

    enable_sfx = data.get("enableSfx", True)
    if enable_sfx:
        for sfx_name in ["audio/sfx_transition.wav", "audio/sfx_pop.wav"]:
            full_sfx = os.path.join(PUBLIC_DIR, sfx_name)
            if not os.path.exists(full_sfx):
                errors.append(f"必选音效资产缺失: {sfx_name} (请运行 python scripts/generate_sfx_bgm.py 自动生成)")

    # 打印审查结果
    if warnings:
        print(f"\n{BColors.WARNING}⚠️  发现 {len(warnings)} 个警告项 (建议优化):{BColors.ENDC}")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"\n{BColors.FAIL}❌ 发现 {len(errors)} 个致命错误 (阻断渲染):{BColors.ENDC}")
        for err in errors:
            print(f"  ✖ {err}")
        print(f"\n{BColors.FAIL}💥 审查未通过！请修正上述错误后再启动 Remotion 渲染。{BColors.ENDC}\n")
        sys.exit(1)
    else:
        print(f"\n{BColors.OKGREEN}✅ [ALL CHECKS PASSED] 所有数据契约与资产审查 100% 通过！{BColors.ENDC}")
        print(f"{BColors.OKGREEN}🚀 可以安全启动 Remotion Studio 或执行 MP4 导出。{BColors.ENDC}\n")

def validate_script_file(script_path: str):
    """分镜脚本 Schema 契约与各类型视效组件规范性审查"""
    print(f"\n{BColors.HEADER}===================================================={BColors.ENDC}")
    print(f"{BColors.BOLD}🔍 [Quality Gate] 启动分镜脚本数据契约审查...{BColors.ENDC}")
    print(f"{BColors.HEADER}===================================================={BColors.ENDC}\n")

    errors = []
    warnings = []

    if not os.path.exists(script_path):
        print(f"{BColors.FAIL}[ERROR] 关键剧本缺失: 找不到 {script_path}{BColors.ENDC}")
        sys.exit(1)

    with open(script_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"{BColors.FAIL}[ERROR] {script_path} JSON 解析失败: {e}{BColors.ENDC}")
            sys.exit(1)

    project = data.get("project")
    if not project:
        errors.append("剧本根对象缺少必填字段: 'project'")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) == 0:
        errors.append("剧本 'scenes' 列表为空或未配置！")
        scenes = []

    print(f"📊 项目名称: {BColors.OKCYAN}{project or 'unknown'}{BColors.ENDC}")
    print(f"🎯 视觉主题: {data.get('theme', 'default')} | 分镜总数: {len(scenes)} 幕")
    print(f"🎙️ 配音引擎: {data.get('engine', 'unknown')} | 音色: {data.get('voice', 'default')}")
    print("-" * 52)

    for i, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{i+1}")
        scene_type = scene.get("type", "Default")
        text = scene.get("text", "").strip()

        if not text:
            errors.append(f"分镜 [{scene_id}] 缺少有效旁白文案 (text 为空)！")

        # 视效组件契约审查
        if scene_type == "TweetEmbed":
            tweet = scene.get("tweet")
            if not isinstance(tweet, dict):
                errors.append(f"分镜 [{scene_id}] 声明为 TweetEmbed，但 tweet 不是合法字典对象！")
            else:
                if not (tweet.get("authorName") or tweet.get("author")):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'authorName'！")
                if not (tweet.get("authorHandle") or tweet.get("handle")):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'authorHandle'！")
                if not tweet.get("content"):
                    errors.append(f"分镜 [{scene_id}] tweet 缺失核心字段 'content'！")
        elif scene_type == "BinaryBento":
            bento = scene.get("binaryBento")
            if not isinstance(bento, dict):
                errors.append(f"分镜 [{scene_id}] 声明为 BinaryBento，但 binaryBento 不是合法字典对象！")
            else:
                left_card = bento.get("leftCard")
                right_card = bento.get("rightCard")
                if not isinstance(left_card, dict) or not isinstance(right_card, dict):
                    errors.append(f"分镜 [{scene_id}] binaryBento 必须同时包含 leftCard 与 rightCard 对象！")
                else:
                    if not left_card.get("title") or not right_card.get("title"):
                        errors.append(f"分镜 [{scene_id}] binaryBento 卡片缺少 title 字段！")
        elif scene_type == "MinimalHeadline":
            title = scene.get("title") or text
            if not title:
                errors.append(f"分镜 [{scene_id}] MinimalHeadline 缺少 title 或 text！")
        elif scene_type in ["MetricComparison", "MetricChart"]:
            metrics = scene.get("metrics", [])
            if not metrics:
                errors.append(f"分镜 [{scene_id}] 声明类型为 {scene_type}，但未提供 metrics 数据数组！")
        elif scene_type in ["ArchitectureTopology", "TopologyFlow"]:
            nodes = scene.get("topologyNodes", [])
            if not nodes:
                errors.append(f"分镜 [{scene_id}] 声明类型为 {scene_type}，但未提供 topologyNodes 节点列表！")

    # 打印审查结果
    if warnings:
        print(f"\n{BColors.WARNING}⚠️  发现 {len(warnings)} 个警告项 (建议优化):{BColors.ENDC}")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"\n{BColors.FAIL}❌ 发现 {len(errors)} 个致命错误 (阻断生成):{BColors.ENDC}")
        for err in errors:
            print(f"  ✖ {err}")
        print(f"\n{BColors.FAIL}💥 剧本契约审查未通过！{BColors.ENDC}\n")
        sys.exit(1)
    else:
        print(f"\n{BColors.OKGREEN}✅ [ALL CHECKS PASSED] 分镜脚本契约审查 100% 通过！{BColors.ENDC}")
        print(f"{BColors.OKGREEN}🚀 剧本契约完备，可安全进入音频合成与 ASR 声学对齐。{BColors.ENDC}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频工程数据契约与静态资产审查 (Quality Gate)")
    parser.add_argument("--timeline", type=str, default=None, help="指定待审查的 timeline.json 路径")
    parser.add_argument("--project", type=str, default=None, help="项目名称 (自动寻找 public/projects/{project}/timeline.json)")
    parser.add_argument("--script", type=str, default=None, help="指定待审查的分镜脚本 JSON 路径 (content/scripts/xxx.json)")
    args = parser.parse_args()

    if args.script:
        validate_script_file(script_path=args.script)
    else:
        target_timeline = args.timeline
        if not target_timeline and args.project:
            target_timeline = os.path.join(PUBLIC_DIR, "projects", args.project, "timeline.json")

        validate(timeline_path=target_timeline)


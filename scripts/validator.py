#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/validator.py
视频工程数据契约与资产完整性自动化审查工具 (Quality Gate Validator)
"""

import os
import sys
import json
import wave

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMELINE_PATH = os.path.join(PROJECT_ROOT, "public", "timeline.json")
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
    """计算 WAV 文件真实时长"""
    try:
        with wave.open(audio_full_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        # 非 WAV 或特殊格式使用预估
        return None

def validate():
    print(f"\n{BColors.HEADER}===================================================={BColors.ENDC}")
    print(f"{BColors.BOLD}🔍 [Quality Gate] 启动视频数据契约与静态资产审查...{BColors.ENDC}")
    print(f"{BColors.HEADER}===================================================={BColors.ENDC}\n")

    errors = []
    warnings = []

    # 1. 检查 timeline.json 存在性
    if not os.path.exists(TIMELINE_PATH):
        print(f"{BColors.FAIL}[ERROR] 关键契约缺失: 找不到 {TIMELINE_PATH}{BColors.ENDC}")
        print("请先运行 scripts/pipeline.py 或 scripts/sensevoice_aligner.py 生成时间轴！")
        sys.exit(1)

    with open(TIMELINE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"{BColors.FAIL}[ERROR] timeline.json JSON 解析失败: {e}{BColors.ENDC}")
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

        # 检查时间轴连续性
        if start_frame != current_expected_frame:
            errors.append(
                f"分镜 [{scene_id}] 起始帧不连续! 预期: {current_expected_frame}, 实际: {start_frame}"
            )

        current_expected_frame += duration
        calculated_total_frames += duration

        # 检查音频文件存在性
        if audio_rel_path:
            audio_full_path = os.path.join(PUBLIC_DIR, audio_rel_path)
            if not os.path.exists(audio_full_path):
                errors.append(f"分镜 [{scene_id}] 音频文件不存在: {audio_rel_path}")
            else:
                # 校验音频物理时长与 Remotion 帧数对齐精度
                real_sec = get_audio_duration_seconds(audio_full_path)
                if real_sec is not None:
                    ideal_frames = int(round(real_sec * fps))
                    diff = abs(ideal_frames - duration)
                    if diff > 3: # 允许 3 帧以内的舍入缓冲
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

    # 检查总帧数一致性
    if total_frames != calculated_total_frames:
        errors.append(
            f"全局 totalDurationInFrames ({total_frames}) 与各分镜累计帧数 ({calculated_total_frames}) 不匹配！"
        )

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

if __name__ == "__main__":
    validate()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/sensevoice_aligner.py
阿里 SenseVoice 毫秒打点与情绪提取中枢 (CPU 极速版)
"""

import os
import sys
import json
import time
import wave
import argparse

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
AUDIO_DIR = os.path.join(PUBLIC_DIR, "audio")
DEFAULT_TIMELINE = os.path.join(PUBLIC_DIR, "timeline.json")

def get_audio_duration_seconds(audio_full_path: str) -> float:
    try:
        with wave.open(audio_full_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        return 0.0

def load_sensevoice_model():
    print(">>> 正在加载阿里 SenseVoice-Small 模型 (纯 CPU 极速推理)...")
    from funasr import AutoModel
    from funasr.utils.postprocess_utils import rich_transcription_postprocess

    t0 = time.time()
    model = AutoModel(
        model="iic/SenseVoiceSmall",
        vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        vad_kwargs={"max_single_segment_time": 30000},
        device="cpu",
        hub="ms",
        disable_update=True
    )
    print(f"SenseVoice 模型就绪，耗时: {time.time() - t0:.2f}秒")
    return model, rich_transcription_postprocess

def align_audio_files(audio_files: list, fps: int = 30, project_name: str = "demo_project"):
    model, postprocess_fn = load_sensevoice_model()

    scenes = []
    current_start_frame = 0

    print(f"\n>>> 正在批量对齐 {len(audio_files)} 段分镜音频...")

    for i, audio_file in enumerate(audio_files):
        audio_name = os.path.basename(audio_file)
        rel_audio_path = os.path.join("audio", audio_name).replace("\\", "/")
        scene_id = os.path.splitext(audio_name)[0]

        duration_sec = get_audio_duration_seconds(audio_file)
        duration_frames = int(round(duration_sec * fps))

        # ASR 推理
        res = model.generate(
            input=audio_file,
            cache={},
            language="auto",
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
        )

        raw_text = ""
        clean_text = ""
        emotion = "<|NEUTRAL|>"

        if res and len(res) > 0:
            raw_text = res[0].get("text", "")
            clean_text = postprocess_fn(raw_text)

            # 提取情绪标签
            for tag in ["<|HAPPY|>", "<|SAD|>", "<|ANGRY|>", "<|NEUTRAL|>"]:
                if tag in raw_text:
                    emotion = tag
                    break

        # 简单字级切片估算（若需要更细粒度字级对齐，配合时间戳切片）
        # 建立 scene 结构
        scene_data = {
            "id": scene_id,
            "type": "ExplainerWhiteboard" if i % 2 == 0 else "TerminalCodeDemo",
            "startFrame": current_start_frame,
            "durationInFrames": duration_frames,
            "audioPath": rel_audio_path,
            "text": clean_text,
            "rawText": raw_text,
            "emotion": emotion,
            "words": []
        }

        # 简单的逐字/逐词帧映射
        words = clean_text.split() if " " in clean_text else list(clean_text)
        if words and duration_frames > 0:
            frames_per_word = max(1, duration_frames // len(words))
            for w_idx, word in enumerate(words):
                w_start_frame = current_start_frame + w_idx * frames_per_word
                w_end_frame = min(current_start_frame + duration_frames, w_start_frame + frames_per_word)
                scene_data["words"].append({
                    "text": word,
                    "startFrame": w_start_frame,
                    "endFrame": w_end_frame,
                    "startMs": int((w_start_frame / fps) * 1000),
                    "endMs": int((w_end_frame / fps) * 1000)
                })

        scenes.append(scene_data)
        print(f"  [✓] {scene_id}: 时长 {duration_sec:.2f}s -> {duration_frames}帧, 情绪: {emotion}")
        print(f"      文本: {clean_text}")

        current_start_frame += duration_frames

    timeline_data = {
        "project": project_name,
        "fps": fps,
        "totalDurationInFrames": current_start_frame,
        "scenes": scenes
    }

    with open(DEFAULT_TIMELINE, "w", encoding="utf-8") as f:
        json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    print(f"\n>>> 成功生成标准时间轴契约文件: {DEFAULT_TIMELINE}")
    print(f"    总分镜: {len(scenes)} | 总帧数: {current_start_frame} ({current_start_frame / fps:.2f}秒)\n")

def main():
    parser = argparse.ArgumentParser(description="SenseVoice 毫秒打点与时间轴契约生成")
    parser.add_argument("--audio_dir", type=str, default=AUDIO_DIR, help="音频目录")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--project", type=str, default="auto_video_project", help="项目名称")
    args = parser.parse_args()

    if not os.path.exists(args.audio_dir):
        os.makedirs(args.audio_dir, exist_ok=True)

    audio_files = [
        os.path.join(args.audio_dir, f)
        for f in sorted(os.listdir(args.audio_dir))
        if f.lower().endswith((".wav", ".mp3"))
    ]

    if not audio_files:
        print(f"[!] {args.audio_dir} 目录下未找到任何音频文件。")
        print("请先放置或生成分镜音频 (如 scene_01.wav, scene_02.wav)！")
        sys.exit(0)

    align_audio_files(audio_files, fps=args.fps, project_name=args.project)

if __name__ == "__main__":
    main()

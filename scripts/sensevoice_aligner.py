#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/sensevoice_aligner.py
高精度声学物理时间戳对齐与时间轴契约生成中枢 (Paraformer 物理打点 + SenseVoice 情绪回退)
"""

import os
import sys
import json
import time
import wave
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
AUDIO_DIR = os.path.join(PUBLIC_DIR, "audio")
DEFAULT_TIMELINE = os.path.join(PUBLIC_DIR, "timeline.json")

def get_audio_duration_seconds(audio_full_path: str) -> float:
    try:
        import soundfile as sf
        info = sf.info(audio_full_path)
        return info.duration
    except Exception:
        try:
            with wave.open(audio_full_path, 'rb') as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            return 0.0

def load_aligner_model(engine: str = "auto"):
    """
    加载声学打点与识别模型。
    默认首选 Paraformer (支持高精度字符级物理时间戳)，
    若加载失败或显式指定则回退至 SenseVoice-Small (支持情绪标签与字数比例拟合)。
    """
    from funasr import AutoModel
    postprocess_fn = None

    if engine in ("auto", "paraformer"):
        try:
            print(">>> 正在加载阿里 Paraformer 高精度物理时间戳对齐模型 (纯 CPU 极速推理)...")
            t0 = time.time()
            model = AutoModel(
                model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                vad_kwargs={"max_single_segment_time": 30000},
                device="cpu",
                hub="ms",
                disable_update=True
            )
            print(f"Paraformer 模型就绪，耗时: {time.time() - t0:.2f}秒 (声学物理打点模式开启)")
            return model, "paraformer", None
        except Exception as e:
            print(f"⚠️ Paraformer 加载失败 ({e})，正在自动回退至 SenseVoice-Small...")

    print(">>> 正在加载阿里 SenseVoice-Small 模型 (纯 CPU 极速推理)...")
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
    return model, "sensevoice", rich_transcription_postprocess

def align_audio_files(
    audio_files: list,
    fps: int = 30,
    project_name: str = "demo_project",
    script_path: str = None,
    engine: str = "auto",
    timeline_path: str = DEFAULT_TIMELINE
):
    model, engine_used, postprocess_fn = load_aligner_model(engine)

    script_meta_map = {}
    if script_path and os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                s_data = json.load(f)
                for sc in s_data.get("scenes", []):
                    if "id" in sc:
                        script_meta_map[sc["id"]] = sc
        except Exception as e:
            print(f"⚠️ 读取分镜元数据异常 ({e})")

    scenes = []
    current_start_frame = 0

    print(f"\n>>> 正在批量对齐 {len(audio_files)} 段分镜音频 (引擎: {engine_used})...")

    for i, audio_file in enumerate(audio_files):
        audio_name = os.path.basename(audio_file)
        rel_audio_path = os.path.join("audio", audio_name).replace("\\", "/")
        scene_id = os.path.splitext(audio_name)[0]

        duration_sec = get_audio_duration_seconds(audio_file)
        duration_frames = max(1, int(round(duration_sec * fps)))

        raw_text = ""
        clean_text = ""
        emotion = "<|NEUTRAL|>"
        tokens = []
        timestamps = []

        try:
            if engine_used == "paraformer":
                res = model.generate(input=audio_file, batch_size_s=300)
                if res and len(res) > 0:
                    raw_text = res[0].get("text", "")
                    clean_text = raw_text.replace(" ", "")
                    tokens = raw_text.split()
                    timestamps = res[0].get("timestamp", [])
            else:
                res = model.generate(
                    input=audio_file,
                    cache={},
                    language="auto",
                    use_itn=True,
                    batch_size_s=60,
                    merge_vad=True,
                    merge_length_s=15,
                )
                if res and len(res) > 0:
                    raw_text = res[0].get("text", "")
                    if postprocess_fn:
                        clean_text = postprocess_fn(raw_text)
                    else:
                        clean_text = raw_text
                    for tag in ["<|HAPPY|>", "<|SAD|>", "<|ANGRY|>", "<|NEUTRAL|>"]:
                        if tag in raw_text:
                            emotion = tag
                            break
        except Exception as e:
            print(f"⚠️ ASR 推理异常 ({audio_file}): {e}")

        # 优先使用分镜原稿文字，确保中英文术语与专有名词 100% 准确
        original_text = ""
        if script_meta_map and scene_id in script_meta_map:
            original_text = script_meta_map[scene_id].get("text", "")
        display_text = original_text if original_text.strip() else clean_text

        scene_data = {
            "id": scene_id,
            "type": "ExplainerWhiteboard" if i % 2 == 0 else "TerminalCodeDemo",
            "startFrame": current_start_frame,
            "durationInFrames": duration_frames,
            "audioPath": rel_audio_path,
            "text": display_text,
            "rawText": raw_text,
            "emotion": emotion,
            "words": []
        }

        # 视觉元数据无缝继承
        if script_meta_map and scene_id in script_meta_map:
            meta = script_meta_map[scene_id]
            for field in ["title", "badge", "subtitle", "cards", "bulletPoints", "codeSnippet", "codeLang", "type"]:
                if field in meta:
                    scene_data[field] = meta[field]

        # 智能短句切分 (按标点符号分句)
        chunks = [c.strip() for c in re.split(r'[,，。！？、；;!\?\n]+', display_text) if c.strip()]
        if not chunks:
            chunks = [display_text] if display_text.strip() else ["..."]

        has_physical_timestamps = bool(timestamps and len(timestamps) > 0 and len(tokens) > 0)

        if has_physical_timestamps:
            # === 声学物理时间戳映射模式 ===
            token_idx = 0
            prev_end_ms = 0

            for c_idx, chunk in enumerate(chunks):
                chunk_clean = re.sub(r'[^\w]', '', chunk)
                chunk_clean_len = max(1, len(chunk_clean))

                start_idx = token_idx
                acc_chars = ""
                while token_idx < len(tokens) and len(acc_chars) < chunk_clean_len:
                    acc_chars += tokens[token_idx]
                    token_idx += 1

                if start_idx < len(timestamps) and token_idx <= len(timestamps) and token_idx > start_idx:
                    start_ms = timestamps[start_idx][0]
                    end_ms = timestamps[token_idx - 1][1]
                elif start_idx < len(timestamps):
                    start_ms = timestamps[start_idx][0]
                    end_ms = timestamps[-1][1]
                else:
                    # 音频末尾超出部分按时长平滑延续
                    start_ms = prev_end_ms
                    end_ms = int(duration_sec * 1000)

                # 单调递增与边界约束防越界
                start_ms = max(prev_end_ms, start_ms)
                end_ms = max(start_ms + 100, end_ms)
                end_ms = min(int(duration_sec * 1000), end_ms)
                prev_end_ms = end_ms

                rel_start_frame = max(0, min(duration_frames - 1, int(round((start_ms / 1000.0) * fps))))
                rel_end_frame = max(rel_start_frame + 1, min(duration_frames, int(round((end_ms / 1000.0) * fps))))

                scene_data["words"].append({
                    "text": chunk,
                    "startFrame": rel_start_frame,
                    "endFrame": rel_end_frame,
                    "globalStartFrame": current_start_frame + rel_start_frame,
                    "globalEndFrame": current_start_frame + rel_end_frame,
                    "startMs": start_ms,
                    "endMs": end_ms
                })
        else:
            # === 字符加权拟合回退模式 ===
            total_chars = sum(max(1, len(c)) for c in chunks)
            allocated_frame = 0

            for c_idx, chunk in enumerate(chunks):
                if c_idx == len(chunks) - 1:
                    chunk_frames = max(1, duration_frames - allocated_frame)
                else:
                    chunk_ratio = len(chunk) / float(total_chars)
                    chunk_frames = max(15, int(round(duration_frames * chunk_ratio)))
                    if allocated_frame + chunk_frames >= duration_frames:
                        chunk_frames = max(1, duration_frames - allocated_frame - (len(chunks) - 1 - c_idx))

                rel_start_frame = allocated_frame
                rel_end_frame = min(duration_frames, rel_start_frame + chunk_frames)
                allocated_frame += chunk_frames

                scene_data["words"].append({
                    "text": chunk,
                    "startFrame": rel_start_frame,
                    "endFrame": rel_end_frame,
                    "globalStartFrame": current_start_frame + rel_start_frame,
                    "globalEndFrame": current_start_frame + rel_end_frame,
                    "startMs": int((rel_start_frame / fps) * 1000),
                    "endMs": int((rel_end_frame / fps) * 1000)
                })

        scenes.append(scene_data)
        align_mode_str = "物理时间戳" if has_physical_timestamps else "字数比例拟合"
        print(f"  [✓] {scene_id}: 时长 {duration_sec:.2f}s -> {duration_frames}帧 ({align_mode_str})")
        print(f"      短句数量: {len(scene_data['words'])} | 文本: {display_text[:40]}...")

        current_start_frame += duration_frames

    timeline_data = {
        "project": project_name,
        "fps": fps,
        "totalDurationInFrames": current_start_frame,
        "scenes": scenes
    }

    out_file = timeline_path or DEFAULT_TIMELINE
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    print(f"\n>>> 成功生成标准时间轴契约文件: {out_file}")
    print(f"    总分镜: {len(scenes)} | 总帧数: {current_start_frame} ({current_start_frame / fps:.2f}秒)\n")

def main():
    parser = argparse.ArgumentParser(description="声学物理打点与时间轴契约生成")
    parser.add_argument("--audio_dir", type=str, default=AUDIO_DIR, help="音频目录")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--project", type=str, default="auto_video_project", help="项目名称")
    parser.add_argument("--script", type=str, default=None, help="分镜脚本路径以继承元数据")
    parser.add_argument("--engine", type=str, choices=["auto", "paraformer", "sensevoice"], default="auto", help="对齐引擎")
    parser.add_argument("--timeline", type=str, default=DEFAULT_TIMELINE, help="输出时间轴文件路径")
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

    align_audio_files(
        audio_files,
        fps=args.fps,
        project_name=args.project,
        script_path=args.script,
        engine=args.engine,
        timeline_path=args.timeline
    )

if __name__ == "__main__":
    main()

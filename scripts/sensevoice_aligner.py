#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/sensevoice_aligner.py
高精度声学物理时间戳对齐与时间轴契约生成中枢
- 首选阿里 Paraformer 提取字符/词级物理时间戳 (毫秒级真实现实发音打点)
- 自动/指定回退阿里 SenseVoice-Small (提取文本与情绪标签)
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

def natural_sort_key(s: str):
    """自然数字排序 (避免 scene_1, scene_10, scene_2 乱序)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_audio_duration_seconds(audio_full_path: str) -> float:
    """高精度多后端音频时长探测 (soundfile -> torchaudio -> wave)"""
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

    print(f"⚠️ [WARN] 无法计算音频物理时长: {audio_full_path}")
    return 0.0

def load_aligner_model(engine: str = "auto", device: str = "cpu"):
    """
    加载声学打点与识别模型。
    engine:
      - 'auto': 优先 Paraformer，失败时平滑回退至 SenseVoice-Small
      - 'paraformer': 强制要求 Paraformer，失败则直接报错
      - 'sensevoice': 强制使用 SenseVoice-Small
    """
    from funasr import AutoModel
    postprocess_fn = None

    if engine in ("auto", "paraformer"):
        try:
            print(f">>> 正在加载阿里 Paraformer 高精度物理时间戳对齐模型 (设备: {device})...")
            t0 = time.time()
            model = AutoModel(
                model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                vad_kwargs={"max_single_segment_time": 30000},
                device=device,
                hub="ms",
                disable_update=True
            )
            print(f"Paraformer 模型就绪，耗时: {time.time() - t0:.2f}秒 (声学物理打点模式开启)")
            return model, "paraformer", None
        except Exception as e:
            if engine == "paraformer":
                raise RuntimeError(f"Paraformer 模型加载失败: {e}")
            print(f"⚠️ Paraformer 加载失败 ({e})，正在自动回退至 SenseVoice-Small...")

    print(f">>> 正在加载阿里 SenseVoice-Small 模型 (设备: {device})...")
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    t0 = time.time()
    model = AutoModel(
        model="iic/SenseVoiceSmall",
        vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        vad_kwargs={"max_single_segment_time": 30000},
        device=device,
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
    device: str = "cpu",
    timeline_path: str = DEFAULT_TIMELINE
):
    model, engine_used, postprocess_fn = load_aligner_model(engine=engine, device=device)

    script_meta_map = {}
    global_theme = "obsidian-minimal"
    script_root_data = {}
    if script_path and os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                s_data = json.load(f)
                script_root_data = s_data
                global_theme = s_data.get("theme", "obsidian-minimal")
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
        rel_audio_path = os.path.relpath(audio_file, PUBLIC_DIR).replace("\\", "/")
        scene_id = os.path.splitext(audio_name)[0]

        duration_sec = get_audio_duration_seconds(audio_file)
        if duration_sec <= 0.0:
            duration_sec = 1.0  # 兜底保护，防除零
        duration_frames = max(1, int(round(duration_sec * fps)))
        total_duration_ms = int(duration_sec * 1000)

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
            for field in [
                "title", "badge", "subtitle", "cards", "bulletPoints",
                "codeSnippet", "codeLang", "codeTitle", "type",
                "topologyNodes", "topologyLinks", "metrics", "theme", "voiceVolume",
                "heroImage", "heroVideo", "videoPath", "cameraMotion", "highlights", "pill", "sceneIndex", "totalScenes",
                "tag", "dateText", "date", "desc",
                "tweet", "binaryBento", "inverted", "category", "blocksActive", "blocksTotal", "highlightWords"
            ]:
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
            num_chunks = len(chunks)

            for c_idx, chunk in enumerate(chunks):
                is_last_chunk = (c_idx == num_chunks - 1)
                chunk_clean = re.sub(r'[^\w]', '', chunk)
                chunk_clean_len = max(1, len(chunk_clean))

                start_idx = token_idx
                acc_chars = ""

                if is_last_chunk:
                    # 最后一个分句吞下所有剩余 token，避免尾音未标注提前截断
                    token_idx = len(tokens)
                else:
                    while token_idx < len(tokens) and len(acc_chars) < chunk_clean_len:
                        acc_chars += tokens[token_idx]
                        token_idx += 1

                # 提取声学物理起止毫秒
                if start_idx < len(timestamps) and token_idx <= len(timestamps) and token_idx > start_idx:
                    start_ms = timestamps[start_idx][0]
                    end_ms = timestamps[token_idx - 1][1]
                elif start_idx < len(timestamps):
                    start_ms = timestamps[start_idx][0]
                    end_ms = timestamps[-1][1]
                else:
                    # token 超出时的平滑分配，按剩余分句比例平摊剩余时长，杜绝 0ms 压扁 bug
                    remaining_chunks = max(1, num_chunks - c_idx)
                    remaining_time_ms = max(100 * remaining_chunks, total_duration_ms - prev_end_ms)
                    slot_ms = remaining_time_ms // remaining_chunks
                    start_ms = prev_end_ms
                    end_ms = min(total_duration_ms, start_ms + slot_ms)

                # 严格双向边界约束与单调递增保障
                start_ms = min(max(0, start_ms), total_duration_ms)
                start_ms = max(prev_end_ms, start_ms)
                start_ms = min(start_ms, max(0, total_duration_ms - 100))
                end_ms = min(total_duration_ms, max(start_ms + 100, end_ms))
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
                    chunk_frames = max(1, int(round(duration_frames * chunk_ratio)))
                    if allocated_frame + chunk_frames >= duration_frames:
                        chunk_frames = max(1, duration_frames - allocated_frame - (len(chunks) - 1 - c_idx))

                rel_start_frame = allocated_frame
                rel_end_frame = min(duration_frames, max(rel_start_frame + 1, rel_start_frame + chunk_frames))
                allocated_frame = rel_end_frame

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
        "theme": global_theme,
        "fps": fps,
        "totalDurationInFrames": current_start_frame,
        "scenes": scenes
    }
    for opt_key in ["bgmVolume", "bgmDuckRatio", "voiceVolume", "enableBgm", "enableSfx", "bgmPath"]:
        if opt_key in script_root_data:
            timeline_data[opt_key] = script_root_data[opt_key]

    out_file = timeline_path or DEFAULT_TIMELINE
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    # 若输出至项目隔离路径，同步镜像更新一份至 public/timeline.json，以便 Remotion Studio 即时预览
    if os.path.abspath(out_file) != os.path.abspath(DEFAULT_TIMELINE):
        try:
            with open(DEFAULT_TIMELINE, "w", encoding="utf-8") as f:
                json.dump(timeline_data, f, ensure_ascii=False, indent=2)
            print(f"    (已同步镜像至全局活动时间轴: {DEFAULT_TIMELINE})")
        except Exception as e:
            print(f"⚠️ [WARN] 镜像同步至 {DEFAULT_TIMELINE} 失败: {e}")

    print(f"\n>>> 成功生成标准时间轴契约文件: {out_file}")
    print(f"    总分镜: {len(scenes)} | 总帧数: {current_start_frame} ({current_start_frame / fps:.2f}秒)\n")

def main():
    parser = argparse.ArgumentParser(description="声学物理打点与时间轴契约生成")
    parser.add_argument("--audio_dir", type=str, default=AUDIO_DIR, help="音频目录")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--project", type=str, default=None, help="项目名称")
    parser.add_argument("--script", type=str, default=None, help="分镜脚本路径以继承元数据")
    parser.add_argument("--engine", type=str, choices=["auto", "paraformer", "sensevoice"], default="auto", help="对齐引擎")
    parser.add_argument("--device", type=str, default="cpu", help="推理设备 (cpu/cuda)")
    parser.add_argument("--timeline", type=str, default=DEFAULT_TIMELINE, help="输出时间轴文件路径")
    args = parser.parse_args()

    # 多项目隔离自动目录适配 (采用 normpath 规避 Windows 反斜杠/相对路径匹配缺陷)
    target_audio_dir = args.audio_dir
    target_timeline = args.timeline

    is_default_audio = os.path.normpath(args.audio_dir) == os.path.normpath(AUDIO_DIR)
    is_default_timeline = os.path.normpath(args.timeline) == os.path.normpath(DEFAULT_TIMELINE)

    if args.project:
        if is_default_audio:
            target_audio_dir = os.path.join(PUBLIC_DIR, "projects", args.project, "audio")
        if is_default_timeline:
            target_timeline = os.path.join(PUBLIC_DIR, "projects", args.project, "timeline.json")

    if not os.path.exists(target_audio_dir):
        os.makedirs(target_audio_dir, exist_ok=True)

    SUPPORTED_EXTS = (".wav", ".mp3", ".flac", ".m4a", ".aac")
    audio_files = [
        os.path.join(target_audio_dir, f)
        for f in sorted(os.listdir(target_audio_dir), key=natural_sort_key)
        if f.lower().endswith(SUPPORTED_EXTS)
    ]

    if not audio_files:
        print(f"[!] {target_audio_dir} 目录下未找到任何音频文件。")
        print("请先放置或生成分镜音频 (如 scene_01.wav, scene_02.wav)！")
        sys.exit(1)

    align_audio_files(
        audio_files,
        fps=args.fps,
        project_name=args.project,
        script_path=args.script,
        engine=args.engine,
        device=args.device,
        timeline_path=target_timeline
    )

if __name__ == "__main__":
    main()

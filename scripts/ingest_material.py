#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/ingest_material.py
基于 yt-dlp 与 ffmpeg 的流媒体素材/B-Roll/干声音频切片采集中枢
支持精准时间切片下载（--section）、CFR 30fps 标准化转码、
干声音频提取（--audio-only）及原文字幕/元数据抓取（--subtitles / --extract-info）。
"""

import os
import sys
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 优先探测 LiveClip 专用 Python（内置完整 yt-dlp 与音视频编解码环境），否则回退至当前解释器
LIVECLIP_PYTHON = r"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe"
PYTHON_EXE = LIVECLIP_PYTHON if os.path.exists(LIVECLIP_PYTHON) else sys.executable


def parse_time_to_seconds(t_str: str) -> float:
    """
    将时间字符串解析为浮点秒数。
    支持格式：
      - 00:01:15 (hh:mm:ss)
      - 01:15 (mm:ss)
      - 75 (纯秒数整数)
      - 10.5 / 00:00:10.5 (含小数位)
    若格式非法或数值为负，抛出 ValueError。
    """
    t_str = t_str.strip()
    if not t_str:
        raise ValueError("Empty time string is not allowed")

    if ":" in t_str:
        parts = t_str.split(":")
        if len(parts) == 2:
            m = float(parts[0])
            s = float(parts[1])
            if m < 0 or s < 0:
                raise ValueError(f"Negative time component not allowed: {t_str}")
            return m * 60.0 + s
        elif len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            if h < 0 or m < 0 or s < 0:
                raise ValueError(f"Negative time component not allowed: {t_str}")
            return h * 3600.0 + m * 60.0 + s
        else:
            raise ValueError(f"Invalid time format (too many colons): {t_str}")
    else:
        val = float(t_str)
        if val < 0:
            raise ValueError(f"Negative time value not allowed: {t_str}")
        return val


def parse_section(section_str: str) -> Tuple[float, float]:
    """
    解析时间切片区间字符串，返回 (start_seconds, end_seconds)。
    支持格式：
      - "00:01:15-00:01:30"
      - "01:15-01:30"
      - "75-90"
      - "*00:01:00-00:01:10" (前导 '*' 兼容 yt-dlp 语法)
    若起始时间大于等于结束时间，或格式不合法，抛出 ValueError。
    """
    if not section_str:
        raise ValueError("Section string cannot be empty")

    sec = section_str.strip().lstrip("*")
    if "-" not in sec:
        raise ValueError(
            f"Invalid section format: {section_str}. Expected 'start-end' (e.g. 00:01:15-00:01:30)"
        )

    parts = sec.split("-")
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(
            f"Invalid section format: {section_str}. Expected exactly two non-empty components separated by '-'"
        )

    start_sec = parse_time_to_seconds(parts[0])
    end_sec = parse_time_to_seconds(parts[1])

    if start_sec >= end_sec:
        raise ValueError(
            f"Start time ({start_sec}s) must be strictly less than end time ({end_sec}s)"
        )

    return (start_sec, end_sec)


def normalize_name(raw_name: str) -> str:
    """
    清洗素材名称，转换为全小写、下划线连接的规范文件名。
    保留英文字母、数字、中文字符。
    例如: "OpenAI Day 6 Reset!!" -> "openai_day_6_reset"
    """
    if not raw_name:
        return "material"

    # 保留字母、数字、中文、空格与破折号
    cleaned = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', raw_name).strip()
    # 空格与连字符替换为下划线
    cleaned = re.sub(r'[-\s]+', '_', cleaned).lower()
    # 消除连续下划线并去除首尾下划线
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')

    return cleaned or "material"


def build_ytdlp_command(
    url: str,
    out_path: str,
    section: Optional[str] = None,
    audio_only: bool = False,
    subtitles: bool = False,
    extract_info: bool = False,
) -> List[str]:
    """
    拼装合法 yt-dlp 命令行参数列表。
    """
    cmd = [PYTHON_EXE, "-m", "yt_dlp", url]

    if extract_info:
        cmd.extend(["--dump-json", "--no-download"])
        return cmd

    if audio_only:
        if section:
            start_sec, end_sec = parse_section(section)
            cmd.extend([
                "--download-sections",
                f"*{start_sec:.1f}-{end_sec:.1f}",
                "--force-keyframes-at-cuts",
            ])
        cmd.extend(["-x", "--audio-format", "wav", "-o", out_path])
        return cmd

    if section:
        start_sec, end_sec = parse_section(section)
        cmd.extend([
            "--download-sections",
            f"*{start_sec:.1f}-{end_sec:.1f}",
            "--force-keyframes-at-cuts",
        ])

    if subtitles:
        cmd.extend(["--write-sub", "--sub-lang", "zh-Hans,zh,en"])

    cmd.extend([
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o",
        out_path,
    ])
    return cmd


def standardize_video(input_path: str, output_path: str, fps: int = 30) -> str:
    """
    调用 ffmpeg 滤镜转码为 CFR 30fps、CRF 18、AAC 192k 的高品质恒定帧率 MP4。
    锁定恒定帧率（fps=30），杜绝 VFR 导致音画不同步。
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"fps={fps},scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]

    ret = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if ret.returncode != 0:
        raise RuntimeError(f"FFmpeg 转码失败 (code {ret.returncode}): {ret.stderr}")

    return output_path


def ingest_asset(
    url: str,
    project: str = "common",
    section: Optional[str] = None,
    audio_only: bool = False,
    subtitles: bool = False,
    extract_info: bool = False,
    name: Optional[str] = None,
    fps: int = 30,
) -> Dict[str, Any]:
    """
    主执行函数：根据配置采集流媒体素材、提取音频或抓取字幕与元数据。
    返回包含采集状态及目标文件绝对路径的结果字典。
    """
    project_slug = project if project and project != "common" else "common"
    clean_name = normalize_name(name) if name else None
    cached_info = None

    # 若未指定 name 且需要执行下载/提取，可尝试快速拉取元数据获取 title
    if not clean_name:
        try:
            info_cmd = [PYTHON_EXE, "-m", "yt_dlp", url, "--dump-json", "--no-download"]
            probe_ret = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
            cached_info = json.loads(probe_ret.stdout)
            clean_name = normalize_name(cached_info.get("title", "material"))
        except Exception:
            clean_name = "material"

    # 路径规则配置
    if project_slug != "common":
        footage_dir = PROJECT_ROOT / "public" / "projects" / project_slug / "footage"
        audio_dir = PROJECT_ROOT / "public" / "projects" / project_slug / "audio"
    else:
        footage_dir = PROJECT_ROOT / "public" / "footage" / "common"
        audio_dir = PROJECT_ROOT / "public" / "projects" / "common" / "audio"

    metadata_dir = PROJECT_ROOT / "inputs" / "transcripts"
    metadata_path = metadata_dir / f"{project_slug}_{clean_name}_metadata.json"

    # 1. 仅提取元数据
    if extract_info:
        metadata_dir.mkdir(parents=True, exist_ok=True)
        if cached_info is not None:
            info_json = cached_info
        else:
            cmd = build_ytdlp_command(url=url, out_path="", extract_info=True)
            ret = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info_json = json.loads(ret.stdout)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(info_json, f, ensure_ascii=False, indent=2)
        return {
            "status": "success",
            "type": "metadata",
            "project": project_slug,
            "name": clean_name,
            "metadata_path": str(metadata_path),
            "info": info_json,
        }

    # 2. 纯音频干声提取
    if audio_only:
        audio_dir.mkdir(parents=True, exist_ok=True)
        final_audio_path = audio_dir / f"{clean_name}.wav"
        cmd = build_ytdlp_command(
            url=url,
            out_path=str(final_audio_path),
            section=section,
            audio_only=True,
        )
        ret = subprocess.run(cmd, capture_output=True, text=True)
        if ret.returncode != 0:
            raise RuntimeError(f"yt-dlp 音频提取失败: {ret.stderr}")
        return {
            "status": "success",
            "type": "audio",
            "project": project_slug,
            "name": clean_name,
            "audio_path": str(final_audio_path),
        }

    # 3. 视频切片下载与标准化 CFR 30fps 转码
    footage_dir.mkdir(parents=True, exist_ok=True)
    final_video_path = footage_dir / f"{clean_name}.mp4"
    temp_raw_path = footage_dir / f"raw_{clean_name}.mp4"

    cmd = build_ytdlp_command(
        url=url,
        out_path=str(temp_raw_path),
        section=section,
        audio_only=False,
        subtitles=subtitles,
    )
    ret = subprocess.run(cmd, capture_output=True, text=True)
    if ret.returncode != 0:
        raise RuntimeError(f"yt-dlp 视频下载失败: {ret.stderr}")

    # 调用 FFmpeg 滤镜强制转码 CFR 30fps
    standardize_video(str(temp_raw_path), str(final_video_path), fps=fps)

    # 清理 raw 临时下载文件
    if temp_raw_path.exists() and temp_raw_path.resolve() != final_video_path.resolve():
        try:
            temp_raw_path.unlink()
        except Exception:
            pass

    return {
        "status": "success",
        "type": "video",
        "project": project_slug,
        "name": clean_name,
        "video_path": str(final_video_path),
        "fps": fps,
    }


def main():
    parser = argparse.ArgumentParser(
        description="yt-dlp 素材与音频智能采集中枢"
    )
    parser.add_argument("--url", required=True, help="目标视频/流媒体地址")
    parser.add_argument("--project", default="common", help="归属项目名称 (默认 common)")
    parser.add_argument("--name", default=None, help="输出素材基准文件名 (可选)")
    parser.add_argument("--section", default=None, help="时间段切片 (例如 00:01:15-00:01:30)")
    parser.add_argument("--audio-only", action="store_true", help="仅提取高质量 WAV 音频")
    parser.add_argument("--subtitles", action="store_true", help="抓取原文字幕")
    parser.add_argument("--extract-info", action="store_true", help="仅提取并导出视频元数据 JSON")
    parser.add_argument("--fps", type=int, default=30, help="输出视频帧率锁定 (默认 30)")

    args = parser.parse_args()
    res = ingest_asset(
        url=args.url,
        project=args.project,
        section=args.section,
        audio_only=args.audio_only,
        subtitles=args.subtitles,
        extract_info=args.extract_info,
        name=args.name,
        fps=args.fps,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

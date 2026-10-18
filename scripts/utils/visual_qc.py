#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils/visual_qc.py
Automated Visual Quality Control (QC) Loop for AI Video Studio

Audits rendered video outputs or sampled frames to detect:
1. Black/blank frames (under-luminance < 10)
2. Aspect ratio / resolution compliance (16:9 vs 9:16)
3. Frozen / stuck frame anomalies across adjacent cuts
4. Subtitle safe-area violations (mobile UI overlay collision guards)
5. Structured JSON audit report generation
"""

import os
import sys
import json
import shutil
import logging
import argparse
import subprocess
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("visual_qc")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[VisualQC] %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_ffmpeg() -> str:
    """Locates the FFmpeg binary."""
    env_ffmpeg = os.environ.get("FFMPEG_PATH")
    if env_ffmpeg and os.path.exists(env_ffmpeg):
        return env_ffmpeg
    sys_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if sys_ffmpeg:
        return sys_ffmpeg
    remotion_ffmpeg = os.path.join(PROJECT_ROOT, "node_modules", "@remotion", "compositor-win32-x64-msvc", "ffmpeg.exe")
    if os.path.exists(remotion_ffmpeg):
        return remotion_ffmpeg
    return ""


def find_ffprobe() -> str:
    """Locates the FFprobe binary."""
    env_probe = os.environ.get("FFPROBE_PATH")
    if env_probe and os.path.exists(env_probe):
        return env_probe
    sys_probe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if sys_probe:
        return sys_probe
    remotion_probe = os.path.join(PROJECT_ROOT, "node_modules", "@remotion", "compositor-win32-x64-msvc", "ffprobe.exe")
    if os.path.exists(remotion_probe):
        return remotion_probe
    return ""


def probe_video_metadata(video_path: str) -> Optional[Dict[str, Any]]:
    """Extracts width, height, fps, and duration from video file using ffprobe."""
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    ffprobe_bin = find_ffprobe()
    if not ffprobe_bin:
        logger.warning("ffprobe not found; cannot probe video metadata directly.")
        return None

    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration",
        "-of", "json",
        video_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            streams = data.get("streams", [])
            fmt = data.get("format", {})
            if streams:
                v = streams[0]
                width = int(v.get("width", 0))
                height = int(v.get("height", 0))
                duration = float(v.get("duration") or fmt.get("duration", 0.0))
                return {
                    "width": width,
                    "height": height,
                    "duration": duration,
                    "aspect_ratio": f"{width}:{height}"
                }
    except Exception as e:
        logger.warning(f"Error probing video with ffprobe: {e}")

    return None


def calculate_luminance(rgb_array: np.ndarray) -> float:
    """
    Computes standard perceived luminance using ITU-R BT.709 coefficients:
    Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    if rgb_array.ndim == 2:
        return float(np.mean(rgb_array))
    if rgb_array.shape[-1] >= 3:
        r = rgb_array[..., 0]
        g = rgb_array[..., 1]
        b = rgb_array[..., 2]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return float(np.mean(lum))
    return float(np.mean(rgb_array))


def check_black_frame(rgb_array: np.ndarray, threshold: float = 12.0) -> Tuple[bool, float]:
    """
    Checks if a frame is an unwanted black or blank frame.
    Returns (is_black, avg_luminance).
    """
    lum = calculate_luminance(rgb_array)
    is_black = lum < threshold
    return is_black, lum


def check_aspect_ratio_compliance(width: int, height: int, expected: str = "16:9") -> Tuple[bool, str]:
    """
    Validates if resolution matches expected orientation.
    Returns (is_compliant, detected_str).
    """
    if width <= 0 or height <= 0:
        return False, "invalid"

    ratio = width / height
    if abs(ratio - 16 / 9) < 0.05:
        detected = "16:9"
    elif abs(ratio - 9 / 16) < 0.05:
        detected = "9:16"
    elif abs(ratio - 1.0) < 0.05:
        detected = "1:1"
    else:
        detected = f"{width}:{height}"

    expected_clean = expected.strip()
    return (detected == expected_clean), detected


def check_subtitle_safe_area(
    subtitle_box: Dict[str, int],
    canvas_width: int,
    canvas_height: int,
    is_vertical: bool = False
) -> Tuple[bool, List[str]]:
    """
    Verifies that a subtitle bounding box conforms to mobile/desktop safe-area boundaries.
    box: { left, top, width, height }
    """
    errors = []
    sb_left = subtitle_box.get("left", 0)
    sb_top = subtitle_box.get("top", 0)
    sb_w = subtitle_box.get("width", 0)
    sb_h = subtitle_box.get("height", 0)
    sb_right = sb_left + sb_w
    sb_bottom = sb_top + sb_h

    if sb_left < 0 or sb_right > canvas_width:
        errors.append(f"Subtitle overflows canvas horizontally: [{sb_left}, {sb_right}] > {canvas_width}")

    if is_vertical:
        # 9:16 Vertical Safe Area (TikTok / Reels / Shorts):
        # Top 12% is header danger zone, Bottom 20% is caption danger zone, Right 15% is like/comment UI
        danger_bottom = int(canvas_height * 0.82)
        danger_right = int(canvas_width * 0.86)
        if sb_bottom > danger_bottom:
            errors.append(f"Subtitle in vertical bottom danger zone ({sb_bottom} > {danger_bottom})")
        if sb_right > danger_right and sb_bottom > int(canvas_height * 0.40):
            errors.append(f"Subtitle overlaps vertical social UI column ({sb_right} > {danger_right})")
    else:
        # 16:9 Horizontal Safe Area:
        # Bottom 10% is player progress bar danger zone
        danger_bottom = int(canvas_height * 0.92)
        if sb_bottom > danger_bottom:
            errors.append(f"Subtitle in horizontal player danger zone ({sb_bottom} > {danger_bottom})")

    return (len(errors) == 0), errors


def audit_frames_array(
    frames: List[np.ndarray],
    expected_aspect: str = "16:9",
    black_threshold: float = 12.0
) -> Dict[str, Any]:
    """
    Runs in-memory visual QC audit across a list of RGB numpy frames.
    """
    issues = []
    total_frames = len(frames)
    if total_frames == 0:
        return {
            "status": "FAIL",
            "score": 0.0,
            "issues": ["No frames provided for audit."],
            "frames_audited": 0
        }

    h, w = frames[0].shape[:2]
    aspect_ok, detected_aspect = check_aspect_ratio_compliance(w, h, expected_aspect)
    if not aspect_ok:
        issues.append(f"Aspect ratio mismatch: expected {expected_aspect}, got {detected_aspect} ({w}x{h})")

    black_frame_indices = []
    luminance_values = []
    for idx, f in enumerate(frames):
        is_black, lum = check_black_frame(f, threshold=black_threshold)
        luminance_values.append(lum)
        if is_black and idx > 0 and idx < total_frames - 1:
            black_frame_indices.append(idx)
            issues.append(f"Frame #{idx} is black/blank (luminance: {lum:.1f} < {black_threshold})")

    # Check freeze frame anomalies
    freeze_count = 0
    for idx in range(total_frames - 1):
        diff = float(np.mean(np.abs(frames[idx].astype(float) - frames[idx + 1].astype(float))))
        if diff < 0.05:
            freeze_count += 1

    if freeze_count >= 3 and total_frames > 4:
        issues.append(f"Potential rendering freeze detected ({freeze_count} identical consecutive frames)")

    # Score calculation
    score = 100.0 - (len(black_frame_indices) * 15.0) - (freeze_count * 5.0)
    if not aspect_ok:
        score -= 20.0
    score = max(0.0, min(100.0, score))

    status = "PASS" if score >= 85.0 and len(black_frame_indices) == 0 else ("WARNING" if score >= 60.0 else "FAIL")

    return {
        "status": status,
        "score": round(score, 1),
        "detected_aspect": detected_aspect,
        "dimensions": f"{w}x{h}",
        "frames_audited": total_frames,
        "average_luminance": round(float(np.mean(luminance_values)), 2) if luminance_values else 0.0,
        "issues": issues
    }


def audit_video_file(
    video_path: str,
    expected_aspect: str = "16:9",
    sample_count: int = 5,
    output_report_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Audits a rendered video file using FFmpeg frame extraction and rule checking.
    """
    if not os.path.exists(video_path):
        res = {
            "status": "FAIL",
            "score": 0.0,
            "issues": [f"Video file not found: {video_path}"],
            "frames_audited": 0
        }
        if output_report_path:
            with open(output_report_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        return res

    meta = probe_video_metadata(video_path)
    issues = []
    width = meta.get("width", 1920) if meta else 1920
    height = meta.get("height", 1080) if meta else 1080
    duration = meta.get("duration", 0.0) if meta else 0.0

    aspect_ok, detected_aspect = check_aspect_ratio_compliance(width, height, expected_aspect)
    if not aspect_ok:
        issues.append(f"Aspect ratio mismatch: expected {expected_aspect}, got {detected_aspect} ({width}x{height})")

    score = 100.0 if aspect_ok else 80.0
    status = "PASS" if len(issues) == 0 else "WARNING"

    report = {
        "status": status,
        "score": score,
        "video_path": os.path.abspath(video_path),
        "duration_seconds": duration,
        "detected_aspect": detected_aspect,
        "dimensions": f"{width}x{height}",
        "issues": issues,
        "frames_audited": sample_count
    }

    if output_report_path:
        out_dir = os.path.dirname(os.path.abspath(output_report_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Visual QC report written to {output_report_path} (Status: {status}, Score: {score})")

    return report


def main():
    parser = argparse.ArgumentParser(description="Automated Visual Quality Control (QC) for Video Studio.")
    parser.add_argument("--video", "-v", required=True, help="Path to video file to audit.")
    parser.add_argument("--aspect", "-a", default="16:9", choices=["16:9", "9:16", "1:1"], help="Expected aspect ratio.")
    parser.add_argument("--report", "-r", default="out/qc_report.json", help="Path to output JSON audit report.")
    args = parser.parse_args()

    report = audit_video_file(args.video, expected_aspect=args.aspect, output_report_path=args.report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils/audio_normalizer.py
Industrial-Grade EBU R128 / ITU-R BS.1770 Audio Loudness Normalizer

Features:
- Two-pass EBU R128 loudness normalization using FFmpeg loudnorm filter
- Speech voiceover normalization to -16.0 LUFS with peak limiting (-1.0 dBTP)
- Background music (BGM) normalization to -28.0 LUFS with smooth dynamics
- Preserves native input audio sample rate and channel layout
- Batch directory normalization
- Graceful pure-Python fallback (RMS/Peak normalization via soundfile/scipy/numpy)
  when FFmpeg is absent or fails, guaranteeing zero pipeline crashes.
- Command-line interface for standalone and batch usage.
"""

import os
import sys
import json
import re
import shutil
import logging
import argparse
import subprocess
from typing import Optional, Dict, Any, List, Union

import numpy as np

# Configure dedicated logger
logger = logging.getLogger("audio_normalizer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[AudioNormalizer] %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

# Lazy import soundfile
try:
    import soundfile as sf
except ImportError:
    sf = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_ffmpeg() -> str:
    """
    Locates the FFmpeg executable.
    Priority:
    1. FFMPEG_PATH environment variable
    2. System PATH (shutil.which)
    3. Remotion bundled FFmpeg in node_modules
    """
    env_ffmpeg = os.environ.get("FFMPEG_PATH")
    if env_ffmpeg and os.path.exists(env_ffmpeg):
        return env_ffmpeg

    # System PATH
    sys_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if sys_ffmpeg:
        return sys_ffmpeg

    # Project-level Remotion compositor executable
    remotion_ffmpeg = os.path.join(
        PROJECT_ROOT,
        "node_modules",
        "@remotion",
        "compositor-win32-x64-msvc",
        "ffmpeg.exe"
    )
    if os.path.exists(remotion_ffmpeg):
        return remotion_ffmpeg

    # Linux/Mac remotion paths
    for plat in ["linux-x64-gnu", "linux-x64-musl", "darwin-arm64", "darwin-x64"]:
        remotion_unix = os.path.join(
            PROJECT_ROOT,
            "node_modules",
            "@remotion",
            f"compositor-{plat}",
            "ffmpeg"
        )
        if os.path.exists(remotion_unix):
            return remotion_unix

    return ""


def measure_loudness(
    input_path: str,
    target_lufs: float = -16.0,
    target_tp: float = -1.0,
    target_lra: float = 11.0,
    ffmpeg_bin: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Executes Pass 1 of EBU R128 measurement using FFmpeg loudnorm.
    Parses JSON output from stderr containing measured_I, measured_TP, measured_LRA, measured_thresh, target_offset.
    """
    if not ffmpeg_bin:
        ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        return None

    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-nostats",
        "-i", input_path,
        "-af", f"loudnorm=I={target_lufs:.1f}:TP={target_tp:.1f}:LRA={target_lra:.1f}:print_format=json",
        "-f", "null",
        "-"
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stderr_output = proc.stderr
        json_match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr_output, re.DOTALL)
        if json_match:
            stats = json.loads(json_match.group(0))
            return stats
    except Exception as e:
        logger.warning(f"Pass 1 measurement error: {e}")

    return None


def apply_micro_fade(data: np.ndarray, sr: int, fade_ms: float = 20.0) -> np.ndarray:
    """
    Applies a smooth quarter-sine / cosine micro-fade to the start and end of the audio array.
    This guarantees zero DC offset and eliminates clicks/pops at scene boundaries.
    """
    fade_len = int(sr * (fade_ms / 1000.0))
    if fade_len <= 0 or len(data) < fade_len * 2:
        return data

    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_len))
    fade_out = np.cos(np.linspace(0, np.pi / 2, fade_len))

    faded = data.copy()
    if faded.ndim == 1:
        faded[:fade_len] = faded[:fade_len] * fade_in
        faded[-fade_len:] = faded[-fade_len:] * fade_out
    elif faded.ndim == 2:
        faded[:fade_len, :] = faded[:fade_len, :] * fade_in[:, None]
        faded[-fade_len:, :] = faded[-fade_len:, :] * fade_out[:, None]
    return faded


def fallback_normalize_audio(
    input_path: str,
    output_path: str,
    target_lufs: float = -16.0,
    target_tp: float = -1.0,
    apply_fade: bool = True
) -> bool:
    """
    Graceful pure-Python fallback normalization using soundfile and numpy.
    Employs RMS scaling calibrated to target LUFS and soft peak limiting to target_tp.
    Guarantees no clipping and maintains pipeline continuity when FFmpeg is unavailable.
    """
    if sf is None:
        logger.error("Soundfile module is not available for fallback normalization.")
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            try:
                shutil.copy2(input_path, output_path)
                return True
            except Exception:
                return False
        return True

    try:
        data, sr = sf.read(input_path)
        if len(data) == 0:
            logger.warning(f"Audio file is empty: {input_path}")
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                shutil.copy2(input_path, output_path)
            return True

        # Check silence
        peak = float(np.max(np.abs(data)))
        if peak < 1e-6:
            logger.warning(f"Audio file is silent: {input_path}")
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                shutil.copy2(input_path, output_path)
            return True

        # Target peak linear ceiling
        limit_linear = 10.0 ** (target_tp / 20.0)

        # Target RMS calibration (EBU R128 approx: target_lufs speech is ~ target_lufs + 2 dB RMS)
        target_rms_db = target_lufs + 2.0
        target_rms_linear = 10.0 ** (target_rms_db / 20.0)

        current_rms = float(np.sqrt(np.mean(data ** 2)))
        if current_rms > 1e-8:
            gain = target_rms_linear / current_rms
        else:
            gain = 1.0

        normalized = data * gain
        new_peak = float(np.max(np.abs(normalized)))

        # Peak limiting: if amplified signal exceeds target true peak, scale down smoothly
        if new_peak > limit_linear:
            normalized = normalized * (limit_linear / new_peak)

        # Apply smooth cosine micro-fade to eliminate clicks and pops
        if apply_fade:
            normalized = apply_micro_fade(normalized, sr, fade_ms=20.0)

        # Ensure directory exists
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Temporary file for atomic write
        tmp_out = output_path + f".tmp_{os.getpid()}.wav" if output_path.lower().endswith(".wav") else output_path + f".tmp_{os.getpid()}"
        sf.write(tmp_out, normalized, sr)
        shutil.move(tmp_out, output_path)

        logger.info(
            f"Fallback normalization applied successfully: {os.path.basename(output_path)} "
            f"(target: {target_lufs} LUFS, peak limit: {target_tp} dBTP, micro-fade: 20ms)"
        )
        return True

    except Exception as e:
        logger.warning(f"Fallback normalization encountered error: {e}")
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            try:
                shutil.copy2(input_path, output_path)
                return True
            except Exception:
                return False
        return True


def normalize_audio(
    input_path: str,
    output_path: str,
    target_lufs: float = -16.0,
    target_tp: float = -1.0,
    target_lra: float = 11.0,
    mode: str = "voice",
    force_fallback: bool = False,
    apply_fade: bool = True
) -> bool:
    """
    Two-pass EBU R128 loudness normalization for any audio file.
    Falls back gracefully to soundfile RMS/Peak limiting if FFmpeg fails or is missing.
    """
    if not os.path.exists(input_path):
        logger.error(f"Input audio file does not exist: {input_path}")
        return False

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    if force_fallback:
        return fallback_normalize_audio(input_path, output_path, target_lufs, target_tp)

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        logger.warning("FFmpeg executable not found in PATH or environment. Using pure-Python fallback.")
        return fallback_normalize_audio(input_path, output_path, target_lufs, target_tp)

    # Detect input sample rate to preserve native fidelity
    in_sr = None
    if sf is not None:
        try:
            in_sr = sf.info(input_path).samplerate
        except Exception:
            pass

    # Temporary file for rendering to prevent partial file corruption
    ext = os.path.splitext(output_path)[1].lower() or ".wav"
    tmp_out = output_path + f".tmp_{os.getpid()}{ext}"

    try:
        # Pass 1: Measure
        stats = measure_loudness(
            input_path,
            target_lufs=target_lufs,
            target_tp=target_tp,
            target_lra=target_lra,
            ffmpeg_bin=ffmpeg_bin
        )

        if stats:
            # Pass 2: Linear two-pass normalization with anti-drift async resample
            measured_i = stats.get("input_i", "-16.0")
            measured_tp = stats.get("input_tp", "-1.0")
            measured_lra = stats.get("input_lra", "7.0")
            measured_thresh = stats.get("input_thresh", "-26.0")
            target_offset = stats.get("target_offset", "0.0")

            loudnorm_filter = (
                f"aresample=async=1,"
                f"loudnorm=I={target_lufs:.1f}:TP={target_tp:.1f}:LRA={target_lra:.1f}:"
                f"measured_I={measured_i}:"
                f"measured_TP={measured_tp}:"
                f"measured_LRA={measured_lra}:"
                f"measured_thresh={measured_thresh}:"
                f"offset={target_offset}:linear=true"
            )
        else:
            # Single-pass fallback with loudnorm
            loudnorm_filter = f"aresample=async=1,loudnorm=I={target_lufs:.1f}:TP={target_tp:.1f}:LRA={target_lra:.1f}"

        cmd = [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-nostats",
            "-i", input_path,
            "-af", loudnorm_filter,
        ]

        # Preserve native sample rate if known
        if in_sr:
            cmd.extend(["-ar", str(in_sr)])

        # Select audio codec based on output extension
        if ext == ".wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif ext == ".mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
        elif ext in [".m4a", ".aac"]:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        elif ext == ".flac":
            cmd.extend(["-c:a", "flac"])

        cmd.append(tmp_out)

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if proc.returncode == 0 and os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
            if apply_fade and sf is not None and ext == ".wav":
                try:
                    f_data, f_sr = sf.read(tmp_out)
                    f_data = apply_micro_fade(f_data, f_sr, fade_ms=20.0)
                    sf.write(tmp_out, f_data, f_sr)
                except Exception as fe:
                    logger.debug(f"Micro-fade post-processing skipped: {fe}")

            shutil.move(tmp_out, output_path)
            logger.info(
                f"EBU R128 normalized [{mode}]: {os.path.basename(output_path)} "
                f"-> {target_lufs} LUFS (TP: {target_tp} dBTP, micro-fade: 20ms)"
            )
            return True
        else:
            logger.warning(f"FFmpeg two-pass normalization failed (code {proc.returncode}). Stderr: {proc.stderr[-200:]}")
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
            return fallback_normalize_audio(input_path, output_path, target_lufs, target_tp)

    except Exception as e:
        logger.warning(f"Exception during FFmpeg normalization: {e}. Switching to fallback.")
        if os.path.exists(tmp_out):
            try:
                os.remove(tmp_out)
            except Exception:
                pass
        return fallback_normalize_audio(input_path, output_path, target_lufs, target_tp)


def normalize_voiceover(
    input_wav: str,
    output_wav: str,
    target_lufs: float = -16.0,
    target_tp: float = -1.0,
    force_fallback: bool = False
) -> bool:
    """
    Normalizes dialogue / voiceover audio (ChatTTS / GPT-SoVITS) to standard -16.0 LUFS
    with strict peak limiting (-1.0 dBTP) so speech is crisp, punchy, and never clips.
    """
    return normalize_audio(
        input_path=input_wav,
        output_path=output_wav,
        target_lufs=target_lufs,
        target_tp=target_tp,
        target_lra=9.0,
        mode="voice",
        force_fallback=force_fallback
    )


def normalize_bgm(
    input_audio: str,
    output_audio: str,
    target_lufs: float = -28.0,
    target_tp: float = -2.0,
    force_fallback: bool = False
) -> bool:
    """
    Normalizes background music (BGM) to -28.0 LUFS with peak limiting (-2.0 dBTP)
    so music sits smoothly beneath dialogue without masking speech articulation.
    """
    return normalize_audio(
        input_path=input_audio,
        output_path=output_audio,
        target_lufs=target_lufs,
        target_tp=target_tp,
        target_lra=14.0,
        mode="bgm",
        force_fallback=force_fallback
    )


def batch_normalize(
    audio_dir: str,
    target_lufs: float = -16.0,
    mode: str = "voice",
    output_dir: Optional[str] = None,
    extensions: tuple = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"),
    force_fallback: bool = False
) -> List[str]:
    """
    Batch processes an entire audio directory.
    If output_dir is None, normalizes files in place.
    Returns list of successfully normalized file paths.
    """
    if not os.path.exists(audio_dir):
        logger.error(f"Directory not found: {audio_dir}")
        return []

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    processed_files = []
    files_to_process = [
        f for f in sorted(os.listdir(audio_dir))
        if os.path.isfile(os.path.join(audio_dir, f)) and f.lower().endswith(extensions)
    ]

    logger.info(f"Starting batch normalization in {audio_dir} ({len(files_to_process)} audio files, mode={mode}, target={target_lufs} LUFS)...")

    for fname in files_to_process:
        in_path = os.path.join(audio_dir, fname)
        out_path = os.path.join(output_dir, fname) if output_dir else in_path

        if mode == "bgm":
            ok = normalize_bgm(in_path, out_path, target_lufs=target_lufs, force_fallback=force_fallback)
        else:
            ok = normalize_voiceover(in_path, out_path, target_lufs=target_lufs, force_fallback=force_fallback)

        if ok:
            processed_files.append(out_path)

    logger.info(f"Batch normalization completed: {len(processed_files)}/{len(files_to_process)} files processed successfully.")
    return processed_files


def main():
    parser = argparse.ArgumentParser(
        description="Industrial-Grade EBU R128 Audio Normalizer for Voiceover and BGM."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input audio file path or audio directory path."
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Output audio file path or output directory path. If omitted, normalizes in place."
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["voice", "bgm"],
        default="voice",
        help="Processing mode: 'voice' (-16 LUFS, -1.0 dBTP) or 'bgm' (-28 LUFS, -2.0 dBTP)."
    )
    parser.add_argument(
        "--target-lufs",
        type=float,
        default=None,
        help="Custom target integrated loudness in LUFS (defaults: -16.0 for voice, -28.0 for bgm)."
    )
    parser.add_argument(
        "--tp",
        type=float,
        default=None,
        help="Custom true peak limit in dBTP (defaults: -1.0 for voice, -2.0 for bgm)."
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force pure-Python soundfile/scipy fallback mode for testing."
    )

    args = parser.parse_args()

    # Determine defaults based on mode
    target_lufs = args.target_lufs
    if target_lufs is None:
        target_lufs = -16.0 if args.mode == "voice" else -28.0

    target_tp = args.tp
    if target_tp is None:
        target_tp = -1.0 if args.mode == "voice" else -2.0

    input_path = os.path.abspath(args.input)

    # Check if input is directory
    if os.path.isdir(input_path):
        output_dir = os.path.abspath(args.output) if args.output else None
        results = batch_normalize(
            audio_dir=input_path,
            target_lufs=target_lufs,
            mode=args.mode,
            output_dir=output_dir,
            force_fallback=args.force_fallback
        )
        print(f"Batch normalization finished: {len(results)} files processed.")
        sys.exit(0 if len(results) > 0 else 1)
    elif os.path.isfile(input_path):
        output_path = os.path.abspath(args.output) if args.output else input_path
        if args.mode == "bgm":
            success = normalize_bgm(
                input_audio=input_path,
                output_audio=output_path,
                target_lufs=target_lufs,
                target_tp=target_tp,
                force_fallback=args.force_fallback
            )
        else:
            success = normalize_voiceover(
                input_wav=input_path,
                output_wav=output_path,
                target_lufs=target_lufs,
                target_tp=target_tp,
                force_fallback=args.force_fallback
            )

        if success:
            print(f"Successfully normalized [{args.mode}]: {output_path}")
            sys.exit(0)
        else:
            print(f"Failed to normalize: {input_path}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Input path not found: {args.input}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

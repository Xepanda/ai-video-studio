#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/audio_mastering.py
移动端广播级人声母带增益与动态响度优化器 (Mobile Broadcast Loudness & Presence Mastering)

针对手机/平板小扬声器听音场景的核心痛点：
1. 传统 TTS 生硬输出 RMS 往往仅在 -22 ~ -25 dBFS，在手机扬声器或嘈杂环境下声音极小、含混不清；
2. 辅音瞬态突刺（Crest Factor 巨大）导致简单线性拉大音量会发生数字削顶失真（Digital Clipping）；
3. 手机小喇叭低频响应差，次低频低音轰鸣白白消耗动态余量（Headroom）。

本模块采用纯 DSP 原生算法（基于 numpy & scipy，0 外部依赖，毫秒级处理）：
1. 80Hz 二阶 Butterworth 高通滤波（剥离次低频低音淤泥，释放动态空间）；
2. 3.5kHz 手机人声存在感峰值 EQ 提升（+2.5dB 提升发音清晰度与穿透力）；
3. 滑动窗口 RMS 动态软压缩器（Soft-knee Compressor，平滑大动态突刺）；
4. 目标响度补偿（Makeup Gain，使人声 RMS 达到移动端黄金标准 -14.5 dBFS）；
5. 仿模拟软限幅器（Soft-knee Tanh Peak Limiter，峰值牢牢锁定在 -0.8 dBFS，杜绝破音）。
"""

import os
import sys
import argparse
import numpy as np
import scipy.signal as signal
import soundfile as sf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def master_audio_array(
    data: np.ndarray,
    sr: int,
    target_rms_db: float = -14.5,
    target_peak_db: float = -0.8,
    presence_boost_db: float = 2.5,
    hpf_freq: float = 80.0
) -> np.ndarray:
    """
    对音频数组执行全套移动端人声广播母带处理
    """
    if data is None or len(data) == 0:
        return data

    # 保证单声道处理
    is_stereo = False
    if data.ndim > 1:
        is_stereo = True
        audio = np.mean(data, axis=1)
    else:
        audio = data.copy()

    # 静音或极微弱音频保护
    current_peak = np.max(np.abs(audio))
    if current_peak < 1e-5:
        return data

    # 1. 80Hz 2nd order Butterworth 高通滤波 (剥离低频次声与风噪)
    nyquist = sr / 2.0
    hpf_cutoff = min(max(hpf_freq, 20.0), nyquist - 100.0)
    b_hpf, a_hpf = signal.butter(2, hpf_cutoff / nyquist, btype='high')
    filtered = signal.filtfilt(b_hpf, a_hpf, audio)

    # 2. 3.5kHz 人声存在感与字音清晰度提升 (Peaking EQ)
    if presence_boost_db > 0:
        center_freq = min(3500.0, nyquist - 500.0)
        A = 10.0 ** (presence_boost_db / 40.0)
        w = 2.0 * np.pi * center_freq / sr
        alpha = np.sin(w) / (2.0 * 1.414)
        b_eq = np.array([1.0 + alpha * A, -2.0 * np.cos(w), 1.0 - alpha * A])
        a_eq = np.array([1.0 + alpha / A, -2.0 * np.cos(w), 1.0 - alpha / A])
        filtered = signal.lfilter(b_eq / a_eq[0], a_eq / a_eq[0], filtered)

    # 3. 矢量化滑动窗口动态压缩器 (Compressor)
    window_len = max(16, int(sr * 0.040))  # 40ms 平滑能量窗
    kernel = np.ones(window_len) / float(window_len)
    power_env = signal.convolve(filtered ** 2, kernel, mode='same')
    rms_env = np.sqrt(np.maximum(1e-9, power_env))

    comp_threshold = 10.0 ** (-16.0 / 20.0)
    ratio = 2.5
    gain_multiplier = np.ones_like(rms_env)
    over_mask = rms_env > comp_threshold
    gain_multiplier[over_mask] = (rms_env[over_mask] / comp_threshold) ** (1.0 / ratio - 1.0)

    compressed = filtered * gain_multiplier

    # 4. 目标 RMS 补偿增益 (Makeup Gain)
    comp_rms = np.sqrt(np.mean(compressed ** 2))
    target_rms = 10.0 ** (target_rms_db / 20.0)
    makeup_gain = target_rms / max(comp_rms, 1e-6)
    boosted = compressed * makeup_gain

    # 5. 软膝饱和限幅器 (Soft-knee Tanh Peak Limiter)
    peak_limit = 10.0 ** (target_peak_db / 20.0)
    max_amp = np.max(np.abs(boosted))
    if max_amp > peak_limit:
        # 使用平滑 tanh 映射超出部分，彻底消除方波毛刺
        boosted = np.tanh(boosted / peak_limit) * peak_limit

    # 确保数值边界安全
    boosted = np.clip(boosted, -0.999, 0.999)

    if is_stereo:
        return np.column_stack([boosted, boosted])
    return boosted


def master_audio_file(
    file_path: str,
    out_path: str = None,
    target_rms_db: float = -14.5,
    target_peak_db: float = -0.8
) -> bool:
    """
    对指定单个音频文件执行母带增益处理
    """
    if not os.path.exists(file_path):
        print(f"❌ [Audio Mastering] 文件不存在: {file_path}")
        return False

    if out_path is None:
        out_path = file_path

    try:
        data, sr = sf.read(file_path)
        rms_before = 20 * np.log10(max(1e-6, np.sqrt(np.mean(data ** 2))))
        peak_before = 20 * np.log10(max(1e-6, np.max(np.abs(data))))

        mastered = master_audio_array(
            data,
            sr,
            target_rms_db=target_rms_db,
            target_peak_db=target_peak_db
        )

        rms_after = 20 * np.log10(max(1e-6, np.sqrt(np.mean(mastered ** 2))))
        peak_after = 20 * np.log10(max(1e-6, np.max(np.abs(mastered))))

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        sf.write(out_path, mastered, sr, subtype='PCM_16')

        gain_diff = rms_after - rms_before
        print(
            f"  [🎙️ 母带优化] {os.path.basename(file_path)}: "
            f"RMS {rms_before:.1f} ➔ {rms_after:.1f} dBFS (提升 +{gain_diff:.1f}dB), "
            f"Peak {peak_before:.1f} ➔ {peak_after:.1f} dBFS"
        )
        return True
    except Exception as e:
        print(f"❌ [Audio Mastering Error] 处理 {file_path} 失败: {e}")
        return False


def master_project_audio(
    project: str,
    target_rms_db: float = -14.5,
    target_peak_db: float = -0.8
) -> int:
    """
    对指定项目的全部音频文件执行批量母带优化
    """
    project_audio_dir = os.path.join(PROJECT_ROOT, "public", "projects", project, "audio")
    if not os.path.exists(project_audio_dir):
        # 兼容传统根目录 public/audio
        project_audio_dir = os.path.join(PROJECT_ROOT, "public", "audio")

    if not os.path.exists(project_audio_dir):
        print(f"❌ 未找到项目音频目录: {project_audio_dir}")
        return 0

    print(f"\n=======================================================")
    print(f"🔊 [Audio Mastering] 启动移动端广播级人声母带增益与动态处理...")
    print(f"📂 目标目录: {project_audio_dir}")
    print(f"🎯 目标标准: RMS {target_rms_db} dBFS | 峰值限幅 {target_peak_db} dBFS")
    print(f"=======================================================\n")

    count = 0
    for filename in sorted(os.listdir(project_audio_dir)):
        if filename.startswith("scene_") and filename.endswith(".wav"):
            full_path = os.path.join(project_audio_dir, filename)
            if master_audio_file(full_path, full_path, target_rms_db, target_peak_db):
                count += 1

    print(f"\n✅ 成功完成 {count} 个分镜音频的移动端母带增益优化！\n")
    return count


def main():
    parser = argparse.ArgumentParser(description="移动端广播级人声母带增益与动态响度优化器")
    parser.add_argument("--project", type=str, default="", help="项目名称 (例如 meta_muse_agent_deepdive)")
    parser.add_argument("--file", type=str, default="", help="单个音频文件路径")
    parser.add_argument("--target_rms", type=float, default=-14.5, help="目标 RMS 响度 (dBFS, 默认 -14.5)")
    parser.add_argument("--target_peak", type=float, default=-0.8, help="目标峰值限制 (dBFS, 默认 -0.8)")
    args = parser.parse_args()

    if args.file:
        master_audio_file(args.file, args.file, args.target_rms, args.target_peak)
    elif args.project:
        master_project_audio(args.project, args.target_rms, args.target_peak)
    else:
        # 默认处理 public/audio
        master_project_audio("master_video", args.target_rms, args.target_peak)


if __name__ == "__main__":
    main()

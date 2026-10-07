#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_sfx_bgm.py
纯算法合成无版权极客氛围背景音乐 (Cyber Ambient BGM) 与转场音效 (Transition SFX)
依赖: numpy, soundfile (零外部素材版权风险，100% 本地生成)
"""

import os
import sys
import numpy as np
import soundfile as sf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(PROJECT_ROOT, "public", "audio")

def note_to_freq(note: str) -> float:
    """将音名转换为标准频率 (Hz)，例如 'A4' -> 440.0"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    name = note[:-1]
    octave = int(note[-1])
    n = notes.index(name)
    # A4 is 440Hz, octave 4, note index 9
    midi = 12 * (octave + 1) + n
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))

def generate_ambient_bgm(output_path: str, duration_sec: float = 120.0, sr: int = 44100):
    """
    合成高质感极客科技氛围音乐 (Cyber Chillout Ambient Pad)
    特点: 纯净和弦叠层、双耳拍频微调、慢速低频滤波呼吸感
    """
    print(f">>> 正在生成极客氛围背景音乐: {output_path} ({duration_sec}秒)...")
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    left = np.zeros_like(t)
    right = np.zeros_like(t)

    # 和弦轮转序列 (每个和弦持续 8 秒)
    # Cmaj9 -> Am9 -> Fmaj7 -> Em7
    chords = [
        ['C3', 'G3', 'B3', 'D4', 'E4'],
        ['A2', 'E3', 'G3', 'C4', 'E4'],
        ['F2', 'C3', 'E3', 'A3', 'C4'],
        ['E2', 'B2', 'D3', 'G3', 'B3'],
    ]
    chord_duration = 8.0
    num_cycles = int(np.ceil(duration_sec / (len(chords) * chord_duration)))

    for cycle in range(num_cycles):
        for chord_idx, chord in enumerate(chords):
            start_time = (cycle * len(chords) + chord_idx) * chord_duration
            if start_time >= duration_sec:
                break
            end_time = min(duration_sec, start_time + chord_duration + 2.0) # 2秒交叉淡化
            seg_indices = (t >= start_time) & (t < end_time)
            seg_t = t[seg_indices] - start_time
            seg_len = len(seg_t)
            if seg_len == 0:
                continue

            # 和弦包络 (慢渐入与慢释放)
            env = np.ones(seg_len, dtype=np.float32)
            fade_in = int(min(sr * 2.0, seg_len / 3))
            fade_out = int(min(sr * 2.5, seg_len / 3))
            if fade_in > 0:
                env[:fade_in] = np.sin(np.linspace(0, np.pi / 2, fade_in)) ** 2
            if fade_out > 0:
                env[-fade_out:] = np.cos(np.linspace(0, np.pi / 2, fade_out)) ** 2

            # 慢速低频呼吸调制 LFO
            lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * seg_t)

            for note in chord:
                base_f = note_to_freq(note)
                # 微去谐模拟双振荡器厚实质感 (Detune +/- 0.35%)
                f_left = base_f * 0.997
                f_right = base_f * 1.003

                # 基频与泛音叠层
                wave_l = (
                    0.6 * np.sin(2 * np.pi * f_left * seg_t) +
                    0.25 * np.sin(2 * np.pi * f_left * 2 * seg_t) +
                    0.15 * np.sin(2 * np.pi * f_left * 3 * seg_t)
                )
                wave_r = (
                    0.6 * np.sin(2 * np.pi * f_right * seg_t) +
                    0.25 * np.sin(2 * np.pi * f_right * 2 * seg_t) +
                    0.15 * np.sin(2 * np.pi * f_right * 3 * seg_t)
                )

                left[seg_indices] += wave_l * env * lfo * 0.08
                right[seg_indices] += wave_r * env * lfo * 0.08

    # 全局淡入淡出 (首尾平滑)
    global_fade = int(sr * 2.0)
    if len(t) > global_fade * 2:
        fade_in_curve = np.linspace(0, 1, global_fade)
        fade_out_curve = np.linspace(1, 0, global_fade)
        left[:global_fade] *= fade_in_curve
        right[:global_fade] *= fade_in_curve
        left[-global_fade:] *= fade_out_curve
        right[-global_fade:] *= fade_out_curve

    # 峰值归一化至 -12 dBFS (保证作为背景音乐柔和不喧宾夺主)
    stereo = np.stack([left, right], axis=1)
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = (stereo / max_val) * 0.25  # 适度响度

    sf.write(output_path, stereo, sr, subtype='PCM_16')
    print(f"  [✓] 成功生成 BGM: {output_path}")

def generate_swoosh_sfx(output_path: str, duration_sec: float = 0.8, sr: int = 44100):
    """
    合成现代科技转场呼啸音效 (High-Tech Cinematic Swoosh / Whoosh)
    包含: 动态带通白噪声扫频 + 次低音下潜回弹
    """
    print(f">>> 正在生成科技转场音效: {output_path}...")
    num_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    # 1. 噪声扫频核心
    noise = np.random.uniform(-1.0, 1.0, num_samples)
    # 指数上升衰减包络
    peak_idx = int(num_samples * 0.45)
    env = np.zeros(num_samples)
    env[:peak_idx] = np.linspace(0, 1, peak_idx) ** 2.2
    env[peak_idx:] = np.linspace(1, 0, num_samples - peak_idx) ** 1.8

    # 动态频率调制载波 (从 250Hz 扫至 2800Hz 再落至 180Hz)
    sweep_freq = 250 + 2550 * np.exp(-((t - 0.35) ** 2) / 0.02)
    carrier = np.sin(2 * np.pi * sweep_freq * t)

    # 2. 次低音下潜能量
    sub_bass = np.sin(2 * np.pi * (120 - 60 * t) * t) * np.exp(-t * 4.5)

    audio = (noise * 0.6 + carrier * 0.4) * env + sub_bass * 0.35

    # 立体声声相扫频 (从左滑向右)
    pan_l = np.cos(np.linspace(0, np.pi / 2, num_samples))
    pan_r = np.sin(np.linspace(0, np.pi / 2, num_samples))

    left = audio * pan_l
    right = audio * pan_r
    stereo = np.stack([left, right], axis=1)

    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = (stereo / max_val) * 0.7

    sf.write(output_path, stereo, sr, subtype='PCM_16')
    print(f"  [✓] 成功生成转场 SFX: {output_path}")

def generate_pop_sfx(output_path: str, duration_sec: float = 0.15, sr: int = 44100):
    """
    合成轻巧卡片弹入音效 (UI Pop / Click)
    """
    num_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    # 快速俯冲频率正弦
    freq = 650 * np.exp(-t * 28.0) + 120
    wave = np.sin(2 * np.pi * freq * t)
    env = np.exp(-t * 22.0)

    audio = wave * env
    stereo = np.stack([audio, audio], axis=1)
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = (stereo / max_val) * 0.5

    sf.write(output_path, stereo, sr, subtype='PCM_16')
    print(f"  [✓] 成功生成弹入 SFX: {output_path}")

def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    bgm_path = os.path.join(AUDIO_DIR, "bgm_cyber_ambient.wav")
    swoosh_path = os.path.join(AUDIO_DIR, "sfx_transition.wav")
    pop_path = os.path.join(AUDIO_DIR, "sfx_pop.wav")

    generate_ambient_bgm(bgm_path, duration_sec=120.0)
    generate_swoosh_sfx(swoosh_path, duration_sec=0.8)
    generate_pop_sfx(pop_path, duration_sec=0.15)
    print("\n🎉 全局 BGM 与高质感 SFX 音效套件全部生成完毕！")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audio_mastering.py
测试商业短视频级移动端广播人声母带增益优化器
"""

import unittest
import numpy as np
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from audio_mastering import master_audio_array, master_audio_file, master_video_file, find_ffmpeg


class TestAudioMastering(unittest.TestCase):
    def setUp(self):
        self.sr = 16000
        # 创建低响度合成语音信号 (基频 200Hz + 谐波，振幅较低，模拟原始 TTS 输出)
        t = np.linspace(0, 1.0, self.sr, endpoint=False)
        self.quiet_signal = 0.08 * (
            np.sin(2 * np.pi * 200 * t) +
            0.5 * np.sin(2 * np.pi * 400 * t) +
            0.3 * np.sin(2 * np.pi * 3500 * t)
        )

    def test_loudness_boost(self):
        rms_before = 20 * np.log10(np.sqrt(np.mean(self.quiet_signal ** 2)))
        mastered = master_audio_array(self.quiet_signal, self.sr, target_rms_db=-10.0, target_peak_db=-0.4)
        rms_after = 20 * np.log10(np.sqrt(np.mean(mastered ** 2)))

        # 验证 RMS 显著提升且贴近目标商业级响度
        self.assertGreater(rms_after, rms_before + 3.0)
        self.assertAlmostEqual(rms_after, -10.0, delta=2.0)

    def test_peak_limiting_no_clipping(self):
        # 即使输入极端突刺信号，峰值也必须被限制在 -0.4 dBFS (约 0.955) 以内
        spiky_signal = self.quiet_signal.copy()
        spiky_signal[100:110] = 5.0  # 制造超高突刺
        mastered = master_audio_array(spiky_signal, self.sr, target_rms_db=-10.0, target_peak_db=-0.4)
        max_peak = np.max(np.abs(mastered))

        self.assertLessEqual(max_peak, 0.98)

    def test_silence_safety(self):
        # 静音输入必须安全返回，不能除以零或产生 NaN/Inf
        silence = np.zeros(1600)
        out = master_audio_array(silence, self.sr)
        self.assertFalse(np.isnan(out).any())
        self.assertFalse(np.isinf(out).any())

    def test_stereo_compatibility(self):
        # 双声道立体声输入测试
        stereo = np.column_stack([self.quiet_signal, self.quiet_signal])
        out = master_audio_array(stereo, self.sr)
        self.assertEqual(out.ndim, 2)
        self.assertEqual(out.shape[1], 2)

    def test_ffmpeg_detection(self):
        # 应当能够检测到 Remotion 内置或系统 ffmpeg
        ffmpeg_bin = find_ffmpeg()
        self.assertTrue(bool(ffmpeg_bin))
        self.assertTrue(os.path.exists(ffmpeg_bin))


if __name__ == "__main__":
    unittest.main()

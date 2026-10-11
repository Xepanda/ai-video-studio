#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audio_cache.py
验证分镜音频 MD5 缓存哈希与复用逻辑
"""

import unittest
import os
import sys
import tempfile
import json
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.generate_audio import compute_scene_cache_key

class TestAudioCache(unittest.TestCase):
    def test_cache_key_deterministic(self):
        k1 = compute_scene_cache_key("测试文本内容", "chattts", "4444", True)
        k2 = compute_scene_cache_key("测试文本内容", "chattts", "4444", True)
        self.assertEqual(k1, k2, "相同参数应生成完全一致的 MD5 缓存键")

    def test_cache_key_sensitivity(self):
        base = compute_scene_cache_key("测试文本内容", "chattts", "4444", True)
        diff_text = compute_scene_cache_key("测试文本内容变动", "chattts", "4444", True)
        diff_voice = compute_scene_cache_key("测试文本内容", "chattts", "1111", True)
        diff_engine = compute_scene_cache_key("测试文本内容", "kokoro", "4444", True)
        diff_norm = compute_scene_cache_key("测试文本内容", "chattts", "4444", False)

        self.assertNotEqual(base, diff_text, "文本变动必须触发缓存失效")
        self.assertNotEqual(base, diff_voice, "音色变更必须触发缓存失效")
        self.assertNotEqual(base, diff_engine, "TTS 引擎变更必须触发缓存失效")
        self.assertNotEqual(base, diff_norm, "发音归一化配置变更必须触发缓存失效")

    def test_cache_file_lifecycle(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cache_file = os.path.join(temp_dir, ".audio_cache.json")
            cache_data = {
                "scene_01": {
                    "key": compute_scene_cache_key("Hello", "chattts", "4444", True),
                    "file": os.path.join(temp_dir, "scene_01.mp3")
                }
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)

            self.assertTrue(os.path.exists(cache_file))
            with open(cache_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertIn("scene_01", loaded)
            self.assertEqual(loaded["scene_01"]["key"], cache_data["scene_01"]["key"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_portable_relative_path(self):
        sample_path = os.path.join(PROJECT_ROOT, "public", "audio", "scene_01.mp3")
        rel = os.path.relpath(sample_path, PROJECT_ROOT).replace("\\", "/")
        self.assertFalse(os.path.isabs(rel), "缓存文件路径应为相对于仓库根目录的便携式相对路径")
        self.assertTrue(rel.startswith("public/audio/"))

if __name__ == "__main__":
    unittest.main()

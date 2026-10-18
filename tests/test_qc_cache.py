#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_qc_cache.py
Comprehensive Test Suite for Visual QC, Asset Incremental Cache, and Watcher Sync
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.utils.visual_qc import (
    check_black_frame,
    check_aspect_ratio_compliance,
    check_subtitle_safe_area,
    audit_frames_array,
    calculate_luminance
)
from scripts.utils.asset_cache_manager import AssetCacheManager


class TestVisualQC(unittest.TestCase):
    def test_luminance_and_black_frame_detection(self):
        # 1. Pitch black frame (0, 0, 0)
        black_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        is_black, lum = check_black_frame(black_frame, threshold=10.0)
        self.assertTrue(is_black)
        self.assertAlmostEqual(lum, 0.0, places=1)

        # 2. Normal bright frame (200, 200, 200)
        bright_frame = np.full((100, 100, 3), 200, dtype=np.uint8)
        is_black, lum = check_black_frame(bright_frame, threshold=10.0)
        self.assertFalse(is_black)
        self.assertGreater(lum, 150.0)

    def test_aspect_ratio_compliance(self):
        # 16:9 Landscape
        ok, detected = check_aspect_ratio_compliance(1920, 1080, expected="16:9")
        self.assertTrue(ok)
        self.assertEqual(detected, "16:9")

        # 9:16 Portrait
        ok, detected = check_aspect_ratio_compliance(1080, 1920, expected="9:16")
        self.assertTrue(ok)
        self.assertEqual(detected, "9:16")

        # 1:1 Square
        ok, detected = check_aspect_ratio_compliance(1080, 1080, expected="1:1")
        self.assertTrue(ok)
        self.assertEqual(detected, "1:1")

        # Mismatch
        ok, detected = check_aspect_ratio_compliance(1920, 1080, expected="9:16")
        self.assertFalse(ok)

    def test_subtitle_safe_area_guards(self):
        # 1. 16:9 Desktop safe area: bottom 10% is danger zone
        safe_box_h = {"left": 200, "top": 850, "width": 800, "height": 80}
        ok, errors = check_subtitle_safe_area(safe_box_h, 1920, 1080, is_vertical=False)
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

        # Overflow bottom on 16:9 (top: 1020, bottom: 1070 > 1080 * 0.92 = 993)
        unsafe_box_h = {"left": 200, "top": 1020, "width": 800, "height": 50}
        ok, errors = check_subtitle_safe_area(unsafe_box_h, 1920, 1080, is_vertical=False)
        self.assertFalse(ok)
        self.assertTrue(any("danger zone" in e for e in errors))

        # 2. 9:16 Mobile safe area: bottom 18% is danger zone (1920 * 0.82 = 1574)
        safe_box_v = {"left": 80, "top": 1200, "width": 700, "height": 100}
        ok, errors = check_subtitle_safe_area(safe_box_v, 1080, 1920, is_vertical=True)
        self.assertTrue(ok)

        # Danger zone overlap (bottom: 1700 > 1574)
        unsafe_box_v = {"left": 80, "top": 1600, "width": 700, "height": 100}
        ok, errors = check_subtitle_safe_area(unsafe_box_v, 1080, 1920, is_vertical=True)
        self.assertFalse(ok)

    def test_audit_frames_array_pass_and_failure(self):
        # Clean frames (varying colors, 16:9)
        frames = [
            np.full((108, 192, 3), 50 + i * 20, dtype=np.uint8)
            for i in range(5)
        ]
        res = audit_frames_array(frames, expected_aspect="16:9")
        self.assertEqual(res["status"], "PASS")
        self.assertGreaterEqual(res["score"], 85.0)

        # Array with black frame in the middle
        frames_with_black = [
            np.full((108, 192, 3), 100, dtype=np.uint8),
            np.zeros((108, 192, 3), dtype=np.uint8), # Black frame
            np.full((108, 192, 3), 120, dtype=np.uint8),
        ]
        res_black = audit_frames_array(frames_with_black, expected_aspect="16:9")
        self.assertTrue(any("black/blank" in err for err in res_black["issues"]))


class TestAssetCacheManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="cache_test_")
        self.cache_mgr = AssetCacheManager(cache_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compute_cache_key_deterministic(self):
        params1 = {"template": "architecture_flow", "aspect": "16:9", "fps": 60}
        params2 = {"fps": 60, "aspect": "16:9", "template": "architecture_flow"} # Different key order
        key1 = AssetCacheManager.compute_cache_key("hyperframes", params1)
        key2 = AssetCacheManager.compute_cache_key("hyperframes", params2)
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)

    def test_store_and_retrieve_cached_asset(self):
        # Create a dummy source file
        dummy_src = os.path.join(self.test_dir, "dummy_broll.mp4")
        with open(dummy_src, "wb") as f:
            f.write(b"MOCK_MP4_HEADER_DATA_12345")

        params = {"template": "code_spotlight", "duration": 4.0}
        # First query: should be miss
        cached = self.cache_mgr.get_cached_asset("hyperframes", params)
        self.assertIsNone(cached)

        # Store in cache
        cached_path = self.cache_mgr.store_cached_asset("hyperframes", params, dummy_src)
        self.assertTrue(os.path.exists(cached_path))

        # Second query: should be hit
        hit_path = self.cache_mgr.get_cached_asset("hyperframes", params)
        self.assertIsNotNone(hit_path)
        self.assertEqual(hit_path, cached_path)

        # Check stats
        stats = self.cache_mgr.get_stats()
        self.assertEqual(stats["total_entries"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)

    def test_fetch_or_generate_workflow(self):
        target_out = os.path.join(self.test_dir, "output.mp4")
        params = {"scene": 1, "text": "Testing Cache"}

        generator_calls = 0
        def dummy_generator(dest_path: str) -> bool:
            nonlocal generator_calls
            generator_calls += 1
            with open(dest_path, "wb") as f:
                f.write(b"GENERATED_CONTENT")
            return True

        # Call 1: generator must be called
        ok1 = self.cache_mgr.fetch_or_generate("tts", params, dummy_generator, target_out)
        self.assertTrue(ok1)
        self.assertEqual(generator_calls, 1)

        # Call 2: should hit cache and NOT call generator
        if os.path.exists(target_out):
            os.remove(target_out)

        ok2 = self.cache_mgr.fetch_or_generate("tts", params, dummy_generator, target_out)
        self.assertTrue(ok2)
        self.assertEqual(generator_calls, 1) # Still 1! Generator was bypassed!
        self.assertTrue(os.path.exists(target_out))


if __name__ == "__main__":
    unittest.main()

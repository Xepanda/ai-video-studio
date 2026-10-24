#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audio_utils.py
Comprehensive test suite for:
1. Timeline state version snapshot & safety rollback engine (scripts/utils/snapshot_manager.py)
2. Industrial-grade EBU R128 loudness normalizer & fallback engine (scripts/utils/audio_normalizer.py)
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
import subprocess
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.utils.snapshot_manager import (
    create_snapshot,
    list_snapshots,
    rollback_snapshot,
    validate_timeline_file,
    validate_timeline_data,
    get_timeline_scenes_count,
)

from scripts.utils.audio_normalizer import (
    find_ffmpeg,
    measure_loudness,
    normalize_audio,
    normalize_voiceover,
    normalize_bgm,
    batch_normalize,
    fallback_normalize_audio,
)

try:
    import soundfile as sf
except ImportError:
    sf = None


class TestSnapshotManager(unittest.TestCase):
    """
    Tests for snapshot creation, listing, integrity validation, and safe rollback.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="timeline_test_")
        self.timeline_path = os.path.join(self.test_dir, "timeline.json")
        self.snapshot_dir = os.path.join(self.test_dir, ".snapshots")

        # Initial simulated timeline data with 3 scenes
        self.initial_data = {
            "project": "test_simulated_project",
            "theme": "linear-graphite",
            "fps": 30,
            "totalDurationInFrames": 180,
            "scenes": [
                {"id": "scene_01", "type": "MinimalHeadline", "text": "Intro Headline"},
                {"id": "scene_02", "type": "TweetEmbed", "text": "Tweet Content"},
                {"id": "scene_03", "type": "OutroCard", "text": "Call to action"}
            ]
        }
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validation_helpers(self):
        # Valid data
        self.assertTrue(validate_timeline_data(self.initial_data))
        self.assertTrue(validate_timeline_file(self.timeline_path))
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 3)

        # Invalid data
        self.assertFalse(validate_timeline_data({"foo": "bar"}))
        self.assertFalse(validate_timeline_data([]))
        self.assertFalse(validate_timeline_data({"scenes": "not_a_list"}))

    def test_create_snapshot_creates_file_and_backup(self):
        res = create_snapshot(
            timeline_path=self.timeline_path,
            label="pre_edit",
            snapshot_dir=self.snapshot_dir
        )

        # Snapshot file existence
        self.assertTrue(os.path.exists(res.snapshot_path))
        self.assertTrue(os.path.isfile(str(res)))
        self.assertEqual(res.scenes_count, 3)
        self.assertEqual(res.label, "pre_edit")

        # Backup file existence in timeline directory
        backup_path = os.path.join(self.test_dir, "timeline.backup.json")
        self.assertTrue(os.path.exists(backup_path))

        with open(res.snapshot_path, "r", encoding="utf-8") as f:
            snapshot_content = json.load(f)
        self.assertEqual(snapshot_content["scenes"], self.initial_data["scenes"])

    def test_list_snapshots(self):
        # Create first snapshot
        s1 = create_snapshot(
            timeline_path=self.timeline_path,
            label="v1",
            snapshot_dir=self.snapshot_dir
        )
        time.sleep(1.05)  # Ensure distinct timestamp seconds

        # Modify timeline to 4 scenes and create second snapshot
        self.initial_data["scenes"].append({"id": "scene_04", "type": "Extra"})
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f, indent=2)

        s2 = create_snapshot(
            timeline_path=self.timeline_path,
            label="v2",
            snapshot_dir=self.snapshot_dir
        )

        snapshots = list_snapshots(snapshot_dir=self.snapshot_dir)
        self.assertEqual(len(snapshots), 2)

        # Newest snapshot should be first
        self.assertEqual(snapshots[0]["label"], "v2")
        self.assertEqual(snapshots[0]["scenes_count"], 4)
        self.assertEqual(snapshots[1]["label"], "v1")
        self.assertEqual(snapshots[1]["scenes_count"], 3)

    def test_rollback_default_from_backup(self):
        create_snapshot(
            timeline_path=self.timeline_path,
            label="safe_state",
            snapshot_dir=self.snapshot_dir
        )

        # Simulate catastrophic timeline edit (truncated to 1 scene)
        corrupted_data = {"project": "test", "scenes": [{"id": "scene_01"}]}
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(corrupted_data, f)
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 1)

        # Rollback with default arguments (restores from backup)
        ok = rollback_snapshot(
            snapshot_id_or_path=None,
            timeline_path=self.timeline_path,
            snapshot_dir=self.snapshot_dir
        )
        self.assertTrue(ok)
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 3)

    def test_rollback_to_specific_snapshot(self):
        # Snapshot 1: 3 scenes
        s1 = create_snapshot(
            timeline_path=self.timeline_path,
            label="state_3_scenes",
            snapshot_dir=self.snapshot_dir
        )
        time.sleep(1.05)

        # Update to 5 scenes and take Snapshot 2
        five_scenes_data = dict(self.initial_data)
        five_scenes_data["scenes"] = [{"id": f"sc_{i}"} for i in range(5)]
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(five_scenes_data, f)

        s2 = create_snapshot(
            timeline_path=self.timeline_path,
            label="state_5_scenes",
            snapshot_dir=self.snapshot_dir
        )

        # Clear to 0 scenes
        empty_data = {"project": "test", "scenes": []}
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump(empty_data, f)
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 0)

        # Rollback specifically to Snapshot 1 by ID
        ok = rollback_snapshot(
            snapshot_id_or_path=s1.snapshot_path,
            timeline_path=self.timeline_path,
            snapshot_dir=self.snapshot_dir
        )
        self.assertTrue(ok)
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 3)

    def test_rollback_rejects_corrupted_snapshot(self):
        corrupt_file = os.path.join(self.test_dir, "corrupt_snapshot.json")
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ...")

        # Attempt to rollback to the corrupted file
        ok = rollback_snapshot(
            snapshot_id_or_path=corrupt_file,
            timeline_path=self.timeline_path,
            snapshot_dir=self.snapshot_dir
        )
        self.assertFalse(ok)
        # Original timeline must remain untouched with 3 scenes
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 3)

    def test_snapshot_cli(self):
        script_path = os.path.join(PROJECT_ROOT, "scripts", "utils", "snapshot_manager.py")

        # Test CLI create
        cmd_create = [
            sys.executable, script_path,
            "create",
            "--timeline", self.timeline_path,
            "--dir", self.snapshot_dir,
            "--label", "cli_test"
        ]
        p_create = subprocess.run(cmd_create, capture_output=True, text=True)
        self.assertEqual(p_create.returncode, 0, f"CLI create failed: {p_create.stderr}")

        # Test CLI list
        cmd_list = [
            sys.executable, script_path,
            "list",
            "--dir", self.snapshot_dir
        ]
        p_list = subprocess.run(cmd_list, capture_output=True, text=True)
        self.assertEqual(p_list.returncode, 0)
        self.assertIn("cli_test", p_list.stdout)

        # Modify timeline
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            json.dump({"project": "test", "scenes": []}, f)

        # Test CLI rollback
        cmd_rollback = [
            sys.executable, script_path,
            "rollback",
            "--timeline", self.timeline_path,
            "--dir", self.snapshot_dir
        ]
        p_rollback = subprocess.run(cmd_rollback, capture_output=True, text=True)
        self.assertEqual(p_rollback.returncode, 0, f"CLI rollback failed: {p_rollback.stderr}")
        self.assertEqual(get_timeline_scenes_count(self.timeline_path), 3)


class TestAudioNormalizer(unittest.TestCase):
    """
    Tests for audio loudness normalization, parameter checking,
    voice/bgm standard curves, batch processing, and pure-python fallback.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="audio_test_")
        self.sr = 24000

        # Create a synthetic voiceover audio tone (1.0s, fundamental + harmonics, low volume)
        t = np.linspace(0, 1.0, self.sr, endpoint=False)
        self.quiet_voice = 0.08 * (
            np.sin(2 * np.pi * 220 * t) +
            0.5 * np.sin(2 * np.pi * 440 * t) +
            0.3 * np.sin(2 * np.pi * 2500 * t)
        )
        self.voice_wav = os.path.join(self.test_dir, "test_voice.wav")
        sf.write(self.voice_wav, self.quiet_voice, self.sr)

        # Create a synthetic BGM audio track (1.0s, high dynamic range)
        bgm_signal = 0.25 * np.sin(2 * np.pi * 150 * t) + 0.1 * np.sin(2 * np.pi * 800 * t)
        self.bgm_wav = os.path.join(self.test_dir, "test_bgm.wav")
        sf.write(self.bgm_wav, bgm_signal, self.sr)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ffmpeg_finder(self):
        ffmpeg_bin = find_ffmpeg()
        if not ffmpeg_bin:
            self.skipTest("未检测到 FFmpeg (系统 PATH / Remotion 内置均无); CI 环境已安装")
        self.assertTrue(os.path.exists(ffmpeg_bin))

    def test_parameter_validation_missing_file(self):
        res = normalize_voiceover("non_existent_audio_xyz.wav", "out.wav")
        self.assertFalse(res)

    def test_normalize_voiceover(self):
        out_wav = os.path.join(self.test_dir, "out_voice_norm.wav")
        ok = normalize_voiceover(self.voice_wav, out_wav, target_lufs=-16.0)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(out_wav))
        self.assertGreater(os.path.getsize(out_wav), 0)

        data_out, sr_out = sf.read(out_wav)
        self.assertEqual(sr_out, self.sr)
        peak_linear = float(np.max(np.abs(data_out)))
        # -1.0 dBTP ceiling corresponds to ~0.891 linear. Allow margin up to 0.95.
        self.assertLessEqual(peak_linear, 0.96)
        self.assertGreater(peak_linear, 0.20)

    def test_normalize_bgm(self):
        out_bgm = os.path.join(self.test_dir, "out_bgm_norm.wav")
        ok = normalize_bgm(self.bgm_wav, out_bgm, target_lufs=-28.0)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(out_bgm))

        data_bgm, _ = sf.read(out_bgm)
        rms_bgm = float(np.sqrt(np.mean(data_bgm ** 2)))
        rms_bgm_db = 20 * np.log10(max(rms_bgm, 1e-8))

        # -28 LUFS BGM should have RMS substantially lower than dialogue (approx -24 to -30 dBFS)
        self.assertLess(rms_bgm_db, -20.0)

    def test_batch_normalize(self):
        batch_in = os.path.join(self.test_dir, "batch_in")
        batch_out = os.path.join(self.test_dir, "batch_out")
        os.makedirs(batch_in, exist_ok=True)

        # Create multiple audio clips
        for i in range(3):
            sf.write(os.path.join(batch_in, f"scene_0{i+1}.wav"), self.quiet_voice, self.sr)

        processed = batch_normalize(
            audio_dir=batch_in,
            target_lufs=-16.0,
            mode="voice",
            output_dir=batch_out
        )
        self.assertEqual(len(processed), 3)
        for p in processed:
            self.assertTrue(os.path.exists(p))
            self.assertGreater(os.path.getsize(p), 0)

    def test_fallback_normalization_logic(self):
        out_fallback = os.path.join(self.test_dir, "out_fallback.wav")
        # Explicitly force fallback pure-Python soundfile normalization
        ok = fallback_normalize_audio(
            self.voice_wav,
            out_fallback,
            target_lufs=-16.0,
            target_tp=-1.0
        )
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(out_fallback))

        data_fb, _ = sf.read(out_fallback)
        peak_fb = float(np.max(np.abs(data_fb)))
        limit_linear = 10.0 ** (-1.0 / 20.0)
        self.assertLessEqual(peak_fb, limit_linear + 1e-4)

        # Also test normalize_voiceover with force_fallback flag
        out_voice_fb = os.path.join(self.test_dir, "out_voice_fallback.wav")
        ok_voice_fb = normalize_voiceover(self.voice_wav, out_voice_fb, force_fallback=True)
        self.assertTrue(ok_voice_fb)
        self.assertTrue(os.path.exists(out_voice_fb))

    def test_audio_normalizer_cli(self):
        script_path = os.path.join(PROJECT_ROOT, "scripts", "utils", "audio_normalizer.py")
        out_cli = os.path.join(self.test_dir, "out_cli.wav")

        # Test CLI single file voice mode
        cmd = [
            sys.executable, script_path,
            "--input", self.voice_wav,
            "--output", out_cli,
            "--mode", "voice",
            "--target-lufs", "-16.0"
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, f"CLI single voice failed: {p.stderr}")
        self.assertTrue(os.path.exists(out_cli))

        # Test CLI BGM mode
        out_bgm_cli = os.path.join(self.test_dir, "out_bgm_cli.wav")
        cmd_bgm = [
            sys.executable, script_path,
            "--input", self.bgm_wav,
            "--output", out_bgm_cli,
            "--mode", "bgm",
            "--target-lufs", "-28.0"
        ]
        p_bgm = subprocess.run(cmd_bgm, capture_output=True, text=True)
        self.assertEqual(p_bgm.returncode, 0, f"CLI BGM failed: {p_bgm.stderr}")
        self.assertTrue(os.path.exists(out_bgm_cli))

        # Test CLI batch directory
        batch_dir = os.path.join(self.test_dir, "cli_batch")
        os.makedirs(batch_dir, exist_ok=True)
        shutil.copy2(self.voice_wav, os.path.join(batch_dir, "clip1.wav"))
        shutil.copy2(self.voice_wav, os.path.join(batch_dir, "clip2.wav"))

        cmd_batch = [
            sys.executable, script_path,
            "--input", batch_dir,
            "--mode", "voice"
        ]
        p_batch = subprocess.run(cmd_batch, capture_output=True, text=True)
        self.assertEqual(p_batch.returncode, 0, f"CLI batch failed: {p_batch.stderr}")


if __name__ == "__main__":
    unittest.main()

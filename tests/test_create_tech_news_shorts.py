#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_create_tech_news_shorts.py
Comprehensive unit tests for scripts/create_tech_news_shorts.py:
1. CLI argument parsing
2. Topic slugification (pinyin, English, mixed, special characters)
3. Duration estimation (seconds, frames, punctuation handling)
4. Preset generation (codex_day6 exact 8-scene structure)
5. Generic topic generation & Schema conformity
"""

import os
import sys
import json
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.create_tech_news_shorts import (
    slugify,
    estimate_duration_seconds,
    estimate_duration_frames,
    build_codex_day6_preset,
    generate_tech_news_script,
    parse_args,
    save_script_to_file,
    validate_script_schema,
)


class TestSlugify(unittest.TestCase):
    """测试主题 Slug 转化与清理逻辑"""

    def test_slugify_english(self):
        self.assertEqual(slugify("Codex Day 6 Reset Demo 2026"), "codex_day_6_reset_demo_2026")

    def test_slugify_chinese_pinyin(self):
        res = slugify("OpenAI Codex 第六天更新")
        self.assertTrue(res.startswith("openai_codex_"))
        self.assertNotIn(" ", res)
        self.assertNotIn("-", res)

    def test_slugify_mixed_and_special_chars(self):
        res = slugify("AI 突破：DeepSeek 惊艳全网!! --- 2026")
        self.assertTrue(len(res) > 0)
        self.assertNotIn("__", res)
        self.assertNotIn(":", res)
        self.assertNotIn("!", res)

    def test_slugify_fallback_for_empty(self):
        res = slugify("   ---   ")
        self.assertTrue(len(res) > 0)
        self.assertTrue(res.startswith("project_") or res.startswith("shorts_"))


class TestDurationEstimation(unittest.TestCase):
    """测试旁白与分镜时长估算机制"""

    def test_short_sentence_duration(self):
        text = "没有新功能，只有重置！"
        sec = estimate_duration_seconds(text, chars_per_sec=4.5)
        self.assertGreaterEqual(sec, 2.0)
        self.assertLessEqual(sec, 6.0)

    def test_frames_calculation_at_30fps(self):
        text = "二选一规则：要么直接刷新额度，要么给重置卡。"
        frames = estimate_duration_frames(text, fps=30, chars_per_sec=4.5)
        self.assertGreaterEqual(frames, 60)
        self.assertLessEqual(frames, 300)

    def test_empty_text_clamping(self):
        frames = estimate_duration_frames("", fps=30)
        self.assertEqual(frames, 60)  # default min 2.0s * 30fps = 60 frames


class TestCliArgumentParsing(unittest.TestCase):
    """测试 CLI 命令行参数解析与默认值"""

    def test_default_cli_args(self):
        args = parse_args(["--topic", "OpenAI Codex 第六天更新：没有新功能，只有重置"])
        self.assertEqual(args.theme, "linear-graphite")
        self.assertEqual(args.voice, "4444")
        self.assertEqual(args.engine, "chattts")
        self.assertTrue(len(args.project) > 0)
        self.assertTrue(args.output.endswith(f"{args.project}.json"))

    def test_explicit_cli_args(self):
        args = parse_args([
            "--topic", "Custom Topic",
            "--project", "my_custom_project",
            "--theme", "obsidian-minimal",
            "--voice", "cosyvoice_custom",
            "--engine", "siliconflow",
            "--output", "content/scripts/my_custom.json",
            "--preset", "codex_day6"
        ])
        self.assertEqual(args.topic, "Custom Topic")
        self.assertEqual(args.project, "my_custom_project")
        self.assertEqual(args.theme, "obsidian-minimal")
        self.assertEqual(args.voice, "cosyvoice_custom")
        self.assertEqual(args.engine, "siliconflow")
        self.assertEqual(args.output, "content/scripts/my_custom.json")
        self.assertEqual(args.preset, "codex_day6")


class TestCodexDay6Preset(unittest.TestCase):
    """测试 Codex Day 6 参考示范样片内置预设的精准结构契约"""

    def setUp(self):
        self.script = build_codex_day6_preset(
            project="codex_day6_reset_demo",
            theme="linear-graphite",
            voice="4444",
            engine="chattts"
        )

    def test_top_level_contract(self):
        self.assertEqual(self.script["project"], "codex_day6_reset_demo")
        self.assertEqual(self.script["theme"], "linear-graphite")
        self.assertEqual(self.script["voice"], "4444")
        self.assertEqual(self.script["engine"], "chattts")
        self.assertEqual(self.script["fps"], 30)
        self.assertEqual(self.script["bgm"], "bgm_cyber_ambient.wav")
        self.assertEqual(self.script["bgmVolume"], 0.035)
        self.assertEqual(self.script["bgmDuckRatio"], 0.20)
        self.assertEqual(self.script["voiceVolume"], 1.0)
        self.assertEqual(len(self.script["scenes"]), 8)

    def test_eight_scenes_exact_flow(self):
        scenes = self.script["scenes"]

        # Scene 1: MinimalHeadline (inverted: false)
        self.assertEqual(scenes[0]["id"], "scene_01")
        self.assertEqual(scenes[0]["type"], "MinimalHeadline")
        self.assertFalse(scenes[0]["inverted"])
        self.assertEqual(scenes[0]["category"], "CODEX DAY 6")
        self.assertIn("没有新功能", scenes[0]["highlightWords"])
        self.assertIn("重置", scenes[0]["highlightWords"])
        self.assertIn("没有新功能，只有重置！", scenes[0]["text"])

        # Scene 2: TweetEmbed
        self.assertEqual(scenes[1]["id"], "scene_02")
        self.assertEqual(scenes[1]["type"], "TweetEmbed")
        tweet1 = scenes[1]["tweet"]
        self.assertEqual(tweet1["authorName"], "Tibo")
        self.assertEqual(tweet1["authorHandle"], "@tibo_maker")
        self.assertTrue(tweet1["isVerified"])
        self.assertEqual(tweet1["timeAgo"], "14h")
        self.assertIn("Day 6: Reset", tweet1["content"])
        self.assertIn("Reset", tweet1["highlightWords"])
        self.assertEqual(tweet1["metrics"]["replies"], "128")
        self.assertEqual(tweet1["metrics"]["views"], "150K")

        # Scene 3: BinaryBento
        self.assertEqual(scenes[2]["id"], "scene_03")
        self.assertEqual(scenes[2]["type"], "BinaryBento")
        bento = scenes[2]["binaryBento"]
        self.assertEqual(bento["title"], "配额重置机制")
        self.assertEqual(bento["subtitle"], "二选一规则")
        self.assertEqual(bento["dividerText"], "或")
        self.assertEqual(bento["leftCard"]["title"], "消耗每日配额")
        self.assertEqual(bento["leftCard"]["blocksTotal"], 5)
        self.assertEqual(bento["leftCard"]["blocksActive"], 3)
        self.assertEqual(bento["rightCard"]["title"], "使用月度重置卡")
        self.assertEqual(bento["rightCard"]["pill"], "重置卡")

        # Scene 4: MinimalHeadline (inverted: true)
        self.assertEqual(scenes[3]["id"], "scene_04")
        self.assertEqual(scenes[3]["type"], "MinimalHeadline")
        self.assertTrue(scenes[3]["inverted"])
        self.assertEqual(scenes[3]["category"], "UNCONFIRMED")
        self.assertIn("没细说", scenes[3]["highlightWords"])

        # Scene 5: MinimalHeadline (inverted: false)
        self.assertEqual(scenes[4]["id"], "scene_05")
        self.assertEqual(scenes[4]["type"], "MinimalHeadline")
        self.assertFalse(scenes[4]["inverted"])
        self.assertEqual(scenes[4]["category"], "TIMELINE")
        self.assertIn("第二天", scenes[4]["highlightWords"])

        # Scene 6: TweetEmbed
        self.assertEqual(scenes[5]["id"], "scene_06")
        self.assertEqual(scenes[5]["type"], "TweetEmbed")
        tweet2 = scenes[5]["tweet"]
        self.assertEqual(tweet2["authorName"], "Tibo")
        self.assertEqual(tweet2["timeAgo"], "1d")
        self.assertIn("Saturday", tweet2["highlightWords"])
        self.assertEqual(tweet2["metrics"]["likes"], "1.8K")

        # Scene 7: MinimalHeadline (inverted: false)
        self.assertEqual(scenes[6]["id"], "scene_07")
        self.assertEqual(scenes[6]["type"], "MinimalHeadline")
        self.assertFalse(scenes[6]["inverted"])
        self.assertEqual(scenes[6]["category"], "INSIGHT")

        # Scene 8: MinimalHeadline (inverted: true)
        self.assertEqual(scenes[7]["id"], "scene_08")
        self.assertEqual(scenes[7]["type"], "MinimalHeadline")
        self.assertTrue(scenes[7]["inverted"])
        self.assertEqual(scenes[7]["category"], "STAY TUNED")
        self.assertIn("明天接着看", scenes[7]["highlightWords"])


class TestGenericGenerationAndSchema(unittest.TestCase):
    """测试通用主题生成与 Schema 校验机制"""

    def test_generic_topic_generation(self):
        topic = "Claude 3.7 Sonnet 混合推理新特性重磅发布"
        script = generate_tech_news_script(topic=topic, project="claude_37_sonnet")
        self.assertEqual(script["project"], "claude_37_sonnet")
        self.assertGreaterEqual(len(script["scenes"]), 5)
        # 验证包含至少 TweetEmbed 和 BinaryBento 和 MinimalHeadline
        scene_types = [s.get("type") for s in script["scenes"]]
        self.assertIn("MinimalHeadline", scene_types)
        self.assertIn("TweetEmbed", scene_types)
        self.assertIn("BinaryBento", scene_types)

    def test_validate_script_schema_valid(self):
        script = build_codex_day6_preset()
        errors, warnings = validate_script_schema(script)
        self.assertEqual(len(errors), 0, f"Schema validation errors found: {errors}")

    def test_validate_script_schema_detects_errors(self):
        invalid_script = {
            "project": "invalid_project",
            # missing scenes
        }
        errors, warnings = validate_script_schema(invalid_script)
        self.assertTrue(len(errors) > 0)

        # Invalid scene missing required fields
        invalid_scene_script = {
            "project": "test_err",
            "scenes": [
                {"id": "scene_01", "type": "TweetEmbed"} # missing text and tweet
            ]
        }
        errors2, warnings2 = validate_script_schema(invalid_scene_script)
        self.assertTrue(len(errors2) > 0)

    def test_file_persistence(self):
        script = build_codex_day6_preset(project="temp_test_project")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_script_to_file(script, temp_path)
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, "r", encoding="utf-8") as rf:
                loaded = json.load(rf)
            self.assertEqual(loaded["project"], "temp_test_project")
            self.assertEqual(len(loaded["scenes"]), 8)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()

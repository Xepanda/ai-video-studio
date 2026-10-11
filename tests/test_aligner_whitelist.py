#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_aligner_whitelist.py
Unit tests verifying that sensevoice_aligner.py metadata inheritance includes
all required shorts fields: tweet, binaryBento, inverted, category,
blocksActive, blocksTotal, highlightWords.
"""

import unittest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestAlignerMetadataWhitelist(unittest.TestCase):

    def test_whitelist_fields_present_in_aligner_source(self):
        """Ensure sensevoice_aligner.py source code contains all required whitelist fields."""
        aligner_path = os.path.join(PROJECT_ROOT, "scripts", "sensevoice_aligner.py")
        with open(aligner_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_fields = [
            "tag",
            "dateText",
            "date",
            "desc",
            "tweet",
            "binaryBento",
            "inverted",
            "category",
            "blocksActive",
            "blocksTotal",
            "highlightWords",
        ]

        for field in required_fields:
            self.assertIn(
                f'"{field}"',
                content,
                f"Field '{field}' must be present in sensevoice_aligner.py metadata whitelist",
            )

    def test_mock_scene_metadata_inheritance(self):
        """Simulate metadata inheritance logic from sensevoice_aligner.py."""
        script_meta = {
            "scene_01": {
                "id": "scene_01",
                "type": "TweetEmbed",
                "tag": "TECH PULSE",
                "dateText": "2026.10.11",
                "date": "2026-10-11",
                "desc": "极简短视频重置说明",
                "tweet": {
                    "authorName": "Tibo",
                    "content": "Day 6: Reset"
                },
                "binaryBento": {
                    "leftCard": {"title": "A"},
                    "rightCard": {"title": "B"}
                },
                "inverted": True,
                "category": "BREAKING",
                "blocksActive": 3,
                "blocksTotal": 5,
                "highlightWords": ["Reset", "Day 6"]
            }
        }

        scene_data = {
            "id": "scene_01",
            "type": "ExplainerWhiteboard",
            "words": []
        }

        scene_id = "scene_01"
        meta = script_meta[scene_id]

        # Mirror sensevoice_aligner.py inheritance loop
        whitelist = [
            "title", "badge", "subtitle", "cards", "bulletPoints",
            "codeSnippet", "codeLang", "codeTitle", "type",
            "topologyNodes", "topologyLinks", "metrics", "theme", "voiceVolume",
            "heroImage", "heroVideo", "videoPath", "cameraMotion", "highlights", "pill", "sceneIndex", "totalScenes",
            "tag", "dateText", "date", "desc",
            "tweet", "binaryBento", "inverted", "category", "blocksActive", "blocksTotal", "highlightWords"
        ]
        for field in whitelist:
            if field in meta:
                scene_data[field] = meta[field]

        self.assertEqual(scene_data["type"], "TweetEmbed")
        self.assertEqual(scene_data["tag"], "TECH PULSE")
        self.assertEqual(scene_data["dateText"], "2026.10.11")
        self.assertEqual(scene_data["date"], "2026-10-11")
        self.assertEqual(scene_data["desc"], "极简短视频重置说明")
        self.assertEqual(scene_data["tweet"]["authorName"], "Tibo")
        self.assertEqual(scene_data["binaryBento"]["leftCard"]["title"], "A")
        self.assertTrue(scene_data["inverted"])
        self.assertEqual(scene_data["category"], "BREAKING")
        self.assertEqual(scene_data["blocksActive"], 3)
        self.assertEqual(scene_data["blocksTotal"], 5)
        self.assertEqual(scene_data["highlightWords"], ["Reset", "Day 6"])


if __name__ == "__main__":
    unittest.main()

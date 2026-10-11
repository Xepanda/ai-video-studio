import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.timeline_to_hyperframes import (
    convert_timeline_to_hyperframes,
    render_hyperframes_html,
)


class TestTimelineToHyperframes(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "test_hf_project"

        self.sample_timeline = {
            "project": "sample_tech_shorts",
            "theme": "linear-graphite",
            "fps": 30,
            "totalDurationInFrames": 120,
            "scenes": [
                {
                    "id": "scene_01",
                    "type": "MinimalHeadline",
                    "startFrame": 0,
                    "durationInFrames": 60,
                    "audioPath": "audio/scene_01.wav",
                    "text": "没有新功能，只有重置！",
                    "title": "没有新功能，只有重置！",
                    "inverted": False,
                    "category": "CODEX RESET",
                    "highlightWords": ["没有新功能", "重置"],
                    "words": [
                        {
                            "text": "没有新功能",
                            "startMs": 200,
                            "endMs": 1000,
                            "startFrame": 6,
                            "endFrame": 30,
                        },
                        {
                            "text": "只有重置",
                            "startMs": 1050,
                            "endMs": 1800,
                            "startFrame": 31,
                            "endFrame": 54,
                        },
                    ],
                },
                {
                    "id": "scene_02",
                    "type": "TweetEmbed",
                    "startFrame": 60,
                    "durationInFrames": 60,
                    "audioPath": "audio/scene_02.wav",
                    "text": "官方发推确认，这是一次底层重构。",
                    "tweet": {
                        "authorName": "Tibo",
                        "authorHandle": "@tibo_maker",
                        "content": "Day 6: No new features, complete reset.",
                        "metrics": {
                            "replies": "1.2k",
                            "reposts": "3.4k",
                            "likes": "18.5k",
                        },
                    },
                    "words": [
                        {
                            "text": "官方发推确认",
                            "startMs": 100,
                            "endMs": 900,
                            "startFrame": 3,
                            "endFrame": 27,
                        }
                    ],
                },
            ],
        }

        self.timeline_file = Path(self.test_dir) / "timeline.json"
        with open(self.timeline_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_timeline, f, ensure_ascii=False, indent=2)

        # Create dummy audio files
        audio_dir = Path(self.test_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        (audio_dir / "scene_01.wav").write_bytes(b"RIFFdummywav1")
        (audio_dir / "scene_02.wav").write_bytes(b"RIFFdummywav2")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_render_hyperframes_html_structure(self):
        html = render_hyperframes_html(self.sample_timeline, resolution="portrait")
        
        # HyperFrames Core Contracts
        self.assertIn('data-composition-id="main"', html)
        self.assertIn('data-width="1080"', html)
        self.assertIn('data-height="1920"', html)
        self.assertIn('data-duration="4.0"', html) # 120 / 30 = 4.0s
        self.assertIn('class="clip scene-clip"', html)
        self.assertIn('window.__timelines["main"] = tl;', html)
        self.assertIn('gsap.timeline({ paused: true })', html)
        self.assertIn('tl.seek(0);', html)

        # Audio elements
        self.assertIn('<audio id="voice_scene_01"', html)
        self.assertIn('data-start="0.0"', html)
        self.assertIn('data-duration="2.0"', html)
        self.assertIn('<audio id="voice_scene_02"', html)
        self.assertIn('data-start="2.0"', html)

        # Visual Components
        self.assertIn("CODEX RESET", html)
        self.assertIn("没有新功能", html)
        self.assertIn("Tibo", html)
        self.assertIn("@tibo_maker", html)

        # Subtitles safe margin
        self.assertIn("bottom: 220px", html)

    def test_convert_timeline_to_hyperframes_files(self):
        res = convert_timeline_to_hyperframes(
            timeline_path=str(self.timeline_file),
            out_dir=str(self.output_dir),
            resolution="portrait",
        )

        self.assertTrue(res["success"])
        self.assertTrue((self.output_dir / "index.html").exists())
        self.assertTrue((self.output_dir / "hyperframes.json").exists())
        self.assertTrue((self.output_dir / "meta.json").exists())
        self.assertTrue((self.output_dir / "assets" / "audio" / "scene_01.wav").exists())
        self.assertTrue((self.output_dir / "assets" / "audio" / "scene_02.wav").exists())


if __name__ == "__main__":
    unittest.main()

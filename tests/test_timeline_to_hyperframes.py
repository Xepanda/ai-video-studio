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
    build_hyperframes_project,
    convert_timeline_to_hyperframes,
    generate_hyperframes_css,
    generate_scene_html,
    render_broll_clip,
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

        # Subtitles safe margin and exit transition
        self.assertIn("bottom: 220px", html)
        self.assertIn('.scene-subtitles", { opacity: 0', html)

    def test_binary_bento_and_inverted_rendering(self):
        bento_timeline = {
            "fps": 30,
            "totalDurationInFrames": 90,
            "scenes": [
                {
                    "id": "scene_bento",
                    "type": "BinaryBento",
                    "startFrame": 0,
                    "durationInFrames": 45,
                    "binaryBento": {
                        "leftCard": {"title": "方案 A", "desc": "旧版架构", "tag": "V1"},
                        "rightCard": {"title": "方案 B", "desc": "极简重构", "tag": "V2"},
                        "blocksActive": 3,
                        "blocksTotal": 6,
                    },
                },
                {
                    "id": "scene_inv",
                    "type": "MinimalHeadline",
                    "startFrame": 45,
                    "durationInFrames": 45,
                    "title": "震撼反相！",
                    "inverted": True,
                    "category": "BREAKING",
                },
            ],
        }
        html = render_hyperframes_html(bento_timeline, resolution="portrait")
        self.assertIn("bento-card-wrapper", html)
        self.assertIn("方案 A", html)
        self.assertIn("方案 B", html)
        self.assertIn("bento-vs-pill", html)
        self.assertIn("progress-block active", html)
        self.assertIn("inverted-card", html)
        self.assertIn("BREAKING", html)

    def test_special_characters_and_safe_highlights(self):
        special_timeline = {
            "fps": 30,
            "totalDurationInFrames": 60,
            "scenes": [
                {
                    "id": "scene_special",
                    "type": "MinimalHeadline",
                    "startFrame": 0,
                    "durationInFrames": 60,
                    "title": "OpenAI & Apple: <Next Gen> Vision!",
                    "highlightWords": ["OpenAI & Apple", "<Next Gen>"],
                },
                {
                    "id": "scene_tweet_special",
                    "type": "TweetEmbed",
                    "startFrame": 0,
                    "durationInFrames": 60,
                    "tweet": {
                        "authorName": "<Dev & Hacker>",
                        "authorHandle": "@dev_hacker",
                        "content": "Testing \"quotes\" & <tags>",
                        "metrics": {"replies": "100", "reposts": "200", "likes": "300"},
                    },
                },
            ],
        }
        html = render_hyperframes_html(special_timeline, resolution="portrait")
        # Ensure raw < and > are never injected into unescaped DOM text
        self.assertNotIn("<span><Dev", html)
        self.assertIn("&lt;Dev &amp; Hacker&gt;", html)
        self.assertTrue("&lt;Next Gen&gt;" in html or "&amp;lt;Next Gen&amp;gt;" in html)
        self.assertIn("headline-capsule", html)

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

    def test_render_broll_clip_markup(self):
        # 1. Test PIP mode
        pip_scene = {
            "id": "scene_pip",
            "type": "VideoBroll",
            "mode": "pip",
            "footage": "/path/to/raw_cut_720p.mp4",
            "title": "底层大模型重置架构",
            "highlightWords": ["大模型", "重置"],
            "startFrame": 30,
            "durationInFrames": 60,
            "fps": 30,
        }
        pip_html = render_broll_clip(pip_scene, "scene_pip")
        self.assertIn("content-card", pip_html)
        self.assertIn("broll-card", pip_html)
        self.assertIn("pip-frame", pip_html)
        self.assertIn('src="assets/footage/raw_cut_720p.mp4"', pip_html)
        self.assertIn('class="broll-clip"', pip_html)
        self.assertIn("autoplay", pip_html)
        self.assertIn("muted", pip_html)
        self.assertIn("playsinline", pip_html)
        self.assertIn("loop", pip_html)
        self.assertIn('data-in="1.0"', pip_html)
        self.assertIn('data-out="3.0"', pip_html)
        self.assertIn("broll-badge", pip_html)
        self.assertIn("大模型", pip_html)
        self.assertIn("headline-capsule", pip_html)

        # 2. Test Fullscreen mode
        fs_scene = {
            "id": "scene_fs",
            "type": "VideoBroll",
            "mode": "fullscreen",
            "footage": "assets/footage/bg_stream.mp4",
            "title": "全屏背景演示",
            "startFrame": 0,
            "durationInFrames": 90,
            "fps": 30,
        }
        fs_html = render_broll_clip(fs_scene, "scene_fs")
        self.assertIn("fullscreen-broll", fs_html)
        self.assertIn("broll-overlay", fs_html)
        self.assertIn('src="assets/footage/bg_stream.mp4"', fs_html)

    def test_broll_scene_dispatch(self):
        # VideoBroll
        scene_vb = {"type": "VideoBroll", "footage": "clip.mp4"}
        html_vb = generate_scene_html(scene_vb, "s1")
        self.assertIn("broll-card", html_vb)

        # VideoClip
        scene_vc = {"type": "VideoClip", "footage": "clip2.mp4"}
        html_vc = generate_scene_html(scene_vc, "s2")
        self.assertIn("broll-card", html_vc)

        # Broll
        scene_br = {"type": "Broll", "video": "clip3.mp4"}
        html_br = generate_scene_html(scene_br, "s3")
        self.assertIn("broll-card", html_br)

        # Footage presence without type
        scene_ft = {"footage": "clip4.mp4"}
        html_ft = generate_scene_html(scene_ft, "s4")
        self.assertIn("broll-card", html_ft)

        # MinimalHeadline fallback
        scene_hl = {"type": "MinimalHeadline", "title": "Headline Test"}
        html_hl = generate_scene_html(scene_hl, "s5")
        self.assertIn("headline-card", html_hl)

        # TweetEmbed
        scene_tw = {"type": "TweetEmbed", "tweet": {"authorName": "Tester", "content": "Hello"}}
        html_tw = generate_scene_html(scene_tw, "s6")
        self.assertIn("tweet-card", html_tw)

    def test_build_hyperframes_project_with_footage(self):
        # Create a dummy footage file in test_dir
        footage_src = Path(self.test_dir) / "source_broll.mp4"
        footage_src.write_bytes(b"dummy mp4 footage data")

        timeline_with_broll = {
            "project": "broll_project",
            "fps": 30,
            "totalDurationInFrames": 60,
            "scenes": [
                {
                    "id": "scene_broll_01",
                    "type": "VideoBroll",
                    "mode": "pip",
                    "startFrame": 0,
                    "durationInFrames": 60,
                    "footage": str(footage_src),
                    "title": "B-Roll Showcase",
                }
            ],
        }

        timeline_path = Path(self.test_dir) / "timeline_broll.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline_with_broll, f)

        out_broll_dir = Path(self.test_dir) / "hf_broll_out"
        res = build_hyperframes_project(
            timeline_path=str(timeline_path),
            out_dir=str(out_broll_dir),
            resolution="portrait",
        )

        self.assertTrue(res["success"])
        copied_footage = out_broll_dir / "assets" / "footage" / "source_broll.mp4"
        self.assertTrue(copied_footage.exists())
        self.assertEqual(copied_footage.read_bytes(), b"dummy mp4 footage data")

        index_html = (out_broll_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("assets/footage/source_broll.mp4", index_html)
        self.assertIn("broll-clip", index_html)
        self.assertIn("pip-frame", index_html)
        self.assertIn('data-in="0.0"', index_html)
        self.assertIn('data-out="2.0"', index_html)

    def test_generate_hyperframes_css_classes(self):
        css = generate_hyperframes_css("portrait")
        self.assertIn(".broll-card", css)
        self.assertIn(".broll-clip", css)
        self.assertIn(".pip-frame", css)
        self.assertIn(".fullscreen-broll", css)
        self.assertIn(".broll-overlay", css)
        self.assertIn(".broll-badge", css)


if __name__ == "__main__":
    unittest.main()


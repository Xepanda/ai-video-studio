#!/usr/bin/env python3
"""
Unit tests for HyperFrames Automation Engine (hf_builder.py).
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.hf_builder import (
    _deep_merge,
    build_broll,
    create_clip,
    list_templates,
    parse_args,
    render_clip,
)


class TestHyperFramesBuilder(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "test_clip"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_list_templates(self):
        """Verifies that templates are discovered properly."""
        templates = list_templates()
        self.assertIn("architecture_flow", templates)
        self.assertIn("code_spotlight", templates)

    def test_deep_merge(self):
        """Verifies recursive dictionary merging."""
        base = {
            "a": 1,
            "theme": {"accent": "#000", "glow": "rgba(0,0,0,0.5)"},
            "nodes": [1, 2],
        }
        override = {
            "theme": {"accent": "#fff"},
            "title": "New Title",
        }
        merged = _deep_merge(base, override)
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["theme"]["accent"], "#fff")
        self.assertEqual(merged["theme"]["glow"], "rgba(0,0,0,0.5)")
        self.assertEqual(merged["title"], "New Title")
        self.assertEqual(merged["nodes"], [1, 2])

    def test_create_clip_architecture_flow(self):
        """Verifies architecture_flow template creation and parameter injection."""
        custom_params = {
            "title": "CUSTOM ARCH ENGINE",
            "subtitle": "High Scale Worker Flow",
            "badge": "TEST BADGE",
            "duration": 4.5,
            "nodes": [
                {
                    "id": "n0",
                    "type": "Client",
                    "title": "Mobile App",
                    "subtitle": "Flutter Client",
                    "badge": "50k RPS",
                    "icon": "globe",
                    "status": "ONLINE",
                }
            ],
        }

        created_path = create_clip(
            template_name="architecture_flow",
            output_dir=self.output_dir,
            meta_params=custom_params,
        )

        self.assertTrue(created_path.exists())
        self.assertTrue((created_path / "index.html").exists())
        self.assertTrue((created_path / "meta.json").exists())
        self.assertTrue((created_path / "hyperframes.json").exists())

        # Verify meta.json content
        with open(created_path / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["title"], "CUSTOM ARCH ENGINE")
        self.assertEqual(meta["duration"], 4.5)
        self.assertEqual(meta["badge"], "TEST BADGE")
        self.assertEqual(len(meta["nodes"]), 1)
        self.assertEqual(meta["nodes"][0]["title"], "Mobile App")

        # Verify index.html content
        with open(created_path / "index.html", "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("CUSTOM ARCH ENGINE", html)
        self.assertIn('data-duration="4.5"', html)
        self.assertIn('data-composition-id="architecture_flow"', html)

    def test_create_clip_code_spotlight(self):
        """Verifies code_spotlight template creation and code snippet injection."""
        custom_params = {
            "filename": "custom_worker.ts",
            "language": "typescript",
            "badge": "ASYNC PIPELINE",
            "title": "EVENT BUS INTEGRATION",
            "code": [
                "export async function processEvents() {",
                "  const queue = await connectQueue();",
                "  return queue.poll();",
                "}",
            ],
            "highlightLines": [2],
            "lineNotes": {"2": "Non-blocking connection pool"},
        }

        created_path = create_clip(
            template_name="code_spotlight",
            output_dir=self.output_dir,
            meta_params=custom_params,
        )

        with open(created_path / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["filename"], "custom_worker.ts")
        self.assertEqual(meta["language"], "typescript")
        self.assertEqual(len(meta["code"]), 4)
        self.assertEqual(meta["highlightLines"], [2])

        with open(created_path / "index.html", "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("custom_worker.ts", html)
        self.assertIn("EVENT BUS INTEGRATION", html)

    def test_resolution_adaptation_landscape(self):
        """Verifies landscape (16:9 1920x1080) resolution adaptation."""
        custom_params = {
            "resolution": "landscape",
            "duration": 6.0,
        }

        created_path = create_clip(
            template_name="architecture_flow",
            output_dir=self.output_dir,
            meta_params=custom_params,
        )

        with open(created_path / "index.html", "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('data-resolution="landscape"', html)
        self.assertIn('width=1920, height=1080', html)
        self.assertIn('data-width="1920"', html)
        self.assertIn('data-height="1080"', html)
        self.assertIn('data-duration="6.0"', html)

    def test_invalid_template(self):
        """Verifies error raised when nonexistent template is requested."""
        with self.assertRaises(FileNotFoundError):
            create_clip("non_existent_template_xyz", self.output_dir)

    @patch("subprocess.run")
    def test_render_clip_success(self, mock_subproc):
        """Verifies render_clip CLI command construction and success flow."""
        # Create dummy project
        proj = create_clip("architecture_flow", self.output_dir)
        output_mp4 = Path(self.test_dir) / "output.mp4"

        # Mock subprocess.run
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Render completed in 2.1s"
        mock_proc.stderr = ""
        mock_subproc.return_value = mock_proc

        # Create dummy target file to satisfy existence check
        output_mp4.touch()
        with open(output_mp4, "wb") as f:
            f.write(b"dummy mp4 video bytes")

        result_path = render_clip(proj, output_mp4)
        self.assertEqual(result_path, output_mp4)

        # Verify command arguments passed to subprocess.run
        self.assertTrue(mock_subproc.called)
        cmd_args = mock_subproc.call_args[0][0]
        self.assertIn("render", cmd_args)
        self.assertIn(str(proj.resolve()), cmd_args)
        self.assertIn("-o", cmd_args)
        self.assertIn(str(output_mp4.resolve()), cmd_args)

    @patch("subprocess.run")
    def test_render_clip_failure(self, mock_subproc):
        """Verifies error handling when hyperframes render exits with non-zero code."""
        proj = create_clip("architecture_flow", self.output_dir)
        output_mp4 = Path(self.test_dir) / "output.mp4"

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "Error encountered"
        mock_proc.stderr = "Capture crashed"
        mock_subproc.return_value = mock_proc

        with self.assertRaises(RuntimeError) as ctx:
            render_clip(proj, output_mp4)
        self.assertIn("exit code 1", str(ctx.exception))

    def test_cli_parsing(self):
        """Verifies CLI argument parser flags."""
        test_args = [
            "hf_builder.py",
            "--template", "code_spotlight",
            "--out", "custom/path",
            "--resolution", "landscape",
            "--duration", "7.5",
            "--title", "CLI Test Title",
            "--render",
        ]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            self.assertEqual(args.template, "code_spotlight")
            self.assertEqual(args.out, "custom/path")
            self.assertEqual(args.resolution, "landscape")
            self.assertEqual(args.duration, 7.5)
            self.assertEqual(args.title, "CLI Test Title")
            self.assertTrue(args.render)


if __name__ == "__main__":
    unittest.main()

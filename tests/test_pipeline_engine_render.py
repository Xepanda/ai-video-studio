#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_pipeline_engine_render.py
Unit tests for pipeline engine render scheduling (Remotion & HyperFrames).
Covers command building, multi-engine routing, isolated props, and CLI arguments.
"""

import os
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.pipeline import build_render_commands, get_parser


def test_build_render_commands_remotion():
    """Verify Remotion render command structure, output path, and concurrency."""
    cmds = build_render_commands(project="demo", engine="remotion", concurrency=4, isolated=True)
    assert len(cmds) == 1
    remotion_step = cmds[0]
    assert "name" in remotion_step
    assert "Remotion" in remotion_step["name"]
    assert "remotion render" in remotion_step["cmd"]
    assert "out/demo.mp4" in remotion_step["cmd"]
    assert "--concurrency=4" in remotion_step["cmd"]
    assert remotion_step["output_mp4"] == "out/demo.mp4"

    # Verify isolated props
    assert "--props" in remotion_step["cmd"]
    assert "public/projects/demo/timeline.json" in remotion_step["cmd"]

    # Verify non-isolated mode (no --props)
    cmds_non_iso = build_render_commands(project="demo", engine="remotion", concurrency=6, isolated=False)
    assert len(cmds_non_iso) == 1
    assert "--props" not in cmds_non_iso[0]["cmd"]
    assert "--concurrency=6" in cmds_non_iso[0]["cmd"]


def test_build_render_commands_hyperframes():
    """Verify complete 3-step HyperFrames command chain: translate -> check -> render."""
    cmds = build_render_commands(project="demo", engine="hyperframes", concurrency=4)
    assert len(cmds) == 3

    # Step 1: timeline_to_hyperframes clock translation
    step1 = cmds[0]
    assert "timeline_to_hyperframes.py" in step1["cmd"]
    assert "--project" in step1["cmd"]
    assert "demo" in step1["cmd"]
    assert step1["output_mp4"] is None

    # Step 2: hyperframes check static quality gate
    step2 = cmds[1]
    assert "hyperframes check" in step2["cmd"]
    assert "projects_hf/demo" in step2["cmd"]
    assert step2["output_mp4"] is None

    # Step 3: hyperframes render headless rasterization
    step3 = cmds[2]
    assert "hyperframes render" in step3["cmd"]
    assert "projects_hf/demo" in step3["cmd"]
    assert "out/demo.mp4" in step3["cmd"]
    assert step3["output_mp4"] == "out/demo.mp4"


def test_build_render_commands_both():
    """Verify dual-engine command scheduling with distinct output filenames."""
    cmds = build_render_commands(project="demo", engine="both", concurrency=4)
    assert len(cmds) >= 2

    # Check Remotion step exists with _remotion.mp4 suffix
    remotion_steps = [c for c in cmds if "remotion render" in c["cmd"]]
    assert len(remotion_steps) == 1
    assert "out/demo_remotion.mp4" in remotion_steps[0]["cmd"]
    assert remotion_steps[0]["output_mp4"] == "out/demo_remotion.mp4"

    # Check HyperFrames render step exists with _hf.mp4 suffix
    hf_render_steps = [c for c in cmds if "hyperframes render" in c["cmd"]]
    assert len(hf_render_steps) == 1
    assert "out/demo_hf.mp4" in hf_render_steps[0]["cmd"]
    assert hf_render_steps[0]["output_mp4"] == "out/demo_hf.mp4"

    # Check that HyperFrames translation & check steps are present
    assert any("timeline_to_hyperframes.py" in c["cmd"] for c in cmds)
    assert any("hyperframes check" in c["cmd"] for c in cmds)


def test_build_render_commands_invalid_engine():
    """Verify that an unsupported engine choice raises ValueError."""
    with pytest.raises(ValueError):
        build_render_commands(project="demo", engine="unsupported")


def test_pipeline_cli_parser_engine_render():
    """Verify argparse default and choices for --engine_render."""
    parser = get_parser()

    # Default should be remotion
    args_default = parser.parse_args([])
    assert args_default.engine_render == "remotion"

    # Explicit remotion
    args_rem = parser.parse_args(["--engine_render", "remotion"])
    assert args_rem.engine_render == "remotion"

    # Explicit hyperframes
    args_hf = parser.parse_args(["--engine_render", "hyperframes"])
    assert args_hf.engine_render == "hyperframes"

    # Explicit both
    args_both = parser.parse_args(["--engine_render", "both"])
    assert args_both.engine_render == "both"

    # Invalid engine should exit with code 2
    with pytest.raises(SystemExit):
        parser.parse_args(["--engine_render", "invalid_engine"])

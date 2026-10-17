#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ingest_material.py
Unit tests for scripts/ingest_material.py.
Covers time parsing, section validation, name normalization,
yt-dlp command assembly, standardization, and ingest asset handling.
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest_material import (
    parse_time_to_seconds,
    parse_section,
    normalize_name,
    build_ytdlp_command,
    standardize_video,
    ingest_asset,
)


def test_parse_time_to_seconds():
    """Test parse_time_to_seconds with various valid and invalid formats."""
    assert parse_time_to_seconds("00:01:15") == 75.0
    assert parse_time_to_seconds("01:15") == 75.0
    assert parse_time_to_seconds("75") == 75.0
    assert parse_time_to_seconds("10.5") == 10.5
    assert parse_time_to_seconds("00:00:10.5") == 10.5
    assert parse_time_to_seconds("01:00:00") == 3600.0

    with pytest.raises(ValueError):
        parse_time_to_seconds("invalid")
    with pytest.raises(ValueError):
        parse_time_to_seconds("-10")
    with pytest.raises(ValueError):
        parse_time_to_seconds("01:02:03:04")
    with pytest.raises(ValueError):
        parse_time_to_seconds("")


def test_parse_section_formats():
    """Test valid section intervals across different time formats."""
    assert parse_section("00:01:15-00:01:30") == (75.0, 90.0)
    assert parse_section("01:15-01:30") == (75.0, 90.0)
    assert parse_section("75-90") == (75.0, 90.0)
    assert parse_section("00:00:10-00:00:25.5") == (10.0, 25.5)
    assert parse_section("*00:01:00-00:01:10") == (60.0, 70.0)
    assert parse_section(" 10 - 20 ") == (10.0, 20.0)


def test_parse_section_invalid():
    """Test invalid section strings: bad format, non-numbers, start >= end."""
    with pytest.raises(ValueError):
        parse_section("invalid-format")
    with pytest.raises(ValueError):
        parse_section("00:02:00-00:01:00")  # end before start
    with pytest.raises(ValueError):
        parse_section("10-10")  # start equals end
    with pytest.raises(ValueError):
        parse_section("")
    with pytest.raises(ValueError):
        parse_section("10-")
    with pytest.raises(ValueError):
        parse_section("-20")


def test_normalize_name():
    """Test filename normalization into lowercase underscore format."""
    assert normalize_name("OpenAI Day 6 Reset!!") == "openai_day_6_reset"
    assert normalize_name("测试视频 123") == "测试视频_123"
    assert normalize_name("Special & Chars / Test") == "special_chars_test"
    assert normalize_name("---Multiple___Dashes   Spaces---") == "multiple_dashes_spaces"
    assert normalize_name("") == "material"


def test_build_ytdlp_command():
    """Test build_ytdlp_command with sections and standard video formats."""
    cmd = build_ytdlp_command(
        url="https://youtube.com/watch?v=demo",
        out_path="temp/test.mp4",
        section="00:01:00-00:01:10",
        audio_only=False,
    )
    assert "yt-dlp" in cmd[0] or "python" in cmd[0]
    assert "--download-sections" in cmd
    assert "*60.0-70.0" in cmd or "*00:01:00-00:01:10" in cmd
    assert "-o" in cmd
    assert "temp/test.mp4" in cmd


def test_build_ytdlp_command_audio_only():
    """Test build_ytdlp_command with audio_only flag."""
    cmd = build_ytdlp_command(
        url="https://youtube.com/watch?v=demo",
        out_path="temp/audio.wav",
        audio_only=True,
    )
    assert "-x" in cmd
    assert "--audio-format" in cmd
    assert "wav" in cmd
    assert "-o" in cmd
    assert "temp/audio.wav" in cmd


def test_build_ytdlp_command_extract_info():
    """Test build_ytdlp_command with extract_info flag."""
    cmd = build_ytdlp_command(
        url="https://youtube.com/watch?v=demo",
        out_path="",
        extract_info=True,
    )
    assert "--dump-json" in cmd
    assert "--no-download" in cmd or "--skip-download" in cmd


def test_standardize_video(tmp_path):
    """Test standardize_video invokes ffmpeg with CFR fps filter and expected params."""
    in_file = tmp_path / "raw.mp4"
    in_file.write_text("dummy")
    out_file = tmp_path / "standard.mp4"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        res = standardize_video(str(in_file), str(out_file), fps=30)
        assert res == str(out_file)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args[0]
        assert "fps=30" in args[args.index("-vf") + 1]
        assert "18" in args
        assert "192k" in args


def test_ingest_asset_extract_info(tmp_path):
    """Test ingest_asset with extract_info writes metadata json properly."""
    fake_info = {
        "id": "demo123",
        "title": "Super Demo Video",
        "duration": 120,
        "description": "Test video description"
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(fake_info), stderr="")
        res = ingest_asset(
            url="https://youtube.com/watch?v=demo123",
            project="test_proj",
            extract_info=True,
        )
        assert res["status"] == "success"
        assert res["type"] == "metadata"
        assert os.path.exists(res["metadata_path"])
        with open(res["metadata_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["id"] == "demo123"
        # Cleanup
        if os.path.exists(res["metadata_path"]):
            os.remove(res["metadata_path"])

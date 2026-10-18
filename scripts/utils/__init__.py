#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils
Audio processing and safety utilities for ai-video-studio.
"""

from .audio_normalizer import (
    find_ffmpeg,
    measure_loudness,
    normalize_audio,
    normalize_voiceover,
    normalize_bgm,
    batch_normalize,
    fallback_normalize_audio,
)

from .snapshot_manager import (
    create_snapshot,
    list_snapshots,
    rollback_snapshot,
    validate_timeline_file,
    validate_timeline_data,
    get_timeline_scenes_count,
    SnapshotResult,
)

__all__ = [
    "find_ffmpeg",
    "measure_loudness",
    "normalize_audio",
    "normalize_voiceover",
    "normalize_bgm",
    "batch_normalize",
    "fallback_normalize_audio",
    "create_snapshot",
    "list_snapshots",
    "rollback_snapshot",
    "validate_timeline_file",
    "validate_timeline_data",
    "get_timeline_scenes_count",
    "SnapshotResult",
]

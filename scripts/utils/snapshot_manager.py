#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils/snapshot_manager.py
Timeline State Version Snapshot & Safety Rollback Engine

Features:
- Atomic snapshot creation of public/timeline.json to .snapshots/timeline_{timestamp}_{label}.json
- Continuous maintenance of public/timeline.backup.json
- Snapshot history listing with timestamps, labels, and scene counts
- Automated rollback with strict JSON schema and integrity validation
- Automatic pre-rollback safety snapshot to prevent accidental data loss
- CLI interface for script and terminal operations
"""

import os
import sys
import json
import re
import shutil
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

# Configure dedicated logger
logger = logging.getLogger("snapshot_manager")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[SnapshotManager] %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_TIMELINE_PATH = os.path.join(PROJECT_ROOT, "public", "timeline.json")
DEFAULT_SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, ".snapshots")


class SnapshotResult(str):
    """
    Result string representing snapshot path, but also provides dict/attribute access
    for seamless compatibility whether callers expect a string path or a metadata dict.
    """
    def __new__(cls, snapshot_path: str, metadata: Optional[Dict[str, Any]] = None):
        obj = super().__new__(cls, snapshot_path)
        obj.metadata = metadata or {}
        return obj

    @property
    def snapshot_path(self) -> str:
        return str(self)

    @property
    def backup_path(self) -> str:
        return self.metadata.get("backup_path", "")

    @property
    def label(self) -> str:
        return self.metadata.get("label", "")

    @property
    def timestamp(self) -> str:
        return self.metadata.get("timestamp", "")

    @property
    def scenes_count(self) -> int:
        return self.metadata.get("scenes_count", 0)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "snapshot_path":
            return str(self)
        return self.metadata.get(key, default)

    def __getitem__(self, item: str) -> Any:
        if item == "snapshot_path":
            return str(self)
        return self.metadata[item]


def validate_timeline_data(data: Any) -> bool:
    """
    Validates whether the provided parsed data is a structurally valid timeline.
    Must be a dictionary containing a 'scenes' list.
    """
    if not isinstance(data, dict):
        return False
    if "scenes" not in data or not isinstance(data["scenes"], list):
        return False
    return True


def validate_timeline_file(file_path: str) -> bool:
    """
    Checks if a timeline JSON file exists, is non-empty, and satisfies timeline schema.
    """
    if not os.path.isfile(file_path):
        return False
    if os.path.getsize(file_path) == 0:
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return validate_timeline_data(data)
    except Exception:
        return False


def get_timeline_scenes_count(file_path: str) -> int:
    """
    Extracts scene count from a timeline file safely.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("scenes"), list):
            return len(data["scenes"])
    except Exception:
        pass
    return 0


def create_snapshot(
    timeline_path: Optional[str] = None,
    label: str = "pre_edit",
    snapshot_dir: Optional[str] = None,
    update_backup: bool = True
) -> SnapshotResult:
    """
    Creates a snapshot of timeline_path in snapshot_dir (.snapshots/timeline_{timestamp}_{label}.json)
    and updates timeline.backup.json in the same directory as timeline_path (unless update_backup=False).

    Returns:
        SnapshotResult (str subclass with metadata attributes and dict indexing)
    """
    timeline_path = os.path.abspath(timeline_path or DEFAULT_TIMELINE_PATH)
    if not os.path.isfile(timeline_path):
        raise FileNotFoundError(f"Timeline file not found: {timeline_path}")

    # Validate file integrity
    if not validate_timeline_file(timeline_path):
        raise ValueError(f"Timeline file is corrupt or invalid JSON: {timeline_path}")

    # Determine snapshot directory
    if not snapshot_dir:
        snapshot_dir = DEFAULT_SNAPSHOT_DIR
    snapshot_dir = os.path.abspath(snapshot_dir)
    os.makedirs(snapshot_dir, exist_ok=True)

    # Sanitize label
    clean_label = re.sub(r"[^\w\-]+", "_", label.strip()).strip("_") or "snapshot"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"timeline_{timestamp}_{clean_label}.json"
    snapshot_path = os.path.join(snapshot_dir, snapshot_filename)

    # Copy to snapshot file
    shutil.copy2(timeline_path, snapshot_path)

    # Maintain timeline.backup.json in timeline's parent directory if requested
    timeline_dir = os.path.dirname(timeline_path)
    backup_path = os.path.join(timeline_dir, "timeline.backup.json")
    if update_backup:
        shutil.copy2(timeline_path, backup_path)

    scenes_count = get_timeline_scenes_count(snapshot_path)

    metadata = {
        "snapshot_path": snapshot_path,
        "backup_path": backup_path if update_backup else "",
        "snapshot_id": snapshot_filename,
        "timestamp": timestamp,
        "label": clean_label,
        "scenes_count": scenes_count,
        "size_bytes": os.path.getsize(snapshot_path)
    }

    logger.info(
        f"Snapshot created: {snapshot_filename} ({scenes_count} scenes) -> {snapshot_path}"
    )
    if update_backup:
        logger.info(f"Updated backup: {backup_path}")

    return SnapshotResult(snapshot_path, metadata)


def list_snapshots(
    snapshot_dir: Optional[str] = None,
    timeline_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lists all historical snapshots with timestamps, labels, and scene counts,
    sorted chronologically (newest first).
    """
    if not snapshot_dir:
        snapshot_dir = DEFAULT_SNAPSHOT_DIR
    snapshot_dir = os.path.abspath(snapshot_dir)

    if not os.path.isdir(snapshot_dir):
        return []

    snapshots = []
    pattern = re.compile(r"^timeline_(?P<ts>\d{8}_\d{6})_(?P<label>.*)\.json$")

    for fname in os.listdir(snapshot_dir):
        if not fname.endswith(".json"):
            continue
        full_path = os.path.join(snapshot_dir, fname)
        if not os.path.isfile(full_path):
            continue

        match = pattern.match(fname)
        if match:
            ts_str = match.group("ts")
            label_str = match.group("label")
        else:
            ts_str = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y%m%d_%H%M%S")
            label_str = fname.replace("timeline_", "").replace(".json", "")

        scenes_count = get_timeline_scenes_count(full_path)
        size_bytes = os.path.getsize(full_path)
        mtime = os.path.getmtime(full_path)
        iso_time = datetime.fromtimestamp(mtime).isoformat()

        snapshots.append({
            "id": fname,
            "filename": fname,
            "path": full_path,
            "timestamp": ts_str,
            "label": label_str,
            "scenes_count": scenes_count,
            "size_bytes": size_bytes,
            "created_at": iso_time,
            "_mtime": mtime
        })

    # Sort descending by timestamp / mtime
    snapshots.sort(key=lambda x: (x["timestamp"], x["_mtime"]), reverse=True)

    # Clean temporary sorting key
    for s in snapshots:
        s.pop("_mtime", None)

    return snapshots


def rollback_snapshot(
    snapshot_id_or_path: Optional[str] = None,
    timeline_path: Optional[str] = None,
    snapshot_dir: Optional[str] = None,
    create_safety_backup: bool = True
) -> bool:
    """
    Restores timeline_path from latest backup or specified snapshot with automated validation.

    Args:
        snapshot_id_or_path: Snapshot ID (filename), full path, or None for latest backup.
        timeline_path: Path to the target timeline file (default: public/timeline.json).
        snapshot_dir: Directory where snapshots are located.
        create_safety_backup: If True, creates a safety snapshot before overwriting.

    Returns:
        bool: True if restored successfully, False otherwise.
    """
    timeline_path = os.path.abspath(timeline_path or DEFAULT_TIMELINE_PATH)
    timeline_dir = os.path.dirname(timeline_path)
    backup_path = os.path.join(timeline_dir, "timeline.backup.json")

    if not snapshot_dir:
        snapshot_dir = DEFAULT_SNAPSHOT_DIR
    snapshot_dir = os.path.abspath(snapshot_dir)

    source_path = None

    # Step 1: Resolve target source path FIRST before modifying any state
    if not snapshot_id_or_path:
        if os.path.isfile(backup_path) and validate_timeline_file(backup_path):
            source_path = backup_path
        else:
            snapshots = list_snapshots(snapshot_dir=snapshot_dir)
            valid_snaps = [s for s in snapshots if not s["label"].startswith("pre_rollback")]
            if valid_snaps:
                source_path = valid_snaps[0]["path"]
            elif snapshots:
                source_path = snapshots[0]["path"]
            else:
                logger.error("No backup or snapshot found to restore.")
                return False
    else:
        # Specific snapshot ID or path provided
        candidate = os.path.abspath(snapshot_id_or_path)
        if os.path.isfile(candidate):
            source_path = candidate
        else:
            # Check within snapshot_dir
            in_dir = os.path.join(snapshot_dir, snapshot_id_or_path)
            if os.path.isfile(in_dir):
                source_path = in_dir
            elif os.path.isfile(in_dir + ".json"):
                source_path = in_dir + ".json"
            else:
                # Search by prefix or label in existing snapshots
                snapshots = list_snapshots(snapshot_dir=snapshot_dir)
                for s in snapshots:
                    if snapshot_id_or_path in s["id"] or snapshot_id_or_path == s["label"]:
                        source_path = s["path"]
                        break

        if not source_path or not os.path.isfile(source_path):
            logger.error(f"Specified snapshot could not be located: {snapshot_id_or_path}")
            return False

    # AUTOMATED VALIDATION
    if not validate_timeline_file(source_path):
        logger.error(f"Rollback rejected: snapshot {source_path} is invalid or corrupted.")
        return False

    # PRE-ROLLBACK SAFETY SNAPSHOT (Do NOT overwrite timeline.backup.json with current state)
    if create_safety_backup and os.path.isfile(timeline_path) and validate_timeline_file(timeline_path):
        try:
            create_snapshot(
                timeline_path=timeline_path,
                label="pre_rollback_safety",
                snapshot_dir=snapshot_dir,
                update_backup=False
            )
        except Exception as e:
            logger.warning(f"Could not create pre-rollback safety snapshot: {e}")

    # ATOMIC RESTORE
    try:
        tmp_restore = timeline_path + f".tmp_{os.getpid()}"
        shutil.copy2(source_path, tmp_restore)
        shutil.move(tmp_restore, timeline_path)

        restored_scenes = get_timeline_scenes_count(timeline_path)
        logger.info(
            f"Successfully rolled back timeline to {os.path.basename(source_path)} "
            f"({restored_scenes} scenes restored) -> {timeline_path}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to restore timeline: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Timeline State Version Snapshot & Safety Rollback Engine."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: create
    create_p = subparsers.add_parser("create", help="Create a new snapshot of timeline.json")
    create_p.add_argument("--label", "-l", default="pre_edit", help="Snapshot label (e.g. pre_render, scene_add)")
    create_p.add_argument("--timeline", "-t", default=None, help="Path to timeline.json")
    create_p.add_argument("--dir", "-d", default=None, help="Snapshot directory")

    # Command: list
    list_p = subparsers.add_parser("list", help="List all historical timeline snapshots")
    list_p.add_argument("--dir", "-d", default=None, help="Snapshot directory")
    list_p.add_argument("--timeline", "-t", default=None, help="Path to timeline.json")

    # Command: rollback
    rollback_p = subparsers.add_parser("rollback", help="Restore timeline from snapshot or backup")
    rollback_p.add_argument("snapshot", nargs="?", default=None, help="Snapshot ID or path (defaults to latest backup)")
    rollback_p.add_argument("--timeline", "-t", default=None, help="Path to timeline.json to overwrite")
    rollback_p.add_argument("--dir", "-d", default=None, help="Snapshot directory")
    rollback_p.add_argument("--no-safety", action="store_true", help="Skip pre-rollback safety snapshot")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "create":
        try:
            res = create_snapshot(
                timeline_path=args.timeline,
                label=args.label,
                snapshot_dir=args.dir
            )
            print(f"Snapshot created successfully: {res.snapshot_path}")
            print(f"Scenes count: {res.scenes_count}")
            sys.exit(0)
        except Exception as e:
            print(f"Error creating snapshot: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        snapshots = list_snapshots(snapshot_dir=args.dir, timeline_path=args.timeline)
        if not snapshots:
            print("No snapshots found.")
            sys.exit(0)

        print(f"\n{'ID / Filename':<48} {'Timestamp':<16} {'Label':<20} {'Scenes':<8} {'Size':<10}")
        print("-" * 105)
        for s in snapshots:
            size_kb = f"{s['size_bytes'] / 1024:.1f} KB"
            print(f"{s['id']:<48} {s['timestamp']:<16} {s['label']:<20} {s['scenes_count']:<8} {size_kb:<10}")
        print(f"\nTotal snapshots: {len(snapshots)}\n")
        sys.exit(0)

    elif args.command == "rollback":
        ok = rollback_snapshot(
            snapshot_id_or_path=args.snapshot,
            timeline_path=args.timeline,
            snapshot_dir=args.dir,
            create_safety_backup=not args.no_safety
        )
        if ok:
            print("Timeline rolled back successfully.")
            sys.exit(0)
        else:
            print("Timeline rollback failed.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

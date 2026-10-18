#!/usr/bin/env python3
"""
HyperFrames Automation Engine & B-Roll Factory for ai-video-studio.

Programmatically generates, customizes, and batch-renders HTML5/CSS/GSAP
HyperFrames motion templates into deterministic, zero-cost video clips.
"""

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Root project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEMPLATES_DIR = PROJECT_ROOT / "projects_hf" / "templates"
DEFAULT_FOOTAGE_DIR = PROJECT_ROOT / "public" / "footage"
DEFAULT_GENERATED_DIR = PROJECT_ROOT / "projects_hf" / "generated"


def list_templates() -> List[str]:
    """Return available template names in projects_hf/templates."""
    if not TEMPLATES_DIR.exists():
        return []
    return [
        d.name for d in TEMPLATES_DIR.iterdir()
        if d.is_dir() and (d / "index.html").exists()
    ]


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge source dictionary into target dictionary."""
    result = copy.deepcopy(target)
    for key, value in source.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def create_clip(
    template_name: str,
    output_dir: Union[str, Path],
    meta_params: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Clones a HyperFrames motion template and injects dynamic titles,
    resolutions, and timing parameters.

    Args:
        template_name: Name of the template (e.g. 'architecture_flow', 'code_spotlight')
        output_dir: Destination project directory
        meta_params: Optional dict of overrides for meta.json and index.html

    Returns:
        Path to the customized project directory
    """
    output_path = Path(output_dir).resolve()
    src_template_dir = TEMPLATES_DIR / template_name

    if not src_template_dir.exists():
        available = list_templates()
        raise FileNotFoundError(
            f"Template '{template_name}' not found at {src_template_dir}. Available templates: {available}"
        )

    # 1. Clone template files to output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    for item in src_template_dir.iterdir():
        dest = output_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # 2. Merge meta parameters
    meta_file = output_path / "meta.json"
    existing_meta: Dict[str, Any] = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception:
            existing_meta = {}

    merged_meta = _deep_merge(existing_meta, meta_params or {})

    # Ensure id/resolution/duration defaults
    if "id" not in merged_meta:
        merged_meta["id"] = template_name
    if "resolution" not in merged_meta:
        merged_meta["resolution"] = "portrait"
    if "duration" not in merged_meta:
        merged_meta["duration"] = 5.0

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(merged_meta, f, indent=2, ensure_ascii=False)

    # 3. Synchronize index.html with merged meta
    index_file = output_path / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Update embedded template-meta script
        meta_json_str = json.dumps(merged_meta, indent=2, ensure_ascii=False)
        html_content = re.sub(
            r'(<script\s+id="template-meta"\s+type="application/json">)[\s\S]*?(</script>)',
            rf'\1\n{meta_json_str}\n    \2',
            html_content,
        )

        # Update root attributes (duration, resolution, dimensions)
        resolution = merged_meta.get("resolution", "portrait")
        is_landscape = (resolution == "landscape")
        width = 1920 if is_landscape else 1080
        height = 1080 if is_landscape else 1920
        duration = merged_meta.get("duration", 5.0)
        comp_id = merged_meta.get("id", template_name)

        # Update <html> data-resolution
        html_content = re.sub(
            r'<html([^>]*?)data-resolution="[^"]*"',
            f'<html\\1data-resolution="{resolution}"',
            html_content,
        )

        # Update viewport meta
        html_content = re.sub(
            r'<meta\s+name="viewport"\s+content="[^"]*"',
            f'<meta name="viewport" content="width={width}, height={height}"',
            html_content,
        )

        # Update root element attributes
        html_content = re.sub(
            r'(<div\s+id="root"[^>]*?)data-composition-id="[^"]*"',
            f'\\1data-composition-id="{comp_id}"',
            html_content,
        )
        html_content = re.sub(
            r'(<div\s+id="root"[^>]*?)data-duration="[^"]*"',
            f'\\1data-duration="{duration}"',
            html_content,
        )
        html_content = re.sub(
            r'(<div\s+id="root"[^>]*?)data-width="[^"]*"',
            f'\\1data-width="{width}"',
            html_content,
        )
        html_content = re.sub(
            r'(<div\s+id="root"[^>]*?)data-height="[^"]*"',
            f'\\1data-height="{height}"',
            html_content,
        )

        # Update GSAP timeline registration key if needed
        html_content = re.sub(
            r'window\.__timelines\["[^"]*"\]\s*=\s*tl;',
            f'window.__timelines["{comp_id}"] = tl;',
            html_content,
        )

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    return output_path


def _get_hyperframes_cmd() -> List[str]:
    """Finds cross-platform command to execute hyperframes CLI."""
    if os.name == "nt":
        # Windows: check for npx.cmd
        npx_cmd = shutil.which("npx.cmd")
        if npx_cmd:
            return [npx_cmd, "hyperframes"]
        npx = shutil.which("npx")
        if npx:
            return ["cmd.exe", "/c", "npx", "hyperframes"]
        return ["cmd.exe", "/c", "npx", "hyperframes"]
    else:
        npx = shutil.which("npx")
        if npx:
            return [npx, "hyperframes"]
        return ["npx", "hyperframes"]


def render_clip(
    project_dir: Union[str, Path],
    output_mp4: Union[str, Path],
    timeout: int = 180,
    extra_args: Optional[List[str]] = None,
) -> Path:
    """
    Renders a HyperFrames composition into an MP4 video file.

    Args:
        project_dir: Path to the HyperFrames project containing index.html
        output_mp4: Target path for the rendered MP4 file
        timeout: Subprocess timeout in seconds
        extra_args: Additional command line flags to pass to hyperframes render

    Returns:
        Path to the rendered MP4 file
    """
    proj_path = Path(project_dir).resolve()
    out_path = Path(output_mp4).resolve()

    if not proj_path.exists() or not (proj_path / "index.html").exists():
        raise FileNotFoundError(f"Valid HyperFrames project not found at: {proj_path}")

    # Ensure output parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    base_cmd = _get_hyperframes_cmd()
    cmd = base_cmd + ["render", str(proj_path), "-o", str(out_path)]

    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise TimeoutError(f"HyperFrames render timed out after {timeout}s: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to execute HyperFrames render: {e}")

    if proc.returncode != 0:
        raise RuntimeError(
            f"HyperFrames render failed with exit code {proc.returncode}.\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(
            f"Render finished with code 0 but output file was not created or empty: {out_path}\n"
            f"STDOUT: {proc.stdout}"
        )

    return out_path


def build_broll(
    template_name: str,
    clip_name: str,
    meta_params: Optional[Dict[str, Any]] = None,
    render: bool = True,
    output_mp4: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    timeout: int = 180,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    High-level convenience workflow to build and optionally render a B-roll clip.

    Args:
        template_name: Template name ('architecture_flow', 'code_spotlight')
        clip_name: Unique identifier for the clip
        meta_params: Parameter overrides
        render: Whether to immediately render to MP4
        output_mp4: Custom destination MP4 path (defaults to public/footage/<clip_name>.mp4)
        output_dir: Custom destination project directory
        timeout: Render timeout in seconds
        use_cache: Whether to use incremental build cache

    Returns:
        Dict with clip metadata, project_dir, and video_path
    """
    proj_dir = Path(output_dir) if output_dir else (DEFAULT_GENERATED_DIR / clip_name)
    mp4_path = Path(output_mp4) if output_mp4 else (DEFAULT_FOOTAGE_DIR / f"{clip_name}.mp4")

    # Clone and customize
    created_proj = create_clip(template_name, proj_dir, meta_params)

    rendered_video: Optional[Path] = None
    if render:
        if use_cache:
            try:
                from scripts.utils.asset_cache_manager import AssetCacheManager
                cache_mgr = AssetCacheManager()
                cache_params = {"template": template_name, "meta": meta_params or {}}
                cached_file = cache_mgr.get_cached_asset("hyperframes", cache_params)
                if cached_file and Path(cached_file).exists():
                    mp4_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(cached_file, mp4_path)
                    rendered_video = mp4_path
                else:
                    rendered_video = render_clip(created_proj, mp4_path, timeout=timeout)
                    cache_mgr.store_cached_asset("hyperframes", cache_params, str(rendered_video))
            except Exception as e:
                # Fallback to direct render if caching error
                rendered_video = render_clip(created_proj, mp4_path, timeout=timeout)
        else:
            rendered_video = render_clip(created_proj, mp4_path, timeout=timeout)

    return {
        "clip_name": clip_name,
        "template": template_name,
        "project_dir": str(created_proj),
        "video_path": str(rendered_video) if rendered_video else None,
        "duration": (meta_params or {}).get("duration", 5.0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HyperFrames B-Roll Builder & Batch Renderer for ai-video-studio"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="architecture_flow",
        help="Template name to use (e.g. architecture_flow, code_spotlight)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output project directory (or output MP4 path if --render specified)",
    )
    parser.add_argument(
        "--meta",
        type=str,
        default=None,
        help="JSON string or path to JSON file containing meta parameter overrides",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render composition to MP4 after generation",
    )
    parser.add_argument(
        "-o",
        "--output-mp4",
        type=str,
        default=None,
        help="Specific target path for rendered MP4 video (default: public/footage/<name>.mp4)",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["portrait", "landscape"],
        default=None,
        help="Quick override for video resolution (portrait or landscape)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Quick override for video duration in seconds",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Quick override for composition title",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available motion templates and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_templates:
        templates = list_templates()
        print(f"Available HyperFrames templates ({len(templates)}):")
        for t in templates:
            print(f"  - {t}")
        return

    # Parse meta parameters
    meta_params: Dict[str, Any] = {}
    if args.meta:
        meta_str = args.meta.strip()
        if os.path.isfile(meta_str):
            with open(meta_str, "r", encoding="utf-8") as f:
                meta_params = json.load(f)
        else:
            try:
                meta_params = json.loads(meta_str)
            except json.JSONDecodeError as e:
                print(f"Error parsing --meta JSON: {e}", file=sys.stderr)
                sys.exit(1)

    # CLI shortcuts
    if args.resolution:
        meta_params["resolution"] = args.resolution
    if args.duration is not None:
        meta_params["duration"] = args.duration
    if args.title:
        meta_params["title"] = args.title

    clip_name = meta_params.get("id") or args.template

    # Determine project directory and output mp4
    project_dir = args.out if args.out and not args.out.endswith(".mp4") else None
    output_mp4 = args.output_mp4 or (args.out if args.out and args.out.endswith(".mp4") else None)

    print(f"[*] Building HyperFrames clip '{clip_name}' from template '{args.template}'...")
    result = build_broll(
        template_name=args.template,
        clip_name=clip_name,
        meta_params=meta_params,
        render=args.render,
        output_mp4=output_mp4,
        output_dir=project_dir,
    )

    print(f"[+] Project generated at: {result['project_dir']}")
    if result["video_path"]:
        print(f"[+] Video successfully rendered to: {result['video_path']}")


if __name__ == "__main__":
    main()

"""
Timeline to HyperFrames Adapter.
Translates a timeline.json clock contract into a deterministic, seekable
HyperFrames HTML/CSS/GSAP composition project ready for headless rendering.
"""

import argparse
import html as html_lib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def format_sec(val: float) -> str:
    """Format seconds with fixed precision for HTML data attributes."""
    return f"{round(val, 3):.3f}".rstrip("0").rstrip(".") if round(val, 3) != int(val) else f"{float(val):.1f}"


def escape_text(text: str) -> str:
    """Escape text for safe HTML embedding."""
    return html_lib.escape(text or "")


def render_text_with_highlights(raw_text: str, highlight_words: List[str], capsule_class: str) -> str:
    """
    Safely highlights occurrences of highlight_words in raw_text without attribute corruption
    or HTML escaping mismatches.
    """
    if not raw_text:
        return ""
    if not highlight_words:
        return escape_text(raw_text)

    # Filter non-empty words that exist in raw_text, sorted descending by length
    valid_hw = [hw for hw in highlight_words if hw and hw in raw_text]
    if not valid_hw:
        return escape_text(raw_text)
    valid_hw.sort(key=len, reverse=True)

    import re
    pattern = "(" + "|".join(re.escape(w) for w in valid_hw) + ")"
    tokens = re.split(pattern, raw_text)

    rendered_parts = []
    for token in tokens:
        if not token:
            continue
        if token in valid_hw:
            rendered_parts.append(f'<span class="{capsule_class}">{escape_text(token)}</span>')
        else:
            rendered_parts.append(escape_text(token))

    return "".join(rendered_parts)


def render_minimal_headline(scene: Dict[str, Any], scene_id: str) -> str:
    title = scene.get("title") or scene.get("text", "")
    category = scene.get("category", "TECH NEWS")
    inverted = scene.get("inverted", False)
    highlight_words = scene.get("highlightWords", [])

    rendered_title = render_text_with_highlights(title, highlight_words, "headline-capsule")
    bg_class = "inverted-card" if inverted else "standard-card"

    return f"""
    <div class="content-card headline-card {bg_class}">
      <div class="category-pill">{escape_text(category)}</div>
      <h1 class="headline-title">{rendered_title}</h1>
    </div>
    """


def render_tweet_embed(scene: Dict[str, Any], scene_id: str) -> str:
    tweet = scene.get("tweet") or {}
    author_name = tweet.get("authorName", "Tech Insider")
    author_handle = tweet.get("authorHandle", "@tech_insider")
    content = tweet.get("content") or scene.get("text", "")
    metrics = tweet.get("metrics") or {}
    replies_val = metrics.get("replies", "1.2k")
    reposts_val = metrics.get("reposts", "3.4k")
    likes_val = metrics.get("likes", "18.5k")
    highlight_words = scene.get("highlightWords", [])

    rendered_content = render_text_with_highlights(content, highlight_words, "tweet-capsule")

    return f"""
    <div class="content-card tweet-card">
      <div class="tweet-header">
        <div class="tweet-author-info">
          <div class="tweet-avatar">
            <span>{escape_text(author_name[0]) if author_name else "X"}</span>
          </div>
          <div class="tweet-names">
            <div class="tweet-name-row">
              <span class="tweet-author-name">{escape_text(author_name)}</span>
              <svg class="verified-badge" viewBox="0 0 24 24" width="20" height="20">
                <path fill="#38bdf8" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
            </div>
            <span class="tweet-handle">{escape_text(author_handle)}</span>
          </div>
        </div>
        <svg class="x-logo" viewBox="0 0 24 24" width="22" height="22">
          <path fill="#ffffff" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      </div>

      <div class="tweet-body">
        <p class="tweet-text">{rendered_content}</p>
      </div>

      <div class="tweet-footer">
        <div class="tweet-stat">
          <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#71717a" d="M12 2C6.48 2 2 6.48 2 12c0 1.82.49 3.53 1.35 5L2 22l5.22-1.31C8.61 21.43 10.26 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.57 0-3.04-.45-4.29-1.22l-.31-.19-3.1.78.8-3.03-.2-.33C4.38 15.11 4 13.61 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8z"/></svg>
          <span>{escape_text(str(replies_val))}</span>
        </div>
        <div class="tweet-stat">
          <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#71717a" d="M7 6h10v3l4-4-4-4v3H5v6h2V6zm10 12H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/></svg>
          <span>{escape_text(str(reposts_val))}</span>
        </div>
        <div class="tweet-stat">
          <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#71717a" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          <span>{escape_text(str(likes_val))}</span>
        </div>
      </div>
    </div>
    """


def render_binary_bento(scene: Dict[str, Any], scene_id: str) -> str:
    bento = scene.get("binaryBento") or {}
    left = bento.get("leftCard") or {"title": "传统模式", "desc": "冗余功能堆叠"}
    right = bento.get("rightCard") or {"title": "极简重置", "desc": "零杂音效率优先"}
    blocks_active = scene.get("blocksActive", bento.get("blocksActive", 5))
    blocks_total = scene.get("blocksTotal", bento.get("blocksTotal", 8))

    blocks_html = "".join([
        f'<div class="progress-block {"active" if idx < blocks_active else "inactive"}"></div>'
        for idx in range(blocks_total)
    ])

    return f"""
    <div class="content-card bento-card-wrapper">
      <div class="bento-subcard left-subcard">
        <span class="bento-tag left-tag">{escape_text(left.get("tag", "BEFORE"))}</span>
        <h2 class="bento-title">{escape_text(left.get("title", ""))}</h2>
        <p class="bento-desc">{escape_text(left.get("desc", ""))}</p>
      </div>

      <div class="bento-divider">
        <span class="bento-vs-pill">VS</span>
      </div>

      <div class="bento-subcard right-subcard">
        <span class="bento-tag right-tag">{escape_text(right.get("tag", "RESET"))}</span>
        <h2 class="bento-title highlight-text">{escape_text(right.get("title", ""))}</h2>
        <p class="bento-desc">{escape_text(right.get("desc", ""))}</p>
        <div class="progress-blocks-row">
          {blocks_html}
        </div>
      </div>
    </div>
    """


def render_hyperframes_html(timeline: Dict[str, Any], resolution: str = "portrait") -> str:
    fps = timeline.get("fps", 30)
    total_frames = timeline.get("totalDurationInFrames", 300)
    total_duration_sec = total_frames / fps
    scenes = timeline.get("scenes", [])

    is_portrait = resolution == "portrait"
    width = 1080 if is_portrait else 1920
    height = 1920 if is_portrait else 1080

    scenes_html: List[str] = []
    audio_elements: List[str] = []
    gsap_timelines: List[str] = []

    for scene in scenes:
        scene_id = scene.get("id", "scene_00")
        scene_type = scene.get("type", "MinimalHeadline")
        start_frame = scene.get("startFrame", 0)
        duration_frames = scene.get("durationInFrames", 60)

        start_sec = start_frame / fps
        duration_sec = duration_frames / fps

        # Render visual card content
        if scene_type == "TweetEmbed" or scene.get("tweet"):
            card_content = render_tweet_embed(scene, scene_id)
        elif scene_type == "BinaryBento" or scene.get("binaryBento"):
            card_content = render_binary_bento(scene, scene_id)
        else:
            card_content = render_minimal_headline(scene, scene_id)

        # Build Subtitles HTML for this scene
        words = scene.get("words", [])
        sub_spans = []
        for w_idx, w in enumerate(words):
            sub_spans.append(
                f'<span id="sub_{scene_id}_{w_idx}" class="sub-word">{escape_text(w.get("text", ""))}</span>'
            )
        subtitles_html = f'<div class="scene-subtitles">{" ".join(sub_spans)}</div>'

        # Scene clip element
        scene_markup = f"""
        <!-- Scene: {scene_id} ({scene_type}) -->
        <section id="{scene_id}" class="clip scene-clip" data-start="{format_sec(start_sec)}" data-duration="{format_sec(duration_sec)}" data-track-index="0">
          <div class="scene-inner">
            {card_content}
            {subtitles_html}
          </div>
        </section>
        """
        scenes_html.append(scene_markup)

        # Audio tag
        audio_path = scene.get("audioPath")
        if audio_path:
            # Point to local assets path
            asset_audio_rel = f"assets/audio/{Path(audio_path).name}"
            audio_markup = f'<audio id="voice_{scene_id}" src="{asset_audio_rel}" data-start="{format_sec(start_sec)}" data-duration="{format_sec(duration_sec)}" data-volume="1"></audio>'
            audio_elements.append(audio_markup)

        # GSAP Animations
        gsap_timelines.append(f"// Scene {scene_id} Animation")
        # Spring entrance
        gsap_timelines.append(
            f'tl.fromTo("#{scene_id} .content-card", {{ opacity: 0, y: 40, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1.0, duration: 0.45, ease: "power2.out" }}, {format_sec(start_sec)});'
        )
        # Subtle exit transition right before end of clip
        entrance_duration = 0.45
        exit_duration = 0.15
        exit_time = start_sec + duration_sec - exit_duration
        if exit_time >= start_sec + entrance_duration:
            gsap_timelines.append(
                f'tl.to("#{scene_id} .content-card, #{scene_id} .scene-subtitles", {{ opacity: 0, scale: 0.98, duration: {exit_duration}, ease: "power2.in" }}, {format_sec(exit_time)});'
            )

        # Word-level karaoke highlights
        for w_idx, w in enumerate(words):
            word_start_sec = start_sec + (w.get("startMs", 0) / 1000.0)
            word_end_sec = start_sec + (w.get("endMs", 0) / 1000.0)
            word_elem_id = f"#sub_{scene_id}_{w_idx}"
            gsap_timelines.append(
                f'tl.fromTo("{word_elem_id}", {{ color: "#71717a", scale: 0.96 }}, {{ color: "#facc15", scale: 1.06, duration: 0.12, ease: "power1.out" }}, {format_sec(word_start_sec)});'
            )
            gsap_timelines.append(
                f'tl.to("{word_elem_id}", {{ color: "#ffffff", scale: 1.0, duration: 0.12, ease: "power1.out" }}, {format_sec(word_end_sec)});'
            )

    combined_scenes = "\n".join(scenes_html)
    combined_audio = "\n    ".join(audio_elements)
    combined_gsap = "\n      ".join(gsap_timelines)

    html_template = f"""<!doctype html>
<html lang="zh-CN" data-resolution="{resolution}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <title>HyperFrames Video Composition</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      html, body {{
        width: {width}px;
        height: {height}px;
        overflow: hidden;
        background: #09090b;
        color: #f4f4f5;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
      }}
      #root {{
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: radial-gradient(circle at 50% 30%, #18181b 0%, #09090b 100%);
      }}
      .clip {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
      }}
      .scene-inner {{
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 48px;
        position: relative;
      }}
      /* Global Card Styles */
      .content-card {{
        width: 100%;
        max-width: 960px;
        border-radius: 36px;
        border: 2px solid rgba(255, 255, 255, 0.08);
        background: rgba(24, 24, 27, 0.75);
        backdrop-filter: blur(28px);
        box-shadow: 0 24px 64px -12px rgba(0, 0, 0, 0.65);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 64px 48px;
      }}
      /* Minimal Headline Scene */
      .headline-card.standard-card {{
        background: rgba(24, 24, 27, 0.85);
      }}
      .headline-card.inverted-card {{
        background: #f4f4f5;
        color: #09090b;
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 32px 80px rgba(255, 255, 255, 0.12);
      }}
      .headline-card.inverted-card .headline-title {{
        color: #09090b;
      }}
      .headline-card.inverted-card .category-pill {{
        background: #09090b;
        color: #ffffff;
      }}
      .category-pill {{
        display: inline-block;
        padding: 10px 24px;
        border-radius: 9999px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #a5b4fc;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 36px;
      }}
      .headline-title {{
        font-size: 76px;
        font-weight: 800;
        line-height: 1.25;
        color: #ffffff;
        letter-spacing: -0.02em;
        word-break: break-word;
      }}
      .headline-capsule {{
        display: inline-block;
        background: #facc15;
        color: #09090b;
        padding: 4px 18px;
        border-radius: 18px;
        margin: 0 6px;
        font-weight: 900;
      }}
      /* Tweet Card */
      .tweet-card {{
        align-items: flex-start;
        text-align: left;
        padding: 56px 52px;
      }}
      .tweet-header {{
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 36px;
      }}
      .tweet-author-info {{
        display: flex;
        align-items: center;
        gap: 20px;
      }}
      .tweet-avatar {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #3b82f6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 38px;
        font-weight: 800;
        color: #ffffff;
      }}
      .tweet-names {{
        display: flex;
        flex-direction: column;
        gap: 4px;
      }}
      .tweet-name-row {{
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .tweet-author-name {{
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
      }}
      .tweet-handle {{
        font-size: 28px;
        color: #a1a1aa;
      }}
      .tweet-body {{
        margin-bottom: 40px;
      }}
      .tweet-text {{
        font-size: 48px;
        font-weight: 600;
        line-height: 1.45;
        color: #f4f4f5;
      }}
      .tweet-capsule {{
        background: rgba(56, 189, 248, 0.2);
        color: #38bdf8;
        padding: 2px 14px;
        border-radius: 12px;
        border: 1px solid rgba(56, 189, 248, 0.4);
      }}
      .tweet-footer {{
        width: 100%;
        display: flex;
        justify-content: space-between;
        padding-top: 28px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 26px;
        font-weight: 600;
        color: #71717a;
      }}
      .tweet-stat {{
        display: flex;
        align-items: center;
        gap: 10px;
      }}
      /* Binary Bento Scene */
      .bento-card-wrapper {{
        gap: 24px;
        padding: 44px;
      }}
      .bento-subcard {{
        width: 100%;
        border-radius: 28px;
        padding: 36px;
        text-align: left;
      }}
      .left-subcard {{
        background: rgba(39, 39, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
      }}
      .right-subcard {{
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.35);
      }}
      .bento-tag {{
        display: inline-block;
        padding: 6px 16px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.05em;
        margin-bottom: 14px;
      }}
      .left-tag {{
        background: rgba(255, 255, 255, 0.1);
        color: #a1a1aa;
      }}
      .right-tag {{
        background: #6366f1;
        color: #ffffff;
      }}
      .bento-title {{
        font-size: 46px;
        font-weight: 800;
        margin-bottom: 8px;
      }}
      .highlight-text {{
        color: #a5b4fc;
      }}
      .bento-desc {{
        font-size: 28px;
        color: #a1a1aa;
        line-height: 1.4;
      }}
      .bento-divider {{
        position: relative;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
      }}
      .bento-vs-pill {{
        background: #27272a;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 4px 18px;
        border-radius: 9999px;
        font-size: 20px;
        font-weight: 900;
        color: #e4e4e7;
      }}
      .progress-blocks-row {{
        display: flex;
        gap: 8px;
        margin-top: 18px;
      }}
      .progress-block {{
        flex: 1;
        height: 12px;
        border-radius: 6px;
      }}
      .progress-block.active {{
        background: #6366f1;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
      }}
      .progress-block.inactive {{
        background: rgba(255, 255, 255, 0.1);
      }}
      /* Subtitles Fixed Safe Area */
      .scene-subtitles {{
        position: absolute;
        bottom: 220px; /* Safe area for TikTok / Reels UI */
        left: 48px;
        right: 48px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 12px;
        text-align: center;
        pointer-events: none;
      }}
      .sub-word {{
        font-size: 44px;
        font-weight: 800;
        color: #71717a;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{format_sec(total_duration_sec)}"
      data-width="{width}"
      data-height="{height}"
    >
      {combined_scenes}
    </div>

    <!-- Mixer Audio Track -->
    {combined_audio}

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      {combined_gsap}

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
    return html_template


def convert_timeline_to_hyperframes(
    timeline_path: str,
    out_dir: str,
    resolution: str = "portrait",
) -> Dict[str, Any]:
    """
    Main conversion entrypoint.
    """
    timeline_file = Path(timeline_path).resolve()
    if not timeline_file.exists():
        raise FileNotFoundError(f"Timeline file not found: {timeline_path}")

    with open(timeline_file, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    assets_audio_dir = out_path / "assets" / "audio"
    assets_audio_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy audio assets
    timeline_dir = timeline_file.parent
    for scene in timeline.get("scenes", []):
        audio_rel = scene.get("audioPath")
        if not audio_rel:
            continue

        # Look in multiple candidate paths
        candidate_paths = [
            timeline_dir / audio_rel,
            PROJECT_ROOT / "public" / audio_rel,
            PROJECT_ROOT / audio_rel,
            Path(audio_rel),
        ]

        found_src = None
        for cand in candidate_paths:
            if cand.exists() and cand.is_file():
                found_src = cand
                break

        if found_src:
            dest_file = assets_audio_dir / found_src.name
            shutil.copy2(found_src, dest_file)

    # 2. Render index.html
    html_content = render_hyperframes_html(timeline, resolution=resolution)
    index_file = out_path / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. Write hyperframes.json
    hf_config = {
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {
            "blocks": "compositions",
            "components": "compositions/components",
            "assets": "assets",
        },
        "media": {
            "autoProxy": True,
        },
    }
    with open(out_path / "hyperframes.json", "w", encoding="utf-8") as f:
        json.dump(hf_config, f, indent=2)

    # 4. Write meta.json
    meta_config = {
        "id": timeline.get("project", "hyperframes_composition"),
        "name": timeline.get("project", "hyperframes_composition"),
        "resolution": resolution,
    }
    with open(out_path / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_config, f, indent=2)

    return {
        "success": True,
        "out_dir": str(out_path),
        "index_html": str(index_file),
        "total_duration_sec": timeline.get("totalDurationInFrames", 300) / timeline.get("fps", 30),
    }


def main():
    parser = argparse.ArgumentParser(description="Convert timeline.json to HyperFrames composition project")
    parser.add_argument("--timeline", required=True, help="Path to input timeline.json")
    parser.add_argument("--out_dir", required=True, help="Path to output project directory")
    parser.add_argument("--resolution", default="portrait", choices=["portrait", "landscape"], help="Canvas resolution")

    args = parser.parse_args()
    result = convert_timeline_to_hyperframes(
        timeline_path=args.timeline,
        out_dir=args.out_dir,
        resolution=args.resolution,
    )
    print(f"Successfully generated HyperFrames project at: {result['out_dir']}")


if __name__ == "__main__":
    main()

# HyperFrames 动效引擎与 yt-dlp 素材采集中枢工作流集成实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建并整合两大关键子系统：上游流媒体素材/B-Roll/干声音频智能切片采集中枢（基于 `yt-dlp` 与 `ffmpeg`），以及下游确定性 HTML/CSS/GSAP 轻量化动效渲染中枢（基于 `HyperFrames`），并统一由 `scripts/pipeline.py` 实现双轨调度与 EBU R128 -11.0 LUFS 广播级商业母带压制。

**Architecture:** 
1. `scripts/ingest_material.py` 负责将外部视频链接按指定时间切片（`--section`）下载并强制转码为标准的 1080p CFR 30.000 FPS MP4，或一键提取干声 WAV 与字幕；
2. `scripts/timeline_to_hyperframes.py` 负责读取单一时钟契约 `timeline.json`，自包含转译为符合 HeyGen 规范的 `projects_hf/{project}/` 独立工程（支持 B-Roll 视频视窗、Bento 双卡、推文卡片与 220px 底部安全区字幕）；
3. `scripts/pipeline.py` 扩展 `--engine_render [remotion|hyperframes|both]` 参数，形成“采 ➔ 编 ➔ 配 ➔ 排 ➔ 渲 ➔ 母”闭环。

**Tech Stack:** Python 3.10+, yt-dlp 2026+, ffmpeg, Node.js, HyperFrames CLI 0.8+, GSAP 3, HTML5/CSS3, Remotion 4.0, Pytest.

**Spec:** `docs/superpowers/specs/2026-10-17-hyperframes-and-yt-dlp-workflow-integration-design.md`

## Global Constraints

- 画幅与规格：竖屏 1080 × 1920 (9:16) 与横屏 1920 × 1080 (16:9)，严格锁定 CFR 30.000 FPS；
- 底部移动端安全区：竖屏底部预留 220px，确保字幕与卡片不被平台点赞/评论/标题遮挡；
- 音频母带标准：双遍 ITU-R BS.1770 / EBU R128 标准化，严格锁定综合响度 **-11.0 LUFS**，真峰值 **-0.5 dBFS**；
- 架构兼容性：保持向下 100% 兼容，Remotion 生产线不受任何负面影响；
- 仓库清洁度：通用代码与工具脚本入库，非通用业务音视频素材存本地目录。

---

### Task 1: yt-dlp 素材与音频智能采集中枢 (`scripts/ingest_material.py`)

**Files:**
- Create: `scripts/ingest_material.py`
- Create: `tests/test_ingest_material.py`

**Interfaces:**
- Produces:
  - `parse_section(section_str: str) -> tuple[float, float]`
  - `build_ytdlp_command(...) -> list[str]`
  - `standardize_video(input_path: str, output_path: str, fps: int = 30) -> str`
  - `ingest_asset(url: str, project: str, ...) -> dict`
- CLI Entrypoint: `python scripts/ingest_material.py --url <URL> [--project <PROJECT>] [--section <SEC>] [--audio-only] [--subtitles] [--extract-info]`

- [ ] **Step 1: 编写失败的单元测试 `tests/test_ingest_material.py`**

```python
import os
import pytest
from scripts.ingest_material import parse_section, build_ytdlp_command, normalize_name

def test_parse_section_formats():
    assert parse_section("00:01:15-00:01:30") == (75.0, 90.0)
    assert parse_section("01:15-01:30") == (75.0, 90.0)
    assert parse_section("75-90") == (75.0, 90.0)
    assert parse_section("00:00:10-00:00:25.5") == (10.0, 25.5)

def test_parse_section_invalid():
    with pytest.raises(ValueError):
        parse_section("invalid-format")
    with pytest.raises(ValueError):
        parse_section("00:02:00-00:01:00")  # end before start

def test_normalize_name():
    assert normalize_name("OpenAI Day 6 Reset!!") == "openai_day_6_reset"
    assert normalize_name("测试视频 123") == "测试视频_123"

def test_build_ytdlp_command():
    cmd = build_ytdlp_command(
        url="https://youtube.com/watch?v=demo",
        out_path="temp/test.mp4",
        section="00:01:00-00:01:10",
        audio_only=False
    )
    assert "yt-dlp" in cmd[0] or "python" in cmd[0]
    assert "--download-sections" in cmd
    assert "*60.0-70.0" in cmd or "*00:01:00-00:01:10" in cmd
```

- [ ] **Step 2: 运行测试验证失败**

运行：`pytest tests/test_ingest_material.py -v`  
预期：FAIL with `ModuleNotFoundError: No module named 'scripts.ingest_material'`

- [ ] **Step 3: 实现 `scripts/ingest_material.py`**

实现完整参数解析、时间段转换、yt-dlp 命令拼装、CFR 30fps 转码与文件落地：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/ingest_material.py
基于 yt-dlp 与 ffmpeg 的流媒体素材/B-Roll/干声音频切片采集中枢
"""

import os
import sys
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIVECLIP_PYTHON = r"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe"
PYTHON_EXE = LIVECLIP_PYTHON if os.path.exists(LIVECLIP_PYTHON) else sys.executable

def parse_time_to_seconds(t_str: str) -> float:
    t_str = t_str.strip()
    if ":" in t_str:
        parts = t_str.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return float(t_str)

def parse_section(section_str: str) -> Tuple[float, float]:
    if not section_str or "-" not in section_str:
        raise ValueError(f"Invalid section format: {section_str}. Expected 'start-end' (e.g. 00:01:15-00:01:30)")
    parts = section_str.split("-", 1)
    start_sec = parse_time_to_seconds(parts[0])
    end_sec = parse_time_to_seconds(parts[1])
    if start_sec >= end_sec:
        raise ValueError(f"Start time ({start_sec}s) must be less than end time ({end_sec}s)")
    return (start_sec, end_sec)

def normalize_name(raw_name: str) -> str:
    cleaned = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', raw_name).strip()
    return re.sub(r'[-\s]+', '_', cleaned).lower()

def build_ytdlp_command(
    url: str,
    out_path: str,
    section: Optional[str] = None,
    audio_only: bool = False,
    subtitles: bool = False,
    extract_info: bool = False
) -> list:
    cmd = [PYTHON_EXE, "-m", "yt_dlp", url]
    if extract_info:
        cmd.extend(["--dump-json", "--no-download"])
        return cmd
    if audio_only:
        cmd.extend(["-x", "--audio-format", "wav", "-o", out_path])
        return cmd
    if section:
        start_sec, end_sec = parse_section(section)
        cmd.extend(["--download-sections", f"*{start_sec:.1f}-{end_sec:.1f}", "--force-keyframes-at-cuts"])
    if subtitles:
        cmd.extend(["--write-sub", "--sub-lang", "zh-Hans,zh,en", "--skip-download"])
    cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", out_path])
    return cmd

def standardize_video(input_path: str, output_path: str, fps: int = 30) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"fps={fps}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    ret = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if ret.returncode != 0:
        raise RuntimeError(f"FFmpeg 转码失败: {ret.stderr}")
    return output_path
```

- [ ] **Step 4: 运行单元测试验证全部通过**

运行：`pytest tests/test_ingest_material.py -v`  
预期：PASS (3/3 tests passed)

- [ ] **Step 5: 提交代码**

```bash
git add scripts/ingest_material.py tests/test_ingest_material.py
git commit -m "feat(ingest): add yt-dlp material ingestion and video standardization hub"
```

---

### Task 2: HyperFrames 转译中枢增强与 B-Roll 视窗支持 (`scripts/timeline_to_hyperframes.py`)

**Files:**
- Modify: `scripts/timeline_to_hyperframes.py`
- Modify: `tests/test_timeline_to_hyperframes.py`

**Interfaces:**
- Consumes: `timeline.json` (scenes, words, audioPath, broll, layout)
- Produces: `projects_hf/{project}/` (`index.html`, `styles.css`, `script.js`, `hyperframes.json`)
- Adds component support: `render_broll_clip(scene, scene_id)`

- [ ] **Step 1: 编写针对 B-Roll 视窗与 HyperFrames 契约的测试用例**

在 `tests/test_timeline_to_hyperframes.py` 中增加对 `render_broll_clip`、全自包含资产复制与 `projects_hf/` 目录结构的断言测试：
```python
def test_render_broll_clip_markup():
    from scripts.timeline_to_hyperframes import render_broll_clip
    scene = {
        "id": "scene_02",
        "type": "VideoBroll",
        "title": "展示开源系统运行画面",
        "footage": "assets/footage/demo_broll.mp4",
        "mode": "pip"  # pip (画中画) 或 background (全屏背景)
    }
    markup = render_broll_clip(scene, "scene_02")
    assert "<video" in markup
    assert 'class="broll-clip' in markup
    assert 'src="assets/footage/demo_broll.mp4"' in markup
```

- [ ] **Step 2: 运行测试验证失败**

运行：`pytest tests/test_timeline_to_hyperframes.py -v`  
预期：FAIL with `ImportError: cannot import name 'render_broll_clip'`

- [ ] **Step 3: 扩展 `scripts/timeline_to_hyperframes.py`**

1. 增加 `render_broll_clip` 组件生成器；
2. 在 `generate_hyperframes_html` 中加入对 `VideoBroll`、`scene.footage` 的多态路由；
3. 在 `styles.css` 模板中完善 `.broll-clip`、`.pip-card`、`.broll-overlay` 等高质量动效样式；
4. 确保生成自包含音频与视频资产拷贝至 `projects_hf/{project}/assets/`。

- [ ] **Step 4: 运行测试验证全部通过**

运行：`pytest tests/test_timeline_to_hyperframes.py -v`  
预期：PASS

- [ ] **Step 5: 提交代码**

```bash
git add scripts/timeline_to_hyperframes.py tests/test_timeline_to_hyperframes.py
git commit -m "feat(hyperframes): enhance timeline_to_hyperframes adapter with b-roll video clip support"
```

---

### Task 3: 总控流水线双轨调度与工程规范 (`scripts/pipeline.py` & `package.json`)

**Files:**
- Modify: `scripts/pipeline.py:40-125`
- Modify: `package.json:6-14`
- Create: `tests/test_pipeline_engine_render.py`

**Interfaces:**
- CLI Flags:
  - `--engine_render`: `['remotion', 'hyperframes', 'both']` (default: `'remotion'`)
- Pipeline Steps:
  - Step 3: 条件路由到 Remotion 或 HyperFrames 渲染器
  - Step 4: 统一调用 `audio_mastering.py --video` 进行 -11.0 LUFS 广播级母带压制

- [ ] **Step 1: 编写针对 `pipeline.py` 双引擎调度的测试**

```python
import pytest
from scripts.pipeline import build_render_commands

def test_build_render_commands_remotion():
    cmds = build_render_commands(project="demo", engine="remotion", concurrency=4)
    assert len(cmds) == 1
    assert "remotion render" in cmds[0]["cmd"]
    assert "out/demo.mp4" in cmds[0]["cmd"]

def test_build_render_commands_hyperframes():
    cmds = build_render_commands(project="demo", engine="hyperframes", concurrency=4)
    assert len(cmds) == 3
    # Step 1: timeline_to_hyperframes
    assert "timeline_to_hyperframes.py" in cmds[0]["cmd"]
    # Step 2: hyperframes check
    assert "hyperframes check" in cmds[1]["cmd"]
    # Step 3: hyperframes render
    assert "hyperframes render" in cmds[2]["cmd"]

def test_build_render_commands_both():
    cmds = build_render_commands(project="demo", engine="both", concurrency=4)
    assert any("remotion render" in c["cmd"] for c in cmds)
    assert any("hyperframes render" in c["cmd"] for c in cmds)
```

- [ ] **Step 2: 运行测试验证失败**

运行：`pytest tests/test_pipeline_engine_render.py -v`  
预期：FAIL with `cannot import name 'build_render_commands'`

- [ ] **Step 3: 修改 `scripts/pipeline.py` 与 `package.json`**

1. 在 `scripts/pipeline.py` 中抽象 `build_render_commands`，并支持 `--engine_render` 参数；
2. 调度执行 `hyperframes check` 与 `hyperframes render`；
3. 更新 `package.json` 中的快捷指令：
   ```json
   "ingest": "python scripts/ingest_material.py",
   "dev:hf": "hyperframes preview",
   "render:hf": "hyperframes render",
   "pipeline:hf": "python scripts/pipeline.py --render --engine_render hyperframes"
   ```

- [ ] **Step 4: 运行测试验证全部通过**

运行：`pytest tests/test_pipeline_engine_render.py -v`  
预期：PASS

- [ ] **Step 5: 提交代码**

```bash
git add scripts/pipeline.py package.json tests/test_pipeline_engine_render.py
git commit -m "feat(pipeline): support dual-engine render scheduling for Remotion and HyperFrames"
```

---

### Task 4: 端到端全链路集成验证与质量门禁

**Files:**
- Create: `content/scripts/test_hyperframes_integration.json`
- Verify: `out/test_hyperframes_integration.mp4`

**Interfaces:**
- Verifies:
  - `ingest_material.py` 能成功抓取/切片素材
  - `pipeline.py --engine_render hyperframes` 走通全链路
  - `hyperframes check` 质量门禁 100% 通过
  - 音频母带压制满足 EBU R128 -11.0 LUFS 广播级标准

- [ ] **Step 1: 准备测试分镜脚本 `content/scripts/test_hyperframes_integration.json`**

包含 Headline、TweetEmbed、BinaryBento 与 B-Roll 视窗的典型短视频结构。

- [ ] **Step 2: 执行全链路流水线构建与渲染**

```bash
python scripts/pipeline.py --script content/scripts/test_hyperframes_integration.json --project test_hyperframes_integration --render --engine_render hyperframes
```

- [ ] **Step 3: 校验导出成片质量**

1. 确认 `out/test_hyperframes_integration.mp4` 文件存在，大小合理；
2. 确认 `hyperframes check projects_hf/test_hyperframes_integration` 输出 0 错误；
3. 确认音轨综合响度满足 -11.0 ± 0.5 LUFS。

- [ ] **Step 4: 运行全套单元测试**

运行：`pytest tests/`  
预期：所有测试 100% 通过。

- [ ] **Step 5: 提交最终集成代码**

```bash
git add content/scripts/test_hyperframes_integration.json
git commit -m "test(integration): verify end-to-end hyperframes dual-engine render pipeline"
```

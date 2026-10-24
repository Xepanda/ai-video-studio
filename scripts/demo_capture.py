#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/demo_capture.py
GitHub 项目深度演示: Playwright 真实网页捕获模块 (Phase 1 W5-6 场景二)

功能特性:
  1. 对规格声明的目标 URL 执行真实浏览器捕获 (Chromium headless):
     - 全页/视口截图 (PNG) -> public/images/demo_capture/{id}.png
     - 页面录屏 (WebM)     -> public/footage/demo_capture/{id}.webm
     - 运行时 events: console 消息 / pageerror / requestfailed (如实记录, 供质检)
  2. 数据诚信承诺 (延续审计 A3 + 执行计划"安装失败显式降级"同款策略):
     - 导航超时/浏览器不可用/截图失败 -> 该目标记录 status=failed 并附真实错误,
       manifest 中 screenshot/video 一律为 null, 绝不伪造捕获证据;
     - Playwright 未安装 -> 全局 CaptureError (环境问题, 附安装指引), 不静默降级;
  3. manifest 与 storyboard 消费契约:
     - screenshotStatic: public/ 相对路径, 供 Remotion staticFile() 直接引用
       (UniversalScene WebBrowserMockup/BrowserScreenshot 分支的 browser.image);
     - events 每类上限 50 条, 防止 manifest 膨胀。

用法 (通常由 github_demo_pipeline.py 调用, 亦可独立使用):
  python scripts/demo_capture.py --url https://github.com/yt-dlp/yt-dlp --id ytdlp_home
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SCREENSHOT_DIR = os.path.join("public", "images", "demo_capture")
DEFAULT_VIDEO_DIR = os.path.join("public", "footage", "demo_capture")

DEFAULT_NAV_TIMEOUT_MS = 30000       # 导航超时 (毫秒)
DEFAULT_SETTLE_MS = 1500             # 页面稳定等待 (毫秒)
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
VALID_WAIT_UNTIL = ("load", "domcontentloaded", "networkidle", "commit")
MAX_EVENTS_PER_KIND = 50             # events 每类记录上限


class CaptureError(Exception):
    """捕获环境级失败 (Playwright 未安装等全局问题)。

    与单目标失败 (记录 status=failed) 区分: 环境问题影响所有目标, 必须显式抛错。
    """


def _load_playwright():
    """延迟加载 Playwright sync API (测试可经 sys.modules 注入伪模块)。"""
    try:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    except ImportError as e:
        raise CaptureError(
            f"缺少 Playwright 依赖 (requirements.txt 核心层已声明): {e}\n"
            "  请执行: pip install playwright && playwright install chromium"
        )
    return sync_playwright, PlaywrightError, PlaywrightTimeoutError


def _new_record(target_id: str, url: str) -> Dict[str, Any]:
    return {
        "id": target_id,
        "url": url,
        "status": "pending",
        "screenshot": None,        # PROJECT_ROOT 相对路径
        "screenshotStatic": None,  # public/ 相对路径 (Remotion staticFile 消费)
        "video": None,             # PROJECT_ROOT 相对路径
        "videoStatic": None,       # public/ 相对路径
        "fullPage": True,
        "waitUntil": "networkidle",
        "events": {"console": [], "pageErrors": [], "failedRequests": []},
        "error": None,
        "capturedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }


def _fail_record(record: Dict[str, Any], error: str) -> Dict[str, Any]:
    """单目标失败: 状态如实标记, 证据字段保持 null (绝不伪造)。"""
    record["status"] = "failed"
    record["error"] = error
    record["screenshot"] = None
    record["screenshotStatic"] = None
    record["video"] = None
    record["videoStatic"] = None
    return record


def _safe_relpath(path: str, start: str) -> str:
    """跨盘符时 relpath 不可用 (Windows ValueError), 回退绝对路径 (绝不因此失败)。"""
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return path


def capture_target(
    url: str,
    target_id: str,
    out_dir: str = DEFAULT_SCREENSHOT_DIR,
    video_dir: str = DEFAULT_VIDEO_DIR,
    full_page: bool = True,
    wait_until: str = "networkidle",
    nav_timeout_ms: int = DEFAULT_NAV_TIMEOUT_MS,
    settle_ms: int = DEFAULT_SETTLE_MS,
    viewport: Optional[Dict[str, int]] = None,
    record_video: bool = True,
) -> Dict[str, Any]:
    """真实捕获单个目标 URL, 返回 manifest 记录 (status: ok/failed)。

    失败策略: 任何单目标级失败 (导航超时/截图异常/浏览器启动失败) 均记录为
    status=failed 并携带真实错误; 不抛出, 由调用方汇总 (与热点聚合器单源失败同款语义)。
    环境级失败 (Playwright 缺失) 抛 CaptureError。
    """
    if wait_until not in VALID_WAIT_UNTIL:
        return _fail_record(_new_record(target_id, url),
                            f"非法 wait_until: {wait_until!r} (可选: {VALID_WAIT_UNTIL})")
    if not url or not url.strip():
        return _fail_record(_new_record(target_id, url), "目标 URL 为空")

    sync_playwright, pw_error, pw_timeout = _load_playwright()

    record = _new_record(target_id, url)
    record["fullPage"] = full_page
    record["waitUntil"] = wait_until

    shot_dir_abs = out_dir if os.path.isabs(out_dir) else os.path.join(PROJECT_ROOT, out_dir)
    vid_dir_abs = video_dir if os.path.isabs(video_dir) else os.path.join(PROJECT_ROOT, video_dir)
    os.makedirs(shot_dir_abs, exist_ok=True)
    shot_path = os.path.join(shot_dir_abs, f"{target_id}.png")
    if record_video:
        os.makedirs(vid_dir_abs, exist_ok=True)

    events = record["events"]

    def _on_console(msg: Any) -> None:
        if len(events["console"]) < MAX_EVENTS_PER_KIND:
            events["console"].append({"type": getattr(msg, "type", "?"), "text": str(getattr(msg, "text", ""))[:200]})

    def _on_pageerror(err: Any) -> None:
        if len(events["pageErrors"]) < MAX_EVENTS_PER_KIND:
            events["pageErrors"].append(str(err)[:300])

    def _on_requestfailed(req: Any) -> None:
        if len(events["failedRequests"]) < MAX_EVENTS_PER_KIND:
            events["failedRequests"].append({
                "url": str(getattr(req, "url", ""))[:200],
                "failure": str(getattr(req, "failure", "") or "")[:200],
            })

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context_kwargs: Dict[str, Any] = {
                    "viewport": viewport or DEFAULT_VIEWPORT,
                }
                if record_video:
                    context_kwargs["record_video_dir"] = vid_dir_abs
                context = browser.new_context(**context_kwargs)
                page = context.new_page()
                page.on("console", _on_console)
                page.on("pageerror", _on_pageerror)
                page.on("requestfailed", _on_requestfailed)

                page.goto(url.strip(), timeout=nav_timeout_ms, wait_until=wait_until)
                if settle_ms > 0:
                    page.wait_for_timeout(settle_ms)

                page.screenshot(path=shot_path, full_page=full_page)

                video_tmp: Optional[str] = None
                if record_video and page.video is not None:
                    try:
                        video_tmp = page.video.path()
                    except Exception:  # noqa: BLE001 - video 路径获取失败不阻断截图成果
                        video_tmp = None
                context.close()  # 关闭上下文以 finalized 录屏文件

                if not os.path.exists(shot_path) or os.path.getsize(shot_path) == 0:
                    return _fail_record(record, f"截图文件未生成或为空: {shot_path}")

                record["status"] = "ok"
                record["screenshot"] = _safe_relpath(shot_path, PROJECT_ROOT)
                record["screenshotStatic"] = _safe_relpath(
                    shot_path, os.path.join(PROJECT_ROOT, "public")
                )
                if video_tmp and os.path.exists(video_tmp):
                    video_final = os.path.join(vid_dir_abs, f"{target_id}.webm")
                    shutil.move(video_tmp, video_final)
                    record["video"] = _safe_relpath(video_final, PROJECT_ROOT)
                    record["videoStatic"] = _safe_relpath(
                        video_final, os.path.join(PROJECT_ROOT, "public")
                    )
            finally:
                browser.close()
    except pw_timeout as e:
        return _fail_record(record, f"导航超时 ({nav_timeout_ms}ms, wait_until={wait_until}): {e}")
    except pw_error as e:
        return _fail_record(record, f"Playwright 执行错误: {e}")
    except Exception as e:  # noqa: BLE001 - 未预期异常同样如实记录, 绝不静默
        return _fail_record(record, f"未预期异常 {type(e).__name__}: {e}")

    return record


def run_captures(
    targets: List[Dict[str, Any]],
    out_dir: str = DEFAULT_SCREENSHOT_DIR,
    video_dir: str = DEFAULT_VIDEO_DIR,
    nav_timeout_ms: int = DEFAULT_NAV_TIMEOUT_MS,
    settle_ms: int = DEFAULT_SETTLE_MS,
) -> List[Dict[str, Any]]:
    """按序捕获规格声明的目标列表; 单目标失败不影响其他目标 (状态如实记录)。"""
    records: List[Dict[str, Any]] = []
    for idx, target in enumerate(targets):
        target_id = str(target.get("id") or f"target_{idx + 1}")
        url = str(target.get("url") or "")
        print(f"📸 [Capture {idx + 1}/{len(targets)}] 正在真实捕获: {target_id} ({url})")
        try:
            rec = capture_target(
                url=url,
                target_id=target_id,
                out_dir=out_dir,
                video_dir=video_dir,
                full_page=bool(target.get("full_page", True)),
                wait_until=str(target.get("wait_until", "networkidle")),
                nav_timeout_ms=nav_timeout_ms,
                settle_ms=settle_ms,
                record_video=bool(target.get("record_video", True)),
            )
        except CaptureError as e:
            # 环境级失败 (如 Playwright 缺失): 记录为 failed 并继续其他目标
            rec = _fail_record(_new_record(target_id, url), str(e))
        if rec["status"] == "ok":
            print(f"✅ [Capture] {target_id}: 截图 + 录屏 + events 已归档")
        else:
            print(f"⚠️ [Capture] {target_id} 失败 (已如实记录, 未伪造证据): {rec['error']}")
        records.append(rec)
    return records


def summarize_captures(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """捕获结果汇总 (供 storyboard source 元数据与收尾提示消费)。"""
    ok = [r for r in records if r.get("status") == "ok"]
    failed = [r for r in records if r.get("status") != "ok"]
    return {
        "attempted": len(records),
        "ok": len(ok),
        "failed": len(failed),
        "failedIds": [r.get("id") for r in failed],
        "records": records,
    }


def get_parser() -> argparse.ArgumentParser:
    """定义并返回独立捕获命令行解析器 (调试/补捕入口)"""
    parser = argparse.ArgumentParser(description="Playwright 真实网页捕获 (截图+录屏+events)")
    parser.add_argument("--url", type=str, required=True, help="目标 URL")
    parser.add_argument("--id", type=str, required=True, help="目标标识 (产物文件名)")
    parser.add_argument("--out-dir", type=str, default=DEFAULT_SCREENSHOT_DIR, help="截图输出目录")
    parser.add_argument("--video-dir", type=str, default=DEFAULT_VIDEO_DIR, help="录屏输出目录")
    parser.add_argument("--no-video", action="store_true", help="禁用录屏 (仅截图)")
    parser.add_argument("--viewport-only", action="store_true", help="仅截取视口 (默认全页)")
    parser.add_argument("--wait-until", type=str, default="networkidle", choices=list(VALID_WAIT_UNTIL))
    parser.add_argument("--nav-timeout-ms", type=int, default=DEFAULT_NAV_TIMEOUT_MS)
    parser.add_argument("--settle-ms", type=int, default=DEFAULT_SETTLE_MS)
    parser.add_argument("--json", action="store_true", help="以 JSON 输出 manifest 记录")
    return parser


def main():
    args = get_parser().parse_args()

    try:
        record = capture_target(
            url=args.url,
            target_id=args.id,
            out_dir=args.out_dir,
            video_dir=args.video_dir,
            full_page=not args.viewport_only,
            wait_until=args.wait_until,
            nav_timeout_ms=args.nav_timeout_ms,
            settle_ms=args.settle_ms,
            record_video=not args.no_video,
        )
    except CaptureError as e:
        print(f"\n❌ [Capture] {e}")
        sys.exit(2)

    if args.json:
        print(json.dumps(record, ensure_ascii=False, indent=2))
    else:
        print(f"\n=======================================================")
        print(f"📸 [Capture] 目标 {args.id}: status={record['status']}")
        if record["status"] == "ok":
            print(f"   截图: {record['screenshot']}")
            print(f"   录屏: {record['video'] or '<未启用>'}")
            print(f"   events: console={len(record['events']['console'])} "
                  f"pageErrors={len(record['events']['pageErrors'])} "
                  f"failedRequests={len(record['events']['failedRequests'])}")
        else:
            print(f"   错误: {record['error']}")
        print(f"=======================================================\n")

    sys.exit(0 if record["status"] == "ok" else 1)


if __name__ == "__main__":
    main()

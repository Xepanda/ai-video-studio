#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_demo_capture.py
scripts/demo_capture.py 与 github_demo_pipeline.py 捕获集成 单元测试 (离线):
1. 伪 Playwright 模块经 sys.modules 注入 (不启动真实浏览器):
   - 成功捕获: 截图文件生成 + 录屏归位 + manifest 路径契约
   - 各类失败: 导航超时 / Playwright 错误 / 空截图文件 -> status=failed 且证据为 null
   - events 收集与 50 条上限
2. run_captures 多目标汇总 (单目标失败不影响其他) 与环境级 CaptureError 降级
3. github_demo_pipeline 集成:
   - validate_spec 对 capture.targets 的契约校验 (重复 id/非法 url/wait_until/full_page/duration)
   - build_storyboard 生成 BrowserScreenshot 场景 (仅成功捕获入画面) + captureResult 元数据
"""

import os
import sys
import json
import types
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts import demo_capture
from scripts.demo_capture import CaptureError, capture_target, run_captures, summarize_captures
from scripts.github_demo_pipeline import (
    DemoPipelineError,
    validate_spec,
    build_storyboard,
    SPEC_VERSION,
)


# ---------------------------------------------------------------------------
# 伪 Playwright 模块 (行为经模块级 CURRENT_BEHAVIOR 控制)
# ---------------------------------------------------------------------------

class FakePWError(Exception):
    pass


class FakePWTimeout(Exception):
    pass


CURRENT_BEHAVIOR: dict = {}


class FakeConsoleMsg:
    def __init__(self, type_, text):
        self.type = type_
        self.text = text


class FakeRequest:
    def __init__(self, url, failure):
        self.url = url
        self.failure = failure


class FakeVideo:
    def __init__(self, path):
        self._path = path

    def path(self):
        return self._path


class FakePage:
    def __init__(self):
        self.handlers = {}
        self.video = None

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def _emit(self, event, payload):
        for h in self.handlers.get(event, []):
            h(payload)

    def goto(self, url, timeout=None, wait_until=None):
        b = CURRENT_BEHAVIOR
        if b.get("goto_error") == "timeout":
            raise FakePWTimeout(f"Timeout {timeout}ms exceeded.")
        if b.get("goto_error") == "error":
            raise FakePWError("net::ERR_NAME_NOT_RESOLVED")
        # 模拟加载期间的 events
        for i in range(b.get("console_count", 0)):
            self._emit("console", FakeConsoleMsg("log", f"console-{i}"))
        for i in range(b.get("pageerror_count", 0)):
            self._emit("pageerror", f"ReferenceError: x{i} is not defined")
        for i in range(b.get("failed_request_count", 0)):
            self._emit("requestfailed", FakeRequest(f"https://cdn.example.com/{i}.png", "net::ERR_FAILED"))

    def wait_for_timeout(self, ms):
        pass

    def screenshot(self, path=None, full_page=False):
        if CURRENT_BEHAVIOR.get("screenshot_empty"):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")  # 空文件 -> 应判失败
            return
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)


class FakeContext:
    def __init__(self, record_video):
        self._record_video = record_video
        self.page = FakePage()

    def new_page(self):
        return self.page

    def close(self):
        pass


class FakeBrowser:
    def __init__(self):
        self.closed = False

    def new_context(self, **kwargs):
        ctx = FakeContext(record_video="record_video_dir" in kwargs)
        if ctx._record_video:
            # 录屏临时文件 (模拟 Playwright 的 uuid 命名)
            tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
            tmp.write(b"\x1a\x45\xdf\xa3" + b"\x00" * 32)
            tmp.close()
            ctx.page.video = FakeVideo(tmp.name)
            CURRENT_BEHAVIOR["_video_tmp"] = tmp.name
        return ctx

    def close(self):
        self.closed = True


class FakeChromium:
    def launch(self, headless=True):
        if CURRENT_BEHAVIOR.get("launch_error"):
            raise FakePWError("Browser doesn't exist... run playwright install")
        return FakeBrowser()


class FakePlaywright:
    def __init__(self):
        self.chromium = FakeChromium()


class FakePWCtx:
    def __enter__(self):
        return FakePlaywright()

    def __exit__(self, *args):
        return False


def fake_sync_playwright():
    return FakePWCtx()


def install_fake_playwright():
    """注入伪 playwright 包与 sync_api 模块, 返回原始模块字典 (供卸载)。"""
    saved = {k: sys.modules.get(k) for k in ("playwright", "playwright.sync_api")}
    pkg = types.ModuleType("playwright")
    api = types.ModuleType("playwright.sync_api")
    api.sync_playwright = fake_sync_playwright
    api.Error = FakePWError
    api.TimeoutError = FakePWTimeout
    sys.modules["playwright"] = pkg
    sys.modules["playwright.sync_api"] = api
    return saved


def uninstall_fake_playwright(saved):
    for key, mod in saved.items():
        if mod is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = mod


class FakePlaywrightTestCase(unittest.TestCase):
    def setUp(self):
        CURRENT_BEHAVIOR.clear()
        self._saved_modules = install_fake_playwright()

    def tearDown(self):
        uninstall_fake_playwright(self._saved_modules)
        video_tmp = CURRENT_BEHAVIOR.pop("_video_tmp", None)
        if video_tmp and os.path.exists(video_tmp):
            os.remove(video_tmp)  # 捕获成功时已被 move; 失败时清理残留
        CURRENT_BEHAVIOR.clear()


class TestCaptureTarget(FakePlaywrightTestCase):

    def test_success_with_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            shot_dir = os.path.join(tmp, "shots")
            vid_dir = os.path.join(tmp, "videos")
            rec = capture_target(
                url="https://github.com/yt-dlp/yt-dlp",
                target_id="ytdlp_home",
                out_dir=shot_dir, video_dir=vid_dir,
            )
            self.assertEqual(rec["status"], "ok")
            self.assertIsNone(rec["error"])
            # 截图文件真实存在
            self.assertTrue(os.path.exists(os.path.join(shot_dir, "ytdlp_home.png")))
            # 路径契约: PROJECT_ROOT 相对 + public 相对 (Remotion staticFile 消费)
            self.assertTrue(rec["screenshot"].endswith("ytdlp_home.png"))
            self.assertNotIn("\\public\\", rec["screenshotStatic"].replace("/", "\\"))
            # 录屏归位为确定性文件名
            self.assertTrue(rec["video"].endswith("ytdlp_home.webm"))
            self.assertTrue(os.path.exists(os.path.join(vid_dir, "ytdlp_home.webm")))
            self.assertEqual(rec["waitUntil"], "networkidle")
            self.assertTrue(rec["fullPage"])

    def test_success_without_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://example.com", target_id="novideo",
                out_dir=os.path.join(tmp, "s"), video_dir=os.path.join(tmp, "v"),
                record_video=False,
            )
            self.assertEqual(rec["status"], "ok")
            self.assertIsNone(rec["video"])
            self.assertIsNone(rec["videoStatic"])

    def test_goto_timeout_is_failed_not_fabricated(self):
        CURRENT_BEHAVIOR["goto_error"] = "timeout"
        with tempfile.TemporaryDirectory() as tmp:
            shot_dir = os.path.join(tmp, "s")
            rec = capture_target(
                url="https://slow.example.com", target_id="slow",
                out_dir=shot_dir, video_dir=os.path.join(tmp, "v"),
            )
            self.assertEqual(rec["status"], "failed")
            self.assertIn("超时", rec["error"])
            # 数据诚信: 失败时证据字段一律 null, 且不产生截图文件
            self.assertIsNone(rec["screenshot"])
            self.assertIsNone(rec["video"])
            self.assertFalse(os.path.exists(os.path.join(shot_dir, "slow.png")))

    def test_playwright_error_is_failed(self):
        CURRENT_BEHAVIOR["goto_error"] = "error"
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://nope.invalid", target_id="nope",
                out_dir=os.path.join(tmp, "s"), video_dir=os.path.join(tmp, "v"),
            )
            self.assertEqual(rec["status"], "failed")
            self.assertIn("Playwright", rec["error"])

    def test_browser_launch_failure_is_failed(self):
        CURRENT_BEHAVIOR["launch_error"] = True
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://example.com", target_id="nobrowser",
                out_dir=os.path.join(tmp, "s"), video_dir=os.path.join(tmp, "v"),
            )
            self.assertEqual(rec["status"], "failed")
            self.assertIn("Browser", rec["error"])

    def test_empty_screenshot_file_is_failed(self):
        CURRENT_BEHAVIOR["screenshot_empty"] = True
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://example.com", target_id="blank",
                out_dir=os.path.join(tmp, "s"), video_dir=os.path.join(tmp, "v"),
            )
            self.assertEqual(rec["status"], "failed")
            self.assertIn("为空", rec["error"])

    def test_invalid_wait_until_fails_without_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://example.com", target_id="badwait",
                out_dir=os.path.join(tmp, "s"), wait_until="not-a-mode",
            )
            self.assertEqual(rec["status"], "failed")
            self.assertIn("wait_until", rec["error"])

    def test_empty_url_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(url="   ", target_id="empty", out_dir=os.path.join(tmp, "s"))
            self.assertEqual(rec["status"], "failed")
            self.assertIn("URL", rec["error"])

    def test_events_collected_and_capped(self):
        CURRENT_BEHAVIOR.update({
            "console_count": 60,       # 超过 50 上限
            "pageerror_count": 2,
            "failed_request_count": 3,
        })
        with tempfile.TemporaryDirectory() as tmp:
            rec = capture_target(
                url="https://example.com", target_id="events",
                out_dir=os.path.join(tmp, "s"), video_dir=os.path.join(tmp, "v"),
            )
            self.assertEqual(rec["status"], "ok")
            self.assertEqual(len(rec["events"]["console"]), demo_capture.MAX_EVENTS_PER_KIND)
            self.assertEqual(len(rec["events"]["pageErrors"]), 2)
            self.assertEqual(len(rec["events"]["failedRequests"]), 3)
            self.assertEqual(rec["events"]["console"][0]["type"], "log")


class TestRunCaptures(FakePlaywrightTestCase):

    def test_multi_target_partial_failure(self):
        behaviors = [{}, {"goto_error": "timeout"}]
        # run_captures 内部按序调用 capture_target; 用副作用切换行为
        original = demo_capture.capture_target

        def side_effect(**kwargs):
            CURRENT_BEHAVIOR.clear()
            CURRENT_BEHAVIOR.update(behaviors.pop(0))
            return original(**kwargs)

        demo_capture.capture_target = side_effect
        try:
            with tempfile.TemporaryDirectory() as tmp:
                records = run_captures(
                    [
                        {"id": "good", "url": "https://example.com"},
                        {"id": "bad", "url": "https://slow.example.com"},
                    ],
                    out_dir=os.path.join(tmp, "s"),
                    video_dir=os.path.join(tmp, "v"),
                )
        finally:
            demo_capture.capture_target = original

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["status"], "ok")
        self.assertEqual(records[1]["status"], "failed")
        summary = summarize_captures(records)
        self.assertEqual(summary["attempted"], 2)
        self.assertEqual(summary["ok"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["failedIds"], ["bad"])

    def test_env_level_capture_error_recorded_as_failed(self):
        # 环境级失败 (Playwright 缺失) 经 run_captures 收敛为单目标 failed 记录
        original = demo_capture.capture_target

        def raise_env(**kwargs):
            raise CaptureError("缺少 Playwright 依赖")

        demo_capture.capture_target = raise_env
        try:
            records = run_captures([{"id": "t1", "url": "https://example.com"}])
        finally:
            demo_capture.capture_target = original

        self.assertEqual(records[0]["status"], "failed")
        self.assertIn("Playwright", records[0]["error"])
        self.assertIsNone(records[0]["screenshot"])

    def test_capture_target_propagates_env_error_directly(self):
        # 直接调用 capture_target 时环境级失败抛 CaptureError (不被吞)
        self._saved_modules = uninstall_fake_playwright(self._saved_modules) or self._saved_modules
        # 卸载伪模块后, 若真实环境无 playwright 则应抛 CaptureError; 有则跳过本断言
        try:
            import playwright.sync_api  # noqa: F401
            real_installed = True
        except ImportError:
            real_installed = False
        if real_installed:
            self.skipTest("真实环境已安装 Playwright, 无法验证缺失分支")
        with self.assertRaises(CaptureError):
            capture_target(url="https://example.com", target_id="x",
                           out_dir=tempfile.mkdtemp())


# ---------------------------------------------------------------------------
# github_demo_pipeline 捕获集成
# ---------------------------------------------------------------------------

def make_spec_with_capture():
    spec = {
        "spec_version": SPEC_VERSION,
        "project": {
            "name": "demo-proj",
            "repo": "https://github.com/example/demo.git",
            "title": "演示项目",
        },
        "run": {
            "steps": [
                {"id": "s1", "title": "步骤一", "cmd": "echo hi", "duration": 5},
            ],
        },
        "capture": {
            "enabled": True,
            "targets": [
                {"id": "home", "url": "https://github.com/example/demo", "duration": 4},
            ],
        },
    }
    return validate_spec(spec)


def make_capture_summary():
    return {
        "attempted": 2, "ok": 1, "failed": 1, "failedIds": ["wiki"],
        "records": [
            {
                "id": "home", "url": "https://github.com/example/demo", "status": "ok",
                "screenshot": "public/images/demo_capture/home.png",
                "screenshotStatic": "images/demo_capture/home.png",
                "video": "public/footage/demo_capture/home.webm",
                "videoStatic": "footage/demo_capture/home.webm",
                "events": {"console": [], "pageErrors": [], "failedRequests": []},
                "error": None,
            },
            {
                "id": "wiki", "url": "https://github.com/example/demo/wiki", "status": "failed",
                "screenshot": None, "screenshotStatic": None, "video": None, "videoStatic": None,
                "events": {"console": [], "pageErrors": [], "failedRequests": []},
                "error": "导航超时 (30000ms)",
            },
        ],
    }


class TestSpecCaptureValidation(unittest.TestCase):

    def test_valid_capture_targets(self):
        spec = make_spec_with_capture()
        self.assertEqual(spec["capture"]["targets"][0]["id"], "home")

    def test_duplicate_target_id_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["targets"].append(
            {"id": "home", "url": "https://example.com"})
        with self.assertRaises(DemoPipelineError) as ctx:
            validate_spec(spec)
        self.assertIn("重复", str(ctx.exception))

    def test_non_http_url_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["targets"][0]["url"] = "ftp://example.com"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_bad_wait_until_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["targets"][0]["wait_until"] = "forever"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_full_page_non_bool_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["targets"][0]["full_page"] = "yes"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_negative_duration_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["targets"][0]["duration"] = 0
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_enabled_non_bool_rejected(self):
        spec = make_spec_with_capture()
        spec["capture"]["enabled"] = "true"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)


class TestStoryboardCaptureIntegration(unittest.TestCase):

    def test_browser_screenshot_scene_only_for_ok_captures(self):
        spec = make_spec_with_capture()
        install_result = {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}
        step_records = [{
            "id": "s1", "title": "步骤一", "cmd": "echo hi", "expect_exit": 0,
            "capture": "terminal", "narration": "", "duration": 5,
            "status": "ok", "exit_code": 0, "output_excerpt": "hi",
        }]
        storyboard = build_storyboard(
            spec, install_result, step_records, "spec.yaml",
            capture_summary=make_capture_summary(),
        )
        scenes = storyboard["scenes"]
        types = [s["type"] for s in scenes]

        # 场景序列: 开场 -> BrowserScreenshot(仅 ok) -> TerminalWindow -> 收尾
        self.assertEqual(types[0], "MinimalHeadline")
        self.assertEqual(types[1], "BrowserScreenshot")
        self.assertIn("TerminalWindow", types)
        self.assertEqual(types[-1], "MinimalHeadline")
        self.assertEqual(types.count("BrowserScreenshot"), 1)  # 失败的 wiki 不入画面

        cap_scene = scenes[1]
        self.assertEqual(cap_scene["id"], "scene_cap_home")
        self.assertEqual(cap_scene["browser"]["image"], "images/demo_capture/home.png")
        self.assertEqual(cap_scene["browser"]["url"], "https://github.com/example/demo")
        self.assertEqual(cap_scene["demoCapture"]["video"], "public/footage/demo_capture/home.webm")

        # captureResult 元数据完整留痕 (含失败目标)
        cap_result = storyboard["captureResult"]
        self.assertEqual(cap_result["attempted"], 2)
        self.assertEqual(cap_result["ok"], 1)
        self.assertEqual(cap_result["failedIds"], ["wiki"])
        failed_record = [r for r in cap_result["records"] if r["id"] == "wiki"][0]
        self.assertEqual(failed_record["status"], "failed")

    def test_no_capture_summary_keeps_legacy_structure(self):
        spec = make_spec_with_capture()
        install_result = {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}
        step_records = [{
            "id": "s1", "title": "步骤一", "cmd": "echo hi", "expect_exit": 0,
            "capture": "terminal", "narration": "", "duration": 5,
            "status": "ok", "exit_code": 0, "output_excerpt": "hi",
        }]
        storyboard = build_storyboard(spec, install_result, step_records, "spec.yaml")
        self.assertNotIn("BrowserScreenshot", [s["type"] for s in storyboard["scenes"]])
        self.assertEqual(storyboard["captureResult"]["attempted"], 0)

    def test_spec_without_capture_section_still_valid(self):
        spec = {
            "spec_version": SPEC_VERSION,
            "project": {"name": "p", "repo": "https://github.com/x/y.git", "title": "t"},
            "run": {"steps": [{"id": "s1", "title": "步骤", "cmd": "ls"}]},
        }
        validated = validate_spec(spec)  # 不抛错
        self.assertNotIn("capture", validated)


if __name__ == "__main__":
    unittest.main()

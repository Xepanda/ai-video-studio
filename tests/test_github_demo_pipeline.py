#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_github_demo_pipeline.py
scripts/github_demo_pipeline.py 单元测试:
1. .demo.yaml 规格契约校验 (合法/各类非法分支)
2. 占位符渲染
3. storyboard 编译 (场景结构/时长换算/降级与失败的诚实标注)
4. load_spec 文件级容错
5. CLI --dry-run 端到端冒烟 (无网络)
"""

import os
import sys
import json
import tempfile
import unittest
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.github_demo_pipeline import (
    DemoPipelineError,
    validate_spec,
    load_spec,
    render_placeholders,
    build_storyboard,
    save_storyboard,
    SPEC_VERSION,
)

EXAMPLE_SPEC = os.path.join(PROJECT_ROOT, "inputs", "yt-dlp.demo.yaml")


def make_minimal_spec() -> dict:
    """构造一个合法的最小规格 (用于变异测试)"""
    return {
        "spec_version": SPEC_VERSION,
        "project": {
            "name": "demo-proj",
            "repo": "https://github.com/example/demo-proj.git",
            "title": "演示项目",
        },
        "run": {
            "steps": [
                {"id": "step1", "title": "第一步", "cmd": "echo hello"},
            ]
        },
    }


def make_step_record(step_id="s1", status="ok", exit_code=0, excerpt="output line", duration=8) -> dict:
    return {
        "id": step_id,
        "title": f"步骤 {step_id}",
        "cmd": f"run-{step_id} --flag",
        "expect_exit": 0,
        "capture": "terminal",
        "narration": "口播文案",
        "duration": duration,
        "status": status,
        "exit_code": exit_code,
        "output_excerpt": excerpt,
    }


class TestValidateSpec(unittest.TestCase):
    """测试 .demo.yaml 规格契约校验的各合法/非法分支"""

    def test_minimal_valid_spec(self):
        spec = validate_spec(make_minimal_spec())
        self.assertEqual(spec["project"]["name"], "demo-proj")

    def test_missing_spec_version(self):
        spec = make_minimal_spec()
        del spec["spec_version"]
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_unsupported_spec_version(self):
        spec = make_minimal_spec()
        spec["spec_version"] = "2.0"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_root_not_mapping(self):
        with self.assertRaises(DemoPipelineError):
            validate_spec(["not", "a", "mapping"])

    def test_missing_project_fields(self):
        for field in ("name", "repo", "title"):
            spec = make_minimal_spec()
            del spec["project"][field]
            with self.assertRaises(DemoPipelineError, msg=f"missing project.{field} should raise"):
                validate_spec(spec)

    def test_invalid_repo_url(self):
        spec = make_minimal_spec()
        spec["project"]["repo"] = "not-a-url"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_empty_run_steps(self):
        spec = make_minimal_spec()
        spec["run"]["steps"] = []
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_duplicate_step_ids(self):
        spec = make_minimal_spec()
        spec["run"]["steps"].append({"id": "step1", "title": "重复", "cmd": "echo dup"})
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_step_missing_cmd(self):
        spec = make_minimal_spec()
        spec["run"]["steps"][0]["cmd"] = "   "
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_invalid_capture_mode(self):
        spec = make_minimal_spec()
        spec["run"]["steps"][0]["capture"] = "hologram"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_invalid_step_duration(self):
        spec = make_minimal_spec()
        spec["run"]["steps"][0]["duration"] = 0
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_invalid_expect_exit(self):
        spec = make_minimal_spec()
        spec["run"]["steps"][0]["expect_exit"] = "zero"
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_invalid_output_fps(self):
        spec = make_minimal_spec()
        spec["output"] = {"fps": 0}
        with self.assertRaises(DemoPipelineError):
            validate_spec(spec)

    def test_example_spec_file_is_valid(self):
        """仓库示例规格 inputs/yt-dlp.demo.yaml 必须通过契约校验"""
        if not os.path.exists(EXAMPLE_SPEC):
            self.skipTest("示例规格文件不存在")
        spec = load_spec(EXAMPLE_SPEC)
        self.assertEqual(spec["project"]["name"], "yt-dlp")
        self.assertEqual(len(spec["run"]["steps"]), 3)


class TestRenderPlaceholders(unittest.TestCase):
    """测试 {name} / {repo} 占位符渲染"""

    def test_name_substitution(self):
        out = render_placeholders("projects_demo/{name}/x", {"name": "yt-dlp"})
        self.assertEqual(out, "projects_demo/yt-dlp/x")

    def test_unknown_placeholder_preserved(self):
        out = render_placeholders("a/{unknown}/b", {"name": "x"})
        self.assertEqual(out, "a/{unknown}/b")

    def test_non_string_passthrough(self):
        self.assertEqual(render_placeholders(42, {"name": "x"}), 42)


class TestBuildStoryboard(unittest.TestCase):
    """测试 storyboard 编译: 结构、时长换算与诚实标注"""

    def setUp(self):
        self.spec = make_minimal_spec()
        self.spec["output"] = {"fps": 30}

    def test_scene_structure_and_durations(self):
        records = [make_step_record("s1"), make_step_record("s2", duration=12)]
        storyboard = build_storyboard(self.spec, {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}, records, "spec.yaml")

        # 开场 + 2 步骤 + 收尾
        self.assertEqual(len(storyboard["scenes"]), 4)
        self.assertEqual(storyboard["scenes"][0]["type"], "MinimalHeadline")
        self.assertEqual(storyboard["scenes"][0]["title"], "演示项目")
        # 步骤场景: TerminalWindow + codeSnippet 含真实命令
        step_scene = storyboard["scenes"][1]
        self.assertEqual(step_scene["type"], "TerminalWindow")
        self.assertIn("run-s1 --flag", step_scene["codeSnippet"])
        # 时长换算: 8s * 30fps / 12s * 30fps
        self.assertEqual(storyboard["scenes"][1]["durationInFrames"], 240)
        self.assertEqual(storyboard["scenes"][2]["durationInFrames"], 360)
        # 总帧数为各分镜之和
        self.assertEqual(
            storyboard["totalDurationInFrames"],
            sum(s["durationInFrames"] for s in storyboard["scenes"]),
        )
        # 执行事实元数据
        self.assertEqual(storyboard["scenes"][1]["demoRun"]["status"], "ok")
        self.assertEqual(storyboard["scenes"][1]["demoRun"]["exitCode"], 0)
        self.assertFalse(storyboard["source"]["degraded"])

    def test_failed_step_does_not_inject_output(self):
        """退出码偏离契约的步骤: 记录真实退出码, 不注入任何输出节选"""
        records = [make_step_record("bad", status="failed", exit_code=127, excerpt="command not found")]
        storyboard = build_storyboard(self.spec, {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}, records, "spec.yaml")
        scene = storyboard["scenes"][1]
        self.assertEqual(scene["demoRun"]["status"], "failed")
        self.assertEqual(scene["demoRun"]["exitCode"], 127)
        self.assertTrue(scene["demoRun"]["degraded"])
        # codeSnippet 只允许包含命令本身, 不得包含输出
        self.assertIn("$ run-bad --flag", scene["codeSnippet"])
        self.assertNotIn("command not found", scene["codeSnippet"])

    def test_degraded_install_marks_storyboard(self):
        """安装降级: storyboard 如实标注, 收尾文案说明证据受限"""
        records = [make_step_record("s1", status="skipped_degraded_install", exit_code=None, excerpt="")]
        storyboard = build_storyboard(
            self.spec,
            {"attempted": 1, "succeeded": 0, "failed": [{"cmd": "pip install -e .", "exit_code": 1}], "degraded": True},
            records,
            "spec.yaml",
        )
        self.assertTrue(storyboard["source"]["degraded"])
        self.assertEqual(len(storyboard["source"]["installResult"]["failed"]), 1)
        closing = storyboard["scenes"][-1]
        self.assertEqual(closing["type"], "MinimalHeadline")
        self.assertIn("兼容问题", closing["text"])

    def test_save_storyboard_roundtrip(self):
        records = [make_step_record("s1")]
        storyboard = build_storyboard(self.spec, {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}, records, "spec.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "sub", "storyboard.json")
            save_storyboard(storyboard, out_path)
            with open(out_path, encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["project"], "demo-proj")
            self.assertEqual(len(loaded["scenes"]), 3)


class TestLoadSpecFileErrors(unittest.TestCase):
    """测试 load_spec 文件级容错 (显式报错, 不静默吞掉)"""

    def test_nonexistent_file(self):
        with self.assertRaises(DemoPipelineError):
            load_spec("/nonexistent/path/demo.yaml")

    def test_invalid_yaml(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write("spec_version: '1.0'\n  bad: [unclosed\n")
            tmp_path = f.name
        try:
            with self.assertRaises(DemoPipelineError):
                load_spec(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestCliDryRunSmoke(unittest.TestCase):
    """CLI --dry-run 端到端冒烟 (无网络, 仅校验+storyboard 生成)"""

    def test_dry_run_generates_storyboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "dryrun_storyboard.json")
            proc = subprocess.run(
                [sys.executable, os.path.join("scripts", "github_demo_pipeline.py"),
                 "--spec", os.path.relpath(EXAMPLE_SPEC, PROJECT_ROOT),
                 "--dry-run", "--output", out_path],
                cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(proc.returncode, 0, f"dry-run 失败: {proc.stdout}\n{proc.stderr}")
            self.assertTrue(os.path.exists(out_path), "storyboard 未生成")
            with open(out_path, encoding="utf-8") as f:
                storyboard = json.load(f)
            self.assertEqual(storyboard["project"], "yt-dlp")
            # 开场 + 3 步骤 + 收尾
            self.assertEqual(len(storyboard["scenes"]), 5)

    def test_cli_invalid_spec_exit_code(self):
        """非法规格必须以非零退出码显式失败"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write("spec_version: '1.0'\nproject: {name: x}\n")
            tmp_path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join("scripts", "github_demo_pipeline.py"),
                 "--spec", tmp_path],
                cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("规格校验失败", proc.stdout)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()

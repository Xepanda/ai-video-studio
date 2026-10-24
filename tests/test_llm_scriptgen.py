#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_llm_scriptgen.py
scripts/llm_scriptgen.py 单元测试 (离线, FakeClient 注入):
1. 分镜契约校验 validate_storyboard_payload (合法/各类非法与警告分支)
2. 人工审校门 (build/approve/assert, 空审校人拒绝, 未批准阻断)
3. AI 标注自动附加
4. generate_storyboard 归一化 (帧数计算/review 挂起/披露) 与失败显式报错
5. CLI 端到端: --dry-run / --approve / --status (子进程冒烟, 无网络)
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

from scripts.llm_scriptgen import (
    ScriptgenError,
    ReviewGateError,
    validate_storyboard_payload,
    build_review_block,
    approve_storyboard,
    assert_review_approved,
    attach_ai_disclosure,
    generate_storyboard,
    build_scriptgen_messages,
    SCENE_TYPE_REGISTRY,
)


class FakeLLMClient:
    """离线 LLM 客户端: 返回预置响应或抛 LLMError (不发起任何网络请求)。"""

    def __init__(self, responses=None, raise_error=None, model="fake-model"):
        self.model = model
        self._responses = list(responses or [])
        self._raise_error = raise_error
        self.calls = []

    def chat_json(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        if self._raise_error is not None:
            raise self._raise_error
        if not self._responses:
            raise AssertionError("FakeLLMClient 响应队列已空")
        return self._responses.pop(0)


def make_valid_payload(project="tcp_handshake", scene_count=3):
    """构造合法分镜契约 (首尾 MinimalHeadline, 中间 TerminalCodeDemo)。"""
    scenes = [
        {
            "id": "scene_01",
            "type": "MinimalHeadline",
            "title": "三次握手的灵魂拷问",
            "text": "TCP 建立连接为什么要三次握手，两次到底差在哪？",
            "estimatedDuration": 4,
        },
        {
            "id": "scene_02",
            "type": "TerminalCodeDemo",
            "title": "看内核实现",
            "text": "我们直接看 Linux 内核里的三次握手状态跃迁代码。",
            "estimatedDuration": 6,
            "codeTitle": "tcp_connect.c",
            "codeLang": "c",
            "codeSnippet": "tcp_set_state(sk, TCP_SYN_SENT);",
        },
        {
            "id": "scene_03",
            "type": "MinimalHeadline",
            "title": "总结",
            "text": "三次握手，握手的是双方的序列号与接收能力。",
            "estimatedDuration": 3,
        },
    ]
    return {
        "project": project,
        "title": "TCP 三次握手为什么是三次",
        "theme": "linear-graphite",
        "engine": "chattts",
        "voice": "4444",
        "fps": 30,
        "scenes": scenes[:max(1, scene_count)],
    }


class TestValidateStoryboardPayload(unittest.TestCase):

    def test_valid_payload_no_errors(self):
        errors, warnings = validate_storyboard_payload(make_valid_payload())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_root_not_mapping(self):
        errors, _ = validate_storyboard_payload([1, 2, 3])
        self.assertTrue(any("根对象" in e for e in errors))

    def test_missing_required_root_fields(self):
        errors, _ = validate_storyboard_payload({"scenes": [{"id": "s1", "text": "x"}]})
        self.assertTrue(any("'project'" in e for e in errors))
        self.assertTrue(any("'title'" in e for e in errors))

    def test_empty_scenes(self):
        errors, _ = validate_storyboard_payload({"project": "p", "title": "t", "scenes": []})
        self.assertTrue(any("scenes" in e for e in errors))

    def test_duplicate_scene_ids(self):
        payload = {
            "project": "p", "title": "t",
            "scenes": [
                {"id": "s1", "text": "a", "estimatedDuration": 3},
                {"id": "s1", "text": "b", "estimatedDuration": 3},
            ],
        }
        errors, _ = validate_storyboard_payload(payload)
        self.assertTrue(any("重复" in e for e in errors))

    def test_missing_scene_text(self):
        payload = {"project": "p", "title": "t", "scenes": [{"id": "s1"}]}
        errors, _ = validate_storyboard_payload(payload)
        self.assertTrue(any("text" in e for e in errors))

    def test_unknown_scene_type_warns_not_errors(self):
        payload = {
            "project": "p", "title": "t",
            "scenes": [{"id": "s1", "text": "a", "type": "NoSuchType", "estimatedDuration": 3}],
        }
        errors, warnings = validate_storyboard_payload(payload)
        self.assertEqual(errors, [])
        self.assertTrue(any("不在注册表中" in w for w in warnings))

    def test_nested_config_missing_is_error(self):
        # 注册表声明 ProtocolStackTower 必须提供 protocolTower
        payload = {
            "project": "p", "title": "t",
            "scenes": [{"id": "s1", "text": "a", "type": "ProtocolStackTower", "estimatedDuration": 3}],
        }
        errors, _ = validate_storyboard_payload(payload)
        self.assertTrue(any("protocolTower" in e for e in errors))

    def test_nested_config_empty_string_is_error(self):
        payload = {
            "project": "p", "title": "t",
            "scenes": [{"id": "s1", "text": "a", "type": "WeChatMobileMockup",
                        "wechat": "", "estimatedDuration": 3}],
        }
        errors, _ = validate_storyboard_payload(payload)
        self.assertTrue(any("wechat" in e for e in errors))

    def test_bad_duration_is_error(self):
        payload = {
            "project": "p", "title": "t",
            "scenes": [{"id": "s1", "text": "a", "estimatedDuration": -2}],
        }
        errors, _ = validate_storyboard_payload(payload)
        self.assertTrue(any("estimatedDuration" in e for e in errors))

    def test_missing_duration_warns(self):
        payload = {"project": "p", "title": "t", "scenes": [{"id": "s1", "text": "a"}]}
        errors, warnings = validate_storyboard_payload(payload)
        self.assertEqual(errors, [])
        self.assertTrue(any("estimatedDuration" in w for w in warnings))


class TestReviewGate(unittest.TestCase):

    def test_build_review_block_pending(self):
        block = build_review_block()
        self.assertEqual(block["status"], "pending")
        self.assertTrue(block["required"])
        self.assertIsNone(block["reviewer"])
        self.assertGreater(len(block["checklist"]), 0)

    def test_approve_requires_reviewer(self):
        payload = {"review": build_review_block()}
        with self.assertRaises(ReviewGateError):
            approve_storyboard(payload, "   ")
        with self.assertRaises(ReviewGateError):
            approve_storyboard(payload, "")

    def test_approve_happy_path(self):
        payload = {"review": build_review_block()}
        approve_storyboard(payload, "庖丁")
        self.assertEqual(payload["review"]["status"], "approved")
        self.assertEqual(payload["review"]["reviewer"], "庖丁")
        self.assertIsNotNone(payload["review"]["reviewedAt"])

    def test_assert_review_approved_blocks_pending(self):
        payload = {"review": build_review_block()}
        with self.assertRaises(ReviewGateError):
            assert_review_approved(payload, context="[测试] ")

    def test_assert_review_approved_blocks_missing_review(self):
        with self.assertRaises(ReviewGateError):
            assert_review_approved({"scenes": []})

    def test_assert_review_approved_passes_approved(self):
        payload = {"review": build_review_block()}
        approve_storyboard(payload, "reviewer-x")
        assert_review_approved(payload)  # 不抛错即通过


class TestAiDisclosure(unittest.TestCase):

    def test_attach_ai_disclosure(self):
        payload = {}
        attach_ai_disclosure(payload, "deepseek-chat")
        self.assertTrue(payload["aiDisclosure"]["isAiGenerated"])
        self.assertEqual(payload["aiDisclosure"]["model"], "deepseek-chat")
        self.assertIn("AI", payload["aiDisclosure"]["notice"])


class TestGenerateStoryboard(unittest.TestCase):

    def test_generate_normalizes_and_suspends_review(self):
        client = FakeLLMClient(responses=[make_valid_payload()])
        storyboard = generate_storyboard(
            topic="TCP 三次握手", client=client, scene_count=3,
            project_name="tcp_demo", theme="obsidian-minimal",
        )
        # CLI 显式参数优先
        self.assertEqual(storyboard["project"], "tcp_demo")
        self.assertEqual(storyboard["theme"], "obsidian-minimal")
        # 帧数确定性计算: 4+6+3 秒 @30fps
        self.assertEqual(storyboard["totalDurationInFrames"], 390)
        for scene in storyboard["scenes"]:
            self.assertIn("durationInFrames", scene)
            self.assertIn("estimatedFrames", scene)
        # 审校门挂起 + AI 标注 + source 留痕
        self.assertEqual(storyboard["review"]["status"], "pending")
        self.assertTrue(storyboard["aiDisclosure"]["isAiGenerated"])
        self.assertEqual(storyboard["source"]["generatedBy"], "llm_scriptgen.py")
        self.assertEqual(storyboard["source"]["model"], "fake-model")

    def test_generate_default_project_slugified(self):
        client = FakeLLMClient(responses=[make_valid_payload(project="whatever")])
        storyboard = generate_storyboard(topic="Redis 核心架构", client=client, scene_count=3)
        self.assertEqual(storyboard["project"], "redis")

    def test_generate_llm_error_propagates_as_scriptgen_error(self):
        from utils.llm_client import LLMError
        client = FakeLLMClient(raise_error=LLMError("HTTP 429: rate limited"))
        with self.assertRaises(ScriptgenError) as ctx:
            generate_storyboard(topic="x", client=client, scene_count=3)
        self.assertIn("429", str(ctx.exception))

    def test_generate_invalid_contract_rejected_no_write(self):
        client = FakeLLMClient(responses=[{
            "project": "p", "title": "t",
            "scenes": [{"id": "s1", "text": "a", "type": "ProtocolStackTower"}],  # 缺 protocolTower
        }])
        with self.assertRaises(ScriptgenError) as ctx:
            generate_storyboard(topic="x", client=client, scene_count=3)
        self.assertIn("protocolTower", str(ctx.exception))
        # 绝不落盘
        self.assertFalse(os.path.exists(
            os.path.join(PROJECT_ROOT, "content", "scripts", "p.json")))

    def test_generate_missing_duration_defaulted(self):
        payload = {
            "project": "p", "title": "t",
            "scenes": [
                {"id": "scene_01", "type": "MinimalHeadline", "text": "a"},
                {"id": "scene_02", "type": "MinimalHeadline", "text": "b"},
            ],
        }
        client = FakeLLMClient(responses=[payload])
        storyboard = generate_storyboard(topic="x", client=client, scene_count=2)
        # 5s 兜底 @30fps = 150 帧/幕
        self.assertEqual(storyboard["totalDurationInFrames"], 300)


class TestPromptBuilder(unittest.TestCase):

    def test_messages_embed_registry_and_scene_count(self):
        messages = build_scriptgen_messages("测试主题", 7)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("ProtocolStackTower", messages[0]["content"])
        self.assertIn("WeChatMobileMockup", messages[0]["content"])
        self.assertIn("7", messages[0]["content"])
        self.assertIn("测试主题", messages[1]["content"])

    def test_registry_nested_fields_prompted(self):
        messages = build_scriptgen_messages("t", 5)
        system = messages[0]["content"]
        self.assertIn("protocolTower", system)
        self.assertIn("packetAssembly", system)
        self.assertIn("topologyNodes", system)


class TestCliEndToEnd(unittest.TestCase):
    """CLI 子进程冒烟 (FakeClient 无法注入子进程, 故验证参数校验与审校门文件流程)。"""

    def _run(self, args):
        return subprocess.run(
            [sys.executable, os.path.join("scripts", "llm_scriptgen.py")] + args,
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
        )

    def test_topic_required_in_generate_mode(self):
        ret = self._run(["--dry-run"])
        self.assertEqual(ret.returncode, 2)
        self.assertIn("--topic", ret.stderr)

    def test_approve_status_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "draft.json")
            payload = make_valid_payload()
            payload["review"] = build_review_block()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

            # 未批准 -> status 查询退出码 1
            ret = self._run(["--status", "--input", path])
            self.assertEqual(ret.returncode, 1)
            self.assertIn("pending", ret.stdout)

            # 无审校人批准 -> 退出码 5
            ret = self._run(["--approve", "--input", path])
            self.assertEqual(ret.returncode, 5)

            # 正常批准 -> 退出码 0, 状态翻转
            ret = self._run(["--approve", "--input", path, "--reviewer", "测试审校人"])
            self.assertEqual(ret.returncode, 0, msg=ret.stdout + ret.stderr)
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["review"]["status"], "approved")
            self.assertEqual(saved["review"]["reviewer"], "测试审校人")

            # 已批准 -> status 查询退出码 0
            ret = self._run(["--status", "--input", path])
            self.assertEqual(ret.returncode, 0)
            self.assertIn("approved", ret.stdout)


if __name__ == "__main__":
    unittest.main()

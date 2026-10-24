#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_hotspot_scriptgen.py
scripts/hotspot_scriptgen.py 单元测试 (离线, FakeClient 注入):
1. 热点输入加载与话题选择 (缺失文件/坏结构/rank 越界/标题匹配)
2. 事实核查门 fact_check_storyboard:
   - 信源必填 (缺 sources / 非法 url / 缺 title / 未回链热点 URL)
   - AI 标注自动附加 (autoFix)
   - 数量声明 warning
   - 话题绑定元数据
3. generate_hotspot_script: 门禁通过 / 违规反馈重试后通过 / 重试耗尽 FactCheckError
4. CLI --dry-run 冒烟 (参数校验, 无网络)
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

from scripts.hotspot_scriptgen import (
    ScriptgenError,
    FactCheckError,
    load_hotspots,
    select_topic,
    fact_check_storyboard,
    generate_hotspot_script,
    build_hotspot_messages,
    _NUMBER_CLAIM_RE,
)


def make_hotspots(topics=None):
    return {
        "generatedAt": "2026-10-24T00:00:00+08:00",
        "sources": {"weibo": {"status": "ok", "count": 1, "error": None}},
        "topics": topics if topics is not None else [
            {
                "rank": 1,
                "title": "某发布会公布新一代芯片工艺",
                "heat": 4800000,
                "url": "https://s.weibo.com/weibo?q=%23某芯片%23",
                "source": "weibo",
                "tag": "沸",
            },
            {
                "rank": 2,
                "title": "开源社区发布新版本LTS",
                "heat": 1200000,
                "url": "https://www.bilibili.com/video/BV1xx411c7mD",
                "source": "bilibili",
            },
        ],
    }


def make_valid_script_payload(topic_url):
    """合法快稿: 每幕带 sources, 且引用热点 URL。"""
    return {
        "project": "chip_news",
        "title": "新芯片工艺来了",
        "theme": "linear-graphite",
        "engine": "chattts",
        "voice": "4444",
        "fps": 30,
        "scenes": [
            {
                "id": "scene_01",
                "type": "MinimalHeadline",
                "title": "新工艺落地",
                "text": "这场发布会真正的主角，是背后那条全新的芯片工艺产线。",
                "estimatedDuration": 4,
                "sources": [{"title": "微博热搜", "url": topic_url}],
            },
            {
                "id": "scene_02",
                "type": "BinaryBento",
                "title": "新旧对比",
                "text": "能效比提升是这代工艺最直接的卖点，实测数据等第三方复测。",
                "estimatedDuration": 5,
                "binaryBento": {
                    "leftCard": {"title": "上一代工艺", "desc": "能效与密度的基准线"},
                    "rightCard": {"title": "新一代工艺", "desc": "同功耗下性能与能效双改进"},
                },
                "sources": [{"title": "微博热搜", "url": topic_url}],
            },
            {
                "id": "scene_03",
                "type": "MinimalHeadline",
                "title": "冷静看待",
                "text": "量产节奏与良率才是真正的考场，我们拭目以待。",
                "estimatedDuration": 3,
                "sources": [{"title": "微博热搜", "url": topic_url}],
            },
        ],
    }


class FakeLLMClient:
    def __init__(self, responses=None, raise_error=None, model="fake-hotspot-model"):
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


class TestLoadHotspots(unittest.TestCase):

    def test_missing_file_rejected(self):
        with self.assertRaises(ScriptgenError) as ctx:
            load_hotspots(os.path.join(tempfile.gettempdir(), "definitely_not_exist_avs.json"))
        self.assertIn("hotspot_aggregator", str(ctx.exception))

    def test_bad_structure_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"foo": "bar"}, f)
            path = f.name
        try:
            with self.assertRaises(ScriptgenError):
                load_hotspots(path)
        finally:
            os.remove(path)

    def test_valid_file_loads(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(make_hotspots(), f)
            path = f.name
        try:
            payload = load_hotspots(path)
            self.assertEqual(len(payload["topics"]), 2)
        finally:
            os.remove(path)


class TestSelectTopic(unittest.TestCase):

    def test_select_by_rank(self):
        topic = select_topic(make_hotspots(), rank=2)
        self.assertEqual(topic["source"], "bilibili")

    def test_select_by_title(self):
        topic = select_topic(make_hotspots(), topic_title="开源社区发布新版本LTS")
        self.assertEqual(topic["rank"], 2)

    def test_rank_out_of_range(self):
        with self.assertRaises(ScriptgenError):
            select_topic(make_hotspots(), rank=99)

    def test_title_not_found(self):
        with self.assertRaises(ScriptgenError):
            select_topic(make_hotspots(), topic_title="不存在的话题")

    def test_empty_topics_rejected(self):
        with self.assertRaises(ScriptgenError):
            select_topic(make_hotspots(topics=[]))


class TestFactCheckGate(unittest.TestCase):

    def setUp(self):
        self.topic = make_hotspots()["topics"][0]

    def test_pass_with_topic_url_referenced(self):
        payload = make_valid_script_payload(self.topic["url"])
        report = fact_check_storyboard(payload, self.topic)
        self.assertTrue(report["passed"])
        self.assertEqual(report["violations"], [])
        # AI 标注自动附加留痕
        self.assertTrue(any("aiDisclosure" in fix for fix in report["autoFixes"]))
        self.assertTrue(payload["aiDisclosure"]["isAiGenerated"])

    def test_missing_sources_is_violation(self):
        payload = make_valid_script_payload(self.topic["url"])
        del payload["scenes"][1]["sources"]
        report = fact_check_storyboard(payload, self.topic)
        self.assertFalse(report["passed"])
        self.assertTrue(any("sources" in v for v in report["violations"]))

    def test_empty_sources_is_violation(self):
        payload = make_valid_script_payload(self.topic["url"])
        payload["scenes"][1]["sources"] = []
        report = fact_check_storyboard(payload, self.topic)
        self.assertFalse(report["passed"])

    def test_invalid_source_url_is_violation(self):
        payload = make_valid_script_payload(self.topic["url"])
        payload["scenes"][1]["sources"] = [{"title": "野鸡源", "url": "not-a-url"}]
        report = fact_check_storyboard(payload, self.topic)
        self.assertFalse(report["passed"])
        self.assertTrue(any("url 非法" in v for v in report["violations"]))

    def test_source_missing_title_is_violation(self):
        payload = make_valid_script_payload(self.topic["url"])
        payload["scenes"][1]["sources"] = [{"url": self.topic["url"]}]
        report = fact_check_storyboard(payload, self.topic)
        self.assertFalse(report["passed"])
        self.assertTrue(any("title" in v for v in report["violations"]))

    def test_topic_url_not_referenced_is_violation(self):
        payload = make_valid_script_payload(self.topic["url"])
        for scene in payload["scenes"]:
            scene["sources"] = [{"title": "其他信源", "url": "https://example.com/news"}]
        report = fact_check_storyboard(payload, self.topic)
        self.assertFalse(report["passed"])
        self.assertTrue(any("热点话题自身" in v for v in report["violations"]))

    def test_number_claim_warns_but_passes(self):
        payload = make_valid_script_payload(self.topic["url"])
        payload["scenes"][1]["text"] = "能效比提升 30%，功耗下降两成。"
        report = fact_check_storyboard(payload, self.topic)
        self.assertTrue(report["passed"])  # 数量声明不阻断
        self.assertTrue(any("数量声明" in w for w in report["warnings"]))

    def test_ai_disclosure_not_duplicated(self):
        payload = make_valid_script_payload(self.topic["url"])
        payload["aiDisclosure"] = {"isAiGenerated": True, "model": "pre-set"}
        report = fact_check_storyboard(payload, self.topic)
        self.assertEqual(payload["aiDisclosure"]["model"], "pre-set")  # 不覆盖
        self.assertFalse(any("aiDisclosure" in fix for fix in report["autoFixes"]))

    def test_hotspot_binding_metadata(self):
        payload = make_valid_script_payload(self.topic["url"])
        fact_check_storyboard(payload, self.topic, hotspot_path="inputs/hotspots/latest.json")
        hotspot_meta = payload["source"]["hotspot"]
        self.assertEqual(hotspot_meta["title"], self.topic["title"])
        self.assertEqual(hotspot_meta["url"], self.topic["url"])
        self.assertEqual(hotspot_meta["heat"], 4800000)
        self.assertEqual(hotspot_meta["aggregatedFrom"], "latest.json")

    def test_number_claim_regex(self):
        self.assertTrue(_NUMBER_CLAIM_RE.search("提升 30% 的性能"))
        self.assertTrue(_NUMBER_CLAIM_RE.search("市值蒸发 300 亿"))
        self.assertTrue(_NUMBER_CLAIM_RE.search("收入 5 亿美元"))
        self.assertIsNone(_NUMBER_CLAIM_RE.search("性能有所提升"))


class TestGenerateHotspotScript(unittest.TestCase):

    def setUp(self):
        self.topic = make_hotspots()["topics"][0]

    def test_gate_pass_first_try(self):
        client = FakeLLMClient(responses=[make_valid_script_payload(self.topic["url"])])
        storyboard, report = generate_hotspot_script(
            topic=self.topic, client=client, scene_count=3,
            project_name="chip_demo",
        )
        self.assertEqual(storyboard["project"], "chip_demo")
        self.assertTrue(report["passed"])
        self.assertEqual(storyboard["review"]["status"], "pending")
        self.assertTrue(storyboard["aiDisclosure"]["isAiGenerated"])
        self.assertEqual(storyboard["source"]["generatedBy"], "hotspot_scriptgen.py")
        self.assertEqual(storyboard["source"]["hotspot"]["url"], self.topic["url"])
        # 帧数: 4+5+3 @30fps
        self.assertEqual(storyboard["totalDurationInFrames"], 360)
        self.assertEqual(len(client.calls), 1)

    def test_feedback_retry_then_pass(self):
        bad = make_valid_script_payload(self.topic["url"])
        del bad["scenes"][1]["sources"]  # 第一轮缺信源
        client = FakeLLMClient(responses=[bad, make_valid_script_payload(self.topic["url"])])
        storyboard, report = generate_hotspot_script(
            topic=self.topic, client=client, scene_count=3, max_retries=2,
        )
        self.assertTrue(report["passed"])
        self.assertEqual(len(client.calls), 2)
        # 第二轮 prompt 注入了违规反馈
        second_user_msg = client.calls[1]["messages"][1]["content"]
        self.assertIn("打回", second_user_msg)
        self.assertIn("sources", second_user_msg)

    def test_retry_exhausted_raises_fact_check_error(self):
        bad = make_valid_script_payload(self.topic["url"])
        del bad["scenes"][0]["sources"]
        client = FakeLLMClient(responses=[bad, bad, bad])
        with self.assertRaises(FactCheckError) as ctx:
            generate_hotspot_script(
                topic=self.topic, client=client, scene_count=3, max_retries=2,
            )
        self.assertIn("重试耗尽", str(ctx.exception))
        self.assertEqual(len(client.calls), 3)  # 首次 + 2 次重试

    def test_contract_invalid_retries_then_scriptgen_error(self):
        bad = {
            "project": "p", "title": "t",
            "scenes": [
                {"id": "scene_01", "type": "MinimalHeadline", "text": "a",
                 "estimatedDuration": 3, "sources": [{"title": "s", "url": self.topic["url"]}]},
                {"id": "scene_02", "type": "ProtocolStackTower", "text": "b",
                 "estimatedDuration": 3, "sources": [{"title": "s", "url": self.topic["url"]}]},
                # 缺 protocolTower -> 契约校验失败
            ],
        }
        client = FakeLLMClient(responses=[bad, bad, bad])
        with self.assertRaises(ScriptgenError) as ctx:
            generate_hotspot_script(
                topic=self.topic, client=client, scene_count=3, max_retries=2,
            )
        self.assertIn("protocolTower", str(ctx.exception))

    def test_llm_error_propagates(self):
        from utils.llm_client import LLMError
        client = FakeLLMClient(raise_error=LLMError("HTTP 401: unauthorized"))
        with self.assertRaises(ScriptgenError):
            generate_hotspot_script(topic=self.topic, client=client, scene_count=3)


class TestPromptBuilder(unittest.TestCase):

    def test_messages_embed_topic_and_source_requirement(self):
        topic = make_hotspots()["topics"][0]
        messages = build_hotspot_messages(topic, 4)
        system = messages[0]["content"]
        user = messages[1]["content"]
        self.assertIn("sources", system)
        self.assertIn("信源", system)
        self.assertIn(topic["url"], user)
        self.assertIn(topic["title"], user)
        self.assertIn("4", system)

    def test_feedback_injected_into_user_message(self):
        topic = make_hotspots()["topics"][0]
        messages = build_hotspot_messages(topic, 4, feedback=["分镜 [scene_02] 缺少信源"])
        self.assertIn("打回", messages[1]["content"])
        self.assertIn("scene_02", messages[1]["content"])


class TestCli(unittest.TestCase):

    def _run(self, args):
        return subprocess.run(
            [sys.executable, os.path.join("scripts", "hotspot_scriptgen.py")] + args,
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
        )

    def test_missing_hotspots_file_exit_2(self):
        ret = self._run(["--hotspots", "inputs/hotspots/__not_exist__.json"])
        self.assertEqual(ret.returncode, 2)
        self.assertIn("hotspot_aggregator", ret.stdout)

    def test_dry_run_requires_llm_config(self):
        # 无 AVS_LLM_API_KEY 时 LLMClient 显式报错 (数据诚信: 不伪造输出)
        env = dict(os.environ)
        env.pop("AVS_LLM_API_KEY", None)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(make_hotspots(), f)
            hotspots_path = f.name
        try:
            ret = subprocess.run(
                [sys.executable, os.path.join("scripts", "hotspot_scriptgen.py"),
                 "--hotspots", hotspots_path, "--rank", "1", "--dry-run"],
                cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60, env=env,
            )
        finally:
            os.remove(hotspots_path)
        # 走到 LLM 调用阶段才失败 (退出码 4), 证明前置加载/选话题通过
        self.assertEqual(ret.returncode, 4)
        self.assertIn("AVS_LLM_API_KEY", ret.stdout)


if __name__ == "__main__":
    unittest.main()

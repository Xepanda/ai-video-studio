#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_hotspot_aggregator.py
scripts/hotspot_aggregator.py 单元测试 (全离线, 伪 session 注入响应):
1. 话题归一化契约 (heat 缺失/非法值一律 None, 严禁 0 填充)
2. 各源解析器 (合法响应 / HTTP 错误 / 结构不符 / 需要登录态)
3. X Trends 凭证门控 (未配置显式跳过, 不伪造)
4. 聚合层单源失败不影响他源, 失败状态如实记录
5. 落盘往返与 CLI 参数校验
"""

import os
import sys
import json
import tempfile
import unittest
import subprocess
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.hotspot_aggregator import (
    HotspotFetchError,
    _normalize_topic,
    fetch_weibo,
    fetch_douyin,
    fetch_bilibili,
    fetch_x_trends,
    aggregate_topics,
    save_hotspots,
    SOURCE_REGISTRY,
    FETCHERS,
)


class FakeResponse:
    """伪 HTTP 响应: 可配置 status_code 与 json 负载/异常"""

    def __init__(self, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload


class FakeSession:
    """伪 requests.Session: 按 URL 返回预注册响应"""

    def __init__(self, routes):
        self.routes = routes  # url -> FakeResponse | Exception

    def get(self, url, headers=None, timeout=None):
        target = self.routes.get(url)
        if target is None:
            raise AssertionError(f"未预期的 URL 请求: {url}")
        if isinstance(target, Exception):
            raise target
        return target


WEIBO_URL = "https://weibo.com/ajax/side/hotSearch"
DOUYIN_URL = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
BILIBILI_URL = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
X_URL = "https://api.twitter.com/1.1/trends/place.json?id=1"


class TestNormalizeTopic(unittest.TestCase):
    """话题归一化契约: 热度缺失/非法一律 None"""

    def test_heat_none_preserved(self):
        topic = _normalize_topic("weibo", 1, "标题", None, "https://x")
        self.assertIsNone(topic["heat"])

    def test_invalid_heat_becomes_none(self):
        self.assertIsNone(_normalize_topic("weibo", 1, "t", "1234", "u")["heat"])
        self.assertIsNone(_normalize_topic("weibo", 1, "t", -5, "u")["heat"])

    def test_valid_heat_kept(self):
        self.assertEqual(_normalize_topic("weibo", 1, "t", 1234, "u")["heat"], 1234)

    def test_tag_omitted_when_absent(self):
        topic = _normalize_topic("weibo", 1, "t", 1, "u")
        self.assertNotIn("tag", topic)


class TestFetchWeibo(unittest.TestCase):
    """微博热搜解析器"""

    def test_valid_response(self):
        payload = {"data": {"realtime": [
            {"word": "热点一", "num": 1234567, "flag_desc": "新"},
            {"word": "热点二", "num": None},
            {"word": "", "num": 100},  # 空标题应被跳过
        ]}}
        session = FakeSession({WEIBO_URL: FakeResponse(payload=payload)})
        topics = fetch_weibo(session, 10, 0, 20)
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]["title"], "热点一")
        self.assertEqual(topics[0]["heat"], 1234567)
        self.assertEqual(topics[0]["rank"], 1)
        self.assertEqual(topics[1]["heat"], None)
        self.assertEqual(topics[0]["source"], "weibo")

    def test_http_error_raises(self):
        session = FakeSession({WEIBO_URL: FakeResponse(status_code=403)})
        with self.assertRaises(HotspotFetchError):
            fetch_weibo(session, 10, 0, 20)

    def test_malformed_structure_raises(self):
        session = FakeSession({WEIBO_URL: FakeResponse(payload={"data": {}})})
        with self.assertRaises(HotspotFetchError):
            fetch_weibo(session, 10, 0, 20)

    def test_network_error_with_retries_raises(self):
        import requests
        session = FakeSession({WEIBO_URL: requests.ConnectionError("boom")})
        with self.assertRaises(HotspotFetchError):
            fetch_weibo(session, 10, 1, 20)


class TestFetchDouyin(unittest.TestCase):
    """抖音热榜解析器 (通常需要登录态)"""

    def test_valid_response(self):
        payload = {"data": {"word_list": [
            {"word": "抖音热点", "hot_value": 8888888, "sentence_id": "123", "label": "热"},
        ]}}
        session = FakeSession({DOUYIN_URL: FakeResponse(payload=payload)})
        topics = fetch_douyin(session, 10, 0, 20)
        self.assertEqual(topics[0]["title"], "抖音热点")
        self.assertEqual(topics[0]["heat"], 8888888)

    def test_missing_word_list_raises(self):
        session = FakeSession({DOUYIN_URL: FakeResponse(payload={"data": {}})})
        with self.assertRaises(HotspotFetchError):
            fetch_douyin(session, 10, 0, 20)

    def test_http_403_raises(self):
        session = FakeSession({DOUYIN_URL: FakeResponse(status_code=403)})
        with self.assertRaises(HotspotFetchError):
            fetch_douyin(session, 10, 0, 20)


class TestFetchBilibili(unittest.TestCase):
    """B站热榜解析器"""

    def test_valid_response(self):
        payload = {"code": 0, "data": {"list": [
            {"title": "视频一", "bvid": "BV1xx", "stat": {"view": 100000}, "tname": "科技"},
            {"title": "视频二", "bvid": "BV2yy", "stat": {}},  # 无 view -> heat None
        ]}}
        session = FakeSession({BILIBILI_URL: FakeResponse(payload=payload)})
        topics = fetch_bilibili(session, 10, 0, 20)
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]["heat"], 100000)
        self.assertEqual(topics[0]["url"], "https://www.bilibili.com/video/BV1xx")
        self.assertIsNone(topics[1]["heat"])

    def test_api_error_code_raises(self):
        payload = {"code": -412, "message": "请求被拦截"}
        session = FakeSession({BILIBILI_URL: FakeResponse(payload=payload)})
        with self.assertRaises(HotspotFetchError):
            fetch_bilibili(session, 10, 0, 20)


class TestFetchXTrends(unittest.TestCase):
    """X Trends 凭证门控: 未配置显式跳过, 不伪造"""

    def test_missing_token_raises(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AVS_X_BEARER_TOKEN", None)
            session = FakeSession({})
            with self.assertRaises(HotspotFetchError) as ctx:
                fetch_x_trends(session, 10, 0, 20)
            self.assertIn("AVS_X_BEARER_TOKEN", str(ctx.exception))

    def test_valid_response_with_token(self):
        payload = [{"trends": [
            {"name": "#Trending", "url": "https://twitter.com/search?q=%23Trending", "tweet_volume": 50000},
            {"name": "NoVolume", "url": None, "tweet_volume": None},  # volume 缺失保持 None
        ]}]
        with mock.patch.dict(os.environ, {"AVS_X_BEARER_TOKEN": "test-token"}):
            session = FakeSession({X_URL: FakeResponse(payload=payload)})
            topics = fetch_x_trends(session, 10, 0, 20)
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]["heat"], 50000)
        self.assertIsNone(topics[1]["heat"])
        self.assertEqual(topics[1]["url"], "https://twitter.com/explore/tabs/trending")


class TestAggregate(unittest.TestCase):
    """聚合层: 单源失败不影响他源, 状态如实记录, 无编造条目"""

    def test_all_sources_ok(self):
        with mock.patch.dict(FETCHERS, {
            "weibo": lambda s, t, r, l: [_normalize_topic("weibo", 1, "A", 10, "u")],
            "douyin": lambda s, t, r, l: [_normalize_topic("douyin", 1, "B", 20, "u")],
        }):
            payload = aggregate_topics(["weibo", "douyin"], 10, 5, 0)
        self.assertEqual(len(payload["topics"]), 2)
        self.assertEqual(payload["sources"]["weibo"]["status"], "ok")
        self.assertEqual(payload["sources"]["douyin"]["status"], "ok")

    def test_one_source_fails_others_intact(self):
        def failing(s, t, r, l):
            raise HotspotFetchError("HTTP 403")

        with mock.patch.dict(FETCHERS, {
            "weibo": failing,
            "douyin": lambda s, t, r, l: [_normalize_topic("douyin", 1, "B", 20, "u")],
        }):
            payload = aggregate_topics(["weibo", "douyin"], 10, 5, 0)
        # 失败源零条目且状态可读; 成功源条目完整
        self.assertEqual(payload["sources"]["weibo"]["status"], "failed")
        self.assertIn("403", payload["sources"]["weibo"]["error"])
        self.assertEqual(len(payload["topics"]), 1)
        self.assertEqual(payload["topics"][0]["source"], "douyin")

    def test_unknown_source_recorded(self):
        with mock.patch.dict(FETCHERS, {}, clear=False):
            payload = aggregate_topics(["nonexistent"], 10, 5, 0)
        self.assertEqual(payload["sources"]["nonexistent"]["status"], "unknown_source")
        self.assertEqual(payload["topics"], [])

    def test_unexpected_exception_recorded(self):
        def boom(s, t, r, l):
            raise RuntimeError("unexpected")

        with mock.patch.dict(FETCHERS, {"weibo": boom}):
            payload = aggregate_topics(["weibo"], 10, 5, 0)
        self.assertEqual(payload["sources"]["weibo"]["status"], "error")
        self.assertIn("未预期异常", payload["sources"]["weibo"]["error"])


class TestSaveHotspots(unittest.TestCase):
    """落盘往返"""

    def test_roundtrip(self):
        payload = {"generatedAt": "2026-10-22T00:00:00+08:00",
                   "sources": {"weibo": {"status": "ok", "count": 1, "error": None}},
                   "topics": [{"rank": 1, "title": "A", "heat": 1, "url": "u", "source": "weibo"}]}
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "hotspots.json")
            save_hotspots(payload, out)
            with open(out, encoding="utf-8") as f:
                loaded = json.load(f)
        self.assertEqual(loaded["topics"][0]["title"], "A")


class TestCli(unittest.TestCase):
    """CLI 参数校验 (确定性路径)"""

    def test_unknown_source_exit_2(self):
        proc = subprocess.run(
            [sys.executable, os.path.join("scripts", "hotspot_aggregator.py"),
             "--sources", "weibo,nonexistent"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("未注册的热点源", proc.stdout)

    def test_help_exit_0(self):
        proc = subprocess.run(
            [sys.executable, os.path.join("scripts", "hotspot_aggregator.py"), "--help"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()

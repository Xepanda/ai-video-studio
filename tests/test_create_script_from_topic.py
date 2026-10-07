#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_create_script_from_topic.py
Unit tests for scripts/create_script_from_topic.py
"""

import unittest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.create_script_from_topic import (
    slugify,
    detect_domain,
    generate_structured_script
)


class TestCreateScriptFromTopic(unittest.TestCase):

    def test_slugify(self):
        self.assertEqual(slugify("Redis 核心架构"), "redis")
        self.assertEqual(slugify("Kafka-Stream_Demo 101"), "kafka_stream_demo_101")
        # Empty or non-ascii fallback
        res = slugify("纯中文测试")
        self.assertTrue(len(res) > 0)

    def test_detect_domain(self):
        self.assertEqual(detect_domain("Redis 内存数据库"), "database_storage")
        self.assertEqual(detect_domain("LLM 大模型 Agent 编排"), "ai_agent")
        self.assertEqual(detect_domain("Kubernetes 云原生集群"), "devops_infra")
        self.assertEqual(detect_domain("ESP32 单片机 FOC 电机驱动"), "hardware_iot")
        self.assertEqual(detect_domain("高可用分布式系统架构"), "system_architecture")

    def test_generate_structured_script_defaults(self):
        script = generate_structured_script(
            topic="Redis 核心架构剖析",
            project_name="redis_core_demo"
        )
        self.assertEqual(script["project"], "redis_core_demo")
        self.assertEqual(script["engine"], "chattts")
        self.assertEqual(script["voice"], "4444")
        self.assertEqual(script["theme"], "obsidian-minimal")
        self.assertEqual(script["fps"], 30)
        self.assertEqual(len(script["scenes"]), 5)

        # Check scene 2 is ArchitectureTopology
        scene2 = script["scenes"][1]
        self.assertEqual(scene2["type"], "ArchitectureTopology")
        self.assertIn("topologyNodes", scene2)
        self.assertIn("topologyLinks", scene2)
        self.assertTrue(len(scene2["topologyNodes"]) >= 4)
        self.assertTrue(len(scene2["topologyLinks"]) >= 3)

        # Check scene 4 is MetricComparison
        scene4 = script["scenes"][3]
        self.assertEqual(scene4["type"], "MetricComparison")
        self.assertIn("metrics", scene4)
        self.assertTrue(len(scene4["metrics"]) >= 2)

    def test_generate_structured_script_custom_params(self):
        script = generate_structured_script(
            topic="DeepSeek R1 模型架构",
            project_name="deepseek_r1",
            scenes_count=3,
            theme="blueprint-engineering",
            engine="kokoro",
            voice="af_bella",
            domain="ai_agent"
        )
        self.assertEqual(script["engine"], "kokoro")
        self.assertEqual(script["voice"], "af_bella")
        self.assertEqual(script["theme"], "blueprint-engineering")
        self.assertEqual(len(script["scenes"]), 3)


if __name__ == "__main__":
    unittest.main()

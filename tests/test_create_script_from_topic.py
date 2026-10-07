#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_create_script_from_topic.py
Comprehensive unit tests for scripts/create_script_from_topic.py
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
        # Mixed Chinese and English with consecutive underscores
        self.assertEqual(slugify("AI 浪潮下的 LLM 实践"), "ai_llm")
        # Empty or non-ascii fallback
        res = slugify("纯中文测试")
        self.assertTrue(len(res) > 0)
        self.assertNotIn("__", res)

    def test_detect_domain_precise_matching(self):
        # 1. 数据库与存储
        self.assertEqual(detect_domain("Redis 内存数据库与跳表设计"), "database_storage")
        self.assertEqual(detect_domain("PostgreSQL WAL 日志机制"), "database_storage")
        self.assertEqual(detect_domain("RocksDB LSM-Tree 存储引擎"), "database_storage")

        # 2. AI 与 智能体
        self.assertEqual(detect_domain("LLM 大模型 Agent 编排"), "ai_agent")
        self.assertEqual(detect_domain("Transformer 稀疏注意力机制"), "ai_agent")
        self.assertEqual(detect_domain("DeepSeek R1 推理架构"), "ai_agent")

        # 3. 避免单词子串误判 (false positives protection)
        # 'failover' has 'ai' as substring, must NOT be categorized as ai_agent
        self.assertEqual(detect_domain("高可用 Failover 容灾切换"), "system_architecture")
        # 'firewall' has 'wal' as substring, must NOT be categorized as database_storage
        self.assertEqual(detect_domain("Linux Netfilter Firewall 容器安全"), "devops_infra")
        # 'email' has 'ai' as substring, must NOT be categorized as ai_agent
        self.assertEqual(detect_domain("Email 邮件通知分布式系统"), "system_architecture")

        # 4. 云原生与 DevOps
        self.assertEqual(detect_domain("Kubernetes 云原生集群调度"), "devops_infra")
        self.assertEqual(detect_domain("Docker 容器编排与 CI/CD 流水线"), "devops_infra")
        self.assertEqual(detect_domain("Nginx 接入层网关与服务网格"), "devops_infra")

        # 5. 嵌入式与硬件
        self.assertEqual(detect_domain("ESP32 单片机 FOC 电机驱动"), "hardware_iot")
        self.assertEqual(detect_domain("STM32 DMA 中断与 SPI 总线"), "hardware_iot")
        self.assertEqual(detect_domain("RISC-V 芯片架构微内核"), "hardware_iot")

    def test_all_five_domains_generation(self):
        domains = ["database_storage", "ai_agent", "devops_infra", "hardware_iot", "system_architecture"]
        for d in domains:
            script = generate_structured_script(
                topic=f"Testing {d}",
                project_name=f"test_{d}",
                domain=d,
                theme="blueprint-engineering"
            )
            # Top level checks
            self.assertEqual(script["project"], f"test_{d}")
            self.assertEqual(script["theme"], "blueprint-engineering")
            self.assertEqual(script["engine"], "chattts")
            self.assertEqual(script["voice"], "4444")
            self.assertEqual(len(script["scenes"]), 5)

            # Scene 1: Card Grid
            s1 = script["scenes"][0]
            self.assertEqual(s1["theme"], "blueprint-engineering")
            self.assertTrue(len(s1.get("cards", [])) >= 3)

            # Scene 2: ArchitectureTopology
            s2 = script["scenes"][1]
            self.assertEqual(s2["type"], "ArchitectureTopology")
            self.assertEqual(s2["theme"], "blueprint-engineering")
            self.assertTrue(len(s2.get("topologyNodes", [])) >= 4)
            self.assertTrue(len(s2.get("topologyLinks", [])) >= 3)
            # Validate node structure
            for node in s2["topologyNodes"]:
                self.assertIn("id", node)
                self.assertIn("label", node)
                self.assertIn("x", node)
                self.assertIn("y", node)

            # Scene 3: TerminalCodeDemo
            s3 = script["scenes"][2]
            self.assertEqual(s3["type"], "TerminalCodeDemo")
            self.assertEqual(s3["theme"], "blueprint-engineering")
            self.assertIn("codeSnippet", s3)
            self.assertIn("codeLang", s3)
            self.assertIn("codeTitle", s3)

            # Scene 4: MetricComparison (strictly MetricCategory[] format)
            s4 = script["scenes"][3]
            self.assertEqual(s4["type"], "MetricComparison")
            self.assertEqual(s4["theme"], "blueprint-engineering")
            metrics = s4.get("metrics", [])
            self.assertTrue(len(metrics) >= 2)
            for cat in metrics:
                self.assertIn("title", cat)
                self.assertIn("badge", cat)
                self.assertIn("pill", cat)
                self.assertIn("items", cat)
                self.assertTrue(len(cat["items"]) >= 2)
                for item in cat["items"]:
                    self.assertIn("name", item)
                    self.assertIn("value", item)
                    self.assertIn("unit", item)

            # Scene 5: Summary Cards
            s5 = script["scenes"][4]
            self.assertEqual(s5["theme"], "blueprint-engineering")
            self.assertTrue(len(s5.get("cards", [])) >= 3)

    def test_scenes_count_clamping(self):
        # Truncation to 3 scenes
        script_3 = generate_structured_script("Test", "test_3", scenes_count=3)
        self.assertEqual(len(script_3["scenes"]), 3)

        # Clamping negative or zero to minimum 1
        script_0 = generate_structured_script("Test", "test_0", scenes_count=0)
        self.assertEqual(len(script_0["scenes"]), 1)

        # Clamping > 5 to maximum available (5)
        script_10 = generate_structured_script("Test", "test_10", scenes_count=10)
        self.assertEqual(len(script_10["scenes"]), 5)


if __name__ == "__main__":
    unittest.main()

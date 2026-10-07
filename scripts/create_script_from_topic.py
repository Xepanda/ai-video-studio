#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/create_script_from_topic.py
基于主题的一键结构化长视频脚本脚手架生成器 (Topic-to-Script Generator)

功能特性：
1. 完整实现五大前沿技术领域模板：
   - database_storage (数据库与存储引擎: Redis/MySQL/LSM-Tree)
   - ai_agent (人工智能与智能体: LLM/RAG/Attention/Inference)
   - system_architecture (高可用系统设计: 分布式/微服务/RPC)
   - devops_infra (云原生与可观测性: Kubernetes/ServiceMesh/CI-CD)
   - hardware_iot (嵌入式硬件与电机控制: MCU/FOC/DMA/SPI/Pinout)
2. 自动化生成生产级 Schema 契约：
   - 包含分镜大纲、极简工科叙事文案 (支持 G2P 发音优化)
   - 包含 ArchitectureTopology 架构拓扑节点与带方向的链路拓扑
   - 包含 MetricComparison (MetricCategory[]) 性能压测与基准对照卡片，严格匹配组件规范
   - 包含 TerminalWindow 极客终端代码块与工科卡片
3. 严格契合生产规范：
   - 默认使用 ChatTTS Seed 4444 (随和生活男声)
   - 默认使用 obsidian-minimal (黑曜极简工科风)
   - 全链路主题与元数据无缝下发
"""

import os
import sys
import json
import re
import time
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "content", "scripts")


def slugify(text: str) -> str:
    """生成合法且可读的文件名 Slug，消除连续下划线"""
    text = text.lower().strip()
    text = re.sub(r'[\s\-_]+', '_', text)
    text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
    ascii_part = re.sub(r'[^a-zA-Z0-9_]', '', text).strip('_')
    ascii_part = re.sub(r'_+', '_', ascii_part).strip('_')
    if ascii_part:
        return ascii_part
    return f"project_{int(time.time()) % 100000:05d}"


def detect_domain(topic: str) -> str:
    """
    根据主题关键词智能推断技术领域。
    使用严格正则单词边界与中文专有名词，杜绝 'failover' 误判为 'ai' 或 'firewall' 误判为 'wal'。
    """
    t = topic.lower()

    # 1. 数据库与高性能存储
    if re.search(r'\b(redis|mysql|postgres|postgresql|tidb|cache|wal|rocksdb|lsm|btree|skip_list|kv)\b', t) or \
       any(k in t for k in ["数据库", "缓存", "存储引擎", "持久化", "跳表", "数据湖", "存储"]):
        return "database_storage"

    # 2. 人工智能与智能体
    if re.search(r'\b(ai|agent|llm|rag|gpt|transformer|attention|deepseek|diffusion|tts|asr)\b', t) or \
       any(k in t for k in ["大模型", "智能体", "推理", "量化", "深度学习", "注意力机制", "提示词"]):
        return "ai_agent"

    # 3. 云原生、网关与 DevOps 基础设施
    if re.search(r'\b(k8s|kubernetes|docker|container|devops|nginx|gateway|istio|mesh|gitops|cicd|prometheus)\b', t) or \
       any(k in t for k in ["云原生", "网关", "服务网格", "容器", "微服务编排", "集群", "流水线"]):
        return "devops_infra"

    # 4. 嵌入式硬件、物联网与底层驱动
    if re.search(r'\b(mcu|stm32|esp32|arm|risc-v|riscv|foc|iot|dma|gpio|spi|i2c|pwm|pcb|rtos)\b', t) or \
       any(k in t for k in ["硬件", "嵌入式", "单片机", "引脚", "电机", "驱动", "微控制器"]):
        return "hardware_iot"

    # 5. 默认通用高可用分布式系统架构
    return "system_architecture"


def generate_structured_script(topic: str, project_name: str, scenes_count: int = 5,
                               theme: str = "obsidian-minimal",
                               engine: str = "chattts",
                               voice: str = "4444",
                               domain: str = "auto") -> dict:
    """生成完全符合数据契约与组件规范的高信息密度视频脚本"""
    if domain == "auto":
        domain = detect_domain(topic)

    # 领域定制资产模板库 (完整覆盖五大领域)
    domain_templates = {
        # 1. 数据库与存储引擎
        "database_storage": {
            "s1_badge": "ENGINE ARCHITECTURE · 核心架构",
            "s1_title": f"{topic}：高并发存储引擎设计哲学",
            "s1_narration": (
                f"在现代分布式系统与海量高并发业务场景中，{topic} 扮演着数据层核心底座的关键角色。"
                "面对每秒百万级的高吞吐读写压力，传统的磁盘顺序检索与单机锁机制早已成为性能瓶颈。"
                "今天我们将深入其内部内核，从内存数据布局、事件驱动循环到高可用复制协议，完整拆解其工业级架构设计。"
            ),
            "s1_cards": [
                {"title": "内存布局优化", "desc": "精细化内存对齐与零拷贝缓冲区，大幅降低 CPU 缓存缺失率", "tag": "CACHE LOCALITY"},
                {"title": "非阻塞事件循环", "desc": "单线程或工作线程池搭配多路复用 I/O，杜绝上下文切换损耗", "tag": "EVENT LOOP"},
                {"title": "持久化双轨机制", "desc": "WAL 预写日志与快照备份协同运作，保障秒级灾难恢复与数据强一致", "tag": "PERSISTENCE"}
            ],
            "topology_title": "端到端高可用存储读写链路",
            "nodes": [
                {"id": "client", "label": "Client Cluster", "sublabel": "连接池与哈希路由", "icon": "🖥️", "status": "ACTIVE", "statusColor": "#38bdf8", "x": 10, "y": 50},
                {"id": "proxy", "label": "Proxy / Gateway", "sublabel": "协议解析与负载均衡", "icon": "🌐", "status": "ROUTING", "statusColor": "#818cf8", "x": 30, "y": 30},
                {"id": "master", "label": "Primary Node", "sublabel": "内存核心与 WAL 写入", "icon": "⚡", "status": "WRITE LEADER", "statusColor": "#10b981", "x": 55, "y": 30},
                {"id": "replica", "label": "Replica Sync", "sublabel": "流式日志异步追赶", "icon": "📦", "status": "REPLICATING", "statusColor": "#f59e0b", "x": 55, "y": 70},
                {"id": "storage", "label": "Storage Engine", "sublabel": "B-Tree / LSM 树持久化", "icon": "💾", "status": "FLUSHED", "statusColor": "#64748b", "x": 85, "y": 50}
            ],
            "links": [
                {"from": "client", "to": "proxy", "label": "TCP KeepAlive", "active": True},
                {"from": "proxy", "to": "master", "label": "Write Command", "active": True},
                {"from": "master", "to": "replica", "label": "Replication Stream", "active": True},
                {"from": "master", "to": "storage", "label": "Async fsync", "active": True}
            ],
            "code_title": "StorageEngine.rs",
            "code_lang": "rust",
            "code_content": (
                "pub struct StorageEngine {\n"
                "    memtable: Arc<RwLock<SkipList<Vec<u8>, Vec<u8>>>>,\n"
                "    wal_writer: Mutex<WalWriter>,\n"
                "    block_cache: LruCache<BlockId, BlockData>,\n"
                "}\n\n"
                "impl StorageEngine {\n"
                "    pub fn put(&self, key: &[u8], val: &[u8]) -> Result<()> {\n"
                "        // 1. 预写日志保障崩溃一致性\n"
                "        self.wal_writer.lock().append(key, val)?;\n"
                "        // 2. 写入内存跳表索引\n"
                "        self.memtable.write().insert(key.to_vec(), val.to_vec());\n"
                "        Ok(())\n"
                "    }\n"
                "}"
            ),
            "metrics": [
                {
                    "title": "QPS 吞吐表现 (Requests/sec)",
                    "badge": "THROUGHPUT",
                    "pill": "5.2x 吞吐跃升",
                    "items": [
                        {"name": "基线标准方案", "value": 240000, "maxValue": 1300000, "unit": "req/s", "color": "#64748b"},
                        {"name": "优化后内核管道", "value": 1250000, "maxValue": 1300000, "unit": "req/s", "color": "#10b981", "highlight": True}
                    ]
                },
                {
                    "title": "P99 尾部延迟 (Latency)",
                    "badge": "LATENCY",
                    "pill": "95.5% 延迟削减",
                    "items": [
                        {"name": "传统阻塞锁模型", "value": 8.50, "maxValue": 10.0, "unit": "ms", "color": "#ef4444"},
                        {"name": "零拷贝非阻塞模型", "value": 0.38, "maxValue": 10.0, "unit": "ms", "color": "#38bdf8", "highlight": True}
                    ]
                }
            ]
        },

        # 2. 人工智能与智能体
        "ai_agent": {
            "s1_badge": "NEURAL COMPUTE · 认知智能",
            "s1_title": f"{topic}：端到端推理与智体架构",
            "s1_narration": (
                f"伴随着大语言模型与多模态技术的发展，{topic} 正在重构软件工程的交付界面。"
                "如何突破注意力机制的平方复杂度开销、如何保证大模型长程推理的状态连贯性，是工业界的核心攻坚战场。"
                "本期视频我们将聚焦其深层推理引擎、显存管理机制以及自主智能体的全周期闭环。"
            ),
            "s1_cards": [
                {"title": "稀疏注意力加速", "desc": "分块注意力与 KV 缓存显存分页管理，长文本推理显存占用降低 70%", "tag": "ATTENTION"},
                {"title": "自适应思维链推理", "desc": "多路径采样与自省纠错回溯机制，大幅提升复杂逻辑推理准确率", "tag": "REASONING"},
                {"title": "端侧轻量化量化", "desc": "AWQ 与 GGUF 高精度量化算子，使千亿大模型可在消费级硬件流畅运行", "tag": "QUANTIZATION"}
            ],
            "topology_title": "多智能体协作与端到端推理闭环",
            "nodes": [
                {"id": "planner", "label": "Orchestrator Agent", "sublabel": "意图理解与任务编排", "icon": "🧠", "status": "THINKING", "statusColor": "#818cf8", "x": 12, "y": 50},
                {"id": "retriever", "label": "Hybrid RAG Engine", "sublabel": "稠密向量与全文检索", "icon": "🔍", "status": "INDEXED", "statusColor": "#38bdf8", "x": 38, "y": 30},
                {"id": "llm", "label": "Inference Kernel", "sublabel": "KV-Cache 持续批处理", "icon": "⚡", "status": "STREAMING", "statusColor": "#10b981", "x": 62, "y": 30},
                {"id": "tools", "label": "Sandbox Tooling", "sublabel": "代码沙箱与外部 API", "icon": "🛠️", "status": "EXECUTING", "statusColor": "#f59e0b", "x": 62, "y": 70},
                {"id": "verifier", "label": "Self-Reflection Gate", "sublabel": "形式化验证与质量门禁", "icon": "🛡️", "status": "VERIFIED", "statusColor": "#a855f7", "x": 88, "y": 50}
            ],
            "links": [
                {"from": "planner", "to": "retriever", "label": "Semantic Query", "active": True},
                {"from": "retriever", "to": "llm", "label": "Context Injection", "active": True},
                {"from": "llm", "to": "tools", "label": "Tool Calls", "active": True},
                {"from": "tools", "to": "verifier", "label": "Execution Output", "active": True}
            ],
            "code_title": "AgentRuntime.py",
            "code_lang": "python",
            "code_content": (
                "class AutonomousAgentRuntime:\n"
                "    def __init__(self, model_client, memory_bank):\n"
                "        self.model = model_client\n"
                "        self.memory = memory_bank\n\n"
                "    async def step(self, task: TaskContext) -> StepResult:\n"
                "        # 1. 结构化上下文与历史召回\n"
                "        context = await self.memory.retrieve(task.query)\n"
                "        # 2. 流式推理生成行为动作\n"
                "        action = await self.model.generate_action(task, context)\n"
                "        return await action.execute_in_sandbox()\n"
            ),
            "metrics": [
                {
                    "title": "首字延迟 TTFT (Time to First Token)",
                    "badge": "LATENCY",
                    "pill": "8.9x 极速首字",
                    "items": [
                        {"name": "传统原生推理框架", "value": 165.0, "maxValue": 180.0, "unit": "ms", "color": "#ef4444"},
                        {"name": "PagedAttention 优化", "value": 18.5, "maxValue": 180.0, "unit": "ms", "color": "#38bdf8", "highlight": True}
                    ]
                },
                {
                    "title": "长上下文任务吞吐 (Tokens/sec)",
                    "badge": "THROUGHPUT",
                    "pill": "6.7x 吞吐提速",
                    "items": [
                        {"name": "自回归单步解码", "value": 42.0, "maxValue": 320.0, "unit": "tok/s", "color": "#64748b"},
                        {"name": "自适应投机解码", "value": 285.0, "maxValue": 320.0, "unit": "tok/s", "color": "#10b981", "highlight": True}
                    ]
                }
            ]
        },

        # 3. 云原生与 DevOps 基础设施
        "devops_infra": {
            "s1_badge": "CLOUD NATIVE · 云原生基建",
            "s1_title": f"{topic}：弹性编排与高可用控制面",
            "s1_narration": (
                f"在现代微服务与不可变基础设施实践中，{topic} 构筑了自动化交付与弹性运维的基石。"
                "从声明式 API、控制循环协调器到细粒度的服务网格流量管理，系统能够在节点故障时实现自愈。"
                "接下来，我们将深入其控制平面、调度算法以及零停机发布的底层闭环。"
            ),
            "s1_cards": [
                {"title": "声明式状态协调", "desc": "基于实际状态与期望状态的无休止 Reconciliation 循环，保障集群秒级自愈", "tag": "CONTROLLER"},
                {"title": "智能拓扑感知调度", "desc": "综合节点亲和性、污点容忍与网络延迟矩阵，达成集群算力最优化分配", "tag": "SCHEDULING"},
                {"title": "精细化服务网格", "desc": "Sidecar 代理无侵入接管南北与东西向流量，实现金丝雀渐进式发布", "tag": "SERVICE MESH"}
            ],
            "topology_title": "云原生编排与流量调度全景",
            "nodes": [
                {"id": "ingress", "label": "Ingress Controller", "sublabel": "BGP Anycast & TLS 卸载", "icon": "🌐", "status": "ONLINE", "statusColor": "#38bdf8", "x": 10, "y": 50},
                {"id": "mesh", "label": "Envoy Service Mesh", "sublabel": "双向 mTLS 与熔断限流", "icon": "🛡️", "status": "SECURED", "statusColor": "#818cf8", "x": 32, "y": 30},
                {"id": "pod_a", "label": "Pod Replica Alpha", "sublabel": "无状态容器实例池", "icon": "📦", "status": "RUNNING", "statusColor": "#10b981", "x": 60, "y": 25},
                {"id": "pod_b", "label": "Pod Replica Beta", "sublabel": "多可用区高可用热备", "icon": "📦", "status": "READY", "statusColor": "#10b981", "x": 60, "y": 75},
                {"id": "storage", "label": "CSI Persistent Vol", "sublabel": "分布式块存储动态挂载", "icon": "💾", "status": "BOUND", "statusColor": "#f59e0b", "x": 88, "y": 50}
            ],
            "links": [
                {"from": "ingress", "to": "mesh", "label": "HTTP/2 Route", "active": True},
                {"from": "mesh", "to": "pod_a", "label": "mTLS Stream", "active": True},
                {"from": "mesh", "to": "pod_b", "label": "Canary Split", "active": True},
                {"from": "pod_a", "to": "storage", "label": "NVMe-oF Mount", "active": True}
            ],
            "code_title": "deployment.yaml",
            "code_lang": "yaml",
            "code_content": (
                "apiVersion: apps/v1\n"
                "kind: Deployment\n"
                "metadata:\n"
                "  name: core-service-pipeline\n"
                "spec:\n"
                "  replicas: 5\n"
                "  strategy:\n"
                "    rollingUpdate:\n"
                "      maxSurge: 25%\n"
                "      maxUnavailable: 0\n"
                "  template:\n"
                "    spec:\n"
                "      containers:\n"
                "      - name: app\n"
                "        image: registry.internal/app:v2.4.0\n"
                "        resources:\n"
                "          limits: { cpu: '2', memory: 4Gi }\n"
                "          requests: { cpu: 500m, memory: 1Gi }\n"
            ),
            "metrics": [
                {
                    "title": "Pod 冷启动耗时 (Cold-Start Duration)",
                    "badge": "STARTUP TIME",
                    "pill": "12.1x 极速扩容",
                    "items": [
                        {"name": "传统镜像分发", "value": 14.5, "maxValue": 16.0, "unit": "s", "color": "#ef4444"},
                        {"name": "按需延迟加载 eStargz", "value": 1.2, "maxValue": 16.0, "unit": "s", "color": "#10b981", "highlight": True}
                    ]
                },
                {
                    "title": "单机容器调度密度 (Pods per Node)",
                    "badge": "DENSITY",
                    "pill": "4.9x 资源密度",
                    "items": [
                        {"name": "常规重型虚拟机", "value": 85, "maxValue": 450, "unit": "pods", "color": "#64748b"},
                        {"name": "轻量微容器运行时", "value": 420, "maxValue": 450, "unit": "pods", "color": "#38bdf8", "highlight": True}
                    ]
                }
            ]
        },

        # 4. 嵌入式硬件、物联网与驱动控制
        "hardware_iot": {
            "s1_badge": "EMBEDDED SYSTEMS · 硬件微内核",
            "s1_title": f"{topic}：硬实时微控制器与外设控制",
            "s1_narration": (
                f"在软硬件协同与嵌入式控制领域，{topic} 展现了贴合物理世界极限的工程艺术。"
                "在资源极度受限的微控制器上，如何实现微秒级的无抖动中断响应、零 CPU 占用的 DMA 异步外设通信，是硬件工程师的核心功底。"
                "今天我们将自底向上剖析其寄存器交互、时钟树分频与高频总线拓扑。"
            ),
            "s1_cards": [
                {"title": "零开销直接内存访问", "desc": "外设与 SRAM 之间通过多通道 DMA 独立交换数据，彻底解放核心运算单元", "tag": "DMA PIPELINE"},
                {"title": "纳秒级硬件中断抢占", "desc": "嵌套向量中断控制器配合尾链技术，达成确定性极强的硬件低延迟响应", "tag": "NVIC ISR"},
                {"title": "硬件闭环互锁防护", "desc": "互补 PWM 发生器带可编程死区插入与刹车输入，物理级防范过流击穿", "tag": "DEADTIME"}
            ],
            "topology_title": "微控制器硬件总线与外设拓扑",
            "nodes": [
                {"id": "mcu", "label": "MCU CPU Core", "sublabel": "Cortex-M4 168MHz 内核", "icon": "⚡", "status": "RUNNING", "statusColor": "#38bdf8", "x": 12, "y": 50},
                {"id": "dma", "label": "DMA Controller", "sublabel": "双缓冲循环流式传输", "icon": "🔄", "status": "STREAMING", "statusColor": "#10b981", "x": 38, "y": 30},
                {"id": "spi", "label": "High-Speed SPI/I2C", "sublabel": "42MHz 硬件外设总线", "icon": "🔌", "status": "SYNCED", "statusColor": "#818cf8", "x": 64, "y": 30},
                {"id": "timer", "label": "Advanced PWM Timer", "sublabel": "三相互补死区发生器", "icon": "⏱️", "status": "PULSING", "statusColor": "#f59e0b", "x": 64, "y": 70},
                {"id": "power", "label": "Power Stage / Gate", "sublabel": "半桥驱动与电机绕组", "icon": "🔋", "status": "OUTPUT", "statusColor": "#ef4444", "x": 88, "y": 50}
            ],
            "links": [
                {"from": "mcu", "to": "dma", "label": "AHB Bus", "active": True},
                {"from": "dma", "to": "spi", "label": "TX/RX FIFO", "active": True},
                {"from": "mcu", "to": "timer", "label": "APB2 Clock", "active": True},
                {"from": "timer", "to": "power", "label": "Complementary PWM", "active": True}
            ],
            "code_title": "foc_controller.c",
            "code_lang": "c",
            "code_content": (
                "void TIM1_UP_TIM10_IRQHandler(void) {\n"
                "    if (TIM1->SR & TIM_SR_UIF) {\n"
                "        TIM1->SR = ~TIM_SR_UIF; // 清除中断标志\n"
                "        // 1. 采集双路相电流 ADC 瞬时值\n"
                "        float i_a = read_current_phase_a();\n"
                "        float i_b = read_current_phase_b();\n"
                "        // 2. Clarke & Park 矢量变换并计算 SVPWM 占空比\n"
                "        foc_calculate_vector(i_a, i_b, &duty_u, &duty_v, &duty_w);\n"
                "        TIM1->CCR1 = duty_u;\n"
                "        TIM1->CCR2 = duty_v;\n"
                "        TIM1->CCR3 = duty_w;\n"
                "    }\n"
                "}\n"
            ),
            "metrics": [
                {
                    "title": "控制循环时序抖动 (Loop Jitter)",
                    "badge": "DETERMINISM",
                    "pill": "42x 时序精度",
                    "items": [
                        {"name": "软件模拟控制环路", "value": 2.10, "maxValue": 2.5, "unit": "μs", "color": "#ef4444"},
                        {"name": "硬件中断与定时器同步", "value": 0.05, "maxValue": 2.5, "unit": "μs", "color": "#10b981", "highlight": True}
                    ]
                },
                {
                    "title": "CPU 负载占用率 (CPU Overhead)",
                    "badge": "EFFICIENCY",
                    "pill": "83% 负载解放",
                    "items": [
                        {"name": "软件轮询中断模式", "value": 88, "maxValue": 100, "unit": "%", "color": "#64748b"},
                        {"name": "DMA 双缓冲直通模式", "value": 15, "maxValue": 100, "unit": "%", "color": "#38bdf8", "highlight": True}
                    ]
                }
            ]
        },

        # 5. 高可用分布式系统架构
        "system_architecture": {
            "s1_badge": "SYSTEM DESIGN · 架构全景",
            "s1_title": f"{topic}：高可用系统架构全景",
            "s1_narration": (
                f"在分布式软件工程中，{topic} 展现了优秀的系统抽象与高吞吐架构哲学。"
                "面对突发流量洪峰与复杂不可控的网络分区，如何构建具备弹性伸缩能力与毫秒级容灾自愈的高可用架构，是系统设计的永恒命题。"
                "接下来，我们将全景剖析其架构演进脉络与关键治理方案。"
            ),
            "s1_cards": [
                {"title": "服务分层解耦", "desc": "接入网关、计算编排与数据存储彻底解耦，支持任意节点的无状态横向扩容", "tag": "DECOUPLING"},
                {"title": "自适应背压流控", "desc": "基于滑动窗口算法的动态拥塞控制，防止瞬时峰值击穿下游依赖服务", "tag": "FLOW CONTROL"},
                {"title": "分布式事务与幂等", "desc": "两阶段提交结合本地事务消息表，确保复杂分布式操作的最终一致性", "tag": "CONSISTENCY"}
            ],
            "topology_title": "多层级高可用系统数据拓扑",
            "nodes": [
                {"id": "ingress", "label": "Ingress Edge", "sublabel": "BGP Anycast 与 SSL 卸载", "icon": "🌐", "status": "ONLINE", "statusColor": "#38bdf8", "x": 10, "y": 50},
                {"id": "gateway", "label": "API Gateway", "sublabel": "身份鉴权与熔断限流", "icon": "🛡️", "status": "GUARDED", "statusColor": "#818cf8", "x": 32, "y": 30},
                {"id": "service", "label": "Microservices", "sublabel": "无状态 RPC 业务集群", "icon": "⚙️", "status": "SCALED", "statusColor": "#10b981", "x": 58, "y": 30},
                {"id": "mq", "label": "Event Streaming", "sublabel": "Kafka 异步削峰填谷", "icon": "📬", "status": "BUFFERED", "statusColor": "#f59e0b", "x": 58, "y": 70},
                {"id": "db", "label": "Distributed DB", "sublabel": "分库分表与多副本共识", "icon": "🗄️", "status": "SYNCHRONIZED", "statusColor": "#64748b", "x": 86, "y": 50}
            ],
            "links": [
                {"from": "ingress", "to": "gateway", "label": "TLS 1.3", "active": True},
                {"from": "gateway", "to": "service", "label": "gRPC Stream", "active": True},
                {"from": "service", "to": "mq", "label": "Async Event", "active": True},
                {"from": "service", "to": "db", "label": "Read/Write Split", "active": True}
            ],
            "code_title": "PipelineOrchestrator.go",
            "code_lang": "go",
            "code_content": (
                "type ServicePipeline struct {\n"
                "    rateLimiter  *TokenBucket\n"
                "    circuitBreaker *Breaker\n"
                "    rpcPool      *ClientPool\n"
                "}\n\n"
                "func (p *ServicePipeline) Dispatch(ctx context.Context, req *Request) (*Response, error) {\n"
                "    if !p.rateLimiter.Allow() {\n"
                "        return nil, ErrTrafficShed\n"
                "    }\n"
                "    return p.circuitBreaker.Execute(func() (*Response, error) {\n"
                "        return p.rpcPool.Call(ctx, req)\n"
                "    })\n"
                "}"
            ),
            "metrics": [
                {
                    "title": "突发流量处理容量 (Concurrencies)",
                    "badge": "CONCURRENCY",
                    "pill": "15x 并发提升",
                    "items": [
                        {"name": "经典同步线程池", "value": 12000, "maxValue": 200000, "unit": "conns", "color": "#64748b"},
                        {"name": "响应式无锁管道", "value": 180000, "maxValue": 200000, "unit": "conns", "color": "#10b981", "highlight": True}
                    ]
                },
                {
                    "title": "节点故障切换耗时 (Failover Time)",
                    "badge": "HIGH AVAILABILITY",
                    "pill": "99.2% 恢复提速",
                    "items": [
                        {"name": "人工告警介入切换", "value": 15000, "maxValue": 16000, "unit": "ms", "color": "#ef4444"},
                        {"name": "Raft 自动心跳选举", "value": 120, "maxValue": 16000, "unit": "ms", "color": "#38bdf8", "highlight": True}
                    ]
                }
            ]
        }
    }

    tmpl = domain_templates.get(domain, domain_templates["system_architecture"])

    # 构造完整 5 幕标准分镜，显式为每一幕分镜透传 theme
    scenes = [
        # Scene 1: 痛点与背景剖析 (Card Grid)
        {
            "id": "scene_01",
            "title": tmpl["s1_title"],
            "badge": tmpl["s1_badge"],
            "theme": theme,
            "text": tmpl["s1_narration"],
            "cards": tmpl["s1_cards"]
        },
        # Scene 2: 核心架构拓扑 (ArchitectureTopology)
        {
            "id": "scene_02",
            "type": "ArchitectureTopology",
            "title": f"{topic}：核心数据拓扑与流转机制",
            "badge": "ARCHITECTURE TOPOLOGY · 拓扑设计",
            "theme": theme,
            "text": (
                f"在整个 {topic} 体系中，数据与控制信令的流转路径被划分为多层清晰的拓扑结构。"
                "请求自左侧接入端发起，经过负载网关的路由决策与状态拦截，分流至高并发计算集群。"
                "各个节点之间通过轻量级心跳与异步管道保持高内聚低耦合，确保单点故障不扩散。"
            ),
            "topologyNodes": tmpl["nodes"],
            "topologyLinks": tmpl["links"]
        },
        # Scene 3: 底层核心代码/机制深度推演 (TerminalCodeDemo)
        {
            "id": "scene_03",
            "type": "TerminalCodeDemo",
            "title": f"{topic}：关键底层实现与核心代码剖析",
            "badge": "CODE DEEP DIVE · 代码实现",
            "theme": theme,
            "text": (
                "纸上得来终觉浅，绝知此事要躬行。我们通过屏幕上的核心源码，直观审视其底层的关键实现机制。"
                "注意这里的无锁队列与状态校验逻辑，它在纳秒级维度规避了昂贵的内核态切换，"
                "正是这些极致的软硬件协同优化，构筑了系统坚不可摧的高性能基石。"
            ),
            "codeTitle": tmpl["code_title"],
            "codeLang": tmpl["code_lang"],
            "codeSnippet": tmpl["code_content"]
        },
        # Scene 4: 性能压测与基准对照 (MetricComparison)
        {
            "id": "scene_04",
            "type": "MetricComparison",
            "title": f"{topic}：工业级压测基准与性能对照",
            "badge": "BENCHMARK SCORECARD · 性能基准",
            "theme": theme,
            "text": (
                "口说无凭，数据说话。我们搭建了模拟生产真实负载的严苛压测环境，对系统进行了高压力饱和测试。"
                "在吞吐量与尾部延迟两个最核心的衡量维度上，优化后的架构展现出了压倒性的性能优势，"
                "P99 延迟显著降低，整体资源占用下降超百分之六十。"
            ),
            "metrics": tmpl["metrics"]
        },
        # Scene 5: 生产实践总结与架构权衡 (Card Grid)
        {
            "id": "scene_05",
            "title": f"{topic}：生产落地最佳实践与工程权衡",
            "badge": "ENGINEERING TRADEOFF · 落地演进",
            "theme": theme,
            "text": (
                f"回顾整个 {topic} 的设计与实现，软件工程中没有免费的午餐，任何架构都是权衡的艺术。"
                "在拥抱极致性能的同时，我们必须建立完善的指标监控可观测性体系，制定清晰的灾备降级预案。"
                "掌握底层原理，方能以不变应万变，在架构演进的道路上游刃有余。"
            ),
            "cards": [
                {"title": "全链路可观测性", "desc": "指标监控、链路追踪与实时告警无缝串联，构建透明的系统黑盒观察窗", "tag": "OBSERVABILITY"},
                {"title": "渐进式灰度发布", "desc": "金丝雀发布结合自动化指标巡检，将生产发布风险控制在毫厘之间", "tag": "PROGRESSIVE ROLLOUT"},
                {"title": "极客工程文化", "desc": "坚持基准评测驱动优化，用数据和代码衡量每一次架构迭代的真实价值", "tag": "DATA DRIVEN"}
            ]
        }
    ]

    # 根据请求分镜数裁剪或保护性截取 (严格保证至少 1 幕，至多 len(scenes))
    actual_count = max(1, min(scenes_count, len(scenes)))
    scenes = scenes[:actual_count]

    return {
        "project": project_name,
        "engine": engine,
        "voice": voice,
        "theme": theme,
        "fps": 30,
        "title": topic,
        "scenes": scenes
    }


def main():
    parser = argparse.ArgumentParser(description="基于技术主题的一键视频脚本脚手架生成器")
    parser.add_argument("--topic", type=str, required=True, help="视频核心主题 (例如: 'Redis 核心架构与高性能底层原理')")
    parser.add_argument("--project", type=str, default="", help="项目隔离标识 (默认由 topic 自动生成)")
    parser.add_argument("--scenes", type=int, default=5, choices=range(1, 6), help="生成的分镜数 (1 ~ 5 幕，默认 5 幕)")
    parser.add_argument("--theme", type=str, choices=["obsidian-minimal", "blueprint-engineering", "cinema-editorial"], default="obsidian-minimal", help="视频视觉主题风格")
    parser.add_argument("--engine", type=str, default="chattts", help="TTS 配音服务商 (默认 chattts)")
    parser.add_argument("--voice", type=str, default="4444", help="TTS 配音音色 Seed (默认 4444 随和生活男声)")
    parser.add_argument("--domain", type=str, choices=["auto", "system_architecture", "ai_agent", "database_storage", "devops_infra", "hardware_iot"], default="auto", help="技术领域预设")
    parser.add_argument("--output", type=str, default="", help="输出文件路径 (默认 content/scripts/{project}.json)")
    parser.add_argument("--dry_run", action="store_true", help="仅打印至控制台，不写入磁盘")

    args = parser.parse_args()

    if not args.topic.strip():
        parser.error("错误: --topic 不能为空或纯空白字符串！")

    project_name = args.project.strip() if args.project.strip() else slugify(args.topic)
    output_path = args.output.strip() if args.output.strip() else os.path.join(SCRIPTS_DIR, f"{project_name}.json")

    print(f"\n=======================================================")
    print(f"🎬 [Script Generator] 正在根据主题生成专业级长视频脚本")
    print(f"  核心主题: {args.topic}")
    print(f"  项目标识: {project_name}")
    print(f"  分镜数量: {args.scenes}")
    print(f"  视觉主题: {args.theme}")
    print(f"  默认配音: {args.engine} (音色: {args.voice})")
    print(f"  技术领域: {args.domain}")
    print(f"=======================================================\n")

    script_data = generate_structured_script(
        topic=args.topic,
        project_name=project_name,
        scenes_count=args.scenes,
        theme=args.theme,
        engine=args.engine,
        voice=args.voice,
        domain=args.domain
    )

    formatted_json = json.dumps(script_data, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(formatted_json)
        return

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)

    print(f"✅ 脚本已成功生成并持久化至:")
    print(f"   {os.path.relpath(output_path, PROJECT_ROOT)}")
    print(f"\n💡 建议下一步操作:")
    print(f"   python scripts/pipeline.py --script content/scripts/{project_name}.json --project {project_name}\n")


if __name__ == "__main__":
    main()

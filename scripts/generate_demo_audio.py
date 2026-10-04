#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_demo_audio.py
生成工作流介绍视频的配音与 SenseVoice 毫秒级打点契约
"""

import os
import sys
import asyncio
import edge_tts
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(PROJECT_ROOT, "public", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICE = "zh-CN-YunxiNeural"

SCENES_SCRIPT = [
    {
        "id": "scene_01",
        "type": "ExplainerWhiteboard",
        "text": "欢迎来到 AI Video Studio 全链路视频自动化工作流。传统剪辑费时费力，文生视频乱码不可控。我们采用代码即视频理念，实现程序化精准渲染。"
    },
    {
        "id": "scene_02",
        "type": "TimelineContract",
        "text": "核心第一步，声音先行。配音时长决定画面寿命，阿里 SenseVoice 毫秒打点，秒级提取词级时间戳与情绪标签，生成唯一时钟契约 timeline.json。"
    },
    {
        "id": "scene_03",
        "type": "TerminalCodeDemo",
        "text": "核心第二步，组件化装配与 Google Flow 电影级镜头协同。网页端极速生成概念素材，React 声明式驱动终端打字机与逐字弹跳大字幕。"
    },
    {
        "id": "scene_04",
        "type": "QualityAudit",
        "text": "核心第三步，五重质量门禁。自动化校验音频与素材完整性，多核并发无头光栅化压制，音画分毫不差。你的自动化流水线已正式启航！"
    }
]

async def synthesize_all():
    print(">>> [1/2] 正在调用 edge-tts 生成 4 段分镜神经配音...")
    for scene in SCENES_SCRIPT:
        out_path = os.path.join(AUDIO_DIR, f"{scene['id']}.mp3")
        print(f"  🎙️ 生成配音: {scene['id']} -> {scene['text'][:20]}...")
        communicate = edge_tts.Communicate(scene["text"], VOICE, rate="+5%")
        await communicate.save(out_path)
    print(">>> 配音生成完毕！\n")

if __name__ == "__main__":
    asyncio.run(synthesize_all())

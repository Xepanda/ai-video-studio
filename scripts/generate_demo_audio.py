#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_demo_audio.py
生成全技能大满贯视频的配音与 SenseVoice 毫秒级打点契约
"""

import os
import sys
import asyncio
import edge_tts

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(PROJECT_ROOT, "public", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICE = "zh-CN-YunxiNeural"

SCENES_SCRIPT = [
    {
        "id": "scene_01",
        "title": "声音克隆与声纹时钟底座",
        "text": "第一模块，自声音克隆与毫秒时钟中枢。仅需五秒参考干声，提取个人声纹特征向量，驱动神经网络复刻音色；再由阿里 SenseVoice 毫秒打点，生成唯一时钟契约。"
    },
    {
        "id": "scene_02",
        "title": "科普视频白板手绘",
        "text": "形态一，科普白板手绘。基于 SVG 虚线偏移模拟真实铅笔笔触，动态手绘擦除，点阵图标瞬间转化为活体矢量描边，打造形象生动的技术图解。"
    },
    {
        "id": "scene_03",
        "title": "项目实战与终端架构",
        "text": "形态二，项目实战教程。极客打字机毫秒同步敲入命令，输出彩色终端流；架构双卡阻尼对比，配合单片机引脚正弦脉冲流光，直击硬核技术原理。"
    },
    {
        "id": "scene_04",
        "title": "实拍视频与硬件混剪",
        "text": "形态三，实拍视频混剪。金属质感悬浮手机壳画中画，原生嵌入实拍硬件原片；激光扫描线与发光指示引线，毫秒级精准追踪实物元器件。"
    },
    {
        "id": "scene_05",
        "title": "日常自媒体与 Google Flow 电影镜头",
        "text": "形态四，日常自媒体与 Google Flow 电影镜头。网页端极速生成 Veo 概念镜头，Remotion 电影级微推慢移，搭配逐字弹跳彩色字幕，七大技能融为一体！"
    }
]

async def synthesize_all():
    print(">>> 正在为 5 大场景生成神经配音...")
    for scene in SCENES_SCRIPT:
        out_path = os.path.join(AUDIO_DIR, f"{scene['id']}.mp3")
        print(f"  🎙️ 场景 {scene['id']} [{scene['title']}]: {scene['text'][:24]}...")
        communicate = edge_tts.Communicate(scene["text"], VOICE, rate="+6%")
        await communicate.save(out_path)
    print(">>> 全部 5 段音频生成完毕！\n")

if __name__ == "__main__":
    asyncio.run(synthesize_all())

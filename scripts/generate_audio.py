#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_audio.py
全链路视频自动化音频生成中枢
支持：
  1. SiliconFlow 专属克隆音色 (CosyVoice2 / FishSpeech)
  2. Fish Audio API 专属音色
  3. MiniMax 海螺语音克隆音色
  4. 微软 Edge-TTS 免费本地神经语音回退机制
"""

import os
import sys
import json
import argparse
import asyncio
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

def load_env():
    env_vars = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def synthesize_siliconflow(text: str, out_path: str, api_key: str, voice_id: str, model: str):
    url = "https://api.siliconflow.cn/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model or "FunAudioLLM/CosyVoice2-0.5B",
        "input": text,
        "voice": voice_id,
        "response_format": "mp3",
        "sample_rate": 24000
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"SiliconFlow TTS 失败 ({resp.status_code}): {resp.text}")
    with open(out_path, "wb") as f:
        f.write(resp.content)

def synthesize_fish_audio(text: str, out_path: str, api_key: str, voice_id: str):
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3"
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Fish Audio TTS 失败 ({resp.status_code}): {resp.text}")
    with open(out_path, "wb") as f:
        f.write(resp.content)

def synthesize_minimax(text: str, out_path: str, api_key: str, group_id: str, voice_id: str):
    url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "speech-01-turbo",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0
        },
        "audio_setting": {
            "sample_rate": 24000,
            "format": "mp3"
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"MiniMax TTS 失败 ({resp.status_code}): {resp.text}")
    data = resp.json()
    audio_hex = data.get("data", {}).get("audio")
    if not audio_hex:
        raise RuntimeError(f"MiniMax 未返回音频数据: {data}")
    import binascii
    audio_bytes = binascii.unhexlify(audio_hex)
    with open(out_path, "wb") as f:
        f.write(audio_bytes)

async def synthesize_edge_tts(text: str, out_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural")
    await communicate.save(out_path)

def generate_scene_audio(text: str, out_path: str, env: dict):
    provider = env.get("TTS_PROVIDER", "siliconflow").lower()
    sf_key = env.get("SILICONFLOW_API_KEY")
    sf_voice = env.get("CUSTOM_VOICE_ID")
    sf_model = env.get("SILICONFLOW_MODEL", "FunAudioLLM/CosyVoice2-0.5B")

    # 1. 优先尝试使用 SiliconFlow 专属音色
    if provider == "siliconflow":
        if sf_key and not sf_key.startswith("sk-your-") and sf_voice:
            print(f"    [SiliconFlow] 正在使用专属克隆音色: {sf_voice}")
            synthesize_siliconflow(text, out_path, sf_key, sf_voice, sf_model)
            return
        else:
            print(f"    ⚠️ 未检测到有效的 SILICONFLOW_API_KEY 或 CUSTOM_VOICE_ID")
            print(f"    ➡️ 自动回退至高质量 Edge-TTS (YunxiNeural)")

    # 2. 尝试 Fish Audio
    elif provider == "fish_audio":
        fish_key = env.get("FISH_AUDIO_API_KEY")
        fish_voice = env.get("FISH_VOICE_ID")
        if fish_key and fish_voice:
            print(f"    [Fish Audio] 正在使用专属音色: {fish_voice}")
            synthesize_fish_audio(text, out_path, fish_key, fish_voice)
            return

    # 3. 尝试 MiniMax
    elif provider == "minimax":
        mm_key = env.get("MINIMAX_API_KEY")
        mm_group = env.get("MINIMAX_GROUP_ID")
        mm_voice = env.get("MINIMAX_VOICE_ID")
        if mm_key and mm_group and mm_voice:
            print(f"    [MiniMax] 正在使用专属音色: {mm_voice}")
            synthesize_minimax(text, out_path, mm_key, mm_group, mm_voice)
            return

    # 回退到本地 Edge-TTS
    asyncio.run(synthesize_edge_tts(text, out_path))

def main():
    parser = argparse.ArgumentParser(description="分镜音频批量自动生成")
    parser.add_argument("--script", type=str, default="inputs/script.json", help="分镜脚本文件路径")
    parser.add_argument("--output_dir", type=str, default="public/audio", help="音频输出目录")
    args = parser.parse_args()

    script_path = os.path.join(PROJECT_ROOT, args.script) if not os.path.isabs(args.script) else args.script
    output_dir = os.path.join(PROJECT_ROOT, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(script_path):
        print(f"❌ 找不到分镜脚本: {script_path}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    scenes = script_data.get("scenes", [])
    if not scenes:
        print(f"❌ 脚本中没有找到 scenes 分镜定义！")
        sys.exit(1)

    env = load_env()
    provider = env.get("TTS_PROVIDER", "siliconflow")
    custom_voice = env.get("CUSTOM_VOICE_ID", "默认/未配置")

    print(f"\n=======================================================")
    print(f"🎙️ [Audio Generator] 正在生成分镜配音音频")
    print(f"  TTS 服务商: {provider}")
    print(f"  专属音色 ID: {custom_voice}")
    print(f"  分镜总数: {len(scenes)}")
    print(f"=======================================================\n")

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{idx+1:02d}")
        text = scene.get("text", "").strip()
        if not text:
            continue

        out_file = os.path.join(output_dir, f"{scene_id}.mp3")
        print(f"  ▶️ [{scene_id}] 正在合成: {text[:28]}...")
        generate_scene_audio(text, out_file, env)
        print(f"    ✓ 已输出: {os.path.relpath(out_file, PROJECT_ROOT)}")

    print(f"\n✅ 所有分镜配音音频生成完毕！存储于 {os.path.relpath(output_dir, PROJECT_ROOT)}")

if __name__ == "__main__":
    main()

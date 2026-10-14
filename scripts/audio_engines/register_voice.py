#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/register_voice.py
一键上传专属参考音频到云端 API (SiliconFlow)，完成音色克隆并自动写入 .env
"""

import os
import sys
import argparse
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

def save_or_update_env(key: str, value: str):
    lines = []
    found = False
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"💾 已将配置 [{key}={value}] 保存至 .env 文件")

def register_siliconflow_voice(api_key: str, audio_path: str, voice_name: str, reference_text: str, model: str):
    print(f"🚀 正在上传参考音频至 SiliconFlow 进行音色指纹抽取...")
    print(f"  音频路径: {audio_path}")
    print(f"  音色标识: {voice_name}")
    print(f"  基座模型: {model}")
    print(f"  参考文本: {reference_text}")

    url = "https://api.siliconflow.cn/v1/uploads/audio/voice"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f, "audio/mpeg")
        }
        data = {
            "model": model,
            "customName": voice_name,
            "text": reference_text
        }
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)

    if resp.status_code != 200:
        print(f"❌ 上传失败 (HTTP {resp.status_code}): {resp.text}")
        sys.exit(1)

    res_json = resp.json()
    voice_uri = res_json.get("uri")
    if not voice_uri:
        print(f"❌ 返回结果中未找到 uri: {res_json}")
        sys.exit(1)

    print(f"\n🎉 专属音色克隆成功！")
    print(f"  Voice URI: {voice_uri}")
    save_or_update_env("CUSTOM_VOICE_ID", voice_uri)
    save_or_update_env("TTS_PROVIDER", "siliconflow")
    print("\n✅ 现在您可以在所有视频制作中直接使用自己的音色了！")

def main():
    parser = argparse.ArgumentParser(description="一键克隆音色并注册到云端平台")
    parser.add_argument("--audio", type=str, default="models/reference_audio/my_voice_sample.mp3", help="参考音频文件路径")
    parser.add_argument("--name", type=str, default="my_custom_voice", help="自定义音色名称")
    parser.add_argument("--text", type=str, default="玩转ESP32嵌入式开发，串口通信硬件调试", help="参考音频所说的文本")
    parser.add_argument("--model", type=str, default="FunAudioLLM/CosyVoice2-0.5B", help="TTS 基座模型")
    args = parser.parse_args()

    audio_full_path = os.path.join(PROJECT_ROOT, args.audio) if not os.path.isabs(args.audio) else args.audio

    env = load_env()
    api_key = env.get("SILICONFLOW_API_KEY")

    if not api_key or api_key == "sk-your-siliconflow-api-key":
        print("❌ 未检测到有效的 SILICONFLOW_API_KEY！")
        print("💡 请先按以下步骤获取 API Key：")
        print("  1. 访问 https://cloud.siliconflow.cn/ 注册并登录")
        print("  2. 进入 'API密钥' 页面创建密钥")
        print("  3. 复制并在 .env 中设置 SILICONFLOW_API_KEY=sk-xxxxxx")
        sys.exit(1)

    register_siliconflow_voice(api_key, audio_full_path, args.name, args.text, args.model)

if __name__ == "__main__":
    main()

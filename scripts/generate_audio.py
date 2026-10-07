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
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
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

def synthesize_gpt_sovits(text: str, out_path: str, api_url: str = "http://127.0.0.1:9880/tts", ref_audio: str = None, prompt_text: str = None, prompt_lang: str = "zh", text_lang: str = "zh"):
    payload = {
        "text": text,
        "text_lang": text_lang,
        "ref_audio_path": ref_audio,
        "prompt_text": prompt_text or "",
        "prompt_lang": prompt_lang,
        "media_type": "wav"
    }
    resp = requests.post(api_url, json=payload, timeout=180)
    if resp.status_code != 200:
        raise RuntimeError(f"GPT-SoVITS 合成失败 ({resp.status_code}): {resp.text}")
    wav_path = os.path.splitext(out_path)[0] + ".wav"
    with open(wav_path, "wb") as f:
        f.write(resp.content)
    old_mp3 = os.path.splitext(out_path)[0] + ".mp3"
    if os.path.exists(old_mp3) and old_mp3 != wav_path:
        try:
            os.remove(old_mp3)
        except Exception:
            pass
    return wav_path

async def synthesize_edge_tts(text: str, out_path: str, voice: str = "zh-CN-YunxiNeural", max_retries: int = 3):
    import edge_tts
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(out_path)
            return out_path
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"    ⚠️ Edge-TTS 网络超时 ({e})，自动切换至本地 Kokoro-82M 离线高可用兜底...")
                from scripts.tts_kokoro import synthesize_kokoro
                return synthesize_kokoro(text, out_path, voice="zm_031")
            await asyncio.sleep(2)

def generate_scene_audio(text: str, out_path: str, env: dict):
    provider = env.get("TTS_PROVIDER", "chattts").lower()
    edge_voice = env.get("EDGE_TTS_VOICE", "zh-CN-YunxiNeural")
    sf_key = env.get("SILICONFLOW_API_KEY")
    sf_voice = env.get("CUSTOM_VOICE_ID")
    sf_model = env.get("SILICONFLOW_MODEL", "FunAudioLLM/CosyVoice2-0.5B")

    # 1. 主力引擎: ChatTTS 本地口语化对话与多元种子声学引擎
    if provider in ("chattts", "chat_tts"):
        from scripts.tts_chattts import synthesize_chattts
        seed = int(env.get("CHATTTS_SEED", 4444))
        print(f"    [ChatTTS] 正在使用本地极速口语合成 (Seed: {seed} · 随和生活男声)...")
        return synthesize_chattts(text, out_path, seed=seed)

    # 2. Kokoro-82M 超轻量极速 CPU 引擎 (保留)
    elif provider in ("kokoro", "kokoro-82m", "kokoro_82m"):
        from scripts.tts_kokoro import synthesize_kokoro
        kokoro_voice = env.get("KOKORO_VOICE", "zm_031")
        print(f"    [Kokoro-82M] 正在使用本地 CPU 极速合成 (音色: {kokoro_voice})...")
        return synthesize_kokoro(text, out_path, voice=kokoro_voice)

    # 2. 优先尝试 F5-TTS 扩散流匹配引擎
    elif provider in ("f5_tts", "f5tts", "f5"):
        from scripts.tts_f5tts import synthesize_f5tts
        f5_ref = env.get("F5_REF_AUDIO", os.path.join(PROJECT_ROOT, "models", "reference_audio", "my_voice_ref_5s.wav"))
        f5_text = env.get("F5_REF_TEXT", "大家好，接下来我简单聊聊日常观察到的生活与技术里的小事。")
        print(f"    [F5-TTS] 正在使用本地扩散流匹配零样本克隆...")
        return synthesize_f5tts(text, out_path, ref_audio=f5_ref, ref_text=f5_text)

    # 3. 尝试本地/自建 GPT-SoVITS 专属个人或社区音色
    elif provider in ("gpt_sovits", "gpt-sovits", "sovits"):
        api_url = env.get("GPT_SOVITS_API_URL", "http://127.0.0.1:9880/tts")
        ref_audio = env.get("GPT_SOVITS_REF_AUDIO", os.path.join(PROJECT_ROOT, "models", "reference_audio", "my_voice_ref_5s.wav"))
        if not os.path.isabs(ref_audio):
            ref_audio = os.path.join(PROJECT_ROOT, ref_audio)
        ref_audio = ref_audio.replace("\\", "/")
        prompt_text = env.get("GPT_SOVITS_PROMPT_TEXT", "大家好，接下来我简单聊聊日常观察到的生活与技术里的小事。")
        try:
            print(f"    [GPT-SoVITS] 正在使用克隆音色合成 (服务: {api_url})...")
            actual_path = synthesize_gpt_sovits(text, out_path, api_url=api_url, ref_audio=ref_audio, prompt_text=prompt_text)
            return actual_path
        except Exception as e:
            print(f"    ⚠️ GPT-SoVITS 服务调用异常 ({e})")
            print(f"    ➡️ 自动无缝回退至高质量 Edge-TTS 保证视频流水线不中断")

    # 3. 尝试使用 SiliconFlow 专属音色
    elif provider == "siliconflow":
        if sf_key and not sf_key.startswith("sk-your-") and sf_voice:
            print(f"    [SiliconFlow] 正在使用专属克隆音色: {sf_voice}")
            synthesize_siliconflow(text, out_path, sf_key, sf_voice, sf_model)
            return
        else:
            print(f"    ⚠️ 未检测到有效的 SILICONFLOW_API_KEY 或 CUSTOM_VOICE_ID")
            print(f"    ➡️ 自动回退至高质量 Edge-TTS (YunxiNeural)")

    # 4. 尝试 Fish Audio
    elif provider == "fish_audio":
        fish_key = env.get("FISH_AUDIO_API_KEY")
        fish_voice = env.get("FISH_VOICE_ID")
        if fish_key and fish_voice:
            print(f"    [Fish Audio] 正在使用专属音色: {fish_voice}")
            synthesize_fish_audio(text, out_path, fish_key, fish_voice)
            return

    # 5. 尝试 MiniMax
    elif provider == "minimax":
        mm_key = env.get("MINIMAX_API_KEY")
        mm_group = env.get("MINIMAX_GROUP_ID")
        mm_voice = env.get("MINIMAX_VOICE_ID")
        if mm_key and mm_group and mm_voice:
            print(f"    [MiniMax] 正在使用专属音色: {mm_voice}")
            synthesize_minimax(text, out_path, mm_key, mm_group, mm_voice)
            return

    # 回退到本地 Edge-TTS (或默认使用 Edge-TTS)
    asyncio.run(synthesize_edge_tts(text, out_path, voice=edge_voice))
    old_wav = os.path.splitext(out_path)[0] + ".wav"
    if os.path.exists(old_wav) and old_wav != out_path:
        try:
            os.remove(old_wav)
        except Exception:
            pass
    return out_path

def main():
    parser = argparse.ArgumentParser(description="分镜音频批量自动生成")
    parser.add_argument("--script", type=str, default="inputs/script.json", help="分镜脚本文件路径")
    parser.add_argument("--output_dir", type=str, default="public/audio", help="音频输出目录")
    parser.add_argument("--provider", type=str, default=None, help="覆盖 TTS 服务商 (kokoro/f5_tts/gpt_sovits/edge_tts)")
    parser.add_argument("--voice", type=str, default=None, help="覆盖音色名称或代码")
    parser.add_argument("--ref_audio", type=str, default=None, help="参考音频文件路径")
    parser.add_argument("--ref_text", type=str, default=None, help="参考音频对应文本")
    args = parser.parse_args()

    script_path = os.path.join(PROJECT_ROOT, args.script) if not os.path.isabs(args.script) else args.script
    output_dir = os.path.join(PROJECT_ROOT, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    # 清理历史残留分镜音频，杜绝多视频批处理时前序视频音频残留导致的分镜串扰
    for old_file in os.listdir(output_dir):
        if old_file.lower().startswith("scene_") and old_file.lower().endswith((".wav", ".mp3")):
            try:
                os.remove(os.path.join(output_dir, old_file))
            except Exception:
                pass

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
    # 自动继承脚本文件中声明的 engine 与 voice
    if not args.provider and script_data.get("engine"):
        env["TTS_PROVIDER"] = script_data.get("engine")
    if not args.voice and script_data.get("voice"):
        v = str(script_data.get("voice"))
        if env.get("TTS_PROVIDER") in ("kokoro", "kokoro-82m", "kokoro_82m"):
            env["KOKORO_VOICE"] = v
        elif env.get("TTS_PROVIDER") in ("chattts", "chat_tts"):
            try:
                env["CHATTTS_SEED"] = int(v)
            except Exception:
                env["CHATTTS_SEED"] = 4444
        elif env.get("TTS_PROVIDER") == "edge_tts":
            env["EDGE_TTS_VOICE"] = v
        else:
            env["CUSTOM_VOICE_ID"] = v

    if args.provider:
        env["TTS_PROVIDER"] = args.provider
    if args.voice:
        if env.get("TTS_PROVIDER") in ("kokoro", "kokoro-82m", "kokoro_82m"):
            env["KOKORO_VOICE"] = args.voice
        elif env.get("TTS_PROVIDER") in ("chattts", "chat_tts"):
            env["CHATTTS_SEED"] = int(args.voice)
        else:
            env["EDGE_TTS_VOICE"] = args.voice
            env["CUSTOM_VOICE_ID"] = args.voice
    if args.ref_audio:
        env["GPT_SOVITS_REF_AUDIO"] = args.ref_audio
        env["F5_REF_AUDIO"] = args.ref_audio
    if args.ref_text:
        env["GPT_SOVITS_PROMPT_TEXT"] = args.ref_text
        env["F5_REF_TEXT"] = args.ref_text

    provider = env.get("TTS_PROVIDER", "chattts")
    custom_voice = env.get("KOKORO_VOICE") or env.get("CHATTTS_SEED") or env.get("EDGE_TTS_VOICE") or env.get("CUSTOM_VOICE_ID", "默认/未配置")

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
        actual_file = generate_scene_audio(text, out_file, env) or out_file
        print(f"    ✓ 已输出: {os.path.relpath(actual_file, PROJECT_ROOT)}")

    print(f"\n✅ 所有分镜配音音频生成完毕！存储于 {os.path.relpath(output_dir, PROJECT_ROOT)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/tts_kokoro.py
Kokoro-82M 超轻量本地 CPU 极速语音合成适配器
"""

import os
import json
import numpy as np
import onnxruntime as ort
import soundfile as sf
from misaki import zh

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "kokoro")
ONNX_PATH = os.path.join(MODEL_DIR, "model_dynamic.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
VOICES_DIR = os.path.join(MODEL_DIR, "voices")

_SESSION = None
_VOCAB = None
_G2P = None

def get_kokoro_session():
    global _SESSION, _VOCAB, _G2P
    if _SESSION is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        _VOCAB = cfg["vocab"]
        _SESSION = ort.InferenceSession(ONNX_PATH)
        _G2P = zh.ZHG2P()
    return _SESSION, _VOCAB, _G2P

def synthesize_kokoro(text: str, out_path: str, voice: str = "zm_031", speed: float = 1.0):
    sess, vocab, g2p = get_kokoro_session()
    
    # 转换为音素
    phonemes = g2p(text)
    tokens = [0] + [vocab[c] for c in phonemes if c in vocab] + [0]
    input_ids = np.array([tokens], dtype=np.int64)
    
    # 加载声音特征向量
    voice_file = voice if voice.endswith(".bin") else f"{voice}.bin"
    voice_path = os.path.join(VOICES_DIR, voice_file)
    if not os.path.exists(voice_path):
        voice_path = os.path.join(VOICES_DIR, "zm_031.bin")
        
    raw_voice = np.fromfile(voice_path, dtype=np.float32).reshape(-1, 256)
    idx = min(len(tokens) - 1, len(raw_voice) - 1)
    ref_s = raw_voice[idx : idx + 1].copy()
    
    speed_arr = np.array([speed], dtype=np.float32)
    
    audio, _ = sess.run(None, {
        "input_ids": input_ids,
        "ref_s": ref_s,
        "speed": speed_arr
    })
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    # 保存 wav 文件
    wav_path = os.path.splitext(out_path)[0] + ".wav"
    sf.write(wav_path, audio, 24000)
    
    old_mp3 = os.path.splitext(out_path)[0] + ".mp3"
    if os.path.exists(old_mp3) and old_mp3 != wav_path:
        try:
            os.remove(old_mp3)
        except Exception:
            pass
            
    return wav_path

if __name__ == "__main__":
    out = synthesize_kokoro("你好，这是 Kokoro 本地离线快速合成验证。", "test_kokoro_standalone.wav", voice="zm_031")
    print("Kokoro Standalone Success:", out)

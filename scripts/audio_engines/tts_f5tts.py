#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/tts_f5tts.py
F5-TTS 扩散流匹配 (Diffusion Flow-Matching) 本地 CPU 语音合成适配器
"""

import os
import torch
import soundfile as sf
import torchaudio

def _soundfile_load(uri, *args, **kwargs):
    data, samplerate = sf.read(uri)
    tensor = torch.from_numpy(data).float()
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 2:
        tensor = tensor.t()
    return tensor, samplerate

torchaudio.load = _soundfile_load

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "f5tts")
CKPT_PATH = os.path.join(MODEL_DIR, "model_1250000.safetensors")
VOCAB_PATH = os.path.join(MODEL_DIR, "vocab.txt")

_F5_INSTANCE = None

def get_f5tts_instance():
    global _F5_INSTANCE
    if _F5_INSTANCE is None:
        from f5_tts.api import F5TTS
        _F5_INSTANCE = F5TTS(
            model="F5TTS_Base",
            ckpt_file=CKPT_PATH,
            vocab_file=VOCAB_PATH,
            device="cpu"
        )
    return _F5_INSTANCE

def synthesize_f5tts(text: str, out_path: str, ref_audio: str = None, ref_text: str = None, nfe_step: int = 16):
    f5 = get_f5tts_instance()
    
    if not ref_audio or not os.path.exists(ref_audio):
        ref_audio = os.path.join(PROJECT_ROOT, "models", "reference_audio", "my_voice_ref_5s.wav")
    if not ref_text:
        ref_text = "大家好，接下来我简单聊聊日常观察到的生活与技术里的小事。"
        
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wav_path = os.path.splitext(out_path)[0] + ".wav"
    
    f5.infer(
        ref_file=ref_audio,
        ref_text=ref_text,
        gen_text=text,
        file_wave=wav_path,
        nfe_step=nfe_step
    )
    
    old_mp3 = os.path.splitext(out_path)[0] + ".mp3"
    if os.path.exists(old_mp3) and old_mp3 != wav_path:
        try:
            os.remove(old_mp3)
        except Exception:
            pass
            
    return wav_path

if __name__ == "__main__":
    out = synthesize_f5tts("你好，这是 F5-TTS 本地离线流匹配合成独立验证。", "test_f5_standalone.wav", nfe_step=16)
    print("F5-TTS Standalone Success:", out)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/start_local_sovits.py
一键启动本地 GPT-SoVITS 专属声音推理 API 服务 (9880 端口)
针对 Windows + AMD Ryzen CPU 纯 CPU 推理深度定制
"""

import os
import sys
import yaml
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOVITS_ROOT = "D:\\tools\\GPT-SoVITS"
PYTHON_EXE = r"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe"

SOVITS_WEIGHTS = os.path.join(PROJECT_ROOT, "models", "gpt_sovits", "epanda_voice_e8_s120.pth").replace("\\", "/")
GPT_WEIGHTS = os.path.join(PROJECT_ROOT, "models", "gpt_sovits", "epanda_voice-e15.ckpt").replace("\\", "/")
REF_AUDIO = os.path.join(PROJECT_ROOT, "models", "reference_audio", "my_voice_ref_5s.wav").replace("\\", "/")

def ensure_config():
    config_path = os.path.join(SOVITS_ROOT, "GPT_SoVITS", "configs", "tts_infer_local.yaml")
    cfg = {
        "custom": {
            "device": "cpu",
            "is_half": False,
            "version": "v2",
            "bert_base_path": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
            "cnhuhbert_base_path": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
            "t2s_weights_path": GPT_WEIGHTS,
            "vits_weights_path": SOVITS_WEIGHTS,
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    return config_path

def main():
    if not os.path.exists(SOVITS_ROOT):
        print(f"❌ 找不到 GPT-SoVITS 目录: {SOVITS_ROOT}")
        sys.exit(1)

    print("=======================================================")
    print("🎙️ [GPT-SoVITS 本地推理引擎]")
    print(f"  工作根目录: {SOVITS_ROOT}")
    print(f"  SoVITS 权重: {SOVITS_WEIGHTS}")
    print(f"  GPT 权重:    {GPT_WEIGHTS}")
    print("  运行模式:    CPU (AMD Ryzen 7 5800H AVX2 加速)")
    print("  监听端口:    http://127.0.0.1:9880")
    print("=======================================================\n")

    cfg_file = ensure_config()
    cmd = [
        PYTHON_EXE,
        "api_v2.py",
        "-c", cfg_file,
        "-a", "127.0.0.1",
        "-p", "9880"
    ]

    print("🚀 正在启动本地 API 服务，请保持本窗口开启...")
    subprocess.run(cmd, cwd=SOVITS_ROOT)

if __name__ == "__main__":
    main()

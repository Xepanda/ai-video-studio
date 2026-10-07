#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/tts_chattts.py
ChatTTS 本地 CPU 高保真口语/极客对话语音合成适配器
支持指定音色 Seed 生成口语化、带叹词与停顿的生动语音
"""

import os
import sys
import torch
import numpy as np
import ChatTTS

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = r"C:\Users\ePanda\.cache\modelscope\models\AI-ModelScope--ChatTTS\snapshots\master"

_chat_instance = None

def get_chat_model():
    global _chat_instance
    if _chat_instance is None:
        print(">>> 正在加载 ChatTTS 0.2.5 神经声学模型 (CPU 推理)...")
        import ChatTTS
        chat = ChatTTS.Chat()
        success = chat.load(source="custom", custom_path=MODELS_DIR, device=torch.device("cpu"))
        if not success:
            raise RuntimeError(f"ChatTTS 模型加载失败，路径: {MODELS_DIR}")
        _chat_instance = chat
        print(">>> ChatTTS 模型就绪！")
    return _chat_instance

def synthesize_chattts(text: str, out_path: str, seed: int = 4444, speed: float = 1.0) -> str:
    """
    使用 ChatTTS 合成音频
    :param text: 输入中文文本
    :param out_path: 输出音频路径 (.wav 或 .mp3)
    :param seed: 音色随机种子
    :param speed: 语速调节
    :return: 实际输出文件绝对路径
    """
    import soundfile as sf

    chat = get_chat_model()

    # 设置固定声纹特征向量
    torch.manual_seed(seed)
    spk_emb = chat.sample_random_speaker()

    # 口语微调参数
    params_infer_code = ChatTTS.Chat.InferCodeParams(
        spk_emb=spk_emb,
        temperature=0.3,
        top_P=0.7,
        top_K=20,
    )

    # 推理生成音频波形
    wavs = chat.infer([text], params_infer_code=params_infer_code, use_decoder=True)

    if not wavs or len(wavs) == 0:
        raise RuntimeError("ChatTTS 未生成任何有效音频波形")

    wav_data = wavs[0]
    if isinstance(wav_data, np.ndarray):
        wav_array = wav_data
    else:
        wav_array = wav_data.cpu().numpy()

    # 如果是二维数组，转为 1D
    if wav_array.ndim > 1:
        wav_array = wav_array.squeeze()

    wav_path = os.path.splitext(out_path)[0] + ".wav"
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    sf.write(wav_path, wav_array, 24000)

    # 清理旧的 mp3
    old_mp3 = os.path.splitext(out_path)[0] + ".mp3"
    if os.path.exists(old_mp3) and old_mp3 != wav_path:
        try:
            os.remove(old_mp3)
        except Exception:
            pass

    return wav_path

if __name__ == "__main__":
    test_out = os.path.join(PROJECT_ROOT, "test_chattts_standalone.wav")
    print(f"正在测试 ChatTTS 独立运行: {test_out} ...")
    res = synthesize_chattts("大家好！这是 ChatTTS 本地运行生成的随和生活语音，带有自然的呼吸与停顿。", test_out, seed=4444)
    print(f"ChatTTS Standalone Success: {res}")

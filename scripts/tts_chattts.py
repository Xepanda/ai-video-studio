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

def split_long_text(text: str, max_chars: int = 55) -> list:
    """
    智能将较长文案按标点符号切分为自然子句，控制在安全长度内，避免 ChatTTS 自回归崩溃。
    优先按句尾强标点 (。！？!?；;\n) 切分，如果单个片段仍然超长，再按逗号 (,，、) 切分。
    如果连续单句缺少逗号且超过 max_chars，执行硬截断兜底。
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    import re
    sentences = re.split(r'([。！？!?；;\n]+)', text)
    merged_sents = []
    i = 0
    while i < len(sentences):
        s = sentences[i].strip()
        punct = sentences[i+1].strip() if i + 1 < len(sentences) else ""
        if s or punct:
            merged_sents.append(s + punct)
        i += 2

    if not merged_sents:
        merged_sents = [text]

    final_chunks = []
    for sent in merged_sents:
        if len(sent) <= max_chars:
            final_chunks.append(sent)
        else:
            clauses = re.split(r'([,，、]+)', sent)
            curr = ""
            c_idx = 0
            while c_idx < len(clauses):
                part = clauses[c_idx]
                p_punct = clauses[c_idx+1] if c_idx + 1 < len(clauses) else ""
                piece = part + p_punct
                if len(curr) + len(piece) <= max_chars:
                    curr += piece
                else:
                    if curr.strip():
                        final_chunks.append(curr.strip())
                    if len(piece) <= max_chars:
                        curr = piece
                    else:
                        # 兜底：处理超长且内部无逗号的连续长从句
                        for k in range(0, len(piece), max_chars):
                            sub = piece[k:k+max_chars].strip()
                            if sub:
                                final_chunks.append(sub)
                        curr = ""
                c_idx += 2
            if curr.strip():
                final_chunks.append(curr.strip())

    return [c for c in final_chunks if c.strip()]

def synthesize_chattts(text: str, out_path: str, seed: int = 4444, speed: float = 1.0) -> str:
    """
    使用 ChatTTS 合成音频，自带超长文本智能分句与微停顿无缝拼接
    :param text: 输入中文文本
    :param out_path: 输出音频路径 (.wav 或 .mp3)
    :param seed: 音色随机种子
    :param speed: 语速调节 (保留参数)
    :return: 实际输出文件绝对路径
    """
    text = text.strip()
    if not text:
        raise ValueError("synthesize_chattts: 输入文本不能为空")

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

    chunks = split_long_text(text, max_chars=55)
    if not chunks:
        raise ValueError("synthesize_chattts: 文本分句后无有效文本片段")

    all_wav_arrays = []
    silence_samples = int(24000 * 0.2)  # 句间注入 200ms 自然换气微停顿
    silence_arr = np.zeros(silence_samples, dtype=np.float32)

    for chunk in chunks:
        wavs = chat.infer([chunk], params_infer_code=params_infer_code, use_decoder=True)
        if not wavs or len(wavs) == 0:
            continue
        wav_data = wavs[0]
        arr = wav_data if isinstance(wav_data, np.ndarray) else wav_data.cpu().numpy()
        arr = np.atleast_1d(np.squeeze(arr))
        if arr.size == 0:
            continue
        if all_wav_arrays and len(silence_arr) > 0:
            all_wav_arrays.append(silence_arr)
        all_wav_arrays.append(arr)

    if not all_wav_arrays:
        raise RuntimeError("ChatTTS 未生成任何有效音频波形")
    wav_array = np.concatenate(all_wav_arrays)

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

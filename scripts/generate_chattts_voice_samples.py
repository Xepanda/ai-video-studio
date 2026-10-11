#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_chattts_voice_samples.py
生成 ChatTTS 多音色精选试听音频 (每段约 5~10 秒)
供用户收听并选定最终主力音色
"""

import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.tts_chattts import synthesize_chattts

# 试听示范文本 (约 45 字，语速正常发音约 7~9 秒，兼顾技术名词与自然口语)
SAMPLE_TEXT = "欢迎来到技术探索实验室。今天我们聊聊全栈自动化架构，看看如何用代码驱动每一个富有创意的灵感瞬间。"

# 精选候选音色矩阵 (涵盖沉稳男声、知性女声、青年极客、磁性解说、温和随和等风格)
CANDIDATE_SEEDS = [
    {"seed": 2222, "id": "voice_01_seed_2222", "label": "沉稳极客男声", "desc": "语速平稳，带有极客对话口吻，适合深度技术与系统架构"},
    {"seed": 3333, "id": "voice_02_seed_3333", "label": "知性科技女声", "desc": "吐字轻快清晰，音色明亮温和，适合产品讲解与科普"},
    {"seed": 4444, "id": "voice_03_seed_4444", "label": "随和生活男声", "desc": "随和亲切，语调生活化自然，适合日常实战与开箱教程"},
    {"seed": 5555, "id": "voice_04_seed_5555", "label": "严谨架构男声", "desc": "逻辑感强，句间微停顿自然，适合工程代码与系统设计"},
    {"seed": 6666, "id": "voice_05_seed_6666", "label": "阳光青年男声", "desc": "充满活力，节奏明快富有感染力，适合技术短视频与横评"},
    {"seed": 7777, "id": "voice_06_seed_7777", "label": "温润知性男声", "desc": "磁性低沉，叙事感极佳，适合纪录片与长篇原理推导"},
    {"seed": 8888, "id": "voice_07_seed_8888", "label": "深沉工科讲师", "desc": "厚重沉稳，学术讲师质感，适合算法底层与论文精读"},
    {"seed": 1111, "id": "voice_08_seed_1111", "label": "清澈灵动女声", "desc": "音质柔和灵动，富有亲和力，适合引导与交互式教程"},
    {"seed": 1984, "id": "voice_09_seed_1984", "label": "磁性电影解说", "desc": "富有叙事氛围感与电影质感，适合大叙事与全栈哲学"},
    {"seed": 2024, "id": "voice_10_seed_2024", "label": "现代干练男声", "desc": "干练有力，商务与极客兼顾，适合前沿发布会与实战拆解"}
]

OUT_DIR = os.path.join(PROJECT_ROOT, "out", "chattts_voice_samples")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print(f"\n=======================================================")
    print(f"🎙️ [ChatTTS 音色矩阵] 批量生成精选试听音频")
    print(f"   输出目录: {OUT_DIR}")
    print(f"   试听文本: {SAMPLE_TEXT}")
    print(f"   音色总数: {len(CANDIDATE_SEEDS)} 款")
    print(f"=======================================================\n")

    manifest = []

    for item in CANDIDATE_SEEDS:
        seed = item["seed"]
        name = f"{item['id']}_{item['label']}"
        wav_file = os.path.join(OUT_DIR, f"{name}.wav")
        print(f">>> 正在生成: [{item['label']}] (Seed {seed}) ...")
        t0 = time.time()
        actual_path = synthesize_chattts(SAMPLE_TEXT, wav_file, seed=seed)
        cost = time.time() - t0

        import soundfile as sf
        info = sf.info(actual_path)
        dur = info.duration

        print(f"    ✓ 生成成功: {os.path.basename(actual_path)} | 时长: {dur:.2f}s | 耗时: {cost:.1f}s")

        manifest.append({
            "seed": seed,
            "id": item["id"],
            "label": item["label"],
            "description": item["desc"],
            "file": os.path.relpath(actual_path, PROJECT_ROOT).replace("\\", "/"),
            "duration": round(dur, 2)
        })

    # 保存清单供前端与用户查阅
    import json
    manifest_path = os.path.join(OUT_DIR, "samples_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 所有试听音频生成完毕！清单已保存至: {manifest_path}")

if __name__ == "__main__":
    main()

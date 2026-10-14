#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_more_chattts_seeds.py
生成第二批 ChatTTS 精选试听音频 (16 款全新男女不同风格音色)
使用《计算机网络》开场经典台词实测，方便直观比对出片效果
"""

import os
import sys
import time
import json
import soundfile as sf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.tts_chattts import synthesize_chattts

# 使用当前网络分层视频的真实开场台词作为统一样本，试听体验最直接
SAMPLE_TEXT = "在微信发一句在吗，这句短短两个字的消息，底层究竟经历了怎样惊心动魄的星际航行？"

CANDIDATES = [
    # --- 组 1: 活力极客男声 ---
    {"seed": 2, "category": "男声", "label": "清脆少年极客", "desc": "语速偏快、清脆干脆，极具科技探索感"},
    {"seed": 22, "category": "男声", "label": "阳光数码博主", "desc": "自然随和、富有节奏感，类似B站数码区头部UP主"},
    {"seed": 666, "category": "男声", "label": "高燃解说男声", "desc": "情绪饱满、重音有力，适合高节奏快反转内容"},
    {"seed": 1024, "category": "男声", "label": "自然硬核程序员", "desc": "平和真实、不油腻，程序员日常对谈质感"},

    # --- 组 2: 磁性沉稳男声 ---
    {"seed": 42, "category": "男声", "label": "磁性沙哑大叔", "desc": "中低音共鸣充足、略带颗粒感，高级极客质感"},
    {"seed": 7890, "category": "男声", "label": "从容沉稳工科男", "desc": "不疾不徐、温和扎实，适合长篇逻辑推导"},
    {"seed": 88888, "category": "男声", "label": "播音主持男声", "desc": "字正腔圆、腔调周正，权威感十足"},
    {"seed": 9999, "category": "男声", "label": "纪录片厚重男声", "desc": "胸腔共鸣强、宏大叙事感，适合深度硬核科普"},

    # --- 组 3: 灵动知性女声 ---
    {"seed": 100, "category": "女声", "label": "清新邻家女声", "desc": "温润亲切、音质柔和，听感极度放松没有压迫感"},
    {"seed": 520, "category": "女声", "label": "柔和知性漫谈", "desc": "轻声慢语、自然换气，适合睡前科普或唯美视觉"},
    {"seed": 2333, "category": "女声", "label": "灵动科技少女", "desc": "元气活泼、跳跃灵动，适合短视频快节奏教学"},
    {"seed": 6688, "category": "女声", "label": "干练产品经理", "desc": "吐字利落、清晰明了，商业与科技感拉满"},

    # --- 组 4: 优雅御姐与讲师女声 ---
    {"seed": 1234, "category": "女声", "label": "经典知性女主播", "desc": "娓娓道来、端庄清晰，知识博主典范"},
    {"seed": 4321, "category": "女声", "label": "沉静穿透女声", "desc": "音色冷冽、穿透力强，适合硬科幻与严肃架构"},
    {"seed": 7000, "category": "女声", "label": "新闻专业女主播", "desc": "播音标准、字词分明，专业资讯感强"},
    {"seed": 9000, "category": "女声", "label": "学术讲师女声", "desc": "典雅深厚、知性权威，适合高校课程或技术长篇"},
]

OUT_DIR = os.path.join(PROJECT_ROOT, "out", "chattts_voice_samples", "batch2")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print(f"\n=======================================================")
    print(f"🎙️ [ChatTTS 第二批试听矩阵] 批量生成 16 款全新音色样片")
    print(f"   输出目录: {OUT_DIR}")
    print(f"   实测试听台词: {SAMPLE_TEXT}")
    print(f"   音色总数: {len(CANDIDATES)} 款")
    print(f"=======================================================\n")

    manifest = []

    for idx, item in enumerate(CANDIDATES, 1):
        seed = item["seed"]
        label = item["label"]
        category = item["category"]
        file_name = f"seed_{seed:05d}_{category}_{label}.wav"
        wav_path = os.path.join(OUT_DIR, file_name)

        print(f"[{idx:02d}/{len(CANDIDATES):02d}] 正在合成: [{category} · {label}] (Seed: {seed}) ...")
        t0 = time.time()
        actual_path = synthesize_chattts(SAMPLE_TEXT, wav_path, seed=seed)
        cost = time.time() - t0

        info = sf.info(actual_path)
        dur = info.duration

        print(f"    ✓ 完成: {file_name} | 时长: {dur:.2f}s | 耗时: {cost:.1f}s")

        manifest.append({
            "seed": seed,
            "category": category,
            "label": label,
            "desc": item["desc"],
            "file": os.path.relpath(actual_path, PROJECT_ROOT).replace("\\", "/"),
            "duration": round(dur, 2)
        })

    manifest_file = os.path.join(OUT_DIR, "batch2_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 16 款全新音色全部生成完毕！清单已保存至: {manifest_file}\n")

if __name__ == "__main__":
    main()

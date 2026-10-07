#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pipeline.py
全链路视频自动化端到端中枢调度脚本 (One-Click Pipeline)
"""

import os
import sys
import argparse
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVECLIP_PYTHON = r"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe"
PYTHON_EXE = LIVECLIP_PYTHON if os.path.exists(LIVECLIP_PYTHON) else sys.executable

def run_step(step_name: str, cmd: list):
    print(f"\n=======================================================")
    print(f"🚀 [Pipeline Step] 正在执行: {step_name}")
    print(f"=======================================================\n")
    ret = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if ret.returncode != 0:
        print(f"\n❌ [Pipeline Failed] 步骤 [{step_name}] 执行失败，错误码: {ret.returncode}")
        sys.exit(ret.returncode)
    print(f"\n✅ 步骤 [{step_name}] 顺利完成！")

def main():
    parser = argparse.ArgumentParser(description="全链路 AI 视频自动化总控流水线")
    parser.add_argument("--script", type=str, default="inputs/script.json", help="输入的分镜脚本文件")
    parser.add_argument("--project", type=str, default="master_video", help="项目输出名称")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--skip_tts", action="store_true", help="跳过 TTS 配音生成（仅使用已有音频）")
    parser.add_argument("--skip_align", action="store_true", help="跳过 ASR 毫秒打点")
    parser.add_argument("--skip_validate", action="store_true", help="跳过静态审查")
    parser.add_argument("--render", action="store_true", help="直接调用 Remotion 渲染出最终 MP4")
    parser.add_argument("--engine", type=str, choices=["auto", "paraformer", "sensevoice"], default="auto", help="ASR 对齐引擎 (auto/paraformer/sensevoice)")
    parser.add_argument("--device", type=str, default="cpu", help="ASR 推理设备 (cpu/cuda)")
    parser.add_argument("--isolated", action="store_true", default=True, help="启用项目资产隔离 (输出至 public/projects/{project})")
    parser.add_argument("--no_isolated", action="store_false", dest="isolated", help="禁用项目资产隔离 (直接使用根目录 public/audio)")
    parser.add_argument("--no_normalize_phonetics", action="store_true", default=False, help="禁用 TTS 技术名词发音规范化")
    parser.add_argument("--force", "--force_audio", dest="force_audio", action="store_true", default=False, help="强制重新生成所有分镜音频，忽略 MD5 缓存")
    parser.add_argument("--concurrency", type=int, default=4, help="Remotion 并发渲染进程数")
    args = parser.parse_args()

    # 步骤 0: 专属音色 TTS 配音生成
    if not args.skip_tts:
        tts_script = os.path.join(PROJECT_ROOT, "scripts", "generate_audio.py")
        tts_cmd = [PYTHON_EXE, tts_script, "--script", args.script]
        if args.isolated and args.project:
            tts_cmd.extend(["--project", args.project])
        if args.no_normalize_phonetics:
            tts_cmd.append("--no_normalize_phonetics")
        if args.force_audio:
            tts_cmd.append("--force")
        run_step(
            "专属克隆音色分镜配音生成",
            tts_cmd
        )

    # 步骤 0.5: 确保全局科技氛围 BGM 与转场/弹入 SFX 音效就绪
    bgm_file = os.path.join(PROJECT_ROOT, "public", "audio", "bgm_cyber_ambient.wav")
    sfx_file = os.path.join(PROJECT_ROOT, "public", "audio", "sfx_transition.wav")
    pop_file = os.path.join(PROJECT_ROOT, "public", "audio", "sfx_pop.wav")
    if not os.path.exists(bgm_file) or not os.path.exists(sfx_file) or not os.path.exists(pop_file):
        sfx_script = os.path.join(PROJECT_ROOT, "scripts", "generate_sfx_bgm.py")
        run_step(
            "无版权极客氛围音乐与转场音效套件合成",
            [PYTHON_EXE, sfx_script]
        )

    # 步骤 1: ASR 毫秒打点与 timeline.json 契约生成
    if not args.skip_align:
        align_script = os.path.join(PROJECT_ROOT, "scripts", "sensevoice_aligner.py")
        align_cmd = [
            PYTHON_EXE, align_script,
            "--fps", str(args.fps),
            "--script", args.script,
            "--engine", args.engine,
            "--device", args.device
        ]
        if args.isolated and args.project:
            align_cmd.extend(["--project", args.project])
        run_step(
            "声学物理打点与时间轴契约生成",
            align_cmd
        )

    # 步骤 2: 质量门禁自动审查
    if not args.skip_validate:
        validator_script = os.path.join(PROJECT_ROOT, "scripts", "validator.py")
        val_cmd = [PYTHON_EXE, validator_script]
        if args.isolated and args.project:
            val_cmd.extend(["--project", args.project])
        run_step(
            "数据契约与静态资产审查 (Quality Gate)",
            val_cmd
        )

    # 步骤 3: 可选一键多核渲染
    if args.render:
        out_mp4 = os.path.join(PROJECT_ROOT, "out", f"{args.project}.mp4")
        os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
        remotion_cmd = f"npx remotion render src/index.ts MasterVideo out/{args.project}.mp4 --concurrency={args.concurrency}"
        run_step(
            "Remotion 多核光栅化渲染 MP4",
            ["cmd.exe", "/c", remotion_cmd]
        )
        print(f"\n🎉 视频渲染完成！成片文件: {out_mp4}")
    else:
        print(f"\n🎉🎉 全链路数据契约就绪！接下来请执行：")
        print(f"  1. 启动网页交互预览: npm run dev")
        print(f"  2. 极速导出 1080p 成片: python scripts/pipeline.py --render --project {args.project}\n")

if __name__ == "__main__":
    main()

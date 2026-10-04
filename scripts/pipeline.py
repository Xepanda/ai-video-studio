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
PYTHON_EXE = sys.executable

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
    args = parser.parse_args()

    # 步骤 0: 专属音色 TTS 配音生成
    if not args.skip_tts:
        tts_script = os.path.join(PROJECT_ROOT, "scripts", "generate_audio.py")
        run_step(
            "专属克隆音色分镜配音生成",
            [PYTHON_EXE, tts_script, "--script", args.script]
        )

    # 步骤 1: ASR 毫秒打点与 timeline.json 契约生成
    if not args.skip_align:
        align_script = os.path.join(PROJECT_ROOT, "scripts", "sensevoice_aligner.py")
        run_step(
            "SenseVoice 毫秒打点与时间轴契约生成",
            [PYTHON_EXE, align_script, "--project", args.project, "--fps", str(args.fps)]
        )

    # 步骤 2: 质量门禁自动审查
    if not args.skip_validate:
        validator_script = os.path.join(PROJECT_ROOT, "scripts", "validator.py")
        run_step(
            "数据契约与静态资产审查 (Quality Gate)",
            [PYTHON_EXE, validator_script]
        )

    # 步骤 3: 可选一键多核渲染
    if args.render:
        out_mp4 = os.path.join(PROJECT_ROOT, "out", f"{args.project}.mp4")
        os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
        remotion_cmd = f"npx remotion render src/index.ts MasterVideo out/{args.project}.mp4 --concurrency=6"
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

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
    parser.add_argument("--project", type=str, default="master_video", help="项目名称")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--skip_align", action="store_true", help="跳过 ASR 打点")
    parser.add_argument("--skip_validate", action="store_true", help="跳过静态审查")
    args = parser.parse_args()

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

    print(f"\n🎉🎉 流水线就绪！接下来请执行：")
    print(f"  1. 启动网页交互预览: npm run dev")
    print(f"  2. 极速导出 1080p 成片: npx remotion render src/index.ts MasterVideo out/{args.project}.mp4 --concurrency=6\n")

if __name__ == "__main__":
    main()

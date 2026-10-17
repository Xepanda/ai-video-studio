#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pipeline.py
全链路视频自动化端到端中枢调度脚本 (One-Click Pipeline)
支持双渲染引擎 (Remotion & HyperFrames) 调度与 EBU R128 -11.0 LUFS 广播级商业母带压制
"""

import os
import sys
import argparse
import subprocess
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVECLIP_PYTHON = r"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe"
PYTHON_EXE = LIVECLIP_PYTHON if os.path.exists(LIVECLIP_PYTHON) else sys.executable


def run_step(step_name: str, cmd):
    """跨平台执行流水线子步骤，健壮支持字符串命令与列表命令"""
    print(f"\n=======================================================")
    print(f"🚀 [Pipeline Step] 正在执行: {step_name}")
    print(f"=======================================================\n")
    if isinstance(cmd, str):
        if sys.platform == "win32":
            actual_cmd = ["cmd.exe", "/c", cmd]
        else:
            actual_cmd = ["/bin/sh", "-c", cmd]
    elif isinstance(cmd, list):
        if sys.platform == "win32" and cmd and cmd[0] in ("npx", "hyperframes", "remotion"):
            actual_cmd = ["cmd.exe", "/c"] + cmd
        else:
            actual_cmd = cmd
    else:
        actual_cmd = cmd

    ret = subprocess.run(actual_cmd, cwd=PROJECT_ROOT)
    if ret.returncode != 0:
        print(f"\n❌ [Pipeline Failed] 步骤 [{step_name}] 执行失败，错误码: {ret.returncode}")
        sys.exit(ret.returncode)
    print(f"\n✅ 步骤 [{step_name}] 顺利完成！")


def build_render_commands(
    project: str,
    engine: str = "remotion",
    concurrency: int = 4,
    isolated: bool = True
) -> List[Dict[str, Any]]:
    """
    根据目标渲染引擎构建结构化渲染指令列表。

    每个结构体包含:
      - name: 步骤说明文本
      - cmd: 命令行列表或 shell 命令字符串
      - output_mp4: 该步骤产生的目标 MP4 路径 (若有)
    """
    if engine not in ("remotion", "hyperframes", "both"):
        raise ValueError(f"不支持的渲染引擎: {engine}，可选值为: 'remotion', 'hyperframes', 'both'")

    steps: List[Dict[str, Any]] = []

    # 1. Remotion 引擎分支
    if engine in ("remotion", "both"):
        target_name = f"{project}_remotion" if engine == "both" else project
        out_mp4 = f"out/{target_name}.mp4"
        remotion_cmd = f"npx remotion render src/index.ts MasterVideo {out_mp4} --concurrency={concurrency}"
        if isolated:
            remotion_cmd += f' --props="{{\\"timeline\\": \\"public/projects/{project}/timeline.json\\"}}"'
        steps.append({
            "name": f"Remotion 多核光栅化渲染 MP4 [{target_name}]",
            "cmd": remotion_cmd,
            "output_mp4": out_mp4,
        })

    # 2. HyperFrames 引擎分支
    if engine in ("hyperframes", "both"):
        target_name = f"{project}_hf" if engine == "both" else project
        out_mp4 = f"out/{target_name}.mp4"
        # 步骤 1: timeline_to_hyperframes 时钟转译
        steps.append({
            "name": f"HyperFrames 工程时钟转译 [{project}]",
            "cmd": f'"{PYTHON_EXE}" scripts/timeline_to_hyperframes.py --project {project}',
            "output_mp4": None,
        })
        # 步骤 2: hyperframes check 静态审查质量门禁
        steps.append({
            "name": f"HyperFrames 静态质量门禁 [{project}]",
            "cmd": f"npx hyperframes check projects_hf/{project}",
            "output_mp4": None,
        })
        # 步骤 3: hyperframes render 无头光栅化渲染
        steps.append({
            "name": f"HyperFrames 无头光栅化渲染 MP4 [{target_name}]",
            "cmd": f"npx hyperframes render projects_hf/{project} -o {out_mp4}",
            "output_mp4": out_mp4,
        })

    return steps


def get_parser() -> argparse.ArgumentParser:
    """定义并返回全链路流水线命令行解析器"""
    parser = argparse.ArgumentParser(description="全链路 AI 视频自动化总控流水线")
    parser.add_argument("--script", type=str, default="inputs/script.json", help="输入的分镜脚本文件")
    parser.add_argument("--project", type=str, default="master_video", help="项目输出名称")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--skip_tts", action="store_true", help="跳过 TTS 配音生成（仅使用已有音频）")
    parser.add_argument("--skip_align", action="store_true", help="跳过 ASR 毫秒打点")
    parser.add_argument("--skip_validate", action="store_true", help="跳过静态审查")
    parser.add_argument("--render", action="store_true", help="直接调用渲染引擎输出最终 MP4")
    parser.add_argument("--engine", type=str, choices=["auto", "paraformer", "sensevoice"], default="auto", help="ASR 对齐引擎 (auto/paraformer/sensevoice)")
    parser.add_argument("--engine_render", type=str, choices=["remotion", "hyperframes", "both"], default="remotion", help="渲染引擎选择 (remotion/hyperframes/both)")
    parser.add_argument("--device", type=str, default="cpu", help="ASR 推理设备 (cpu/cuda)")
    parser.add_argument("--isolated", action="store_true", default=True, help="启用项目资产隔离 (输出至 public/projects/{project})")
    parser.add_argument("--no_isolated", action="store_false", dest="isolated", help="禁用项目资产隔离 (直接使用根目录 public/audio)")
    parser.add_argument("--no_normalize_phonetics", action="store_true", default=False, help="禁用 TTS 技术名词发音规范化")
    parser.add_argument("--no_master_audio", action="store_true", default=False, help="禁用移动端人声广播母带增益优化")
    parser.add_argument("--force", "--force_audio", dest="force_audio", action="store_true", default=False, help="强制重新生成所有分镜音频，忽略 MD5 缓存")
    parser.add_argument("--no_master_video", action="store_true", default=False, help="禁用成品视频容器级音频母带标准化")
    parser.add_argument("--concurrency", type=int, default=4, help="Remotion 并发渲染进程数")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # 步骤 0: 专属音色 TTS 配音生成
    if not args.skip_tts:
        tts_script = os.path.join(PROJECT_ROOT, "scripts", "generate_audio.py")
        tts_cmd = [PYTHON_EXE, tts_script, "--script", args.script]
        if args.isolated and args.project:
            tts_cmd.extend(["--project", args.project])
        if args.no_normalize_phonetics:
            tts_cmd.append("--no_normalize_phonetics")
        if args.no_master_audio:
            tts_cmd.append("--no_master_audio")
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

    # 步骤 3: 可选一键多核双引擎渲染
    if args.render:
        os.makedirs(os.path.join(PROJECT_ROOT, "out"), exist_ok=True)
        render_steps = build_render_commands(
            project=args.project,
            engine=args.engine_render,
            concurrency=args.concurrency,
            isolated=args.isolated,
        )
        rendered_mp4s = []
        for step in render_steps:
            run_step(step["name"], step["cmd"])
            if step.get("output_mp4"):
                rendered_mp4s.append(step["output_mp4"])

        # 步骤 4: 成品视频商业级广播响度标准化 (-11 LUFS / -0.5 True Peak)
        master_script = os.path.join(PROJECT_ROOT, "scripts", "audio_mastering.py")
        if not args.no_master_video:
            for mp4_rel in rendered_mp4s:
                mp4_abs = os.path.join(PROJECT_ROOT, mp4_rel) if not os.path.isabs(mp4_rel) else mp4_rel
                if os.path.exists(mp4_abs):
                    run_step(
                        f"成品视频音轨商业广播响度标准化 (EBU R128 -11 LUFS): {os.path.basename(mp4_abs)}",
                        [PYTHON_EXE, master_script, "--video", mp4_abs]
                    )

        print(f"\n🎉 视频渲染完成！成片文件:")
        for mp4_rel in rendered_mp4s:
            mp4_abs = os.path.join(PROJECT_ROOT, mp4_rel) if not os.path.isabs(mp4_rel) else mp4_rel
            print(f"  - {mp4_abs}")
    else:
        print(f"\n🎉🎉 全链路数据契约就绪！接下来请执行：")
        print(f"  1. 启动网页交互预览: npm run dev (Remotion) 或 npm run dev:hf (HyperFrames)")
        print(f"  2. 极速导出 1080p 成片: python scripts/pipeline.py --render --project {args.project} --engine_render {args.engine_render}\n")


if __name__ == "__main__":
    main()

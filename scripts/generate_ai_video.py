#!/usr/bin/env python3
"""
scripts/generate_ai_video.py
AI 视频生成引擎编排器 (Generative Video Orchestrator)

功能:
1. 读取 timeline.json 中的分镜原画 (heroImage) 作为首帧 (First Frame)
2. 调用 Google Gemini Omni Flash / Veo 或开源 Wan 2.1 视频生成模型
3. 生成 1080p/720p 真实物理连续动作的 MP4 动态视频切片
4. 自动回写 timeline.json 的 heroVideo 契约，由 Remotion 动静双模引擎无缝光栅化
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
ENV_FILE = BASE_DIR / ".env"

def load_env():
    """安全加载 .env 环境变量"""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

def get_gemini_api_key():
    load_env()
    return os.environ.get("GEMINI_API_KEY")

def generate_video_with_gemini(prompt: str, first_frame_path: str, output_path: str, resolution: str = "1080p"):
    """调用 Google Gemini Omni 1.1 Flash 进行图生视频 (Image-to-Video)"""
    gemini_script = Path.home() / ".gemini" / "config" / "plugins" / "gemini-api" / "skills" / "gemini-omni-flash-api" / "scripts" / "video" / "generate_video.py"
    
    if not gemini_script.exists():
        print(f"❌ [Video Engine] 未找到 Gemini Omni 视频生成脚本: {gemini_script}")
        return False

    api_key = get_gemini_api_key()
    if not api_key:
        print("\n" + "="*60)
        print("⚠️  [Video Engine] 未检测到 GEMINI_API_KEY 环境变量！")
        print("要启用 Google Veo / Gemini Omni Flash 真实视频生成能力，请在终端运行:")
        print(f'  echo "GEMINI_API_KEY=your_key_here" >> "{ENV_FILE}"')
        print("="*60 + "\n")
        return False

    print(f"🎬 [Video Engine] 正在调用 Google Omni 1.1 Flash 生成视频...")
    print(f"   首帧原画: {first_frame_path}")
    print(f"   运镜提示词: {prompt}")
    print(f"   目标分辨率: {resolution}")
    
    cmd = [
        sys.executable,
        str(gemini_script),
        prompt,
        "--first-frame", str(first_frame_path),
        "--resolution", resolution,
        "--output", str(output_path)
    ]
    
    res = subprocess.run(cmd, env=os.environ)
    return res.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="AI 真实视频生成流水线")
    parser.add_argument("--project", default="meta_muse_agent_deepdive", help="项目名称")
    parser.add_argument("--timeline", default=str(PUBLIC_DIR / "timeline.json"), help="时间轴文件路径")
    parser.add_argument("--engine", choices=["gemini", "wan", "mock"], default="gemini", help="视频生成大模型引擎")
    parser.add_argument("--resolution", choices=["720p", "1080p"], default="1080p", help="视频输出分辨率")
    parser.add_argument("--scene", help="指定生成的分镜 ID (如 scene_01)，缺省则遍历全部")
    args = parser.parse_args()

    timeline_path = Path(args.timeline)
    if not timeline_path.exists():
        print(f"❌ [Error] 时间轴不存在: {timeline_path}")
        sys.exit(1)

    with open(timeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data.get("scenes", [])
    updated = False

    video_motion_prompts = {
        "scene_01": "Cinematic camera slowly glides closer to the iPhone resting on the natural oak desk, soft morning sunlight shifting gently across the wood surface, realistic subtle reflections on screen.",
        "scene_02": "Gentle slow panning shot across the modern sunlit studio desk, human fingers delicately typing code on the aluminum keyboard, terminal text scrolling naturally in the background.",
        "scene_03": "Macro camera track across the brushed aluminum computer chassis and copper heat pipes, subtle clean softbox studio lighting sheen traveling over the metal surface.",
        "scene_04": "Extreme macro commercial shot, a finger reaches into frame and gently presses down on the tactile mechanical button switch, dust particles gently drifting in warm afternoon sunbeams.",
        "scene_05": "Subtle slow cinematic zoom toward the laptop in the boardroom, silhouettes of people in the background quietly conversing, light filtering through window blinds.",
        "scene_06": "Cinematic peaceful 35mm film shot, person by the floor-to-ceiling loft window takes a gentle sip of coffee, soft morning breeze moving outside over the city river."
    }

    for scene in scenes:
        scene_id = scene.get("id")
        if args.scene and scene_id != args.scene:
            continue

        hero_image = scene.get("heroImage")
        if not hero_image:
            continue

        full_image_path = PUBLIC_DIR / hero_image
        if not full_image_path.exists():
            print(f"⚠️  [Skip] 分镜 [{scene_id}] 原画不存在: {full_image_path}")
            continue

        output_video_rel = hero_image.replace(".jpg", ".mp4").replace(".png", ".mp4")
        output_video_full = PUBLIC_DIR / output_video_rel
        output_video_full.parent.mkdir(parents=True, exist_ok=True)

        prompt = video_motion_prompts.get(scene_id, f"Smooth cinematic camera motion forward, photorealistic lighting, natural motion physics.")

        if args.engine == "gemini":
            success = generate_video_with_gemini(prompt, str(full_image_path), str(output_video_full), args.resolution)
            if success and output_video_full.exists():
                scene["heroVideo"] = output_video_rel
                updated = True
                print(f"✅ 分镜 [{scene_id}] 视频生成完毕: {output_video_rel}")
            else:
                print(f"ℹ️  分镜 [{scene_id}] 保持 2.5D 高清摄影运镜模式。")

    if updated:
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 [Done] 时间轴已成功绑定真实动态视频文件！")

if __name__ == "__main__":
    main()

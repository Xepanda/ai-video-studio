#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/batch_render_all.py
全链路 10+ 深度长视频批量自动化生产与质量验收总控脚本
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 保障 utils 包可导入
from utils.runtime import resolve_python, run_command

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = resolve_python()
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "content", "scripts")
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
MANIFEST_FILE = os.path.join(OUT_DIR, "production_manifest.json")
os.makedirs(OUT_DIR, exist_ok=True)

# 11 支长视频生产矩阵
PRODUCTION_QUEUE = [
    {
        "id": "01",
        "script": "content/scripts/01_audio_video_architecture.json",
        "project": "01_audio_video_architecture_sovits",
        "engine": "edge_tts",
        "voice": "zh-CN-XiaoxiaoNeural",
        "title": "AI 音视频自动化架构与底层抉择",
        "category": "架构哲学"
    },
    {
        "id": "02",
        "script": "content/scripts/02_motor_foc_control.json",
        "project": "02_motor_foc_sovits",
        "engine": "edge_tts",
        "voice": "zh-CN-YunyangNeural",
        "title": "BLDC 无刷电机 FOC 磁场定向控制硬件实战",
        "category": "嵌入式硬件"
    },
    {
        "id": "03",
        "script": "content/scripts/03_personal_voice_cloning.json",
        "project": "03_personal_voice_cloning_sovits",
        "engine": "gpt_sovits",
        "voice": "epanda_voice",
        "title": "个人专属 IP 声音克隆与小样本微调实战",
        "category": "声音资产"
    },
    {
        "id": "04",
        "script": "content/scripts/04_cloudflare_edge_computing.json",
        "project": "04_cloudflare_ecosystem_chattts",
        "engine": "chattts",
        "voice": "2222",
        "title": "Cloudflare 全家桶与边缘计算架构实战",
        "category": "边缘计算"
    },
    {
        "id": "05",
        "script": "content/scripts/05_taishanpi_nas_storage.json",
        "project": "05_taishanpi_nas_chattts",
        "engine": "chattts",
        "voice": "4444",
        "title": "泰山派开发板与家庭高可用 NAS 打造",
        "category": "硬件生态"
    },
    {
        "id": "06",
        "script": "content/scripts/06_three_video_pipelines.json",
        "project": "06_three_video_pipelines_chattts",
        "engine": "chattts",
        "voice": "6666",
        "title": "三大 AI 视频生产流水线深度横评",
        "category": "视频工业化"
    },
    {
        "id": "07",
        "script": "content/scripts/07_transformer_flagship_case.json",
        "project": "07_transformer_case_study_chattts",
        "engine": "chattts",
        "voice": "8888",
        "title": "Transformer 架构与注意力机制深度剖析",
        "category": "算法底层"
    },
    {
        "id": "08",
        "script": "content/scripts/08_google_ai_video_ecosystem.json",
        "project": "08_google_ai_video_chattts",
        "engine": "chattts",
        "voice": "3333",
        "title": "Google AI 视频生态与前沿技术实战指南",
        "category": "多模态生态"
    },
    {
        "id": "09",
        "script": "content/scripts/09_ai_video_studio_workflow.json",
        "project": "09_studio_workflow_deepdive_chattts",
        "engine": "chattts",
        "voice": "5555",
        "title": "AI Video Studio 全自动化流水线落地细节",
        "category": "自动化工程"
    },
    {
        "id": "10",
        "script": "content/scripts/10_remotion_flow_matching.json",
        "project": "10_remotion_flow_matching_chattts",
        "engine": "chattts",
        "voice": "7777",
        "title": "Remotion 声明式视频渲染与扩散流匹配",
        "category": "流匹配前沿"
    },
    {
        "id": "11",
        "script": "content/scripts/11_fullstack_hardware_cloud_edge.json",
        "project": "11_fullstack_hardware_cloud_edge",
        "engine": "edge_tts",
        "voice": "zh-CN-YunxiNeural",
        "title": "硬件到底层云端的全栈极客工程哲学",
        "category": "全栈工程"
    }
]

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"), "videos": []}

def save_manifest(manifest):
    manifest["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def run_cmd(cmd_list, desc=""):
    print(f"\n>>> [RUN] {desc} ...")
    t0 = time.time()
    ret = run_command(cmd_list, cwd=PROJECT_ROOT, desc=desc)
    elapsed = time.time() - t0
    if ret.returncode != 0:
        print(f"❌ 步骤失败，返回码: {ret.returncode} (耗时: {elapsed:.1f}s)")
        return False, elapsed
    print(f"✅ 步骤顺利完成！(耗时: {elapsed:.1f}s)")
    return True, elapsed

def get_mp4_duration(mp4_path):
    try:
        import struct
        with open(mp4_path, 'rb') as f:
            data = f.read(100000)
        idx = data.find(b'mvhd')
        if idx != -1:
            version = data[idx+4]
            if version == 0:
                timescale, duration = struct.unpack('>II', data[idx+16:idx+24])
                return duration / timescale
            elif version == 1:
                timescale, duration = struct.unpack('>IQ', data[idx+24:idx+36])
                return duration / timescale
    except Exception:
        pass
    
    # 尝试通过 timeline 获取
    tl_path = os.path.join(PROJECT_ROOT, "public", "timeline.json")
    if os.path.exists(tl_path):
        try:
            with open(tl_path, "r", encoding="utf-8") as f:
                td = json.load(f)
                return td.get("totalDurationInFrames", 0) / float(td.get("fps", 30))
        except Exception:
            pass
    return 0.0

def process_video_item(item, skip_render=False, concurrency=4, force=False):
    out_mp4 = os.path.join(OUT_DIR, f"{item['project']}.mp4")
    
    # 检查是否已完成并且时长合格
    if not force and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 1024 * 1024:
        dur_sec = get_mp4_duration(out_mp4)
        frames = int(round(dur_sec * 30))
        file_size_mb = round(os.path.getsize(out_mp4)/1024/1024, 2)
        print(f"\n=======================================================")
        print(f"⏩ [SKIP] 视频成片已存在: {out_mp4}")
        print(f"   大小: {file_size_mb:.2f} MB | 时长: {dur_sec:.2f}s ({frames} 帧) | 达标 (>=120s): {'✅ 是' if dur_sec >= 120 else '⚠️ 否'}")
        print(f"=======================================================\n")
        return {
            "id": item["id"],
            "title": item["title"],
            "project": item["project"],
            "engine": item["engine"],
            "voice": item["voice"],
            "category": item["category"],
            "outputFile": f"out/{item['project']}.mp4",
            "durationSeconds": round(dur_sec, 2),
            "totalFrames": frames,
            "isOver2Min": dur_sec >= 120,
            "fileSizeMB": file_size_mb,
            "status": "COMPLETED"
        }

    print(f"\n=================================================================")
    print(f"🎬 [PRODUCING] 开始生产第 {item['id']} 号视频: {item['title']}")
    print(f"   声学方案: {item['engine']} | 音色/参数: {item['voice']}")
    print(f"   脚本文件: {item['script']}")
    print(f"=================================================================\n")

    # 步骤 1: 语音合成
    ok, tts_time = run_cmd(
        [PYTHON_EXE, "scripts/generate_audio.py", "--script", item["script"]],
        desc=f"生成分镜配音 ({item['engine']})"
    )
    if not ok:
        return {"id": item["id"], "title": item["title"], "status": "FAILED_TTS"}

    # 步骤 2: SenseVoice 毫秒打点
    ok, align_time = run_cmd(
        [PYTHON_EXE, "scripts/sensevoice_aligner.py", "--project", item["project"], "--fps", "30", "--script", item["script"]],
        desc="SenseVoice 毫秒打点与数据契约生成"
    )
    if not ok:
        return {"id": item["id"], "title": item["title"], "status": "FAILED_ALIGN"}

    # 步骤 3: 质量门禁
    ok, val_time = run_cmd(
        [PYTHON_EXE, "scripts/validator.py"],
        desc="Quality Gate 数据契约与静态资产审查"
    )
    if not ok:
        return {"id": item["id"], "title": item["title"], "status": "FAILED_GATE"}

    # 获取时间轴元数据
    tl_path = os.path.join(PROJECT_ROOT, "public", "timeline.json")
    if not os.path.exists(tl_path):
        print(f"❌ [FAILED_TL] 时间轴契约文件缺失: {tl_path} (打点步骤应生成该文件)")
        return {"id": item["id"], "title": item["title"], "status": "FAILED_TL"}
    try:
        with open(tl_path, "r", encoding="utf-8") as f:
            tl_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ [FAILED_TL] 时间轴契约文件损坏或不可读: {tl_path} ({e})")
        return {"id": item["id"], "title": item["title"], "status": "FAILED_TL"}
    frames = tl_data.get("totalDurationInFrames", 0)
    dur_sec = frames / 30.0

    print(f"\n⏱️ 当前视频标定总长度: {frames} 帧 ({dur_sec:.2f} 秒) | 达标 (>=120s): {'✅ 是' if dur_sec >= 120 else '⚠️ 否'}")

    # 步骤 4: Remotion 渲染导出
    render_time = 0.0
    if not skip_render:
        remotion_cmd = f"npx remotion render src/index.ts MasterVideo out/{item['project']}.mp4 --concurrency={concurrency}"
        ok, render_time = run_cmd(
            ["cmd.exe", "/c", remotion_cmd],
            desc=f"Remotion 多核光栅化渲染 ({frames} 帧)"
        )
        if not ok:
            return {"id": item["id"], "title": item["title"], "status": "FAILED_RENDER"}

    file_size_mb = round(os.path.getsize(out_mp4)/1024/1024, 2) if os.path.exists(out_mp4) else 0.0

    return {
        "id": item["id"],
        "title": item["title"],
        "project": item["project"],
        "engine": item["engine"],
        "voice": item["voice"],
        "category": item["category"],
        "outputFile": f"out/{item['project']}.mp4",
        "durationSeconds": round(dur_sec, 2),
        "totalFrames": frames,
        "isOver2Min": dur_sec >= 120,
        "fileSizeMB": file_size_mb,
        "renderTimeSec": round(render_time, 1),
        "status": "SUCCESS"
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="全链路长视频批量自动化生产与质量验收总控")
    parser.add_argument("--only", type=str, default="", help="指定生产的视频编号列表，例如: 07,08,09,10 或 04,05,06")
    parser.add_argument("--force", action="store_true", help="强制重新合成语音并重新渲染，即使 out/*.mp4 已经存在")
    parser.add_argument("--concurrency", type=int, default=4, help="Remotion 多核并行光栅化线程数 (默认 4)")
    parser.add_argument("--skip-render", action="store_true", help="跳过 Remotion 视频渲染 (仅生成配音与打点契约)")
    args = parser.parse_args()

    manifest = load_manifest()
    completed_projects = {v["project"]: v for v in manifest.get("videos", []) if v.get("status") in ("COMPLETED", "SUCCESS")}

    queue = PRODUCTION_QUEUE
    if args.only:
        targets = set([x.strip() for x in args.only.split(",") if x.strip()])
        queue = [item for item in PRODUCTION_QUEUE if item["id"] in targets or item["project"] in targets]
        print(f"🎯 用户指定过滤生产队列: {[item['id'] for item in queue]}")

    print(f"\n=======================================================")
    print(f"🚀 [Batch Producer] 全链路 10+ 视频流水线批量中枢启动")
    print(f"   本次生产目标: {len(queue)} 支 (总队列: {len(PRODUCTION_QUEUE)} 支)")
    print(f"   当前已完成: {len(completed_projects)} 支")
    print(f"   强制重跑模式: {'🔥 是' if args.force else '⚡ 否'}")
    print(f"=======================================================\n")

    for item in queue:
        res = process_video_item(item, skip_render=args.skip_render, concurrency=args.concurrency, force=args.force)
        
        # 更新清单
        existing_idx = None
        for idx, v in enumerate(manifest["videos"]):
            if v.get("project") == item["project"] or v.get("id") == item["id"]:
                existing_idx = idx
                break
        if existing_idx is not None:
            manifest["videos"][existing_idx] = res
        else:
            manifest["videos"].append(res)

        save_manifest(manifest)
        print(f"\n🎉 视频 [{item['title']}] 状态更新完毕: {res.get('status')}\n")

    print("\n=======================================================")
    print("🏆 全部指定视频流水线执行完毕！请查看生产清单:")
    print(f"   {MANIFEST_FILE}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()

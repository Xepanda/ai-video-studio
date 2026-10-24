#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/github_demo_pipeline.py
GitHub 项目深度演示视频流水线 (立项版: spec 契约 + clone/install/run 编排 + storyboard 生成)
功能:
  1. 加载并校验 .demo.yaml 规格文件 (spec_version / project / setup / run / capture / output 六段契约)
  2. 幂等沙箱 clone 目标仓库 (支持 ref 分支/tag/commit; 已存在则复用, --force 强制重建)
  3. 按序执行 setup.install 安装命令 (统一经 utils.runtime.run_command, 超时/重试可配)
  4. 按序执行 run.steps 演示步骤 (expect_exit 契约校验, capture 元数据记录)
  5. 失败显式降级 (延续审计 A3 数据诚信 + 执行计划风险表"安装失败显式降级"策略):
     - clone 失败    -> 硬错误 (DemoPipelineError), 无仓库即无演示, 绝不编造
     - install 失败  -> 标记 degraded, 不阻断 storyboard 生成, 产出仅含介绍/README 分镜
     - run step 失败 -> 如实记录真实退出码与 stderr 摘要, 不伪造成功输出
  6. 输出 storyboard.json (Remotion 分镜契约, 供 scripts/pipeline.py 后续 TTS/打点/渲染消费)
     W5-6 起: capture.targets 声明的目标 URL 经 scripts/demo_capture.py 真实捕获
     (Playwright 截图+录屏+events), 成功捕获生成 BrowserScreenshot 场景 (browser.image
     引用真实截图), 失败如实记入 source.captureResult, 绝不伪造捕获证据。

用法:
  python scripts/github_demo_pipeline.py --spec .demo.yaml                 # 完整执行
  python scripts/github_demo_pipeline.py --spec .demo.yaml --dry-run       # 仅校验+生成 storyboard
  python scripts/github_demo_pipeline.py --spec .demo.yaml --force         # 强制重新 clone
"""

import os
import sys
import json
import time
import shutil
import argparse
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 保障 utils 包可导入
from utils.runtime import run_command
# Playwright 真实捕获 (W5-6): demo_capture 内部延迟导入 playwright, 本导入安全
from demo_capture import run_captures, CaptureError, summarize_captures

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 各阶段子进程超时 (秒), 均可经环境变量覆盖
CLONE_TIMEOUT = int(os.environ.get("AVS_DEMO_CLONE_TIMEOUT", "600"))
INSTALL_TIMEOUT = int(os.environ.get("AVS_DEMO_INSTALL_TIMEOUT", "1800"))
STEP_TIMEOUT = int(os.environ.get("AVS_DEMO_STEP_TIMEOUT", "300"))

SPEC_VERSION = "1.0"
DEFAULT_FPS = 30
DEFAULT_STEP_DURATION = 8  # 秒

VALID_CAPTURE_MODES = ("terminal", "screenshot", "none")
VALID_WAIT_UNTIL = ("load", "domcontentloaded", "networkidle", "commit")
DEFAULT_CAPTURE_SCENE_DURATION = 4  # 秒 (BrowserScreenshot 场景默认时长)


class DemoPipelineError(Exception):
    """演示流水线规格或执行阶段失败 (显式报错, 由调用方决定降级策略)。

    设计原则 (延续审计 A3 数据诚信): clone/规格失败必须显式报错;
    严禁向 storyboard 注入编造的命令输出、退出码或截图证据。
    """


# ---------------------------------------------------------------------------
# 规格加载与校验
# ---------------------------------------------------------------------------

def _require_mapping(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise DemoPipelineError(f"规格字段 [{field}] 必须为对象 (mapping)，实际为: {type(value).__name__}")
    return value


def _require_nonempty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DemoPipelineError(f"规格字段 [{field}] 必须为非空字符串")
    return value.strip()


def validate_spec(spec: Any) -> Dict[str, Any]:
    """校验 .demo.yaml 规格契约, 返回规范化后的 spec dict; 不合法则抛出可读错误。"""
    spec = _require_mapping(spec, "root")

    version = str(spec.get("spec_version", "")).strip()
    if version != SPEC_VERSION:
        raise DemoPipelineError(
            f"不支持的 spec_version: {version!r}，当前仅支持 {SPEC_VERSION!r}"
        )

    project = _require_mapping(spec.get("project"), "project")
    _require_nonempty_str(project.get("name"), "project.name")
    repo = _require_nonempty_str(project.get("repo"), "project.repo")
    if not (repo.startswith("http://") or repo.startswith("https://") or repo.startswith("git@")):
        raise DemoPipelineError(f"project.repo 必须是合法的 git 仓库地址 (http/https/ssh)，实际为: {repo!r}")
    _require_nonempty_str(project.get("title"), "project.title")

    setup = spec.get("setup") or {}
    _require_mapping(setup, "setup")
    install_cmds = setup.get("install") or []
    if not isinstance(install_cmds, list) or not all(isinstance(c, str) and c.strip() for c in install_cmds):
        raise DemoPipelineError("setup.install 必须为字符串命令列表 (或省略)")
    env_map = setup.get("env") or {}
    _require_mapping(env_map, "setup.env")

    run = _require_mapping(spec.get("run"), "run")
    steps = run.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        raise DemoPipelineError("run.steps 必须为非空列表 (至少 1 个演示步骤)")

    seen_ids = set()
    for idx, step in enumerate(steps):
        step = _require_mapping(step, f"run.steps[{idx}]")
        step_id = _require_nonempty_str(step.get("id"), f"run.steps[{idx}].id")
        if step_id in seen_ids:
            raise DemoPipelineError(f"run.steps 存在重复步骤 id: {step_id!r}")
        seen_ids.add(step_id)
        _require_nonempty_str(step.get("title"), f"run.steps[{idx}].title")
        _require_nonempty_str(step.get("cmd"), f"run.steps[{idx}].cmd")

        expect_exit = step.get("expect_exit", 0)
        if not isinstance(expect_exit, int):
            raise DemoPipelineError(f"run.steps[{idx}].expect_exit 必须为整数，实际为: {expect_exit!r}")

        capture_mode = step.get("capture", "terminal")
        if capture_mode not in VALID_CAPTURE_MODES:
            raise DemoPipelineError(
                f"run.steps[{idx}].capture 必须是 {VALID_CAPTURE_MODES} 之一，实际为: {capture_mode!r}"
            )

        duration = step.get("duration", DEFAULT_STEP_DURATION)
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise DemoPipelineError(f"run.steps[{idx}].duration 必须为正数 (秒)，实际为: {duration!r}")

    capture_cfg = spec.get("capture") or {}
    _require_mapping(capture_cfg, "capture")
    if "enabled" in capture_cfg and not isinstance(capture_cfg["enabled"], bool):
        raise DemoPipelineError(f"capture.enabled 必须为布尔值，实际为: {capture_cfg['enabled']!r}")

    capture_targets = capture_cfg.get("targets") or []
    if not isinstance(capture_targets, list):
        raise DemoPipelineError("capture.targets 必须为列表 (或省略)")
    seen_target_ids = set()
    for idx, target in enumerate(capture_targets):
        target = _require_mapping(target, f"capture.targets[{idx}]")
        target_id = _require_nonempty_str(target.get("id"), f"capture.targets[{idx}].id")
        if target_id in seen_target_ids:
            raise DemoPipelineError(f"capture.targets 存在重复目标 id: {target_id!r}")
        seen_target_ids.add(target_id)
        target_url = _require_nonempty_str(target.get("url"), f"capture.targets[{idx}].url")
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise DemoPipelineError(
                f"capture.targets[{idx}].url 必须是 http(s) 地址 (仅支持真实网页捕获)，实际为: {target_url!r}"
            )
        wait_until = target.get("wait_until", "networkidle")
        if wait_until not in VALID_WAIT_UNTIL:
            raise DemoPipelineError(
                f"capture.targets[{idx}].wait_until 必须是 {VALID_WAIT_UNTIL} 之一，实际为: {wait_until!r}"
            )
        if "full_page" in target and not isinstance(target["full_page"], bool):
            raise DemoPipelineError(f"capture.targets[{idx}].full_page 必须为布尔值")
        if "record_video" in target and not isinstance(target["record_video"], bool):
            raise DemoPipelineError(f"capture.targets[{idx}].record_video 必须为布尔值")
        target_duration = target.get("duration", DEFAULT_CAPTURE_SCENE_DURATION)
        if not isinstance(target_duration, (int, float)) or target_duration <= 0:
            raise DemoPipelineError(
                f"capture.targets[{idx}].duration 必须为正数 (秒)，实际为: {target_duration!r}"
            )

    output_cfg = spec.get("output") or {}
    _require_mapping(output_cfg, "output")
    fps = output_cfg.get("fps", DEFAULT_FPS)
    if not isinstance(fps, int) or fps <= 0:
        raise DemoPipelineError(f"output.fps 必须为正整数，实际为: {fps!r}")

    return spec


def load_spec(spec_path: str) -> Dict[str, Any]:
    """加载 .demo.yaml 规格文件并执行契约校验。"""
    if not os.path.exists(spec_path):
        raise DemoPipelineError(f"规格文件不存在: {spec_path}")

    try:
        import yaml  # 延迟导入: --help 等无需 PyYAML 的场景不被阻断
    except ImportError:
        raise DemoPipelineError(
            "缺少 PyYAML 依赖 (requirements.txt 核心层已声明)，请执行: pip install pyyaml"
        )

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise DemoPipelineError(f"规格文件 YAML 解析失败: {spec_path}\n{e}")

    spec = validate_spec(raw)
    print(f"✅ 规格契约校验通过: {spec_path} (spec_version={SPEC_VERSION})")
    return spec


# ---------------------------------------------------------------------------
# 占位符渲染
# ---------------------------------------------------------------------------

def render_placeholders(text: str, context: Dict[str, str]) -> str:
    """渲染 {name} / {repo} 等占位符 (仅替换已知键, 未知占位符原样保留并告警)。"""
    if not isinstance(text, str):
        return text
    for key, value in context.items():
        text = text.replace("{" + key + "}", str(value))
    return text


# ---------------------------------------------------------------------------
# 执行阶段: clone / install / run
# ---------------------------------------------------------------------------

def clone_repo(spec: Dict[str, Any], force: bool = False) -> Tuple[str, bool]:
    """幂等 clone 目标仓库。返回 (clone_dir, reused)。

    已存在且非 --force 时复用; --force 或首次 clone 走 git clone。
    clone 失败是硬错误 (DemoPipelineError): 无仓库即无演示, 拒绝降级编造。
    """
    project = spec["project"]
    name = project["name"]
    context = {"name": name, "repo": project["repo"]}

    setup = spec.get("setup") or {}
    clone_dir = render_placeholders(setup.get("clone_dir") or "projects_demo/{name}", context)
    clone_dir_abs = clone_dir if os.path.isabs(clone_dir) else os.path.join(PROJECT_ROOT, clone_dir)

    ref = (project.get("ref") or "").strip()

    if os.path.isdir(clone_dir_abs):
        if force:
            print(f"🧹 [Clone] --force 指定，清除既有目录: {clone_dir}")
            shutil.rmtree(clone_dir_abs, ignore_errors=True)
        else:
            print(f"♻️ [Clone] 目录已存在，复用既有检出: {clone_dir}")
            return clone_dir, True

    os.makedirs(os.path.dirname(clone_dir_abs), exist_ok=True)
    cmd = ["git", "clone"]
    if ref:
        cmd.extend(["--branch", ref])
    cmd.extend([project["repo"], clone_dir_abs])

    print(f"\n=======================================================")
    print(f"🚀 [Clone] 正在克隆仓库: {project['repo']}" + (f" (ref={ref})" if ref else ""))
    print(f"=======================================================\n")
    ret = run_command(cmd, cwd=PROJECT_ROOT, timeout=CLONE_TIMEOUT, desc="git clone")
    if ret.returncode != 0:
        raise DemoPipelineError(
            f"仓库 clone 失败 (exit={ret.returncode}): {project['repo']}\n"
            f"  目标目录: {clone_dir}\n"
            f"  请检查网络连通性或仓库地址; 按数据诚信原则，无仓库不生成演示分镜。"
        )
    print(f"✅ [Clone] 克隆完成: {clone_dir}")
    return clone_dir, False


def run_install(spec: Dict[str, Any], clone_dir: str) -> Dict[str, Any]:
    """按序执行 setup.install 安装命令。失败不抛错, 返回降级状态 (显式降级策略)。"""
    setup = spec.get("setup") or {}
    install_cmds: List[str] = setup.get("install") or []
    env_map: Dict[str, Any] = setup.get("env") or {}

    # 规格声明的环境变量应用于流水线进程 (安装/运行阶段共享)
    for key, value in env_map.items():
        os.environ[str(key)] = str(value)

    result: Dict[str, Any] = {"attempted": len(install_cmds), "succeeded": 0, "failed": [], "degraded": False}

    if not install_cmds:
        print("ℹ️ [Install] 规格未声明安装命令，跳过安装阶段")
        return result

    clone_dir_abs = clone_dir if os.path.isabs(clone_dir) else os.path.join(PROJECT_ROOT, clone_dir)

    for idx, cmd in enumerate(install_cmds):
        print(f"\n=======================================================")
        print(f"🚀 [Install {idx + 1}/{len(install_cmds)}] 正在执行: {cmd}")
        print(f"=======================================================\n")
        ret = run_command(cmd, cwd=clone_dir_abs, timeout=INSTALL_TIMEOUT, desc=f"install[{idx}]")
        if ret.returncode != 0:
            # 显式降级: 记录失败事实, 不阻断 storyboard 生成 (执行计划风险表缓解策略)
            print(f"⚠️ [Install] 安装命令失败 (exit={ret.returncode})，进入显式降级模式: {cmd}")
            result["failed"].append({"cmd": cmd, "exit_code": ret.returncode})
            result["degraded"] = True
            break
        result["succeeded"] += 1
        print(f"✅ [Install] 安装命令完成: {cmd}")

    if result["degraded"]:
        print(
            "⚠️ [Install] 安装阶段降级: 演示步骤可能无法运行，storyboard 将如实标注 degraded 状态，\n"
            "   并仅保留介绍分镜; 严禁伪造安装成功或命令输出。"
        )
    return result


def run_steps(spec: Dict[str, Any], clone_dir: str, install_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按序执行 run.steps 演示步骤, 如实记录每步真实退出码与输出摘要。"""
    steps: List[Dict[str, Any]] = spec["run"]["steps"]
    clone_dir_abs = clone_dir if os.path.isabs(clone_dir) else os.path.join(PROJECT_ROOT, clone_dir)
    skip_run = install_result.get("degraded", False)

    records: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps):
        record: Dict[str, Any] = {
            "id": step["id"],
            "title": step["title"],
            "cmd": step["cmd"],
            "expect_exit": step.get("expect_exit", 0),
            "capture": step.get("capture", "terminal"),
            "narration": step.get("narration", ""),
            "duration": step.get("duration", DEFAULT_STEP_DURATION),
            "status": "pending",
            "exit_code": None,
            "output_excerpt": "",
        }

        if skip_run:
            # 安装降级: 不执行演示命令, 如实标记 skipped (绝不伪造输出)
            record["status"] = "skipped_degraded_install"
            print(f"⏭️ [Run {idx + 1}/{len(steps)}] 安装降级，跳过演示步骤: {step['id']} ({step['title']})")
            records.append(record)
            continue

        print(f"\n=======================================================")
        print(f"🚀 [Run {idx + 1}/{len(steps)}] {step['title']}  (id={step['id']})")
        print(f"=======================================================\n")
        ret = run_command(step["cmd"], cwd=clone_dir_abs, timeout=STEP_TIMEOUT,
                          desc=f"run[{step['id']}]", capture_output=True,
                          encoding="utf-8", errors="replace")

        record["exit_code"] = ret.returncode
        stdout = (ret.stdout or "").strip()
        stderr = (ret.stderr or "").strip()
        excerpt = stdout if stdout else stderr
        record["output_excerpt"] = excerpt[:2000]

        if ret.returncode == record["expect_exit"]:
            record["status"] = "ok"
            print(f"✅ [Run] 步骤完成且退出码符合契约: {step['id']} (exit={ret.returncode})")
        else:
            # 如实记录失败: 保留真实退出码, 不篡改为成功
            record["status"] = "failed"
            print(
                f"⚠️ [Run] 步骤退出码偏离契约: {step['id']} "
                f"(期望 {record['expect_exit']}, 实际 {ret.returncode})，storyboard 将如实标注。"
            )
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# storyboard 生成 (Remotion 分镜契约)
# ---------------------------------------------------------------------------

def build_storyboard(
    spec: Dict[str, Any],
    install_result: Dict[str, Any],
    step_records: List[Dict[str, Any]],
    spec_path: str,
    capture_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """将执行结果编译为 Remotion 分镜契约 (storyboard.json)。

    分镜结构:
      scene_01        MinimalHeadline      开场钩子 (项目标题 + 副标题)
      scene_cap_xx    BrowserScreenshot     每个成功捕获的真实网页截图 (W5-6)
      scene_xx        TerminalWindow       每个演示步骤一幕 (codeSnippet=真实命令; 降级/失败如实标注)
      scene_last      MinimalHeadline      收尾 (star 引导 / 总结)
    """
    project = spec["project"]
    output_cfg = spec.get("output") or {}
    fps = output_cfg.get("fps", DEFAULT_FPS)
    degraded = install_result.get("degraded", False)
    capture_targets = {t.get("id"): t for t in (spec.get("capture") or {}).get("targets") or []}

    scenes: List[Dict[str, Any]] = []

    # 1. 开场钩子分镜
    scenes.append({
        "id": "scene_01",
        "type": "MinimalHeadline",
        "title": project["title"],
        "text": project.get("subtitle") or "一条命令，看懂这个开源项目",
        "category": "GITHUB DEMO · 深度演示",
        "highlightWords": project.get("tags") or [],
        "inverted": False,
        "estimatedDuration": 3,
        "durationInFrames": 3 * fps,
    })

    # 2. W5-6: 真实捕获场景 (仅 status=ok 的捕获入画面; 失败只进 source 元数据)
    for rec in (capture_summary or {}).get("records") or []:
        if rec.get("status") != "ok":
            continue
        target = capture_targets.get(rec.get("id")) or {}
        duration = target.get("duration", DEFAULT_CAPTURE_SCENE_DURATION)
        scenes.append({
            "id": f"scene_cap_{rec['id']}",
            "type": "BrowserScreenshot",
            "title": target.get("title") or f"真实捕获: {rec['url']}",
            "text": target.get("narration") or (
                f"先看真实界面。这里是 {rec['url']} 的实机运行画面，"
                "所有截图与录屏均由无头浏览器真实捕获，未做任何伪造。"
            ),
            "browser": {
                "url": rec["url"],
                "image": rec.get("screenshotStatic") or "",
            },
            "estimatedDuration": duration,
            "durationInFrames": int(duration * fps),
            # 捕获事实元数据 (供质检与人工审校, 不进画面)
            "demoCapture": {
                "screenshot": rec.get("screenshot"),
                "video": rec.get("video"),
                "events": rec.get("events"),
            },
        })

    # 2. 每个演示步骤一幕终端场景
    for idx, rec in enumerate(step_records):
        scene_id = f"scene_{idx + 2:02d}"
        code_lines = [f"$ {rec['cmd']}"]
        if rec["status"] == "ok" and rec["output_excerpt"]:
            # 仅注入真实执行输出 (节选), 失败/跳过时绝不编造
            code_lines.append(rec["output_excerpt"].splitlines()[0][:120] if rec["output_excerpt"] else "")
        scene: Dict[str, Any] = {
            "id": scene_id,
            "type": "TerminalWindow",
            "title": rec["title"],
            "text": rec["narration"],
            "codeTitle": f"$ {rec['cmd']}",
            "codeSnippet": "\n".join(code_lines),
            "codeLang": "bash",
            "estimatedDuration": rec["duration"],
            "durationInFrames": int(rec["duration"] * fps),
            # 执行事实元数据 (供质检与人工审校, 不进画面)
            "demoRun": {
                "stepId": rec["id"],
                "status": rec["status"],
                "exitCode": rec["exit_code"],
                "expectExit": rec["expect_exit"],
                "capture": rec["capture"],
            },
        }
        if degraded or rec["status"] != "ok":
            scene["demoRun"]["degraded"] = True
        scenes.append(scene)

    # 3. 收尾分镜
    closing_text = (
        "安装环境存在兼容问题，本片仅展示项目介绍与命令清单，输出证据已如实标注。"
        if degraded else
        "完整源码与文档已附在简介区，三连支持是持续拆解开源项目的动力。"
    )
    scenes.append({
        "id": f"scene_{len(step_records) + 2:02d}",
        "type": "MinimalHeadline",
        "title": "拆解完成",
        "text": closing_text,
        "category": "WRAP UP",
        "highlightWords": [],
        "inverted": False,
        "estimatedDuration": 3,
        "durationInFrames": 3 * fps,
    })

    total_frames = sum(s["durationInFrames"] for s in scenes)

    return {
        "project": project["name"],
        "title": project["title"],
        "theme": "linear-graphite",
        "voice": "4444",
        "engine": "chattts",
        "fps": fps,
        "enableBgm": True,
        "enableSfx": True,
        "voiceVolume": 1.0,
        "totalDurationInFrames": total_frames,
        "source": {
            "repo": project["repo"],
            "ref": (project.get("ref") or "").strip(),
            "spec": os.path.basename(spec_path),
            "generatedBy": "github_demo_pipeline.py",
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "degraded": degraded,
            "installResult": {
                "attempted": install_result.get("attempted", 0),
                "succeeded": install_result.get("succeeded", 0),
                "failed": install_result.get("failed", []),
            },
        },
        # W5-6: 真实捕获汇总 (失败目标仅在此留痕, 绝不入画面伪造)
        "captureResult": capture_summary or {"attempted": 0, "ok": 0, "failed": 0, "failedIds": [], "records": []},
        "scenes": scenes,
    }


def save_storyboard(storyboard: Dict[str, Any], output_path: str) -> str:
    """落盘 storyboard.json (相对路径基于 PROJECT_ROOT 解析)。"""
    out_abs = output_path if os.path.isabs(output_path) else os.path.join(PROJECT_ROOT, output_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    print(f"✅ [Storyboard] 分镜契约已生成: {output_path} "
          f"({len(storyboard['scenes'])} 幕 / {storyboard['totalDurationInFrames']} 帧)")
    return out_abs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_parser() -> argparse.ArgumentParser:
    """定义并返回 GitHub 演示流水线命令行解析器"""
    parser = argparse.ArgumentParser(description="GitHub 项目深度演示视频流水线 (立项版)")
    parser.add_argument("--spec", type=str, required=True, help=".demo.yaml 规格文件路径")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅校验规格并生成 storyboard，不执行 clone/install/run")
    parser.add_argument("--force", action="store_true", help="强制重新 clone (清除既有检出目录)")
    parser.add_argument("--skip-install", action="store_true", help="跳过安装阶段 (等同无安装命令)")
    parser.add_argument("--skip-run", action="store_true", help="跳过演示步骤执行 (storyboard 标记 skipped)")
    parser.add_argument("--skip-capture", action="store_true",
                        help="跳过 Playwright 真实捕获阶段 (storyboard 不含截图场景)")
    parser.add_argument("--output", type=str, default="",
                        help="覆盖 storyboard 输出路径 (默认取规格 output.storyboard 或 content/scripts/{name}_demo.json)")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # 1. 规格加载与契约校验 (失败即硬错误, 可读退出)
    try:
        spec = load_spec(args.spec)
    except DemoPipelineError as e:
        print(f"\n❌ [DemoPipeline] 规格校验失败: {e}")
        sys.exit(2)

    name = spec["project"]["name"]
    context = {"name": name, "repo": spec["project"]["repo"]}

    install_result: Dict[str, Any] = {"attempted": 0, "succeeded": 0, "failed": [], "degraded": False}
    clone_dir = ""

    if not args.dry_run:
        # 2. clone (硬错误语义: 失败即终止)
        try:
            clone_dir, _reused = clone_repo(spec, force=args.force)
        except DemoPipelineError as e:
            print(f"\n❌ [DemoPipeline] {e}")
            sys.exit(3)

        # 3. install (显式降级语义: 失败不终止, storyboard 如实标注)
        if args.skip_install:
            print("ℹ️ [Install] --skip-install 指定，跳过安装阶段")
            install_result["degraded"] = True  # 未安装即视为降级, 演示步骤将跳过
        else:
            install_result = run_install(spec, clone_dir)
    else:
        print("🧪 [DryRun] 跳过 clone/install/run 执行阶段，仅生成 storyboard 契约")

    # 4. run steps
    if args.dry_run or args.skip_run:
        step_records = [
            {
                "id": s["id"],
                "title": s["title"],
                "cmd": s["cmd"],
                "expect_exit": s.get("expect_exit", 0),
                "capture": s.get("capture", "terminal"),
                "narration": s.get("narration", ""),
                "duration": s.get("duration", DEFAULT_STEP_DURATION),
                "status": "skipped",
                "exit_code": None,
                "output_excerpt": "",
            }
            for s in spec["run"]["steps"]
        ]
        if args.dry_run:
            print("🧪 [DryRun] 演示步骤以 skipped 状态写入 storyboard")
        else:
            print("⏭️ [Run] --skip-run 指定，演示步骤以 skipped 状态写入 storyboard")
    else:
        step_records = run_steps(spec, clone_dir, install_result)

    # 4.5 W5-6: Playwright 真实捕获 (dry-run/--skip-capture 跳过; 单目标失败不阻断, 如实记录)
    capture_summary: Optional[Dict[str, Any]] = None
    capture_cfg = spec.get("capture") or {}
    capture_targets: List[Dict[str, Any]] = capture_cfg.get("targets") or []
    if args.dry_run:
        if capture_targets:
            print("🧪 [DryRun] 跳过 Playwright 真实捕获阶段 (capture.targets 已声明但未执行)")
    elif args.skip_capture:
        print("⏭️ [Capture] --skip-capture 指定，跳过 Playwright 真实捕获阶段")
    elif not capture_cfg.get("enabled", True):
        print("ℹ️ [Capture] 规格 capture.enabled=false，跳过真实捕获阶段")
    elif capture_targets:
        capture_records = run_captures(capture_targets)
        capture_summary = summarize_captures(capture_records)

    # 5. storyboard 生成与落盘
    storyboard = build_storyboard(spec, install_result, step_records, args.spec,
                                  capture_summary=capture_summary)
    output_cfg = spec.get("output") or {}
    output_path = args.output or render_placeholders(
        output_cfg.get("storyboard") or "content/scripts/{name}_demo.json", context
    )
    out_abs = save_storyboard(storyboard, output_path)

    degraded = storyboard["source"]["degraded"]
    failed_steps = [r["id"] for r in step_records if r["status"] == "failed"]
    print(f"\n=======================================================")
    print(f"🚀 [DemoPipeline] 流水线阶段完成: {name}")
    print(f"   storyboard: {out_abs}")
    if degraded:
        print(f"   ⚠️ 降级模式: 安装失败或跳过, 演示步骤未执行 (已如实标注)")
    if failed_steps:
        print(f"   ⚠️ 退出码偏离契约的步骤: {', '.join(failed_steps)} (已如实标注)")
    cap_result = storyboard.get("captureResult") or {}
    if cap_result.get("attempted"):
        if cap_result.get("failed"):
            print(f"   ⚠️ 捕获失败目标: {', '.join(str(i) for i in cap_result['failedIds'])} "
                  f"(已如实记录, 未伪造证据; {cap_result['ok']}/{cap_result['attempted']} 成功)")
        else:
            print(f"   📸 真实捕获: {cap_result['ok']}/{cap_result['attempted']} 个目标成功 (截图+录屏+events)")
    print(f"=======================================================\n")
    try:
        script_rel = os.path.relpath(out_abs, PROJECT_ROOT)
    except ValueError:
        # Windows 跨盘符时 relpath 不可用, 回退为绝对路径 (绝不因此中断收尾提示)
        script_rel = out_abs
    print("💡 后续可执行: python scripts/pipeline.py --script "
          f"{script_rel} --project {name} --render")


if __name__ == "__main__":
    main()

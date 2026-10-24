#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils/runtime.py
跨脚本共享的运行时工具：解释器解析与子进程统一封装。

设计目标 (对应审计报告 Phase 0 任务 A4/B1):
  1. 消灭硬编码个人机器路径 (原 LIVECLIP_PYTHON)，换机零配置；
  2. 全仓 subprocess 调用统一带超时与有限重试，子进程挂起不再无限阻塞流水线。

环境变量:
  AVS_PYTHON        指定流水线子进程使用的 Python 解释器绝对路径 (默认: 当前解释器 sys.executable)
  AVS_CMD_TIMEOUT   子进程默认超时秒数 (默认: 1800)
  AVS_CMD_RETRIES   子进程默认重试次数 (默认: 1，即最多执行 2 次)
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, List, Optional, Union

DEFAULT_TIMEOUT = int(os.environ.get("AVS_CMD_TIMEOUT", "1800"))
DEFAULT_RETRIES = max(0, int(os.environ.get("AVS_CMD_RETRIES", "1")))

# Windows 下需要通过 cmd.exe /c 解析的 Node 生态可执行文件
_WIN_SHIM_BINARIES = ("npx", "hyperframes", "remotion")

CommandType = Union[str, List[str]]


def resolve_python() -> str:
    """解析流水线子进程使用的 Python 解释器。

    优先级: AVS_PYTHON 环境变量 > 当前解释器 (sys.executable)。
    历史兼容说明: 早期版本硬编码个人 liveclip conda 环境路径，已移除；
    如确需指定其他解释器 (例如内置 yt-dlp 的环境)，请设置 AVS_PYTHON。
    """
    env_python = os.environ.get("AVS_PYTHON")
    if env_python and os.path.exists(env_python):
        return env_python
    return sys.executable


def _wrap_windows(cmd: List[str]) -> List[str]:
    """Windows 下对 npx/hyperframes/remotion 自动包装 cmd.exe /c (与原行为一致)"""
    if sys.platform == "win32" and cmd and os.path.basename(cmd[0]) in _WIN_SHIM_BINARIES:
        return ["cmd.exe", "/c"] + cmd
    return cmd


def run_command(
    cmd: CommandType,
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    desc: str = "",
    capture_output: bool = False,
    check: bool = False,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """带超时与有限重试的子进程统一封装。

    Args:
        cmd: 字符串命令 (shell=True) 或参数列表。
        cwd: 工作目录。
        timeout: 单次执行超时秒数。
        retries: 失败后的重试次数 (0 表示不重试)。
        desc: 日志用的人类可读描述。
        capture_output: 是否捕获 stdout/stderr。
        check: 最终失败时是否抛 RuntimeError (默认返回 returncode=1 的兼容对象)。
        encoding: 文本解码编码 (仅 capture_output 时生效; 解析工具 JSON 输出建议 utf-8)。
        errors: 文本解码错误策略 (例如 'replace')。

    Returns:
        subprocess.CompletedProcess (最终失败时返回最后一次真实执行的结果；
        若全部因异常 (超时/OSError) 失败，返回 returncode=1 的合成对象，
        保证调用方 `.returncode` / `.stdout` 访问不炸)。
    """
    label = desc or (cmd if isinstance(cmd, str) else " ".join(cmd))
    last_err = "unknown"
    last_proc: Optional[subprocess.CompletedProcess] = None
    run_kwargs: Dict[str, Any] = {}
    if encoding is not None:
        run_kwargs["encoding"] = encoding
    if errors is not None:
        run_kwargs["errors"] = errors

    for attempt in range(1, retries + 2):
        try:
            if isinstance(cmd, str):
                proc = subprocess.run(
                    cmd, shell=True, cwd=cwd, timeout=timeout,
                    capture_output=capture_output, text=True, **run_kwargs,
                )
            else:
                proc = subprocess.run(
                    _wrap_windows(list(cmd)), cwd=cwd, timeout=timeout,
                    capture_output=capture_output, text=True, **run_kwargs,
                )
            if proc.returncode == 0:
                return proc
            last_err = f"exit code {proc.returncode}"
            if capture_output and proc.stderr:
                last_err += f" | {proc.stderr.strip()[:200]}"
            last_proc = proc  # 保留真实退出码供调用方判定
        except subprocess.TimeoutExpired:
            last_err = f"timeout after {timeout}s"
        except Exception as e:  # noqa: BLE001 - 统一收敛为可重试错误
            last_err = f"{type(e).__name__}: {e}"

        print(f"[runtime] 命令执行失败 ({label}) 第 {attempt}/{retries + 1} 次: {last_err}")
        if attempt <= retries:
            time.sleep(2)

    if check:
        raise RuntimeError(f"命令最终失败: {label} ({last_err})")

    if last_proc is not None:
        return last_proc
    return subprocess.CompletedProcess(
        args=cmd if isinstance(cmd, list) else [cmd],
        returncode=1,
        stdout="",
        stderr=last_err,
    )


def find_binary(name: str) -> str:
    """在 PATH 中查找可执行文件，返回绝对路径或空串。"""
    from shutil import which
    return which(name) or which(f"{name}.exe") or ""

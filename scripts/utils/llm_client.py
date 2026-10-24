#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/utils/llm_client.py
跨脚本共享的 LLM 客户端基建 (OpenAI 兼容 Chat Completions 协议)。

设计目标 (对应执行计划 Phase 1 W5-6):
  1. 为 llm_scriptgen.py (知识科普) 与 hotspot_scriptgen.py (热点快剪) 提供统一 LLM 调用入口;
  2. 仅依赖 requests (核心层已声明), 不引入 openai SDK, 适配任意 OpenAI 兼容端点
     (DeepSeek / 通义 / 本地 vLLM / OneAPI 网关等);
  3. 数据诚信承诺 (延续审计 A3): 调用失败一律显式 LLMError 并携带真实状态码与响应摘要,
     严禁向调用方返回编造的"模型输出"。

环境变量:
  AVS_LLM_API_KEY   LLM API Key (必需; 未配置时真实调用直接 LLMError, 测试可注入假 client)
  AVS_LLM_BASE_URL  OpenAI 兼容 base_url (默认 https://api.deepseek.com/v1)
  AVS_LLM_MODEL     模型名 (默认 deepseek-chat)
  AVS_LLM_TIMEOUT   单次请求超时秒数 (默认 120)

用法:
  from utils.llm_client import LLMClient
  client = LLMClient()                      # 读取环境变量
  text = client.chat([{"role": "user", "content": "..."}])
  data = client.chat_json([...])            # 自动剥离 ```json 围栏并解析
"""

import os
import json
import time
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = float(os.environ.get("AVS_LLM_TIMEOUT", "120"))

# 响应体/原始文本摘要截断长度 (错误信息用人话可读, 不刷屏)
_TEXT_EXCERPT_LEN = 300


class LLMError(Exception):
    """LLM 调用失败 (未配置凭证 / 网络错误 / HTTP 非 2xx / 响应结构不符 / JSON 解析失败)。

    设计原则 (延续审计 A3 数据诚信): 模型不可用时必须显式报错,
    由调用方决定降级策略 (跳过该话题/终止流水线); 严禁伪造模型输出。
    """


class LLMClient:
    """OpenAI 兼容 Chat Completions 客户端 (session 可注入, 便于离线测试)。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        session: Any = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("AVS_LLM_API_KEY", "").strip()
        self.base_url = (base_url or os.environ.get("AVS_LLM_BASE_URL", "").strip() or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.environ.get("AVS_LLM_MODEL", "").strip() or DEFAULT_MODEL
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        # session 注入点: 生产环境为 requests.Session; 测试可注入伪 session
        self._session = session

    # -- 内部工具 -----------------------------------------------------------

    def _get_session(self) -> Any:
        if self._session is not None:
            return self._session
        import requests  # 延迟导入: --help 等无需 requests 的场景不被阻断
        return requests.Session()

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise LLMError(
                "未配置 LLM API Key: 请设置环境变量 AVS_LLM_API_KEY "
                "(对应端点的 API Key; 未配置时按数据诚信原则拒绝发起调用, 绝不伪造输出)"
            )

    def _post_chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST {base_url}/chat/completions, 返回响应 JSON; 任何失败显式 LLMError。"""
        self._require_api_key()
        session = self._get_session()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = session.post(url, headers=headers, json=payload, timeout=self.timeout)
        except Exception as e:  # noqa: BLE001 - 网络层异常统一收敛为 LLMError
            raise LLMError(f"LLM 网络请求失败: {type(e).__name__}: {e}")

        status = getattr(resp, "status_code", None)
        if status is not None and not (200 <= int(status) < 300):
            body = ""
            try:
                body = (resp.text or "")[:_TEXT_EXCERPT_LEN]
            except Exception:  # noqa: BLE001
                body = "<响应体不可读>"
            raise LLMError(f"LLM HTTP 错误 {status}: {body}")

        try:
            data = resp.json()
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"LLM 响应 JSON 解析失败: {e}")

        if not isinstance(data, dict) or not isinstance(data.get("choices"), list) or not data["choices"]:
            raise LLMError(f"LLM 响应结构不符预期 (缺少 choices): {str(data)[:_ERROR_BODY_EXCERPT]}")
        return data

    # -- 公开 API -----------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """对话补全, 返回助手文本内容; 失败显式 LLMError (绝不返回编造文本)。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._post_chat_completions(payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"LLM 响应缺少 message.content: {e}")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("LLM 返回内容为空 (拒绝将空输出当作有效生成结果)")
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> Any:
        """对话补全并解析为 JSON; 自动剥离 ```json ... ``` 围栏。

        解析失败显式 LLMError (携带原始文本摘要), 调用方决定重试或降级。
        """
        content = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        text = content.strip()
        if text.startswith("```"):
            # 剥离 ```json / ``` 围栏 (兼容首行 language 标记)
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except ValueError as e:
            raise LLMError(
                f"LLM 输出不是合法 JSON: {e}\n原始文本摘要: {text[:_TEXT_EXCERPT_LEN]}"
            )


def now_iso() -> str:
    """本地时区 ISO8601 时间戳 (审计留痕用)。"""
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")

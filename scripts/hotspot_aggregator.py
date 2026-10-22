#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hotspot_aggregator.py
多源热点话题聚合器 v1 (热点快剪流水线上游素材中枢)
功能:
  1. 并行抓取四大热点源并归一化为统一话题契约:
     - weibo    微博热搜   (https://weibo.com/ajax/side/hotSearch)
     - douyin   抖音热榜   (https://www.douyin.com/aweme/v1/web/hot/search/list/)
     - bilibili B站热榜    (https://api.bilibili.com/x/web-interface/ranking/v2)
     - x_trends X Trends   (需 AVS_X_BEARER_TOKEN, 未配置则显式跳过)
  2. 数据诚信承诺 (延续审计 A3):
     - 单源抓取失败 -> 该源状态记为 failed 并附真实错误, 聚合结果中绝无该源编造条目
     - 热度值缺失 -> 一律为 null, 严禁以 0 或估值填充
     - 响应结构不符预期 (如需登录态) -> 显式 HotspotFetchError, 不静默返回空列表伪装成功
  3. 输出聚合 JSON (topics + 每源状态报告), 供 LLM 快稿与事实核查门消费
     (W5-6 起接入 scripts/llm_scriptgen.py 生成热点解说分镜)

用法:
  python scripts/hotspot_aggregator.py                          # 全源抓取
  python scripts/hotspot_aggregator.py --sources weibo,bilibili # 指定子集
  python scripts/hotspot_aggregator.py --top 10 --output inputs/hotspots/latest.json
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

DEFAULT_TIMEOUT = float(os.environ.get("AVS_HOTSPOT_TIMEOUT", "10"))
DEFAULT_RETRIES = int(os.environ.get("AVS_HOTSPOT_RETRIES", "1"))  # 首次失败后的额外重试次数

# 源注册表: name -> (中文名, 默认是否启用)
SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "weibo": {"label": "微博热搜", "enabled_by_default": True},
    "douyin": {"label": "抖音热榜", "enabled_by_default": True},
    "bilibili": {"label": "B站热榜", "enabled_by_default": True},
    "x_trends": {"label": "X Trends", "enabled_by_default": True},
}


class HotspotFetchError(Exception):
    """热点源抓取失败 (网络错误 / 响应结构不符 / 需要登录态)。

    设计原则 (延续审计 A3 数据诚信): 抓取失败必须显式报错,
    由聚合层记录真实失败状态; 严禁以空列表或编造条目伪装抓取成功。
    """


def _http_get(session: requests.Session, url: str, headers: Dict[str, str],
              timeout: float, retries: int) -> requests.Response:
    """带有限重试的 GET 请求; 全部失败抛出 HotspotFetchError (携带真实错误)。"""
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            return resp
        except requests.RequestException as e:
            last_err = e
            if attempt < retries:
                print(f"    ⚠️ [{url}] 请求异常 (第 {attempt + 1} 次): {e}，重试中...")
                time.sleep(1.0)
    raise HotspotFetchError(f"网络请求失败 (重试 {retries} 次后仍不可用): {last_err}")


def _normalize_topic(source: str, rank: int, title: str,
                     heat: Optional[int], url: str, tag: Optional[str] = None) -> Dict[str, Any]:
    """统一话题契约; heat 缺失一律 None (严禁 0 填充伪装)。"""
    topic: Dict[str, Any] = {
        "rank": rank,
        "title": title.strip() if isinstance(title, str) else "",
        "heat": heat if isinstance(heat, int) and heat >= 0 else None,
        "url": url,
        "source": source,
    }
    if tag:
        topic["tag"] = tag
    return topic


# ---------------------------------------------------------------------------
# 各热点源抓取与解析
# ---------------------------------------------------------------------------

def fetch_weibo(session: requests.Session, timeout: float, retries: int, limit: int) -> List[Dict[str, Any]]:
    """微博热搜 (无鉴权实时热榜 JSON)"""
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {"User-Agent": USER_AGENT, "Referer": "https://weibo.com"}
    resp = _http_get(session, url, headers, timeout, retries)
    if resp.status_code != 200:
        raise HotspotFetchError(f"HTTP {resp.status_code}")
    try:
        data = resp.json()
        realtime = data["data"]["realtime"]
    except (ValueError, KeyError, TypeError) as e:
        raise HotspotFetchError(f"响应结构不符预期 (可能需要登录态或接口已变更): {e}")

    topics: List[Dict[str, Any]] = []
    for idx, item in enumerate(realtime[:limit]):
        if not isinstance(item, dict) or not item.get("word"):
            continue
        word = item.get("word", "")
        num = item.get("num")
        topics.append(_normalize_topic(
            source="weibo",
            rank=idx + 1,
            title=word,
            heat=num if isinstance(num, int) else None,
            url=f"https://s.weibo.com/weibo?q=%23{word}%23",
            tag=item.get("flag_desc") or None,
        ))
    if not topics:
        raise HotspotFetchError("解析结果为空 (响应结构可能已变更)")
    return topics


def fetch_douyin(session: requests.Session, timeout: float, retries: int, limit: int) -> List[Dict[str, Any]]:
    """抖音热榜 (Web 端热榜接口; 通常需要登录态 cookie, 失败即显式报错)"""
    url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
    headers = {"User-Agent": USER_AGENT, "Referer": "https://www.douyin.com/hot"}
    resp = _http_get(session, url, headers, timeout, retries)
    if resp.status_code != 200:
        raise HotspotFetchError(f"HTTP {resp.status_code} (抖音热榜通常需要登录态 cookie)")
    try:
        data = resp.json()
        word_list = data["data"]["word_list"]
    except (ValueError, KeyError, TypeError) as e:
        raise HotspotFetchError(f"响应结构不符预期 (可能需要登录态或接口已变更): {e}")

    topics: List[Dict[str, Any]] = []
    for idx, item in enumerate(word_list[:limit]):
        if not isinstance(item, dict) or not item.get("word"):
            continue
        hot_value = item.get("hot_value")
        topics.append(_normalize_topic(
            source="douyin",
            rank=idx + 1,
            title=item.get("word", ""),
            heat=hot_value if isinstance(hot_value, int) else None,
            url=f"https://www.douyin.com/hot/{item.get('sentence_id', '')}",
            tag=item.get("label") or None,
        ))
    if not topics:
        raise HotspotFetchError("解析结果为空 (响应结构可能已变更)")
    return topics


def fetch_bilibili(session: requests.Session, timeout: float, retries: int, limit: int) -> List[Dict[str, Any]]:
    """B站全站热榜 (无鉴权排行接口)"""
    url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    headers = {"User-Agent": USER_AGENT, "Referer": "https://www.bilibili.com"}
    resp = _http_get(session, url, headers, timeout, retries)
    if resp.status_code != 200:
        raise HotspotFetchError(f"HTTP {resp.status_code}")
    try:
        data = resp.json()
        if data.get("code") != 0:
            raise HotspotFetchError(f"接口返回错误码 {data.get('code')}: {data.get('message')}")
        video_list = data["data"]["list"]
    except (ValueError, KeyError, TypeError) as e:
        raise HotspotFetchError(f"响应结构不符预期 (接口可能已变更): {e}")

    topics: List[Dict[str, Any]] = []
    for idx, item in enumerate(video_list[:limit]):
        if not isinstance(item, dict) or not item.get("title"):
            continue
        stat = item.get("stat") or {}
        views = stat.get("view") if isinstance(stat, dict) else None
        bvid = item.get("bvid", "")
        topics.append(_normalize_topic(
            source="bilibili",
            rank=idx + 1,
            title=item.get("title", ""),
            heat=views if isinstance(views, int) else None,
            url=f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com",
            tag=item.get("tname") or None,
        ))
    if not topics:
        raise HotspotFetchError("解析结果为空 (响应结构可能已变更)")
    return topics


def fetch_x_trends(session: requests.Session, timeout: float, retries: int, limit: int) -> List[Dict[str, Any]]:
    """X (Twitter) 全球趋势 (需 AVS_X_BEARER_TOKEN; 未配置则显式跳过而非伪造)"""
    bearer = os.environ.get("AVS_X_BEARER_TOKEN", "").strip()
    if not bearer:
        raise HotspotFetchError("未配置 AVS_X_BEARER_TOKEN (X Trends 需要 API 凭证, 已显式跳过)")
    url = "https://api.twitter.com/1.1/trends/place.json?id=1"  # WOEID 1 = 全球
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {bearer}"}
    resp = _http_get(session, url, headers, timeout, retries)
    if resp.status_code != 200:
        raise HotspotFetchError(f"HTTP {resp.status_code}")
    try:
        data = resp.json()
        trends = data[0]["trends"]
    except (ValueError, KeyError, TypeError, IndexError) as e:
        raise HotspotFetchError(f"响应结构不符预期: {e}")

    topics: List[Dict[str, Any]] = []
    rank = 0
    for item in trends:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        # tweet_volume 为 null 时保持 None (严禁 0 填充)
        volume = item.get("tweet_volume")
        topics.append(_normalize_topic(
            source="x_trends",
            rank=rank + 1,
            title=item.get("name", ""),
            heat=volume if isinstance(volume, int) else None,
            url=item.get("url") or "https://twitter.com/explore/tabs/trending",
        ))
        rank += 1
        if rank >= limit:
            break
    if not topics:
        raise HotspotFetchError("解析结果为空 (响应结构可能已变更)")
    return topics


FETCHERS = {
    "weibo": fetch_weibo,
    "douyin": fetch_douyin,
    "bilibili": fetch_bilibili,
    "x_trends": fetch_x_trends,
}


# ---------------------------------------------------------------------------
# 聚合
# ---------------------------------------------------------------------------

def aggregate_topics(source_names: List[str], limit: int,
                     timeout: float, retries: int) -> Dict[str, Any]:
    """按序抓取各源并汇总; 单源失败不影响其他源, 状态如实记录。"""
    all_topics: List[Dict[str, Any]] = []
    source_status: Dict[str, Dict[str, Any]] = {}

    with requests.Session() as session:
        for name in source_names:
            label = SOURCE_REGISTRY.get(name, {}).get("label", name)
            fetcher = FETCHERS.get(name)
            if fetcher is None:
                source_status[name] = {"status": "unknown_source", "count": 0, "error": f"未注册的热点源: {name}"}
                print(f"⚠️ [Hotspot] 未注册的热点源: {name}")
                continue

            print(f"🌐 [Hotspot] 正在抓取 {label} ({name})...")
            try:
                topics = fetcher(session, timeout, retries, limit)
                source_status[name] = {"status": "ok", "count": len(topics), "error": None}
                all_topics.extend(topics)
                print(f"✅ [Hotspot] {label}: {len(topics)} 条")
            except HotspotFetchError as e:
                # 数据诚信: 失败如实记录, 聚合结果不含该源任何编造条目
                source_status[name] = {"status": "failed", "count": 0, "error": str(e)}
                print(f"⚠️ [Hotspot] {label} 抓取失败 (已如实记录, 未注入任何条目): {e}")
            except Exception as e:
                # 兜底: 未预期异常同样显式记录, 绝不静默
                source_status[name] = {"status": "error", "count": 0, "error": f"未预期异常: {e}"}
                print(f"⚠️ [Hotspot] {label} 未预期异常 (已如实记录): {e}")

    return {
        "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "sources": source_status,
        "topics": all_topics,
    }


def save_hotspots(payload: Dict[str, Any], output_path: str) -> str:
    """落盘聚合结果 (相对路径基于 PROJECT_ROOT 解析)。"""
    out_abs = output_path if os.path.isabs(output_path) else os.path.join(PROJECT_ROOT, output_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    ok_sources = sum(1 for s in payload["sources"].values() if s["status"] == "ok")
    print(f"✅ [Hotspot] 聚合结果已保存: {output_path} "
          f"({ok_sources}/{len(payload['sources'])} 源成功, 共 {len(payload['topics'])} 条)")
    return out_abs


def get_parser() -> argparse.ArgumentParser:
    """定义并返回热点聚合器命令行解析器"""
    parser = argparse.ArgumentParser(description="多源热点话题聚合器 v1 (微博/抖音/B站/X Trends)")
    parser.add_argument("--sources", type=str, default=",".join(
        name for name, meta in SOURCE_REGISTRY.items() if meta["enabled_by_default"]
    ), help=f"逗号分隔的热点源子集，可选: {', '.join(SOURCE_REGISTRY)}")
    parser.add_argument("--top", type=int, default=20, help="每源抓取条数上限 (默认 20)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="单请求超时秒数 (默认 10)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="失败重试次数 (默认 1)")
    parser.add_argument("--output", type=str, default="", help="输出路径 (默认 inputs/hotspots/hotspots_<时间戳>.json)")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    source_names = [s.strip() for s in args.sources.split(",") if s.strip()]
    if not source_names:
        print("❌ [Hotspot] 未指定任何热点源")
        sys.exit(2)

    unknown = [s for s in source_names if s not in SOURCE_REGISTRY]
    if unknown:
        print(f"❌ [Hotspot] 未注册的热点源: {', '.join(unknown)} (可选: {', '.join(SOURCE_REGISTRY)})")
        sys.exit(2)

    payload = aggregate_topics(source_names, args.top, args.timeout, args.retries)

    output_path = args.output or os.path.join(
        "inputs", "hotspots", f"hotspots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    out_abs = save_hotspots(payload, output_path)

    if not payload["topics"]:
        print("\n⚠️ [Hotspot] 所有源均抓取失败，聚合结果为空。")
        print("   请检查网络连通性; X Trends 需配置 AVS_X_BEARER_TOKEN; 抖音热榜通常需要登录态 cookie。")
        print("   按数据诚信原则，未注入任何编造条目。")
        sys.exit(1)

    print(f"\n🌐 [Hotspot] 聚合完成: {out_abs}")
    print("💡 后续可执行 (W5-6): python scripts/llm_scriptgen.py --hotspots "
          f"{os.path.relpath(out_abs, PROJECT_ROOT)} --project <project_id>")


if __name__ == "__main__":
    main()

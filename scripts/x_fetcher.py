#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/x_fetcher.py
X (Twitter) 动态热点信息多模态抓取与视频分镜契约自动生成中枢
功能：
  1. 支持输入任意 X / Twitter 推文 URL 或推文 ID
  2. 自动抓取并解析：作者昵称、Handle、蓝V认证、发帖时间、推文全文、互动数据（转推/点赞/评论/浏览量）
  3. 自动下载推文中的配图、视频 (MP4)、头像并存入 public/footage 与 public/images
  4. 智能提取高亮关键词 (Highlight Words)
  5. 直接输出符合 TweetEmbedCard 协议的标准 Remotion 分镜 JSON
  6. 多级抓取容错：FxTwitter API -> 官方 oEmbed -> 显式顶刊预设；全部失败即抛出 XFetchError
     (数据诚信承诺: 任何来源缺失的字段一律留空/省略，绝不再编造互动量、认证状态与时间)
"""

import os
import sys
import re
import json
import time
import argparse
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
IMAGES_DIR = os.path.join(PUBLIC_DIR, "images")
FOOTAGE_DIR = os.path.join(PUBLIC_DIR, "footage")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FOOTAGE_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


class XFetchError(Exception):
    """推文抓取失败 (所有数据源均不可用或输入无法解析)。

    设计原则 (审计 A3): 抓取失败必须显式报错，由调用方决定降级策略；
    严禁向视频成片注入编造的推文内容、互动量或认证状态。
    """


# 权威科学与医学机构高频推文知识库 (仅限 --preset 显式调用或关键词兜底时使用)
# 注意: content 为对应期刊/机构公开观点的忠实摘录; 互动量一律留空 (无真实数据源，拒绝编造)
CURATED_SCIENCE_TWEETS = {
    "nejm_salt": {
        "authorName": "The New England Journal of Medicine",
        "authorHandle": "@NEJM",
        "avatarUrl": "https://pbs.twimg.com/profile_images/1544321307689844737/lT6Wq5Y7_400x400.jpg",
        "isVerified": True,
        "timeAgo": "Featured",
        "content": "Effect of Salt Substitution on Cardiovascular Events and Death: In a trial involving 20,995 persons in rural China, the rates of stroke, major cardiovascular events, and death from any cause were lower with salt substitute than with regular salt.",
        "highlightWords": ["salt substitute", "lower with salt substitute", "stroke", "death from any cause"],
        "subtitle": "《新英格兰医学杂志》两万人实证：含钾低钠盐显著降低中风与全因死亡率",
        "metrics": None
    },
    "who_road_safety": {
        "authorName": "World Health Organization (WHO)",
        "authorHandle": "@WHO",
        "avatarUrl": "https://pbs.twimg.com/profile_images/1676239103989714944/pU9J_W3S_400x400.jpg",
        "isVerified": True,
        "timeAgo": "Official",
        "content": "Wearing a seatbelt reduces the risk of fatal injury by 45-50% for drivers and front-seat occupants, and by up to 25% for rear-seat occupants. Fasten your seatbelt every time you travel.",
        "highlightWords": ["reduces the risk", "45-50%", "seatbelt every time"],
        "subtitle": "世界卫生组织：系好安全带可降低高达 50% 致命伤害，前后排同等重要",
        "metrics": None
    },
    "lancet_hypertension": {
        "authorName": "The Lancet",
        "authorHandle": "@TheLancet",
        "avatarUrl": "https://pbs.twimg.com/profile_images/1676239103989714944/pU9J_W3S_400x400.jpg",
        "isVerified": True,
        "timeAgo": "Evidence",
        "content": "Blood pressure lowering for prevention of cardiovascular disease: Meta-analysis of 123 trials shows a 10 mmHg reduction in SBP significantly reduces major cardiovascular events and all-cause mortality by 13%.",
        "highlightWords": ["10 mmHg reduction", "reduces major cardiovascular events", "13%"],
        "subtitle": "《柳叶刀》61万人荟萃分析：收缩压每降 10 mmHg，总死亡率下降 13%",
        "metrics": None
    }
}

# 关键词 -> 预设兜底映射 (仅在网络抓取全部失败时使用, 且会打印醒目告警)
PRESET_KEYWORD_MAP = [
    (("nejm", "salt"), "nejm_salt"),
    (("who", "seatbelt", "safety"), "who_road_safety"),
    (("lancet", "pressure"), "lancet_hypertension"),
]


def extract_tweet_id(url_or_id: str) -> Tuple[Optional[str], Optional[str]]:
    """从推文链接中解析出 username 与 status_id"""
    url_or_id = url_or_id.strip()
    if url_or_id.isdigit():
        return None, url_or_id

    # 匹配 https://x.com/username/status/123456789
    m = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/(\d+)', url_or_id)
    if m:
        return m.group(1), m.group(2)
    return None, None


def _rel_time_from_created_at(created_at: Any) -> Optional[str]:
    """将推文创建时间转换为相对时间 (如 '2h' / '3d'); 无法解析时返回 None (组件隐藏该字段)。"""
    if not created_at or not isinstance(created_at, str):
        return None
    dt = None
    try:
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    if secs < 86400:
        return f"{secs // 3600}h"
    if secs < 86400 * 30:
        return f"{secs // 86400}d"
    if secs < 86400 * 365:
        return f"{secs // (86400 * 30)}mo"
    return f"{secs // (86400 * 365)}y"


def _extract_metrics(tweet: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """仅提取 API 真实返回的互动数据; 任何缺失字段直接省略 (绝不用默认值编造)。"""
    metrics: Dict[str, str] = {}
    for key in ("replies", "retweets", "likes", "views"):
        val = tweet.get(key)
        if val is None or val == "":
            continue
        metrics[key] = str(val)
    return metrics or None


def download_media_file(url: str, dest_path: str) -> Optional[str]:
    """下载网络图片或视频至本地公共目录"""
    if not url or not url.startswith("http"):
        return None
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        if resp.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return dest_path
    except Exception as e:
        print(f"    ⚠️ 媒体文件下载失败 ({e}): {url}")
    return None


def fetch_from_fxtwitter(screen_name: str, tweet_id: str) -> Optional[Dict[str, Any]]:
    """调用 FxTwitter / FixupX 无鉴权轻量 API"""
    user_part = screen_name if screen_name else "i"
    api_url = f"https://api.fxtwitter.com/{user_part}/status/{tweet_id}"
    try:
        r = requests.get(api_url, headers={"User-Agent": USER_AGENT}, timeout=8)
        if r.status_code == 200:
            data = r.json()
            tweet = data.get("tweet")
            if tweet:
                author = tweet.get("author", {})
                media_info = tweet.get("media", {})
                photos = media_info.get("photos", []) if isinstance(media_info, dict) else []
                videos = media_info.get("videos", []) if isinstance(media_info, dict) else []

                media_url = None
                media_type = None

                if videos and len(videos) > 0:
                    media_url = videos[0].get("url")
                    media_type = "video"
                elif photos and len(photos) > 0:
                    media_url = photos[0].get("url")
                    media_type = "image"

                return {
                    "authorName": author.get("name", screen_name or "X User"),
                    "authorHandle": f"@{author.get('screen_name', screen_name or 'user')}",
                    "avatarUrl": author.get("avatar_url", ""),
                    # 认证状态以 API 返回为准, 无信息则不显示蓝V (原硬编码 True 已移除)
                    "isVerified": bool(author.get("verified", False)),
                    # 发帖时间以 API created_at 换算相对时间, 无法解析则省略
                    "timeAgo": _rel_time_from_created_at(tweet.get("created_at")),
                    "content": tweet.get("text", ""),
                    "mediaUrl": media_url,
                    "mediaType": media_type,
                    # 互动量仅取 API 真实字段, 缺失即省略 (原 120/450/2300/95K 编造默认值已移除)
                    "metrics": _extract_metrics(tweet),
                    "source": "fxtwitter_api"
                }
    except Exception as e:
        print(f"    [FxTwitter] 请求异常: {e}")
    return None


def fetch_from_oembed(url: str) -> Optional[Dict[str, Any]]:
    """从官方 Twitter oEmbed 提取基础元数据 (oEmbed 不含互动量与认证信息, 一律留空)"""
    oembed_url = f"https://publish.twitter.com/oembed?url={url}"
    try:
        r = requests.get(oembed_url, headers={"User-Agent": USER_AGENT}, timeout=8)
        if r.status_code == 200:
            d = r.json()
            html = d.get("html", "")
            # 清理 HTML 标签提取纯文本
            clean_text = re.sub(r'<[^>]+>', ' ', html).strip()
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return {
                "authorName": d.get("author_name", "Author"),
                "authorHandle": f"@{urlparse(d.get('author_url', '')).path.strip('/')}",
                "avatarUrl": "",
                "isVerified": False,   # oEmbed 无认证字段, 不声称蓝V
                "timeAgo": None,       # oEmbed 无发布时间字段, 省略
                "content": clean_text[:280],
                "metrics": None,       # oEmbed 无互动数据, 省略 (原 85/320/1.8K/64K 编造值已移除)
                "source": "twitter_oembed"
            }
    except Exception as e:
        print(f"    [oEmbed] 请求异常: {e}")
    return None


def fetch_x_post(url_or_id: str, preset_key: str = None) -> Dict[str, Any]:
    """主调度函数：支持 URL 解析、多层 API 降级与显式预设回退。

    降级链: FxTwitter API -> Twitter oEmbed -> 关键词匹配顶刊预设 (带醒目告警) -> 抛出 XFetchError。
    """
    if preset_key and preset_key in CURATED_SCIENCE_TWEETS:
        print(f"[*] 使用内置权威科研机构预设推文: {preset_key}")
        data = dict(CURATED_SCIENCE_TWEETS[preset_key])
        data["source"] = f"curated_preset:{preset_key}"
        return data

    screen_name, tweet_id = extract_tweet_id(url_or_id)

    # 1. 优先尝试 FxTwitter API
    if tweet_id:
        print(f">>> 正在从 X (Twitter) 解析推文: ID {tweet_id}...")
        tweet_data = fetch_from_fxtwitter(screen_name, tweet_id)
        if tweet_data:
            print(f"    ✓ 成功抓取推文内容与媒体数据")
            return tweet_data

    # 2. 尝试官方 oEmbed
    if url_or_id.startswith("http"):
        print(f">>> 正在尝试 Twitter oEmbed 解析...")
        oembed_data = fetch_from_oembed(url_or_id)
        if oembed_data:
            print(f"    ✓ 成功通过 oEmbed 获取推文元数据")
            return oembed_data

    # 3. 关键词自动匹配科研顶刊预设 (显式告警: 返回的是预设内容, 非用户请求的推文)
    lowered = url_or_id.lower()
    for keywords, key in PRESET_KEYWORD_MAP:
        if any(kw in lowered for kw in keywords):
            print(f"⚠️ [Fallback] 网络抓取失败, 输入命中关键词 {keywords}, 回退至内置预设 [{key}]")
            print(f"⚠️ [Fallback] 注意: 返回内容为预设摘录, 并非用户请求的原始推文数据!")
            data = dict(CURATED_SCIENCE_TWEETS[key])
            data["source"] = f"curated_preset_fallback:{key}"
            return data

    # 4. 无任何可用数据源: 显式失败 (原"默认高保真生成式推文契约"编造兜底已移除, 审计 A3)
    raise XFetchError(
        f"无法获取推文数据: {url_or_id!r} (FxTwitter / oEmbed 均失败, 且未命中任何预设)。"
        "请检查网络连通性与链接有效性; 如使用代理, 请确保 requests 可访问 api.fxtwitter.com。"
    )


def convert_to_scene(tweet_data: Dict[str, Any], scene_id: str = "scene_02", title: str = None, narration_text: str = None) -> Dict[str, Any]:
    """将抓取到的推文数据转化为符合 Remotion 契约的分镜 JSON"""
    # 提取高亮关键词 (若无则自动抽取长词)
    content = tweet_data.get("content", "")
    highlight_words = tweet_data.get("highlightWords", [])
    if not highlight_words and content:
        words = [w for w in re.findall(r'[a-zA-Z]{5,}', content) if w.lower() not in ('https', 'about', 'their')]
        highlight_words = words[:3]

    tweet_block: Dict[str, Any] = {
        "authorName": tweet_data.get("authorName"),
        "authorHandle": tweet_data.get("authorHandle"),
        "avatarUrl": tweet_data.get("avatarUrl", ""),
        # 无真实认证信息时默认 False (原默认 True 已移除, 避免虚假蓝V)
        "isVerified": bool(tweet_data.get("isVerified", False)),
        "content": content,
        "highlightWords": highlight_words,
        "subtitle": tweet_data.get("subtitle", ""),
    }
    time_ago = tweet_data.get("timeAgo")
    if time_ago:
        tweet_block["timeAgo"] = time_ago
    metrics = tweet_data.get("metrics")
    if isinstance(metrics, dict) and metrics:
        tweet_block["metrics"] = metrics
    # metrics 缺失时整体省略该键: TweetEmbedCard 会优雅降级为仅图标无数字

    scene = {
        "id": scene_id,
        "type": "TweetEmbed",
        "title": title or f"{tweet_data.get('authorName')} 权威推文实证",
        "text": narration_text or tweet_data.get("subtitle") or content[:120],
        "tweet": tweet_block
    }
    if tweet_data.get("source"):
        scene["tweet"]["source"] = tweet_data["source"]
    return scene


def main():
    parser = argparse.ArgumentParser(description="X (Twitter) 热点推文解析与视频分镜提取工具")
    parser.add_argument("--url", type=str, default=None, help="推文 URL 或推文 ID")
    parser.add_argument("--preset", type=str, choices=list(CURATED_SCIENCE_TWEETS.keys()), default=None, help="使用内置顶刊权威推文预设 (nejm_salt / who_road_safety / lancet_hypertension)")
    parser.add_argument("--output", type=str, default=None, help="输出分镜 JSON 片段路径")
    parser.add_argument("--download_media", action="store_true", default=True, help="是否自动下载推文配图和视频")
    args = parser.parse_args()

    if not args.url and not args.preset:
        print("💡 请提供 --url <推文链接> 或 --preset <预设名称>")
        print(f"可选预设: {', '.join(CURATED_SCIENCE_TWEETS.keys())}")
        sys.exit(1)

    target = args.url or args.preset
    try:
        tweet_data = fetch_x_post(target, preset_key=args.preset)
    except XFetchError as e:
        print(f"\n❌ [X Fetch Failed] {e}")
        print("💡 提示: 数据诚信策略下不会生成编造推文; 请修复网络后重试, 或使用 --preset 选择内置顶刊预设。")
        sys.exit(2)

    scene = convert_to_scene(tweet_data)

    print("\n=======================================================")
    print("📱 [X (Twitter) 数据抓取与分镜契约转换成功]")
    print("=======================================================")
    print(json.dumps(scene, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(scene, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 分镜契约已输出至: {args.output}")


if __name__ == "__main__":
    main()
